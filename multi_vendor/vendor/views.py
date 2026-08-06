from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages 
from django.contrib.messages import get_messages
from django.utils.timezone import now  # Import timezone
from django.conf import settings
from  django.core.files.storage import FileSystemStorage
from . models import *
from django.http import JsonResponse
from decimal import Decimal
from .forms import ProductForm
from django.db.models import Sum, Count
from django.contrib.auth.hashers import make_password
from .decorators import admin_required, vendor_required, customer_required


def index(request):
    recent_products = Product.objects.order_by("-created_at")[:8]  # Fetch latest 8 products
    return render(request, "index.html", {"recent_products": recent_products})

def shop(request):
    vendors=shopdata.objects.all()
    return render(request, "shop.html",{'vendors': vendors})

def search_shops(request):
    query = request.GET.get('q', '')

    if query:
        shops = shopdata.objects.filter(shopname__icontains=query)[:5]  # Limit results
        shop_list = [{"id": shop.id, "shopname": shop.shopname} for shop in shops]
        return JsonResponse(shop_list, safe=False)

    return JsonResponse([], safe=False)  # Return empty JSON if no query
    

def customerReg(request):
    return render(request,"customerReg.html")

def shopReg(request):
    return render(request,"shopReg.html")


def hshop_details(request, shop_id):
    shop = get_object_or_404(shopdata, id=shop_id)
    products = Product.objects.filter(shop=shop)

    # ✅ Get cart message and remove it from session
    

    return render(request, "hshop_details.html", {"shop": shop, "products": products})

def hproduct_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "hproduct_details.html", {"product": product})

import re
from django.contrib.auth.hashers import make_password, check_password


def signup1(request):
    if request.method == "POST":
        storage = get_messages(request)
        for _ in storage:
            pass

        username = request.POST.get('fullName')
        useremail = request.POST.get('email')
        useraddress = request.POST.get('address')
        userpass = request.POST.get('password')
        confirm_password = request.POST.get("confirmPassword")

        # Fixed: was checking email AND password existed together (wrong logic)
        if custdata.objects.filter(useremail=useremail).exists():
            messages.error(request, "Email is already registered. Please use a different email.")
            return render(request, "customerReg.html")

        if shopdata.objects.filter(useremail=useremail).exists():
            messages.error(request, "Email is already registered as a vendor. Please use a different email.")
            return render(request, "customerReg.html")

        if not all([username, useremail, useraddress, userpass]):
            messages.error(request, "All fields are required.")
            return render(request, "customerReg.html")

        # Validate email format
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, useremail):
            messages.error(request, "Invalid email format.")
            return render(request, "customerReg.html")

        # Validate password length
        if len(userpass) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, "customerReg.html")
        if userpass != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "customerReg.html")

        data = custdata(
            username=username,
            useremail=useremail,
            userpass=make_password(userpass),   # hash before saving
            useraddress=useraddress,
            userstatus='active'
        )
        data.save()
        messages.success(request, "You have successfully registered!")
        return redirect('/login/')
    return render(request, "customerReg.html")


