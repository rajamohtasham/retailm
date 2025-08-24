from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    BranchViewSet,
    UserViewSet,
    SaleViewSet,
    SaleItemViewSet,
    PurchaseViewSet,
    PurchaseItemViewSet,
    ProductViewSet,
    VendorViewSet,
    StockMovementViewSet,
    AuditLogViewSet,
    LedgerEntryViewSet,
    ReportViewSet,
)

# Create DRF Router
router = DefaultRouter()

# Core Resources
router.register(r"branches", BranchViewSet, basename="branch")
router.register(r"users", UserViewSet, basename="user")

# Sales + Purchases
router.register(r"sales", SaleViewSet, basename="sale")
router.register(r"sale-items", SaleItemViewSet, basename="saleitem")
router.register(r"purchases", PurchaseViewSet, basename="purchase")
router.register(r"purchase-items", PurchaseItemViewSet, basename="purchaseitem")

# Inventory & Vendors
router.register(r"products", ProductViewSet, basename="product")
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"stock-movements", StockMovementViewSet, basename="stockmovement")

# Ledger & Audit Logs
router.register(r"ledger-entries", LedgerEntryViewSet, basename="ledgerentry")
router.register(r"audit-logs", AuditLogViewSet, basename="auditlog")

# Reports (Excel/PDF generation endpoints)
router.register(r"reports", ReportViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),   # login
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # refresh
]
