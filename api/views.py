from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.mail import send_mail
from django.http import HttpResponse
from django.db.models import F, Sum
from django.db.models.functions import TruncDate
import io
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas

from .models import (
    Branch,
    Product,
    Vendor,
    Purchase,
    PurchaseItem,
    Sale,
    SaleItem,
    LedgerEntry,
    StockMovement,
    AuditLog,
    CustomUser,
)
from .serializers import (
    BranchSerializer,
    ProductSerializer,
    VendorSerializer,
    PurchaseSerializer,
    PurchaseItemSerializer,
    SaleSerializer,
    SaleItemSerializer,
    LedgerEntrySerializer,
    StockMovementSerializer,
    AuditLogSerializer,
    UserSerializer,
)
from .permissions import IsAdminOrManager, ReadOnly, IsStaff, IsAdminOrReadOnly


# ---------- BRANCH ----------
class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | ReadOnly)]


# ---------- PRODUCT ----------
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | ReadOnly)]

    def get_queryset(self):
        qs = super().get_queryset().select_related("branch")
        user = self.request.user
        if getattr(user, "role", None) != "admin" and user.branch_id:
            return qs.filter(branch_id=user.branch_id)
        return qs

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        low_stock_qs = self.get_queryset().filter(quantity__lte=F("reorder_level"))
        serializer = self.get_serializer(low_stock_qs, many=True, context={"request": request})
        return Response(serializer.data)



# ---------- VENDOR ----------
class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated & IsAdminOrReadOnly]


# ---------- PURCHASE ----------
class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | IsStaff)]

    def get_queryset(self):
        qs = super().get_queryset().select_related("vendor", "branch", "created_by").prefetch_related("items")
        user = self.request.user
        if getattr(user, "role", None) != "admin" and user.branch_id:
            return qs.filter(branch_id=user.branch_id)
        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        purchase = serializer.save(created_by=self.request.user)
        for pi in purchase.items.all():
            if pi.product:
                StockMovement.objects.create(
                    product=pi.product,
                    quantity=pi.quantity,
                    movement_type="in",
                    branch=purchase.branch,
                    created_by=self.request.user,
                    reference=f"PUR-{purchase.invoice_no}",
                )
        send_mail(
            subject=f"New Purchase Recorded (Invoice {purchase.invoice_no})",
            message=f"A new purchase from {getattr(purchase.vendor, 'name', 'Unknown Vendor')} was recorded.",
            from_email="noreply@retailm.com",
            recipient_list=["admin@retailm.com"],
            fail_silently=True,
        )


# ---------- PURCHASE ITEMS ----------
class PurchaseItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseItem.objects.all()
    serializer_class = PurchaseItemSerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | IsStaff)]


# ---------- SALE ----------
class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | IsStaff)]

    def get_queryset(self):
        qs = super().get_queryset().select_related("branch", "created_by").prefetch_related("items__product")
        user = self.request.user
        if getattr(user, "role", None) != "admin" and user.branch_id:
            return qs.filter(branch_id=user.branch_id)
        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        sale = serializer.save(created_by=self.request.user)
        for si in sale.items.all():
            if si.product:
                StockMovement.objects.create(
                    product=si.product,
                    quantity=si.quantity,
                    movement_type="out",
                    branch=sale.branch,
                    created_by=self.request.user,
                    reference=f"SALE-{sale.invoice_no}",
                )
        send_mail(
            subject=f"New Sale Recorded (Invoice {sale.invoice_no})",
            message=f"A new sale for {sale.customer_name or 'Walk-in Customer'} was recorded.",
            from_email="noreply@retailm.com",
            recipient_list=["admin@retailm.com"],
            fail_silently=True,
        )

    @action(detail=False, methods=["get"], url_path="daily-report")
    def daily_report(self, request):
        qs = (
            self.get_queryset()
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("total_amount"))
            .order_by("-day")
        )
        return Response(list(qs))


# ---------- SALE ITEMS ----------
class SaleItemViewSet(viewsets.ModelViewSet):
    queryset = SaleItem.objects.all()
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | IsStaff)]


# ---------- LEDGER ----------
class LedgerEntryViewSet(viewsets.ModelViewSet):
    queryset = LedgerEntry.objects.all()
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | ReadOnly)]


# ---------- STOCK MOVEMENT ----------
class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated & IsAdminOrManager]


# ---------- AUDIT LOG ----------
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated & IsAdminOrManager]


# ---------- USER ----------
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & (IsAdminOrManager | ReadOnly)]






class ReportViewSet(viewsets.ViewSet):
    """
    API endpoints for exporting reports (Excel/PDF).
    """

    @action(detail=False, methods=["get"])
    def sales_excel(self, request):
        qs = Sale.objects.all().values()
        df = pd.DataFrame(qs)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Sales")
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="sales_report.xlsx"'
        return response

    @action(detail=False, methods=["get"])
    def ledger_pdf(self, request):
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        y = 800
        for entry in LedgerEntry.objects.all():
            p.drawString(50, y, f"{entry.date} - {entry.description} - {entry.amount}")
            y -= 20
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="ledger_report.pdf"'
        return response
