from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
import random, string
from .models import *
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Category 
from django.http import JsonResponse
from django.db import transaction
from .models import SiteSettings 
from django.core.files.storage import default_storage
from django.contrib.auth import update_session_auth_hash



# Helper function to generate unique username
def generate_username(email):
    base = email.split('@')[0]
    rand = ''.join(random.choices(string.digits, k=4))
    return base + rand

def register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        profile_image = request.FILES.get('profile_image')

        # Split full name into first and last name
        first_name = ""
        last_name = ""
        if name:
            parts = name.strip().split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, "register.html")

        try:
            with transaction.atomic():
                # Create user
                user = CustomUser.objects.create_user(
                    username=email,  # using email as username
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    address=address,
                )
                if profile_image:
                    user.profile_image = profile_image
                user.save()

                messages.success(request, "Registration successful. You can now login.")
                return redirect("login")

        except IntegrityError:
            messages.error(request, "Database is busy or an error occurred. Try again.")
            return render(request, "register.html")

    return render(request, "register.html")

# Edit User Profile (Admin/Staff only)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        profile_image = request.FILES.get('profile_image')
        
        # Optional: Password update
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Split full name into first and last name
        first_name = ""
        last_name = ""
        if name:
            parts = name.strip().split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        try:
            with transaction.atomic():
                # Check if email already exists (excluding current user)
                if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                    messages.error(request, "Email already exists.")
                    return render(request, "edit_user.html", {"user": user})

                # Update user details
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.username = email
                user.phone = phone
                user.address = address

                # Handle profile image
                if profile_image:
                    user.profile_image = profile_image

                # Handle password change if provided
                if new_password:
                    if new_password == confirm_password:
                        user.set_password(new_password)
                    else:
                        messages.error(request, "Passwords do not match.")
                        return render(request, "edit_user.html", {"user": user})

                user.save()

                # Redirect with success code 2 (User updated successfully)
                return redirect(f"{reverse('user_list')}?success=2")

        except Exception as e:
            messages.error(request, f"Error updating user: {str(e)}")
            return render(request, "edit_user.html", {"user": user})

    # Pre-fill the name field by combining first and last name
    full_name = f"{user.first_name} {user.last_name}".strip()
    
    context = {
        'user': user,
        'full_name': full_name
    }
    return render(request, "edit_user.html", context)


def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return redirect(f"{reverse('user_list')}?success=3")


# Dashboard views
@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@login_required
def user_dashboard(request):
    return render(request, 'user_dashboard.html')

@login_required
def vendor_dashboard(request):
    return render(request, 'vendor_dashboard.html')


