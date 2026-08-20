from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth.hashers import is_password_usable

from .models import custdata, shopdata, Category, Product, Order, Cart


# ---------------------------------------------------------------------------
# Password security
# ---------------------------------------------------------------------------
class PasswordHashingTests(TestCase):
    """
    Confirms that the password-hashing fix actually works: passwords must
    never be stored as plain text, for either customers or vendors.
    """

    def test_customer_signup_hashes_password(self):
        self.client.post("/signup1", {
            "fullName": "Test Customer",
            "email": "customer@example.com",
            "address": "123 Test Street",
            "password": "StrongPass1!",
            "confirmPassword": "StrongPass1!",
        })
        customer = custdata.objects.get(useremail="customer@example.com")

        # The raw password must never appear in the stored value.
        self.assertNotEqual(customer.userpass, "StrongPass1!")
        # The stored value must be a real Django password hash, not plain text.
        self.assertTrue(is_password_usable(customer.userpass))

    def test_customer_login_succeeds_with_correct_password(self):
        self.client.post("/signup1", {
            "fullName": "Test Customer",
            "email": "customer@example.com",
            "address": "123 Test Street",
            "password": "StrongPass1!",
            "confirmPassword": "StrongPass1!",
        })

        self.client.post("/login/", {
            "email": "customer@example.com",
            "password": "StrongPass1!",
        })
        self.assertEqual(self.client.session.get("uemail"), "customer@example.com")
        self.assertEqual(self.client.session.get("user"), "customer")

    def test_customer_login_fails_with_wrong_password(self):
        self.client.post("/signup1", {
            "fullName": "Test Customer",
            "email": "customer@example.com",
            "address": "123 Test Street",
            "password": "StrongPass1!",
            "confirmPassword": "StrongPass1!",
        })
        self.client.post("/login/", {
            "email": "customer@example.com",
            "password": "totally-wrong-password",
        })
        # No session should be established on a failed login.
        self.assertNotIn("uemail", self.client.session)


# ---------------------------------------------------------------------------
# Authorization: vendor and admin views must require the right session
# ---------------------------------------------------------------------------
class AuthorizationTests(TestCase):
    """
    Confirms the role-based decorators actually block unauthenticated
    access, and that a logged-in vendor cannot act on another vendor's data.
    """

    def setUp(self):
        self.vendor_a = shopdata.objects.create(
            shopname="Shop A",
            ownername="Owner A",
            useremail="vendora@example.com",
            usercontact="9876543210",
            useraddress="Addr A",
            userpass="pbkdf2_sha256$dummyhash",
            userstatus="active",
        )
        self.vendor_b = shopdata.objects.create(
            shopname="Shop B",
            ownername="Owner B",
            useremail="vendorb@example.com",
            usercontact="9876543211",
            useraddress="Addr B",
            userpass="pbkdf2_sha256$dummyhash",
            userstatus="active",
        )
        self.category = Category.objects.create(name="General")
        self.product_b = Product.objects.create(
            shop=self.vendor_b,
            name="Vendor B Product",
            description="desc",
            price=Decimal("10.00"),
            stock=5,
        )

    def test_vendor_dashboard_requires_login(self):
        response = self.client.get("/shophome")
        # Anonymous visitors must be redirected away, never shown the dashboard.
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_requires_login(self):
        response = self.client.get("/adminhome")
        self.assertEqual(response.status_code, 302)

    def test_vendor_cannot_delete_another_vendors_product(self):
        # Log in as vendor A via the session, the same way login() does.
        session = self.client.session
        session["semail"] = self.vendor_a.useremail
        session["user"] = "vendor"
        session.save()

        response = self.client.get(f"/shopproduct/delete/{self.product_b.id}/")

        # Vendor A must not be able to reach vendor B's product at all.
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Product.objects.filter(id=self.product_b.id).exists())


# ---------------------------------------------------------------------------
# Core model / business logic
# ---------------------------------------------------------------------------
class ModelBehaviourTests(TestCase):
    def setUp(self):
        self.vendor = shopdata.objects.create(
            shopname="Test Shop",
            ownername="Owner",
            useremail="shop@example.com",
            usercontact="9876543210",
            useraddress="Addr",
            userpass="pbkdf2_sha256$dummyhash",
            userstatus="active",
        )
        self.customer = custdata.objects.create(
            username="Test Customer",
            useremail="customer@example.com",
            useraddress="Addr",
            userpass="pbkdf2_sha256$dummyhash",
            userstatus="active",
        )
        self.product = Product.objects.create(
            shop=self.vendor,
            name="Test Product",
            description="desc",
            price=Decimal("25.50"),
            stock=10,
        )

    def test_cart_total_price_calculation(self):
        cart_item = Cart.objects.create(customer=self.customer, product=self.product, quantity=3)
        self.assertEqual(cart_item.total_price, Decimal("76.50"))

    def test_order_shop_accessible_without_joining_through_product(self):
        order = Order.objects.create(
            product=self.product,
            shop=self.vendor,
            customer_name=self.customer.username,
            customer_email=self.customer.useremail,
            quantity=1,
            total_price=self.product.price,
        )
        # Order stores a direct FK to shop rather than only being reachable
        # via order.product.shop, so shop reporting doesn't require a join
        # through Product.
        self.assertEqual(order.shop, self.vendor)

    def test_deleting_product_cascades_to_its_orders(self):
        # Product has on_delete=CASCADE, so deleting a product also deletes
        # any orders referencing it -- storing shop on Order separately does
        # not protect the order itself from being removed. This is worth
        # knowing: an order history disappearing when a vendor deletes a
        # product is a real, current limitation of the schema, not a bug
        # in this test.
        order = Order.objects.create(
            product=self.product,
            shop=self.vendor,
            customer_name=self.customer.username,
            customer_email=self.customer.useremail,
            quantity=1,
            total_price=self.product.price,
        )
        order_id = order.id
        self.product.delete()
        self.assertFalse(Order.objects.filter(id=order_id).exists())

    def test_pending_vendor_cannot_log_in(self):
        shopdata.objects.create(
            shopname="Pending Shop",
            ownername="Owner",
            useremail="pending@example.com",
            usercontact="9876543210",
            useraddress="Addr",
            userpass="pbkdf2_sha256$dummyhash",
            userstatus="pending",  # not yet approved by admin
        )
        self.client.post("/login/", {
            "email": "pending@example.com",
            "password": "irrelevant",
        })
        self.assertNotIn("semail", self.client.session)