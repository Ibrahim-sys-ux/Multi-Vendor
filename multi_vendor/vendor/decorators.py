# vendor/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('admin') != 'admin':
            messages.error(request, "Admin login required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def vendor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'semail' not in request.session:
            messages.error(request, "Vendor login required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def customer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'uemail' not in request.session:
            messages.error(request, "Please log in to continue.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