def signup2(request):
    if request.method == "POST":
        storage = get_messages(request)
        for _ in storage:
            pass  # Clears previous messages

        userphoto = request.FILES['shopPhoto']
        up = FileSystemStorage()
        img = up.save(userphoto.name, userphoto)

        shopname = request.POST.get('shopName')
        ownername = request.POST.get('ownerName')
        useremail = request.POST.get('email')
        usercontact = request.POST.get('contact')
        useraddress = request.POST.get('address')
        userpass = request.POST.get('password')
        confirm_password = request.POST.get("confirmPassword")
        license = request.FILES.get("license")

        # Fixed: was checking email AND password existed together (wrong logic)
        if custdata.objects.filter(useremail=useremail).exists():
            messages.error(request, "Email is already registered. Please use a different email.")
            return render(request, "shopReg.html")

        if shopdata.objects.filter(useremail=useremail).exists():
            messages.error(request, "Email is already registered as a vendor. Please use a different email.")
            return render(request, "shopReg.html")

        if not shopname or not ownername or not useremail or not usercontact or not useraddress or not userpass or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("shop_registration")

        if len(userpass) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect("shop_registration")

        if userpass != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("shop_registration")

        if not usercontact.isdigit() or len(usercontact) != 10:
            messages.error(request, "Contact number must be 10 digits.")
            return redirect("shop_registration")

        # Save data with registration date
        data = shopdata(
            shopname=shopname,
            ownername=ownername,
            useremail=useremail,
            usercontact=usercontact,
            userpass=make_password(userpass),   # hash before saving
            userphoto=userphoto,
            useraddress=useraddress,
            license=license,
            userstatus='pending',
            registered_at=now()
        )
        data.save()

        messages.success(request, "You have successfully registered your shop!")
        return redirect('/login/')

    return render(request, "shopReg.html")


def login(request):
    if request.method == 'POST':
        storage = get_messages(request)
        for _ in storage:
            pass
        useremail = request.POST.get('email')
        userpass = request.POST.get('password')

        # Admin Login — credentials now pulled from environment, not hardcoded
        import os
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')  # generate once with make_password()
        if admin_email and useremail == admin_email and check_password(userpass, admin_password_hash or ''):
            request.session['adminemail'] = useremail
            request.session['admin'] = 'admin'
            messages.success(request, "Admin login successful!")
            return redirect('/adminhome')

        # Customer Login — fetch by email/status only, then verify hash
        customer = custdata.objects.filter(useremail=useremail, userstatus='active').first()
        if customer and check_password(userpass, customer.userpass):
            request.session['uid'] = customer.id
            request.session['uname'] = customer.username
            request.session['uemail'] = customer.useremail
            request.session['user'] = 'customer'
            messages.success(request, "Customer login successful!")
            return render(request, 'cust_home.html', {'status': 'User login successful'})

        # Vendor Login — same pattern
        vendor = shopdata.objects.filter(useremail=useremail, userstatus='active').first()
        if vendor and check_password(userpass, vendor.userpass):
            request.session['sid'] = vendor.id
            request.session['sname'] = vendor.shopname
            request.session['sownername'] = vendor.ownername
            request.session['semail'] = vendor.useremail
            request.session['user'] = 'vendor'
            messages.success(request, "Vendor login successful!")
            return redirect('/shophome')

        # If no valid user is found
        messages.error(request, "Incorrect credentials or account not active.")
        return render(request, 'login.html', {'status': 'Incorrect credentials or inactive account'})

    return render(request, "login.html")

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Save message to the database (if you have a model)
        Contact.objects.create(name=name, email=email, message=message)

        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

    return render(request, "contact.html")
@admin_required
def contact_list(request):
    contacts = Contact.objects.all().order_by("-created_at")  # Fetch contacts sorted by latest first
    return render(request, "contact_list.html", {"contacts": contacts})
@admin_required
def adminhome(request):
    return render(request, "adminhome.html")
@admin_required
def adminvendor(request):
    vendors=shopdata.objects.all()
    return render(request, "admin_vendor.html",{'vendors': vendors})
@admin_required
def approve_vendor(request, vendor_id):
    vendor = get_object_or_404(shopdata, id=vendor_id)
    vendor.userstatus = "active"
    vendor.save()
    return redirect('/adminvendor')
@admin_required
def reject_vendor(request, vendor_id):
    vendor = get_object_or_404(shopdata, id=vendor_id)
    vendor.userstatus = "reject"  
    vendor.save()
    return redirect('/adminvendor')
@admin_required
def delete_vendor(request, vendor_id):
    vendor = get_object_or_404(shopdata, id=vendor_id)
    vendor.delete() 
    return redirect('/adminvendor') 

