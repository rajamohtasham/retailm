from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Branch, Product, Sale, SaleItem, StockMovement

User = get_user_model()


class RetailAPITestCase(TestCase):
    def setUp(self):
        # Create a branch
        self.branch = Branch.objects.create(name="Main Branch", location="City Center")

        # Create a user for that branch
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
            branch=self.branch,
            role="manager"
        )

        # Authenticate with APIClient
        self.client = APIClient()
        self.client.login(username="testuser", password="password123")

        # Create a product (removed category field)
        self.product = Product.objects.create(
            name="Burger",
            price=100,
            branch=self.branch,
            quantity=50
        )

    def test_create_sale_and_stock_movement(self):
        """Creating a sale should create sale items and stock movements, and update product quantity."""
        sale_data = {
            "branch": self.branch.id,
            "items": [
                {"product": self.product.id, "quantity": 2, "price": 100}
            ]
        }

        response = self.client.post("/api/sales/", sale_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        sale = Sale.objects.get(id=response.data["id"])
        self.assertEqual(sale.total_amount, 200)

        # Check SaleItem created
        sale_items = SaleItem.objects.filter(sale=sale)
        self.assertEqual(sale_items.count(), 1)
        self.assertEqual(sale_items.first().product_name, "Burger")

        # Check StockMovement created
        movement = StockMovement.objects.get(sale_item=sale_items.first())
        self.assertEqual(movement.movement_type, "out")
        self.assertEqual(movement.quantity, 2)

        # Product quantity reduced
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 48)

    def test_stock_adjustment_positive_and_negative(self):
        """StockMovement with adjustment should correctly update product stock."""
        # Increase stock
        StockMovement.objects.create(
            product=self.product,
            branch=self.branch,
            movement_type="adjustment",
            quantity=10
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 60)

        # Decrease stock
        StockMovement.objects.create(
            product=self.product,
            branch=self.branch,
            movement_type="adjustment",
            quantity=-5
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 55)

    def test_product_list_api(self):
        """Ensure product list returns branch-specific products."""
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertEqual(response.data[0]["name"], "Burger")

    def test_sale_permissions(self):
        """Ensure user can only see sales of their branch."""
        # Create sale in branch
        sale = Sale.objects.create(branch=self.branch, created_by=self.user)
        SaleItem.objects.create(sale=sale, product=self.product, product_name="Burger", quantity=1, price=100)

        response = self.client.get("/api/sales/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertEqual(response.data[0]["branch"], self.branch.id)
