from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.models import User
from decimal import Decimal

class custdata(models.Model):
    username = models.CharField(max_length=200)
    useremail = models.CharField(max_length=200, unique=True)
    useraddress = models.CharField(max_length=200)
    userpass = models.CharField(max_length=200)
    userstatus = models.CharField(max_length=200, default='reject')
     # New Field
    
class shopdata(models.Model):
    shopname = models.CharField(max_length=200)
    ownername = models.CharField(max_length=200)
    useremail = models.CharField(max_length=200)
    usercontact = models.CharField(max_length=200)
    useraddress = models.CharField(max_length=200)
    userpass = models.CharField(max_length=200)
    userstatus = models.CharField(max_length=200)
    userphoto = models.ImageField(upload_to='vendor_images/')
    license = models.FileField(upload_to='shop_licenses/', blank=True, null=True)  # New Field
    registered_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Product(models.Model):
    shop = models.ForeignKey("shopdata", on_delete=models.CASCADE)  # Link to shop
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)



class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    shop = models.ForeignKey(shopdata, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    is_paid = models.BooleanField(default=False) 



class Review(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="reviews")
    customer_name = models.CharField(max_length=255)
    rating = models.IntegerField(choices=[(1, "★"), (2, "★★"), (3, "★★★"), (4, "★★★★"), (5, "★★★★★")])
    comment = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(default=timezone.now)

class Transaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="transactions")
    useremail = models.EmailField()  # Linking transaction to user by email (instead of ForeignKey)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_date = models.DateTimeField(auto_now_add=True)

class Complaint(models.Model):
    user = models.ForeignKey(custdata, on_delete=models.CASCADE)  # Link to custdata instead of auth.User
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('resolved', 'Resolved'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(default=now)



class Cart(models.Model):
    customer = models.ForeignKey("custdata", on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Tracks how many of the product is in the cart
    added_at = models.DateTimeField(auto_now_add=True)
    @property
    def total_price(self):
        return Decimal(self.product.price) * self.quantity  # Correct calculation

class Wishlist(models.Model):
    customer = models.ForeignKey(custdata, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("customer", "product")  

class Contact(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    

  
 