@admin_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'admin_category_list.html', {'categories': categories})
@admin_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')

        if Category.objects.filter(name=name).exists():
            messages.error(request, "Category already exists.")
            return redirect('add_category')

        Category.objects.create(name=name, description=description)
        messages.success(request, "Category added successfully!")
        return redirect('category_list')

    return render(request, 'admin_add_category.html')
@admin_required
def admin_products(request):
    products = Product.objects.select_related('shop').all()  # ✅ Include Shop Data
    return render(request, "admin_products.html", {"products": products})


@admin_required
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.stock = request.POST.get("stock")
        category_id = request.POST.get("category")
        product.category = Category.objects.get(id=category_id)

        if 'image' in request.FILES:
            image = request.FILES['image']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)  # Save inside MEDIA folder
            filename = fs.save(image.name, image)
            product.image = filename  # Store relative path

        product.save()
        messages.success(request, "Product updated successfully!")
        return redirect('admin_products')

    return render(request, "edit_product.html", {"product": product, "categories": categories})
@admin_required
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('admin_products')

@admin_required
def admin_orders(request):
    orders = Order.objects.all()
    return render(request, 'admin_orders.html', {'orders': orders})
@admin_required
def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        order.status = request.POST.get('status')
        order.save()
        messages.success(request, "Order status updated successfully!")
        return redirect('admin_orders')
    
    return render(request, 'update_order.html', {'order': order})
@admin_required
def admin_delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, "Order deleted successfully!")
    return redirect('admin_orders')
@admin_required
def admin_reviews(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, "admin_reviews.html", {"reviews": reviews})
@admin_required
def approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.status = "approved"
    review.save()
    messages.success(request, "Review approved successfully!")
    return redirect("admin_reviews")
@admin_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    messages.success(request, "Review deleted successfully!")
    return redirect("admin_reviews")
@admin_required
def transaction_list(request):
    transactions = Transaction.objects.all().order_by('-transaction_date')
    return render(request, "admin_transactions.html", {'transactions': transactions})
@admin_required
def transaction_details(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, "transaction_details.html", {'transaction': transaction})
@admin_required
def admin_complaints(request):
    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'admin_complaints.html', {'complaints': complaints})
@admin_required
def resolve_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    complaint.status = 'resolved'
    complaint.save()
    messages.success(request, "Complaint marked as resolved.")
    return redirect('admin_complaints')
@admin_required
def reject_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    complaint.status = 'rejected'
    complaint.save()
    messages.error(request, "Complaint rejected.")
    return redirect('admin_complaints')
@vendor_required
def shophome(request):
    shop_email = request.session.get("semail")  # Get vendor email from session
    shop = shopdata.objects.filter(useremail=shop_email).first()  # Get the first matching shop

    products = Product.objects.filter(shop=shop)  # Get products linked to this shop

    context = {
        "shop": shop,
        "products": products,
    }
    return render(request, "shop_home.html", context)

@vendor_required
def shop_profile(request):

    vendor_email = request.session["semail"]
    shop = shopdata.objects.filter(useremail=vendor_email).first()  # Get shop or None
    products = Product.objects.filter(shop=shop) if shop else []

    return render(request, "shop_profile.html", {"shop": shop, "products": products})


@vendor_required
def edit_shop_profile(request):
    if "semail" not in request.session:  # Ensure vendor is logged in
        return redirect("/login/")

    vendor_email = request.session["semail"]
    shop = shopdata.objects.filter(useremail=vendor_email).first()

    if request.method == "POST":
        shopname = request.POST.get("shopname", "").strip()
        ownername = request.POST.get("ownername", "").strip()
        useraddress = request.POST.get("useraddress", "").strip()
        usercontact = request.POST.get("usercontact", "").strip()

        # ✅ Validate input fields
        if not shopname or not ownername or not useraddress or not usercontact:
            messages.error(request, "All fields are required!")
            return render(request, "shop_edit_profile.html", {"shop": shop})

        if not usercontact.isdigit() or len(usercontact) != 10:
            messages.error(request, "Contact number must be exactly 10 digits!")
            return render(request, "shop_edit_profile.html", {"shop": shop})

        # ✅ Update shop details
        shop.shopname = shopname
        shop.ownername = ownername
        shop.useraddress = useraddress
        shop.usercontact = usercontact

        # ✅ Handle photo upload
        if "userphoto" in request.FILES:
            shop.userphoto = request.FILES["userphoto"]

        # ✅ Handle license upload
        if "license" in request.FILES:
            shop.license = request.FILES["license"]

        shop.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("shop_profile")  # ✅ Redirect after updating

    return render(request, "shop_edit_profile.html", {"shop": shop})