# Login view
def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            
            # Redirect based on role
            if user.is_superuser or user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'vendor':
                return redirect('vendor_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            error = "Invalid email or password"
            return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')



# Add Banner
def add_banner(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        status = request.POST.get('status', 'inactive')
        photo = request.FILES.get('photo')

        if not title or not photo:
            # Handle missing fields
            return render(request, 'add_banner.html', {'error': 'Title and photo are required!'})

        # Create banner
        Banner.objects.create(
            title=title,
            description=description,
            photo=photo,
            status=status
        )

        # Redirect to banner_list with success query param
        return redirect(reverse('banner_list') + '?success=1')

    return render(request, 'add_banner.html')

def banner_list(request):
    banners_list = Banner.objects.all().order_by('-created_at')

    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        banners_list = banners_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Per page
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Pagination
    paginator = Paginator(banners_list, per_page)
    page_number = request.GET.get('page')
    try:
        banners = paginator.page(page_number)
    except PageNotAnInteger:
        banners = paginator.page(1)
    except EmptyPage:
        banners = paginator.page(paginator.num_pages)

    # Success message logic - simplified
    success_messages = {
        '1': 'Banner added successfully!',
        '2': 'Banner updated successfully!', 
        '3': 'Banner deleted successfully!'
    }
    
    success_code = request.GET.get("success")
    success_message = success_messages.get(success_code, "")

    return render(request, "banner_list.html", {
        "banners": banners,
        "per_page": per_page,
        "search_query": search_query,
        "success_message": success_message
    })


def edit_banner(request, id):
    banner = get_object_or_404(Banner, id=id)
    if request.method == 'POST':
        banner.title = request.POST.get('title')
        banner.description = request.POST.get('description')
        banner.status = request.POST.get('status', 'inactive')
        photo = request.FILES.get('photo')
        if photo:
            banner.photo = photo
        banner.save()
        return redirect(f"{reverse('banner_list')}?success=2")
    return render(request, "edit_banner.html", {"banner": banner})


def banner_delete(request, id):
    banner = get_object_or_404(Banner, id=id)
    banner.delete()
    return redirect(f"{reverse('banner_list')}?success=3")

def category_add(request):
    parent_cats = Category.objects.filter(is_parent=True, status='active').order_by('title')

    if request.method == 'POST':
        title = request.POST.get('title')
        summary = request.POST.get('summary')
        is_parent = request.POST.get('is_parent') == '1'
        parent_id = request.POST.get('parent_id')
        status = request.POST.get('status')
        photo = request.FILES.get('photo')

        if not title:
            return render(request, 'category_add.html', {
                'parent_cats': parent_cats,
                'error_message': "Title is required"
            })

        parent = None
        if not is_parent and parent_id:
            try:
                parent = Category.objects.get(id=parent_id, is_parent=True, status='active')
            except Category.DoesNotExist:
                return render(request, 'category_add.html', {
                    'parent_cats': parent_cats,
                    'error_message': "Selected parent category is invalid or inactive."
                })

        Category.objects.create(
            title=title,
            summary=summary,
            is_parent=is_parent,
            parent=parent,
            status=status,
            photo=photo
        )

        # ✅ Redirect to list with success=1
        return redirect(f"{reverse('category_list')}?success=1")

    return render(request, 'category_add.html', {'parent_cats': parent_cats})


def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    parent_cats = Category.objects.filter(is_parent=True, status='active').exclude(id=pk).order_by('title')

    if request.method == 'POST':
        title = request.POST.get('title')
        summary = request.POST.get('summary')
        is_parent = request.POST.get('is_parent') == '1'
        parent_id = request.POST.get('parent_id')
        status = request.POST.get('status')
        photo = request.FILES.get('photo')

        category.title = title
        category.summary = summary
        category.is_parent = is_parent
        category.status = status

        if not is_parent and parent_id:
            try:
                category.parent = Category.objects.get(id=parent_id, is_parent=True, status='active')
            except Category.DoesNotExist:
                category.parent = None
        else:
            category.parent = None

        if photo:
            category.photo = photo

        category.save()

        # ✅ Redirect with success=2
        return redirect(f"{reverse('category_list')}?success=2")

    return render(request, 'category_edit.html', {
        'category': category,
        'parent_cats': parent_cats
    })


def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    # ✅ Redirect with success=3
    return redirect(f"{reverse('category_list')}?success=3")


def category_list(request):
    categories_list = Category.objects.all().order_by('-id')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        categories_list = categories_list.filter(
            Q(title__icontains=search_query) | Q(summary__icontains=search_query)
        )

    # Per page
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(categories_list, per_page)
    page_number = request.GET.get('page')
    try:
        categories = paginator.page(page_number)
    except PageNotAnInteger:
        categories = paginator.page(1)
    except EmptyPage:
        categories = paginator.page(paginator.num_pages)

    # ✅ Toastify messages
    success_messages = {
        '1': 'Category added successfully!',
        '2': 'Category updated successfully!',
        '3': 'Category deleted successfully!'
    }
    success_code = request.GET.get("success")
    success_message = success_messages.get(success_code, "")

    return render(request, "category_list.html", {
        "categories": categories,
        "per_page": per_page,
        "search_query": search_query,
        "success_message": success_message
    })

def brand_add(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        status = request.POST.get('status')

        if not title:
            return render(request, 'brand_add.html', {
                'error_message': "Title is required"
            })

        Brand.objects.create(
            title=title,
            status=status
        )

        # ✅ Redirect to list with success=1
        return redirect(f"{reverse('brand_list')}?success=1")

    return render(request, 'brand_add.html')


def brand_edit(request, pk):
    brand = get_object_or_404(Brand, pk=pk)

    if request.method == 'POST':
        title = request.POST.get('title')
        status = request.POST.get('status')

        brand.title = title
        brand.status = status

        brand.save()

        # ✅ Redirect with success=2
        return redirect(f"{reverse('brand_list')}?success=2")

    return render(request, 'brand_edit.html', {'brand': brand})


def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.delete()
    # ✅ Redirect with success=3
    return redirect(f"{reverse('brand_list')}?success=3")


def brand_list(request):
    brands_list = Brand.objects.all().order_by('-id')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        brands_list = brands_list.filter(
            Q(title__icontains=search_query)
        )

    # Per page
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(brands_list, per_page)
    page_number = request.GET.get('page')
    try:
        brands = paginator.page(page_number)
    except PageNotAnInteger:
        brands = paginator.page(1)
    except EmptyPage:
        brands = paginator.page(paginator.num_pages)

    # ✅ Toastify messages
    success_messages = {
        '1': 'Brand added successfully!',
        '2': 'Brand updated successfully!',
        '3': 'Brand deleted successfully!'
    }
    success_code = request.GET.get("success")
    success_message = success_messages.get(success_code, "")

    return render(request, "brand_list.html", {
        "brands": brands,
        "per_page": per_page,
        "search_query": search_query,
        "success_message": success_message
    })

def product_add(request):
    categories = Category.objects.filter(parent__isnull=True, status="active")
    brands = Brand.objects.filter(status="active")

    if request.method == "POST":
        title = request.POST.get("title")
        summary = request.POST.get("summary")
        description = request.POST.get("description")
        is_featured = bool(request.POST.get("is_featured"))
        cat_id = request.POST.get("cat_id")
        child_cat_id = request.POST.get("child_cat_id")
        price = request.POST.get("price")
        discount = request.POST.get("discount") or 0
        size = request.POST.get("size")
        brand_id = request.POST.get("brand_id")
        condition = request.POST.get("condition")
        stock = request.POST.get("stock")
        status = request.POST.get("status")
        photo = request.FILES.get("photo")

        # Optional: Validate file type
        if photo and not photo.content_type.startswith(("image", "video")):
            return render(request, "product_add.html", {
                "categories": categories,
                "brands": brands,
                "error_message": "Only images or videos are allowed."
            })

        category = Category.objects.get(id=cat_id) if cat_id else None
        child_category = Category.objects.get(id=child_cat_id) if child_cat_id else None
        brand = Brand.objects.get(id=brand_id) if brand_id else None

        Product.objects.create(
            title=title,
            summary=summary,
            description=description,
            is_featured=is_featured,
            category=category,
            child_category=child_category,
            price=price,
            discount=discount,
            size=size,
            brand=brand,
            condition=condition,
            stock=stock,
            status=status,
            photo=photo,
            user=request.user 
        )

        return redirect(f"{reverse('product_list')}?success=1")

    return render(request, "product_add.html", {
        "categories": categories,
        "brands": brands,
    })


# ✅ Edit Product
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.filter(parent__isnull=True, status="active")
    brands = Brand.objects.filter(status="active")
 # Define the lists for the template
    AVAILABLE_SIZES = ['S', 'M', 'L', 'XL']
    AVAILABLE_CONDITIONS = ['default', 'new', 'hot'] # Define conditions list too

    if request.method == "POST":
        product.title = request.POST.get("title")
        product.summary = request.POST.get("summary")
        product.description = request.POST.get("description")
        product.is_featured = bool(request.POST.get("is_featured"))

        cat_id = request.POST.get("cat_id")
        child_cat_id = request.POST.get("child_cat_id")
        brand_id = request.POST.get("brand_id")

        product.category = Category.objects.get(id=cat_id) if cat_id else None
        product.child_category = Category.objects.get(id=child_cat_id) if child_cat_id else None
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None

        product.price = request.POST.get("price")
        product.discount = request.POST.get("discount") or 0
        product.size = request.POST.get("size")
        product.condition = request.POST.get("condition")
        product.stock = request.POST.get("stock")
        product.status = request.POST.get("status")

        photo = request.FILES.get("photo")
        if photo:
            # Validate file type
            if not photo.content_type.startswith(("image", "video")):
                return render(request, "product_edit.html", {
                    "product": product,
                    "categories": categories,
                    "brands": brands,
                    "error_message": "Only images or videos are allowed."
                })
            product.photo = photo

        product.save()
        return redirect(f"{reverse('product_list')}?success=2")

    return render(request, "product_edit.html", {
        "product": product,
        "categories": categories,
        "brands": brands,
         "sizes": AVAILABLE_SIZES,
        "conditions": AVAILABLE_CONDITIONS,
    })

def product_toggle_status(request, pk):
    # Security Check: Only Admin/Staff can toggle status
    if not request.user.is_staff and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to change product status.")

    product = get_object_or_404(Product, pk=pk)

    # Toggle the status
    if product.status == 'active':
        product.status = 'inactive'
        success_code = "4" # Deactivation message
    else:
        product.status = 'active'
        success_code = "5" # Activation message

    product.save()

    # Redirect back to the product list, preserving URL parameters
    redirect_url = f"{reverse('product_list')}?success={success_code}"
    query_params = request.GET.urlencode()
    if query_params:
        redirect_url += f"&{query_params}"
        
    return redirect(redirect_url)


# ✅ Delete Product
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect(f"{reverse('product_list')}?success=3")


def product_list(request):
    # 1. Initialize QuerySet
    # Start with all products, ordered by descending ID (newest first)
    products_list = Product.objects.all().order_by("-id")

    # --- 2. ROLE-BASED FILTERING ---
    user = request.user
    
    # 🚨 Admin Role (Highest Priority)
    if user.is_authenticated and (user.is_superuser or user.is_staff):
        # Admin sees ALL products (Active and Inactive). No filtering needed here.
        pass

    # 🚨 Vendor Role
    elif user.is_authenticated:
        # Vendor sees ONLY products they have added (Active and Inactive).
        # We filter the initial QuerySet by the logged-in user.
        products_list = products_list.filter(user=user)

    # 🚨 Customer/Public Role (Default)
    else:
        # Customer (or any unauthenticated user) sees ONLY active products.
        products_list = products_list.filter(status='active')
    
    # -------------------------------

    # 3. Search filter (Applied AFTER role filtering)
    search_query = request.GET.get("q", "").strip()
    if search_query:
        products_list = products_list.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # 4. Per page filter (Pagination setup)
    per_page = request.GET.get("per_page", "10")
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(products_list, per_page)
    page_number = request.GET.get("page")
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # 5. Toastify success messages
    success_messages = {
        "1": "Product added successfully!",
        "2": "Product updated successfully!",
        "3": "Product deleted successfully!",
        # Add new codes for status toggle if needed (4 and 5)
        "4": "Product deactivated successfully!",
        "5": "Product activated successfully!"    
    }
    success_code = request.GET.get("success")
    success_message = success_messages.get(success_code, "")

    # 6. Render context
    return render(request, "product_list.html", {
        "products": products,
        "per_page": per_page,
        "search_query": search_query,
        "success_message": success_message
    })  


def get_child_categories(request):
    parent_id = request.GET.get("parent_id")
    if parent_id:
        child_cats = Category.objects.filter(parent_id=parent_id, status="active").values("id", "title")
        data = list(child_cats)
    else:
        data = []
    return JsonResponse({"child_categories": data})

def coupon_add(request):
    if request.method == "POST":
        code = request.POST.get("code").strip()
        discount_type = request.POST.get("discount_type")
        discount_value = request.POST.get("discount_value") or 0
        min_order_amount = request.POST.get("min_order_amount") or 0
        usage_limit = request.POST.get("usage_limit") or 0
        per_user_limit = request.POST.get("per_user_limit") or 0
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        is_active = bool(request.POST.get("is_active"))

        Coupon.objects.create(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_amount=min_order_amount,
            usage_limit=usage_limit,
            per_user_limit=per_user_limit,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
        )

        return redirect(f"{reverse('coupon_list')}?success=1")

    return render(request, "coupon_add.html")

# ✅ Edit Coupon
def coupon_edit(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)

    if request.method == "POST":
        coupon.code = request.POST.get("code").strip()
        coupon.discount_type = request.POST.get("discount_type")
        coupon.discount_value = request.POST.get("discount_value") or 0
        coupon.min_order_amount = request.POST.get("min_order_amount") or 0
        coupon.usage_limit = request.POST.get("usage_limit") or 0
        coupon.per_user_limit = request.POST.get("per_user_limit") or 0
        coupon.start_date = request.POST.get("start_date")
        coupon.end_date = request.POST.get("end_date")
        coupon.is_active = bool(request.POST.get("is_active"))

        coupon.save()
        return redirect(f"{reverse('coupon_list')}?success=2")

    # The template name must be exactly this
    return render(request, "coupon_edit.html", { 
    "coupon": coupon, 
    })

# ✅ Delete Coupon
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.delete()
    return redirect(f"{reverse('coupon_list')}?success=3")

# ✅ List Coupons (Search + Pagination)
def coupon_list(request):
    coupons_list = Coupon.objects.all().order_by("-id")

    # Search filter
    search_query = request.GET.get("q", "").strip()
    if search_query:
        coupons_list = coupons_list.filter(
            Q(code__icontains=search_query) |
            Q(discount_type__icontains=search_query)
        )

    # Per page filter
    per_page = request.GET.get("per_page", "10")
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(coupons_list, per_page)
    page_number = request.GET.get("page")
    try:
        coupons = paginator.page(page_number)
    except PageNotAnInteger:
        coupons = paginator.page(1)
    except EmptyPage:
        coupons = paginator.page(paginator.num_pages)

    # ✅ Toastify success messages
    success_messages = {
        "1": "Coupon added successfully!",
        "2": "Coupon updated successfully!",
        "3": "Coupon deleted successfully!"
    }
    success_code = request.GET.get("success")
    success_message = success_messages.get(success_code, "")

    return render(request, "coupon_list.html", {
        "coupons": coupons,
        "per_page": per_page,
        "search_query": search_query,
        "success_message": success_message
    })

def users_list(request):
    search_query = request.GET.get('q', '').strip()
    per_page = request.GET.get('per_page', 10)

    # Fetch users and apply search filter
    users = CustomUser.objects.all().order_by('-id')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Convert per_page to integer and validate
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Pagination
    paginator = Paginator(users, per_page)
    page_number = request.GET.get('page')
    try:
        users_page = paginator.page(page_number)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    # Success message logic
    success_messages = {
        '1': 'User added successfully!',
        '2': 'User updated successfully!', 
        '3': 'User deleted successfully!',
        '4': 'User activated successfully!',
        '5': 'User deactivated successfully!'
    }
    
    success_code = request.GET.get("success")
    if success_code in success_messages:
        messages.success(request, success_messages[success_code])

    context = {
        'users': users_page,
        'search_query': search_query,
        'per_page': per_page,
    }
    return render(request, 'user_list.html', context)

def settings_view(request):
    # Assuming you have only one settings record
    settings = SiteSettings.objects.first()

    success_message = None
    error_message = None

    if request.method == "POST":
        short_des = request.POST.get('short_des')
        description = request.POST.get('description')
        address = request.POST.get('address')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        logo_file = request.FILES.get('logo')
        photo_file = request.FILES.get('photo')

        try:
            with transaction.atomic():
                if not settings:
                    settings = SiteSettings()

                settings.short_des = short_des
                settings.description = description
                settings.address = address
                settings.email = email
                settings.phone = phone

                if logo_file:
                    settings.logo = logo_file
                if photo_file:
                    settings.photo = photo_file

                settings.save()

                success_message = "Settings updated successfully!"

        except Exception as e:
            error_message = "An error occurred. Please try again."

    context = {
        'settings': settings,
        'success_message': success_message,
        'error_message': error_message,
    }

    return render(request, 'settings.html', context)


@login_required
def profile_view(request):
    user = request.user  # logged-in user
    success_message = ""  # for toast notification

    if request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', '').strip()
        profile_image = request.FILES.get('profile_image')

        if first_name:  # Only save if first_name is provided
            user.first_name = first_name
            user.last_name = last_name
            if role in ['admin', 'customer']:
                user.role = role
                user.is_staff = True if role == 'admin' else False
            if profile_image:
                user.profile_image = profile_image

            user.save()
            # Set success message for toast
            success_message = "Profile updated successfully!"
            # Optional: redirect to avoid POST resubmission
            return redirect(f"{request.path}?success=1")
        else:
            success_message = "First name is required!"

    context = {
        'profile': user,
        'success_message': success_message,
    }
    return render(request, 'profile.html', context)

@login_required
def change_password(request):
    success_message = ""
    error_message = ""

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        # Check if current password is correct
        if not user.check_password(current_password):
            error_message = "Current password is incorrect."
        elif new_password != confirm_password:
            error_message = "New password and confirm password do not match."
        elif user.check_password(new_password):
            error_message = "New password cannot be the same as current password."
        else:
            # Update password
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in

            return redirect(f"{request.path}?success=1")

    context = {
        "success_message": success_message,
        "error_message": error_message,
    }
    return render(request, "change_password.html", context)

def admin_required(user):
    return user.is_superuser or user.role == 'admin'

# Helper to generate unique username from email
def generate_username(email):
    base = email.split('@')[0]
    rand = ''.join(random.choices(string.digits, k=4))
    return base + rand

@login_required
@user_passes_test(admin_required)
def add_vendor(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        profile_image = request.FILES.get("profile_image")

        # Split full name
        first_name = ""
        last_name = ""
        if name:
            parts = name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            error_message = "Email already exists."
            return render(request, "vendor_add.html", {"error_message": error_message})

        try:
            with transaction.atomic():
                user = CustomUser.objects.create_user(
                    username=generate_username(email),
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    address=address,
                    role='vendor',
                    is_staff=False
                )
                if profile_image:
                    user.profile_image = profile_image
                    user.save()

                # ✅ Redirect with success query param
                return redirect("/vendors/list/?success=1")

        except IntegrityError:
            error_message = "An error occurred. Try again."
            return render(request, "vendor_add.html", {"error_message": error_message})

    return render(request, "vendor_add.html")

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from .models import CustomUser

def edit_vendor(request, vendor_id):
    vendor = get_object_or_404(CustomUser, id=vendor_id, role='vendor')
    
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        profile_image = request.FILES.get("profile_image")
        
        # Optional: Password update
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # Split full name into first and last name
        first_name = ""
        last_name = ""
        if name:
            parts = name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        try:
            with transaction.atomic():
                # Check if email already exists (excluding current vendor)
                if CustomUser.objects.filter(email=email).exclude(id=vendor.id).exists():
                    messages.error(request, "Email already exists.")
                    return render(request, "vendor_edit.html", {"vendor": vendor})

                # Update vendor details
                vendor.first_name = first_name
                vendor.last_name = last_name
                vendor.email = email
                vendor.username = email  # Update username to match email
                vendor.phone = phone
                vendor.address = address

                # Handle profile image
                if profile_image:
                    vendor.profile_image = profile_image

                # Handle password change if provided
                if new_password:
                    if new_password == confirm_password:
                        vendor.set_password(new_password)
                        messages.success(request, "Password updated successfully.")
                    else:
                        messages.error(request, "Passwords do not match.")
                        return render(request, "vendor_edit.html", {"vendor": vendor})

                vendor.save()

                # Redirect with success code 2 (Vendor updated successfully)
                return redirect(f"{reverse('vendors_list')}?success=2")

        except Exception as e:
            messages.error(request, f"Error updating vendor: {str(e)}")
            return render(request, "vendor_edit.html", {"vendor": vendor})

    # Pre-fill the name field by combining first and last name
    full_name = f"{vendor.first_name} {vendor.last_name}".strip()
    
    context = {
        'vendor': vendor,
        'full_name': full_name
    }
    return render(request, "vendor_edit.html", context)


@login_required
@user_passes_test(admin_required)
def vendor_list(request):
    vendors_qs = CustomUser.objects.filter(role='vendor').order_by('-id')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        vendors_qs = vendors_qs.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(vendors_qs, per_page)
    page_number = request.GET.get('page')
    try:
        vendors = paginator.page(page_number)
    except PageNotAnInteger:
        vendors = paginator.page(1)
    except EmptyPage:
        vendors = paginator.page(paginator.num_pages)

    # Toastify success messages from query param
    success_messages = {
        "1": "Vendor added successfully!",
        "2": "Vendor updated successfully!",
        "3": "Vendor deleted successfully!"
    }
    success_code = request.GET.get("success")
    success_message = success_messages.get(success_code, "")

    return render(request, "vendor_list.html", {
        "vendors": vendors,
        "per_page": per_page,
        "search_query": search_query,
        "success_message": success_message
    })