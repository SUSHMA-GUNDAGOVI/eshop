from django.shortcuts import render, redirect, get_object_or_404
from eshop_app.models import Product, Banner
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta
from decimal import Decimal
from urllib.parse import quote_plus
from django.urls import reverse
from eshop_app.models import Category
from django.contrib.auth.decorators import login_required
from eshop_app.models import Category, Brand
from eshop_app.models import CustomUser
from django.http import JsonResponse
from eshop_app.models import Contact
from django.core.mail import send_mail
from eshop_app.models import Blog
from eshop_app.models import AboutUs, Team, Client
from .models import Wishlist
from .models import Cart


def index(request):
    filter_type = request.GET.get('filter', 'all')
    
    all_products = Product.objects.filter(status='active')
    featured_products = Product.objects.filter(is_featured=True, status='active').order_by('-created_at')[:3]

    if filter_type == 'new-arrivals':
        all_products = all_products.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')
    elif filter_type == 'hot-sales':
        all_products = all_products.filter(price__lt=50).order_by('-price')
    else:
        all_products = all_products.order_by('-created_at')

    homepage_products = all_products[:9]
    banners = Banner.objects.all()
    
    # ✅ Add wishlisted_ids for authenticated users
    if request.user.is_authenticated:
        wishlisted_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    else:
        wishlisted_ids = []
    
    context = {
        'products': homepage_products,
        'total_products_count': all_products.count(),
        'filter_type': filter_type,
        'banners': banners,
        'featured_products': featured_products,
        'wishlisted_ids': wishlisted_ids,  # ✅ Pass this to template
    }
    
    return render(request, 'index.html', context)



def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Process sizes - split comma-separated string
    sizes = []
    if product.size:
        # Split by comma and remove any whitespace
        sizes = [size.strip() for size in product.size.split(',')]
    
    # Process colors
    colors = []
    if hasattr(product, 'color_data') and product.color_data:
        colors = product.color_data
    
    context = {
        'product': product,
        'sizes': sizes,  # Pass the processed list
        'colors': colors,
    }
    return render(request, 'product_details.html', context)


@login_required
def add_to_cart_view(request, product_id):
    """
    Adds a product to the cart if size and color are selected.
    Shows toast if already in cart or not selected.
    """
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id)

        selected_size = request.POST.get('size', '').strip()
        selected_color = request.POST.get('color', '').strip()

        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        redirect_url = reverse('product_detail', kwargs={'pk': product_id})

        # Validate size & color selection
        if not selected_size or not selected_color:
            # Neither size nor color selected
            return redirect(f"{redirect_url}?cart_invalid=1")

        # Check if the item already exists in cart
        cart_item = Cart.objects.filter(
            user=request.user,
            product=product,
            size=selected_size,
            color=selected_color
        ).first()

        if cart_item:
            # Already in cart
            return redirect(f"{redirect_url}?cart_exists=1")
        else:
            # Not in cart → create new
            Cart.objects.create(
                user=request.user,
                product=product,
                size=selected_size,
                color=selected_color,
                quantity=quantity
            )
            return redirect(f"{redirect_url}?cart_added=1")

    return redirect('product_detail', pk=product_id)


@login_required
def shopping_cart_view(request):
    """
    Show the shopping cart for the logged-in user
    """
    cart_items = Cart.objects.filter(user=request.user).select_related('product')

    cart_subtotal = Decimal('0.00')
    enriched_items = []

    for item in cart_items:
        line_total = item.subtotal
        cart_subtotal += line_total
        enriched_items.append({
            'product': item.product,
            'quantity': item.quantity,
            'size': item.size or 'N/A',
            'color': item.color or 'N/A',
            'price': item.product.price,
            'line_total': line_total,
            'item_id': item.id,  # ✅ DB id for removal
        })

    shipping_cost = Decimal('10.00')
    tax_rate = Decimal('0.05')
    tax_amount = (cart_subtotal * tax_rate).quantize(Decimal('0.01'))
    order_total = cart_subtotal + tax_amount + shipping_cost

    context = {
        'cart_items': enriched_items,
        'cart_subtotal': cart_subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'order_total': order_total,
    }

    return render(request, 'shopping_cart.html', context)


@login_required
@require_POST
def remove_from_cart_view(request):
    """
    Remove a cart item using its DB id (safer than parsing strings)
    """
    cart_id = request.POST.get('cart_id')
    if cart_id:
        try:
            cart_item = Cart.objects.get(id=cart_id, user=request.user)
            product_title = cart_item.product.title
            cart_item.delete()
            return redirect(f"{reverse('shopping_cart')}?cart_removed={product_title}")
        except Cart.DoesNotExist:
            pass
    return redirect('shopping_cart')