# ✅ View only products belonging to the shop
@vendor_required
def product_list(request):
    shop_email = request.session.get("semail")
    shop = shopdata.objects.filter(useremail=shop_email).first()  # Get the first matching shop
    products = Product.objects.filter(shop=shop)  # Fetch products for the shop
    return render(request, "shop_products.html", {"products": products, "shop": shop})

# ✅ Add product
@vendor_required
def add_product(request):
    shop_email = request.session.get("semail")
    shop = shopdata.objects.filter(useremail=shop_email).first()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = shop  # Assign shop to product
            product.save()
            messages.success(request, "Product added successfully!")
            return redirect("shop_product_list")  # Ensure this matches your URL name
    else:
        form = ProductForm()

    return render(request, "shop_add_product.html", {"form": form})

# ✅ Edit product
@vendor_required
def edit_product(request, product_id):
    shop_email = request.session.get("semail")
    shop = shopdata.objects.filter(useremail=shop_email).first()

    product = get_object_or_404(Product, id=product_id, shop=shop)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect("shop_product_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "shop_edit_product.html", {"form": form, "product": product})

# ✅ Delete product
@vendor_required
def delete_product(request, product_id):
    shop_email = request.session.get("semail")
    shop = shopdata.objects.filter(useremail=shop_email).first()

    product = get_object_or_404(Product, id=product_id, shop=shop)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect("shop_product_list")
@vendor_required
def shop_orders(request):
    shop_email = request.session.get("semail")  # Fetch vendor email from session
    shop = get_object_or_404(shopdata, useremail=shop_email)  # Get the shop
    orders = Order.objects.filter(shop=shop).select_related("product")  # Fetch orders for this shop

    return render(request, "shop_orders.html", {"orders": orders, "shop": shop})
@vendor_required
def update_order_status(request, order_id):
    shop_email = request.session.get("semail")
    shop = get_object_or_404(shopdata, useremail=shop_email)
    order = get_object_or_404(Order, id=order_id, shop=shop)   # ✅ scoped
    if request.method == "POST":
        new_status = request.POST.get("delivery_status")
        if new_status in dict(Order.STATUS_CHOICES):
            order.delivery_status = new_status
            order.save()
            messages.success(request, "Order status updated successfully!")
        else:
            messages.error(request, "Invalid status update.")
    return redirect("shop_orders")
@vendor_required
def delete_order(request, order_id):
    shop_email = request.session.get("semail")
    shop = get_object_or_404(shopdata, useremail=shop_email)
    order = get_object_or_404(Order, id=order_id, shop=shop)   # ✅ scoped
    order.delete()
    messages.success(request, "Order deleted successfully!")
    return redirect("shop_orders")
@vendor_required
def sales_revenue(request):
    shop_email = request.session.get("semail")  # Fetch shop email from session
    shop = get_object_or_404(shopdata, useremail=shop_email)  # Get the shop
    
    # ✅ Filter only completed (successful) orders
    completed_orders =  Order.objects.filter(shop=shop, delivery_status="Delivered")

    # ✅ Calculate total revenue
    total_revenue = completed_orders.aggregate(Sum("total_price"))["total_price__sum"] or 0

    # ✅ Count total sales
    total_sales = completed_orders.count()

    # ✅ Fetch latest sales transactions (last 10)
    recent_sales = completed_orders.order_by("-created_at")[:10]

    return render(
        request,
        "shop_sales_revenue.html",
        {
            "shop": shop,
            "total_revenue": total_revenue,
            "total_sales": total_sales,
            "recent_sales": recent_sales,
        },
    )

@vendor_required
def shop_reviews(request):
    shop_email = request.session.get("semail")  
    shop = get_object_or_404(shopdata, useremail=shop_email)  

    # ✅ Get all products for the shop
    products = Product.objects.filter(shop=shop)

    # ✅ Get all reviews for those products
    reviews = Review.objects.filter(product__in=products).order_by("-created_at")

    return render(request, "shop_reviews.html", {"shop": shop, "reviews": reviews})


# ✅ Approve a review
@vendor_required
def approve_reviews(request, review_id):
    shop_email = request.session.get("semail")
    shop = get_object_or_404(shopdata, useremail=shop_email)
    review = get_object_or_404(Review, id=review_id, product__shop=shop)  # scoped through product → shop
    review.status = "Approved"
    review.save()
    messages.success(request, "Review approved successfully!")
    return redirect("shop_reviews")


# ✅ Reject a review
@vendor_required
def reject_reviews(request, review_id):
    shop_email = request.session.get("semail")
    shop = get_object_or_404(shopdata, useremail=shop_email)
    review = get_object_or_404(Review, id=review_id, product__shop=shop)
    review.status = "Rejected"
    review.save()
    messages.success(request, "Review rejected!")
    return redirect("shop_reviews")


# ✅ Delete a review
@vendor_required
def delete_reviews(request, review_id):
    shop_email = request.session.get("semail")
    shop = get_object_or_404(shopdata, useremail=shop_email)
    review = get_object_or_404(Review, id=review_id, product__shop=shop)
    review.delete()
    messages.success(request, "Review deleted successfully!")
    return redirect("shop_reviews")

@vendor_required
def shop_report(request):
    shop_email = request.session.get("semail")
    shop = get_object_or_404(shopdata, useremail=shop_email)

    # Get all orders related to the shop
    orders = Order.objects.filter(shop=shop)

    # Calculate total revenue (Fix: Use total_price instead of total_amount)
    total_revenue = orders.aggregate(total=Sum("total_price"))["total"] or 0

    # Total products sold
    total_products_sold = orders.aggregate(total=Sum("quantity"))["total"] or 0

    # Total orders
    total_orders = orders.count()

    # Best-selling products
    best_selling_products = (
    Product.objects.filter(shop=shop)
    .annotate(total_sold=Count("orders"))  # Use "orders" (if related_name is set)
    .order_by("-total_sold")[:5]
)

    return render(
        request,
        "shop_report.html",
        {
            "shop": shop,
            "total_revenue": total_revenue,
            "total_products_sold": total_products_sold,
            "total_orders": total_orders,
            "best_selling_products": best_selling_products,
            "orders": orders[:5],  # Show latest 5 orders
        },
    )

@vendor_required
def delivery_list(request):
    shop_email = request.session.get("semail")  
    shop = get_object_or_404(shopdata, useremail=shop_email)  

    orders = Order.objects.filter(shop=shop).order_by("-created_at")  

    return render(request, "shop_delivery.html", {"orders": orders})

@vendor_required
def update_delivery_status(request, order_id):
    shop_email = request.session.get("semail")
    shop = get_object_or_404(shopdata, useremail=shop_email)
    order = get_object_or_404(Order, id=order_id, shop=shop)   # ✅ scoped
    if request.method == "POST":
        new_status = request.POST.get("delivery_status")
        if new_status in ["Pending", "Shipped", "Delivered", "Cancelled"]:
            order.delivery_status = new_status
            order.save()
            messages.success(request, "Delivery status updated successfully!")
        else:
            messages.error(request, "Invalid status selected!")
    return redirect("shop_delivery_list")


@customer_required
def custhome(request):
    cust_email = request.session.get("uemail")
    cust = custdata.objects.filter(useremail=cust_email).first()
    context = {"cust": cust}
    return render(request, "cust_home.html", context)

@customer_required
def customer_profile(request):

    customer_email = request.session["uemail"]
    cust = custdata.objects.filter(useremail=customer_email).first()

    return render(request, "customer_profile.html", {"cust": cust})
@customer_required
def edit_customer_profile(request):
    cust_email = request.session.get("uemail")  # Get customer email from session
    cust = custdata.objects.filter(useremail=cust_email).first()

    if request.method == "POST":
        cust.username = request.POST.get("username")
        cust.useraddress = request.POST.get("useraddress")

        if 'profile_photo' in request.FILES:
            cust.profile_photo = request.FILES['profile_photo']  # Save new profile photo



        new_password = request.POST.get("userpass")
        if new_password:
            cust.userpass = make_password(new_password)  # hash before saving  # Update password only if provided

        cust.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("customer_profile")

    return render(request, "editcustprofile.html", {"cust": cust})

def shop_list(request):
    shops = shopdata.objects.filter(userstatus='active')  # Show only approved shops
    return render(request, "shop_list.html", {"shops": shops})


def shop_details(request, shop_id):
    shop = get_object_or_404(shopdata, id=shop_id)
    products = Product.objects.filter(shop=shop)

    # ✅ Get cart message and remove it from session
    cart_message = request.session.pop("cart_message", None)

    return render(request, "shop_details.html", {"shop": shop, "products": products, "cart_message": cart_message})

def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "product_details.html", {"product": product})
@customer_required
def add_to_cart(request, product_id):


    customer_email = request.session["uemail"]
    customer = custdata.objects.filter(useremail=customer_email).first()
    product = get_object_or_404(Product, id=product_id)

    quantity = int(request.POST.get("quantity", 1))

    cart_item, created = Cart.objects.get_or_create(customer=customer, product=product)

    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity

    cart_item.save()

    # ✅ Store message in session so it only shows once
    request.session["cart_message"] = f"{quantity} x {product.name} added to cart!"

    return redirect("shop_details", shop_id=product.shop.id)
