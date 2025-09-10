import json
from decimal import Decimal
from rest_framework import serializers
from .models import (
    Branch,
    Product,
    Vendor,
    Sale,
    SaleItem,
    LedgerEntry,
    StockMovement,
    AuditLog,
    CustomUser,
    Purchase,
    PurchaseItem,
)


# ---------------------- BRANCH ----------------------
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "location", "phone", "email", "created_at", "updated_at"]


# ---------------------- PRODUCT ----------------------
class ProductSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), source="branch", write_only=True, required=False
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "barcode",
            "description",
            "price",
            "cost_price",
            "quantity",
            "reorder_level",
            "expiry_date",
            "branch",
            "branch_id",
            "image",
            "image_url",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ---------------------- VENDOR ----------------------
class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "gst_number",
            "notes",
            "created_at",
            "updated_at",
        ]


# ---------------------- PURCHASES ----------------------
class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ["id", "product", "product_name", "quantity", "unit_cost", "total_price"]
        read_only_fields = ["total_price", "product_name"]


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Purchase
        fields = [
            "id",
            "invoice_no",
            "vendor",
            "vendor_name",
            "branch",
            "branch_name",
            "subtotal",
            "discount",
            "total_amount",
            "paid_amount",
            "payment_method",
            "created_by_name",
            "created_at",
            "notes",
            "items",
        ]
        read_only_fields = ["subtotal", "total_amount", "created_at"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one purchase item is required.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        validated_data.pop("created_by", None)  # ✅ prevent duplicate
        user = self.context["request"].user
        purchase = Purchase.objects.create(created_by=user, **validated_data)

        total_amount = Decimal("0.00")
        for item_data in items_data:
            purchase_item = PurchaseItem.objects.create(
                purchase=purchase,
                product=item_data["product"],
                quantity=item_data["quantity"],
                unit_cost=item_data["unit_cost"],
            )
            total_amount += purchase_item.total_price

            # Stock Movement (IN)
            StockMovement.objects.create(
                product=purchase_item.product,
                branch=purchase.branch,
                movement_type="IN",
                quantity=purchase_item.quantity,
                reference=f"PUR-{purchase.invoice_no}",
                created_by=user,
            )

        purchase.calculate_totals()

        # Ledger Entry (Debit)
        LedgerEntry.objects.create(
            date=purchase.created_at.date(),
            description=f"Purchase Invoice {purchase.invoice_no}",
            transaction_type="Debit",
            amount=total_amount,
            reference=f"PUR-{purchase.invoice_no}",
            branch=purchase.branch,
            created_by=user,
        )

        # Audit Log
        AuditLog.objects.create(
            user=user,
            action="CREATE",
            model_name="Purchase",
            object_id=purchase.id,
            changes=json.dumps({"invoice_no": purchase.invoice_no, "items": len(items_data)}),
            ip_address=self.context["request"].META.get("REMOTE_ADDR"),
        )
        return purchase


# ---------------------- SALES ----------------------
class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "total_price"]
        read_only_fields = ["total_price", "product_name"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "invoice_no",
            "customer_name",
            "customer_phone",
            "branch",
            "branch_name",
            "subtotal",
            "discount",
            "total_amount",
            "paid_amount",
            "payment_method",
            "created_by_name",
            "created_at",
            "notes",
            "items",
        ]
        read_only_fields = ["subtotal", "total_amount", "created_at"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one sale item is required.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        validated_data.pop("created_by", None)  # ✅ prevent duplicate
        user = self.context["request"].user
        sale = Sale.objects.create(created_by=user, **validated_data)

        total_amount = Decimal("0.00")
        for item_data in items_data:
            product = item_data["product"]
            quantity = item_data["quantity"]
            unit_price = item_data["unit_price"]

            if product.quantity < quantity:
                raise serializers.ValidationError(f"Not enough stock for {product.name}")

            sale_item = SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
            )
            total_amount += sale_item.total_price

            # Stock Movement (OUT)
            StockMovement.objects.create(
                product=product,
                branch=sale.branch,
                movement_type="OUT",
                quantity=quantity,
                reference=f"SAL-{sale.invoice_no}",
                created_by=user,
            )

        sale.calculate_totals()

        # Ledger Entry (Credit)
        LedgerEntry.objects.create(
            date=sale.created_at.date(),
            description=f"Sale Invoice {sale.invoice_no}",
            transaction_type="Credit",
            amount=total_amount,
            reference=f"SAL-{sale.invoice_no}",
            branch=sale.branch,
            created_by=user,
        )

        # Audit Log
        AuditLog.objects.create(
            user=user,
            action="CREATE",
            model_name="Sale",
            object_id=sale.id,
            changes=json.dumps({"invoice_no": sale.invoice_no, "items": len(items_data)}),
            ip_address=self.context["request"].META.get("REMOTE_ADDR"),
        )
        return sale


# ---------------------- LEDGER ----------------------
class LedgerEntrySerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "date",
            "description",
            "transaction_type",
            "amount",
            "reference",
            "branch",
            "branch_name",
            "created_by",
            "created_by_name",
        ]


# ---------------------- STOCK ----------------------
class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "movement_type",
            "branch",
            "branch_name",
            "reference",
            "created_by",
            "created_by_name",
            "note",
            "created_at",
        ]


# ---------------------- AUDIT ----------------------
class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    changes = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "model_name",
            "object_id",
            "changes",
            "ip_address",
            "timestamp",
        ]

    def get_changes(self, obj):
        try:
            return json.loads(obj.changes) if obj.changes else None
        except json.JSONDecodeError:
            return obj.changes


# ---------------------- USER ----------------------
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "branch",
            "branch_name",
            "phone",
            "password",
            "is_staff",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["is_staff", "is_active", "date_joined"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
