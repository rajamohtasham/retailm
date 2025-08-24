from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.utils.encoding import smart_str
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO

from .models import (
    Branch, CustomUser, Sale, SaleItem, Product, Vendor,
    StockMovement, AuditLog, LedgerEntry
)

# ---------- EXPORT HELPERS ----------

def export_as_excel(queryset, fields, filename):
    data = queryset.values(*fields)
    df = pd.DataFrame(list(data))
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    df.to_excel(response, index=False)
    return response

def export_as_pdf(queryset, fields, filename):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    y = 800
    for obj in queryset.values(*fields):
        line = ", ".join([f"{k}: {v}" for k, v in obj.items()])
        p.drawString(50, y, smart_str(line))
        y -= 20
        if y <= 50:  # new page if needed
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response

# ---------- BASE ADMIN WITH EXPORT ----------

class ExportAdmin(admin.ModelAdmin):
    export_fields = []  # override in child classes
    export_filename = "data"

    actions = ["export_excel", "export_pdf"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Branch filtering
        if not request.user.is_superuser and hasattr(request.user, "branch"):
            return qs.filter(branch=request.user.branch)
        return qs

    def export_excel(self, request, queryset):
        return export_as_excel(queryset, self.export_fields, self.export_filename)
    export_excel.short_description = "Export selected as Excel"

    def export_pdf(self, request, queryset):
        return export_as_pdf(queryset, self.export_fields, self.export_filename)
    export_pdf.short_description = "Export selected as PDF"

# ---------- MODEL ADMINS ----------

@admin.register(Branch)
class BranchAdmin(ExportAdmin):
    list_display = ("id", "name", "location")
    search_fields = ("name", "location")
    export_fields = ["id", "name", "location"]
    export_filename = "branches"


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, ExportAdmin):
    list_display = ("username", "email", "role", "branch", "phone", "is_staff", "is_superuser")
    list_filter = ("role", "branch", "is_staff", "is_superuser")
    search_fields = ("username", "email", "phone")
    ordering = ("username",)

    export_fields = ["id", "username", "email", "role", "branch__name", "phone", "is_staff", "is_superuser"]
    export_filename = "users"

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "phone")}),
        (_("Role & Branch"), {"fields": ("role", "branch")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "phone", "role", "branch", "password1", "password2"),
        }),
    )


@admin.register(Product)
class ProductAdmin(ExportAdmin):
    list_display = ("id", "name", "sku", "price", "quantity", "branch")
    search_fields = ("name", "sku")
    list_filter = ("branch",)
    export_fields = ["id", "name", "sku", "price", "quantity", "branch__name"]
    export_filename = "products"


@admin.register(Sale)
class SaleAdmin(ExportAdmin):
    list_display = ("id", "invoice_no", "branch", "created_by", "total_amount", "created_at")
    search_fields = ("invoice_no", "created_by__username")
    list_filter = ("branch", "created_at")
    export_fields = ["id", "invoice_no", "branch__name", "created_by__username", "total_amount", "created_at"]
    export_filename = "sales"


@admin.register(SaleItem)
class SaleItemAdmin(ExportAdmin):
    list_display = ("id", "sale", "product", "quantity", "unit_price", "total_price")
    list_filter = ("product", "sale__branch")
    export_fields = ["id", "sale__id", "product__name", "quantity", "unit_price", "total_price"]
    export_filename = "sale_items"


@admin.register(Vendor)
class VendorAdmin(ExportAdmin):
    list_display = ("id", "name", "contact_person", "email", "phone")
    search_fields = ("name", "contact_person", "email", "phone")
    export_fields = ["id", "name", "contact_person", "email", "phone"]
    export_filename = "vendors"


@admin.register(StockMovement)
class StockMovementAdmin(ExportAdmin):
    list_display = ("id", "product", "quantity", "movement_type", "branch", "created_at")
    list_filter = ("movement_type", "branch")
    export_fields = ["id", "product__name", "quantity", "movement_type", "branch__name", "created_at"]
    export_filename = "stock_movements"


@admin.register(AuditLog)
class AuditLogAdmin(ExportAdmin):
    list_display = ("id", "action", "user", "timestamp")
    search_fields = ("action", "user__username")
    list_filter = ("timestamp",)
    export_fields = ["id", "action", "user__username", "timestamp"]
    export_filename = "audit_logs"


@admin.register(LedgerEntry)
class LedgerEntryAdmin(ExportAdmin):
    list_display = ("id", "branch", "description", "amount", "date")
    list_filter = ("branch", "date")
    search_fields = ("description",)
    export_fields = ["id", "branch__name", "description", "amount", "date"]
    export_filename = "ledger_entries"