@customer_required
def view_cart(request):

    customer_email = request.session["uemail"]
    customer = custdata.objects.filter(useremail=customer_email).first()

    cart_items = Cart.objects.filter(customer=customer)
    
    # Ensure total price calculation works
    total_price = sum(item.total_price for item in cart_items)

    return render(request, "cart.html", {"cart_items": cart_items, "total_price": total_price})

@customer_required
def remove_from_cart(request, cart_id):
    customer_email = request.session["uemail"]
    cart_item = get_object_or_404(Cart, id=cart_id, customer__useremail=customer_email)
    cart_item.delete()
    messages.success(request, "Item removed from cart!")
    return redirect("cart")

@customer_required
def checkout(request):

    customer_email = request.session["uemail"]
    customer = custdata.objects.get(useremail=customer_email)

    cart_items = Cart.objects.filter(customer=customer)

    if not cart_items:
        messages.error(request, "Your cart is empty!")
        return redirect("view_cart")

    total_price = sum(Decimal(item.total_price) for item in cart_items)  # Ensure Decimal type

    if request.method == "POST":
        for item in cart_items:
            Order.objects.create(
                product=item.product,
                shop=item.product.shop,
                customer_name=customer.username,
                customer_email=customer_email,
                quantity=item.quantity,
                total_price=Decimal(item.total_price),
            )
        cart_items.delete()  # Clear cart after checkout
        messages.success(request, "Order placed successfully!")
        return redirect("order_success")

    return render(request, "checkout.html", {"cart_items": cart_items, "total_price": total_price})