def shop_all_products(request):
    query = request.GET.get('q', '')  # Search term
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    size = request.GET.get('size')
    color = request.GET.get('color')
    sort_option = request.GET.get('sort')  # Sorting option

    # Base queryset
    products = Product.objects.filter(status='active').order_by('-created_at')

    # --- Filters ---
    if query:
        products = products.filter(title__icontains=query)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if size:
        products = products.filter(size__icontains=size)
    if color:
        products = products.filter(color_data__icontains=color)

    # --- Sorting logic ---
    if sort_option == 'low_to_high':
        products = products.order_by('price')
    elif sort_option == 'high_to_low':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')

    # --- Sidebar data ---
    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')

    # --- Sizes and colors ---
    sizes_list = ['xs', 's', 'm', 'l', 'xl', '2xl', 'xxl', '3xl', '4xl']
    colors_list = ['c-1','c-2','c-3','c-4','c-5','c-6','c-7','c-8','c-9']

    # --- Wishlist data ---
    if request.user.is_authenticated:
        wishlisted_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    else:
        wishlisted_ids = []

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'selected_size': size,
        'selected_color': color,
        'sizes_list': sizes_list,
        'colors_list': colors_list,
        'search_query': query,
        'selected_sort': sort_option,
        'wishlisted_ids': wishlisted_ids,  # ✅ Pass wishlisted product IDs
    }

    return render(request, 'shop_all.html', context)



def shop_by_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id, status='active')

    # Include main category + child categories
    if category.children.exists():
        child_ids = category.children.values_list('id', flat=True)
        all_ids = list(child_ids) + [category.id]
        products = Product.objects.filter(category_id__in=all_ids, status='active')
    else:
        products = Product.objects.filter(category_id=category.id, status='active')

    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')  # Always pass brands to sidebar

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_category': category,
        'selected_brand': None,
    }
    return render(request, 'shop_all.html', context)


def shop_by_brand(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id, status='active')
    products = Product.objects.filter(brand=brand, status='active')
    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_category': None,
        'selected_brand': brand,
    }
    return render(request, 'shop_all.html', context)

@login_required
def profile_view(request):
    user = request.user  # Get the logged-in user

    context = {
        'user': user,
    }
    return render(request, 'landing_profile.html', context)

@login_required
def edit_profile_view(request):
    user = request.user

    # ✅ Check for AJAX POST
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Get POST data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        if hasattr(user, 'phone'):
            user.phone = phone
        if hasattr(user, 'address'):
            user.address = address

        # Update profile image
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']

        # Save changes
        user.save()

        return JsonResponse({"status": "success", "message": "Profile updated successfully!"})

    # Normal GET request renders the edit form
    return render(request, 'landing_edit_profile.html', {'user': user})

def landing_contact(request):
    contact = Contact.objects.last()  # get latest contact info

    # Check if we have a success message in session
    success_message = request.session.pop('success_message', None)

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New Contact Message from {name}"
        full_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        recipient_list = ['vasant@crawlerstechnologies.com']

        try:
            send_mail(subject, full_message, email, recipient_list)
            # Store success message in session
            request.session['success_message'] = "Your message has been sent successfully! We will get back to you."
            return redirect('landing_contact')  # redirect to same page
        except Exception as e:
            success_message = f"Error sending message: {e}"

    return render(request, 'landing_contact.html', {'contact': contact, 'success_message': success_message})

def landing_blog(request):
    """
    Display all published blogs on the landing page.
    """
    blogs = Blog.objects.filter(status=1).order_by('-publish_date')  # only published
    context = {
        'blogs': blogs
    }
    return render(request, 'landing_blog.html', context)

def landing_blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug, status=1)
    return render(request, 'landing_blog_detail.html', {'blog': blog})
def landing_about_us(request):
    # Get AboutUs single record
    about = AboutUs.objects.first()

    # Get all team members
    team_members = Team.objects.all().order_by('id')

    # Get all active clients
    clients = Client.objects.filter(status='active').order_by('id')

    return render(request, "landing_about_us.html", {
        "about": about,
        "team_members": team_members,
        "clients": clients
    })

@login_required
def toggle_wishlist(request, product_id):
    if request.method == "POST":
        try:
            product = get_object_or_404(Product, pk=product_id)
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user, 
                product=product
            )

            if not created:
                wishlist_item.delete()
                is_added = False
            else:
                is_added = True

            # Get updated wishlist count
            wishlist_count = Wishlist.objects.filter(user=request.user).count()

            return JsonResponse({
                'status': 'ok', 
                'is_added': is_added,
                'wishlist_count': wishlist_count  # ✅ Return count
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request method'
    }, status=405)

@login_required
def wishlist_view(request):
    """
    Display all products in user's wishlist
    """
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist.html', context)