@customer_required
def order_success(request):
    return render(request, "order_success.html")
@customer_required
def customer_orders(request):

    customer_email = request.session["uemail"]
    customer = custdata.objects.filter(useremail=customer_email).first()

    orders = Order.objects.filter(customer_email=customer_email).order_by("-created_at")

    return render(request, "customer_orders.html", {"orders": orders})
@customer_required
def make_transaction(request, order_id):
    customer_email = request.session["uemail"]
    order = get_object_or_404(Order, id=order_id, customer_email=customer_email)  # ✅ scoped

    if order.delivery_status != "Delivered":
        messages.error(request, "Transaction is only available for delivered orders.")
        return redirect("customer_orders")

    return render(request, "transaction.html", {"order": order})

from django.http import HttpResponse
@customer_required
def process_payment(request, order_id):
    customer_email = request.session["uemail"]
    order = get_object_or_404(Order, id=order_id, customer_email=customer_email)  # ✅ scoped
    order.is_paid = True
    order.save()

    transaction = Transaction.objects.create(
        useremail=order.customer_email,
        order=order,
        amount=order.total_price,
        status="completed",
        transaction_date=timezone.now(),
    )
    transaction.save()
    messages.success(request, f"Payment successful for Order ID: {order_id}")
    return redirect("customer_orders")
@customer_required
def add_to_wishlist(request, product_id):

    customer_email = request.session["uemail"]
    customer = custdata.objects.filter(useremail=customer_email).first()
    product = get_object_or_404(Product, id=product_id)

    wishlist_item, created = Wishlist.objects.get_or_create(customer=customer, product=product)
    
    if created:
        messages.success(request, f"{product.name} added to your wishlist!")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")

    return redirect("shop_details", shop_id=product.shop.id)  # Redirect back to shop detail page
@customer_required
def view_wishlist(request):

    customer_email = request.session["uemail"]
    customer = custdata.objects.filter(useremail=customer_email).first()
    
    wishlist_items = Wishlist.objects.filter(customer=customer)
    
    return render(request, "wishlist.html", {"wishlist_items": wishlist_items})
@customer_required
def remove_from_wishlist(request, wishlist_id):
    customer_email = request.session["uemail"]
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, customer__useremail=customer_email)
    wishlist_item.delete()
    messages.success(request, "Item removed from wishlist!")
    return redirect("view_wishlist")

def product_reviews(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product, status="Approved")  # Only show approved reviews
    return render(request, "reviews.html", {"product": product, "reviews": reviews})
@customer_required
def submit_review(request, product_id):

    customer_email = request.session["uemail"]
    customer = custdata.objects.filter(useremail=customer_email).first()
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment")

        Review.objects.create(
            product=product,
            customer_name=customer.username,
            rating=rating,
            comment=comment,
            status="Pending",  # Default pending if admin needs to approve
            created_at=now(),
        )

        messages.success(request, "Review submitted successfully! Awaiting approval.")
        return redirect("product_reviews", product_id=product.id)

    return redirect("product_reviews", product_id=product.id)
@customer_required
def submit_complaint(request):

    customer_email = request.session["uemail"]
    customer = custdata.objects.filter(useremail=customer_email).first()

    if not customer:
        messages.error(request, "Invalid customer data.")
        return redirect("login")

    # Try to find a matching Django User (if User model is still in use)
    user = custdata.objects.filter(useremail=customer.useremail).first()
    if not user:
        messages.error(request, "User not found.")
        return redirect("login")

    if request.method == "POST":
        subject = request.POST["subject"]
        message = request.POST["message"]

        Complaint.objects.create(user=customer, subject=subject, message=message)
        messages.success(request, "Complaint submitted successfully!")
        return redirect("submit_complaint")

    complaints = Complaint.objects.filter(user=customer).order_by("-created_at")

    return render(request, "submit_complaint.html", {"complaints": complaints})

def cproduct_list(request):
    products = Product.objects.prefetch_related("reviews").all()
    return render(request, "product_list.html", {"products": products})





