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
from eshop_app.models import Blog, Coupon
from eshop_app.models import AboutUs, Team, Client
from .models import Wishlist, Address
from .models import Cart
from django.db.models import Q
from django.template.loader import render_to_string
from django.db import transaction
from django.db.models import Max 
from eshop_app.models import GeneralFAQ
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages



def index(request):
    filter_type = request.GET.get('filter', 'all')

    # Base queryset
    all_products = Product.objects.filter(status='active')

    # Featured Products
    featured_products = Product.objects.filter(is_featured=True, status='active').order_by('-created_at')

    # Hot & Discounted Products for Carousel
    hot_discounted_products = (
        Product.objects.filter(
            Q(condition__iexact='Hot') | Q(discount__isnull=False),
            status='active',
            deal_end_date__isnull=False
        )
        .exclude(discount=0)
        .filter(deal_end_date__gte=timezone.now())
        .order_by('-discount', '-created_at')[:10]
    )

    # Filtering logic for main product grid
    if filter_type == 'new-arrivals':
        all_products = all_products.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')
    elif filter_type == 'hot-sales':
        all_products = all_products.filter(price__lt=50).order_by('-price')
    else:
        all_products = all_products.order_by('-created_at')

    homepage_products = all_products[:9]

    # Banners
    banners = Banner.objects.all()

    # ✅ Fetch only Parent Categories (Main Categories like Men, Women, Kids)
    parent_categories = Category.objects.filter(is_parent=True, status='active').order_by('title')

    # Wishlist logic
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
        'wishlisted_ids': wishlisted_ids,
        'hot_discounted_products': hot_discounted_products,
        'categories': parent_categories,  # ✅ pass to template
    }

    return render(request, 'index.html', context)

def category_products(request, id):
    # --- Get main category ---
    main_category = get_object_or_404(Category, pk=id, status='active')

    # --- Get all query parameters ---
    query = request.GET.get('q', '')
    brand_id = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    size = request.GET.get('size')
    color = request.GET.get('color')
    sort_option = request.GET.get('sort', 'low_to_high')
    subcategory_id = request.GET.get('subcategory')

    # --- Base queryset ---
    products = Product.objects.filter(status='active')

    # --- Category & Subcategory Filtering ---
    if subcategory_id and subcategory_id != '':  # Fixed: Check for empty string too
        # Filter by selected subcategory
        products = products.filter(
            Q(category_id=subcategory_id) | Q(child_category_id=subcategory_id)
        )
        selected_subcat_id = int(subcategory_id)  # Convert to int for comparison
    else:
        # Include main category and all its children
        child_ids = main_category.children.filter(status='active').values_list('id', flat=True)
        products = products.filter(
            Q(category_id=main_category.id) |
            Q(category_id__in=child_ids) |
            Q(child_category_id__in=child_ids)
        )
        selected_subcat_id = None

    # --- Brand filter ---
    if brand_id:
        try:
            brand_id_int = int(brand_id)
            products = products.filter(brand_id=brand_id_int)
            selected_brand_id = brand_id_int
        except (ValueError, TypeError):
            brand_id = None
            selected_brand_id = None
    else:
        selected_brand_id = None

    # --- Search ---
    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # --- Price range filter ---
    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except (ValueError, TypeError):
            min_price = None
    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except (ValueError, TypeError):
            max_price = None

    # --- Size filter ---
    if size:
        products = products.filter(size__icontains=size)

    # --- Color filter ---
    if color:
        products = products.filter(color_data__icontains=color)

    # --- Sorting logic ---
    if sort_option == 'low_to_high':
        products = products.order_by('price')
    elif sort_option == 'high_to_low':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')

    # --- Sidebar Data ---
    subcategories = main_category.children.filter(status='active')
    brands = Brand.objects.filter(status='active').order_by('title')
    sizes_list = ['xs', 's', 'm', 'l', 'xl', '2xl', 'xxl', '3xl', '4xl']
    colors_list = ['c-1', 'c-2', 'c-3', 'c-4', 'c-5', 'c-6', 'c-7', 'c-8', 'c-9']

    # --- Wishlist Data ---
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    # --- Context ---
    context = {
        'main_category': main_category,
        'subcategories': subcategories,
        'products': products,
        'brands': brands,
        'selected_brand_id': selected_brand_id,
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'selected_size': size,
        'selected_color': color,
        'sizes_list': sizes_list,
        'colors_list': colors_list,
        'search_query': query,
        'selected_sort': sort_option,
        'wishlisted_ids': wishlisted_ids,
        'selected_subcat_id': selected_subcat_id,  # This will be None when no subcategory is selected
    }

    return render(request, 'category_products.html', context)


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # ✅ Handle sizes cleanly
    sizes = [s.strip() for s in product.size.split(',')] if product.size else []

    colors = []
    primary_color = None
    gallery_images = []

    # ✅ Build color-based gallery
    if hasattr(product, 'color_data') and product.color_data:
        for color in product.color_data:
            color_name = color.get('name')
            if not color_name:
                continue

            media = product.media_files.filter(
                file_type='image',
                color_name__iexact=color_name
            )

            if media.exists():
                ordered = list(media.order_by('-is_primary', '-id'))
                color['images'] = [m.file.url for m in ordered]
                color['thumb'] = ordered[0].file.url
                colors.append(color)

        if colors:
            primary_color = colors[0]['name']
            gallery_images = colors[0]['images']

    # ✅ Fallback: no color-specific images
    if not gallery_images:
        gallery_images = [
            m.file.url for m in product.media_files.filter(file_type='image').order_by('-is_primary', '-id')
        ]

    # ✅ Mark active color
    for color in colors:
        color['is_current'] = (color['name'] == primary_color)

    # ✅ Get related products
    top_category = product.category
    while top_category and top_category.parent:
        top_category = top_category.parent

    subcategories = Category.objects.filter(parent=top_category)

    related_products = Product.objects.filter(
        Q(category=top_category) | Q(category__in=subcategories)
    ).exclude(pk=pk).order_by('-id')[:8]

    # ✅ Get wishlisted items for current user
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    context = {
        "product": product,
        "sizes": sizes,
        "colors": colors,
        "gallery_images": gallery_images,
        "primary_color": primary_color,
        "related_products": related_products,
        "wishlisted_ids": wishlisted_ids,
    }

    return render(request, "product_details.html", context)


@login_required
def add_to_cart_view(request, product_id):
    """
    Adds a product to the cart if size and color are selected.
    Stores selected image as well.
    Shows toast if already in cart or not selected.
    """
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id)

        selected_size = request.POST.get('size', '').strip()
        selected_color = request.POST.get('selected_color', '').strip() or request.POST.get('color', '').strip()
        selected_image = request.POST.get('selected_image', '').strip()

        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        redirect_url = reverse('product_detail', kwargs={'pk': product_id})

        # ✅ Validate size & color selection
        if not selected_size or not selected_color:
            return redirect(f"{redirect_url}?cart_invalid=1")

        # ✅ Check if the same product variant already exists in the cart
        cart_item = Cart.objects.filter(
            user=request.user,
            product=product,
            size=selected_size,
            color=selected_color
        ).first()

        if cart_item:
            # ✅ Already in cart
            return redirect(f"{redirect_url}?cart_exists=1")
        else:
            # ✅ Create new cart item and store image
            Cart.objects.create(
                user=request.user,
                product=product,
                size=selected_size,
                color=selected_color,
                quantity=quantity,
                selected_image=selected_image  # ← store image URL/path here
            )
            return redirect(f"{redirect_url}?cart_added=1")

    return redirect('product_detail', pk=product_id)

def cart_preview(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')[:3]
    html = render_to_string('cart_preview.html', {'cart_items': cart_items})
    return JsonResponse({'html': html})


@login_required
@login_required
def shopping_cart_view(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')

    if not cart_items.exists():
        return redirect('shop_all')

    cart_subtotal = Decimal('0.00')
    total_shipping = Decimal('0.00')
    product_discount_total = Decimal('0.00')
    all_free_shipping = True
    enriched_items = []

    # --- Calculate per-item and subtotal ---
    for item in cart_items:
        product = item.product
        qty = item.quantity or 1
        price = Decimal(product.price or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount_percent = Decimal(product.discount or 0)

        per_unit_discount = (price * discount_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if discount_percent > 0 else Decimal('0.00')
        line_original = (price * qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        line_discount = (per_unit_discount * qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        line_after_discount = (line_original - line_discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        cart_subtotal += line_after_discount
        product_discount_total += line_discount

        # Shipping
        if hasattr(product, 'shipping_label') and product.shipping_label == 'free':
            product_shipping = Decimal('0.00')
        else:
            product_shipping = Decimal(str(getattr(product, 'shipping_charge', 10.00))).quantize(Decimal('0.01'))
            all_free_shipping = False

        total_shipping += product_shipping

        image_url = item.selected_image or (getattr(product.photo, 'url', '') if getattr(product, 'photo', None) else "")

        enriched_items.append({
            'product': product,
            'quantity': qty,
            'size': item.size or 'N/A',
            'color': item.color or 'N/A',
            'price': price,
            'discount_percent': discount_percent,
            'per_unit_discount': per_unit_discount,
            'line_original': line_original,
            'line_discount': line_discount,
            'line_after_discount': line_after_discount,
            'item_id': item.id,
            'shipping_charge': product_shipping,
            'selected_image': image_url,
        })

    if all_free_shipping:
        total_shipping = Decimal('0.00')

    # --- Apply coupon if present ---
    applied_coupon = request.session.get('applied_coupon')
    coupon_amount = Decimal('0.00')

    if applied_coupon:
        discount_type = applied_coupon.get('discount_type')
        discount_value = Decimal(applied_coupon.get('discount_value') or 0)
        
        # Calculate coupon discount based on CART SUBTOTAL only (before shipping)
        if discount_type == 'percent':
            coupon_amount = (cart_subtotal * discount_value / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            coupon_amount = min(discount_value, cart_subtotal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Calculate final total: (subtotal - coupon) + shipping
        order_total = (cart_subtotal - coupon_amount + total_shipping).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        order_total = (cart_subtotal + total_shipping).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # --- Coupons list ---
    now = timezone.now()
    coupons = Coupon.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)

    context = {
        'cart_items': enriched_items,
        'cart_subtotal': cart_subtotal.quantize(Decimal('0.01')),
        'shipping_cost': total_shipping.quantize(Decimal('0.01')),
        'product_discount_total': product_discount_total.quantize(Decimal('0.01')),
        'order_total': order_total,
        'coupons': coupons,
        'applied_coupon': applied_coupon,
        'discount_amount': coupon_amount,
    }

    return render(request, 'shopping_cart.html', context)

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        now = timezone.now()

        try:
            coupon = Coupon.objects.get(
                code=code,
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            )
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code.")
            request.session.pop('applied_coupon', None)
            return redirect('shopping_cart')

        cart_items = Cart.objects.filter(user=request.user).select_related('product')

        # Calculate cart subtotal EXACTLY the same way as shopping_cart_view
        cart_subtotal = Decimal('0.00')
        total_shipping = Decimal('0.00')
        all_free_shipping = True

        for item in cart_items:
            product = item.product
            qty = item.quantity or 1
            price = Decimal(product.price or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            discount_percent = Decimal(product.discount or 0)

            # Calculate exactly like shopping_cart_view
            per_unit_discount = (price * discount_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if discount_percent > 0 else Decimal('0.00')
            line_original = (price * qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            line_discount = (per_unit_discount * qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            line_after_discount = (line_original - line_discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            cart_subtotal += line_after_discount

            # Shipping calculation
            if hasattr(product, 'shipping_label') and product.shipping_label == 'free':
                product_shipping = Decimal('0.00')
            else:
                product_shipping = Decimal(str(getattr(product, 'shipping_charge', 10.00))).quantize(Decimal('0.01'))
                all_free_shipping = False
            total_shipping += product_shipping

        if all_free_shipping:
            total_shipping = Decimal('0.00')

        # Check minimum order amount based on SUBTOTAL (not including shipping)
        if cart_subtotal < coupon.min_order_amount:
            messages.error(request, f"Coupon requires minimum order of ₹{coupon.min_order_amount}")
            request.session.pop('applied_coupon', None)
            return redirect('shopping_cart')

        # Calculate discount amount based on SUBTOTAL only
        if coupon.discount_type == 'percent':
            discount_amount = (cart_subtotal * coupon.discount_value / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            discount_amount = min(coupon.discount_value, cart_subtotal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Store in session
        request.session['applied_coupon'] = {
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'discount_amount': str(discount_amount),
            'min_order_amount': str(coupon.min_order_amount),
        }

        messages.success(request, f"Coupon {coupon.code} applied successfully!")
        return redirect('shopping_cart')

    return redirect('shopping_cart')


def remove_coupon(request):
    """
    Remove any applied coupon from session
    """
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
    return redirect('shopping_cart')


@login_required
def remove_from_cart_view(request):
    """
    Remove a cart item - handles both AJAX and regular POST
    """
    if request.method == 'POST':
        # Try to get item_id from POST data
        item_id = request.POST.get('item_id')
        
        print(f"DEBUG: item_id received = {item_id}")  # Debug
        print(f"DEBUG: All POST data = {request.POST}")  # Debug
        
        if item_id:
            try:
                cart_item = Cart.objects.get(id=item_id, user=request.user)
                product_title = cart_item.product.title
                cart_item.delete()
                
                # Check if AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': f'{product_title} was removed from your cart.'
                    })
                else:
                    return redirect(f"{reverse('shopping_cart')}?cart_removed={product_title}")
                    
            except Cart.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Item not found in cart.'
                    }, status=404)
                else:
                    return redirect('shopping_cart')
        else:
            # item_id is missing
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Item ID is missing from request.'
                }, status=400)
            else:
                return redirect('shopping_cart')
    
    return redirect('shopping_cart')

def shop_all_products(request):
    # Get all query parameters
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    size = request.GET.get('size')
    color = request.GET.get('color')
    sort_option = request.GET.get('sort', 'low_to_high')

    # Base queryset
    products = Product.objects.filter(status='active')
    
    # Context variables for tracking selected filters
    selected_category = None
    selected_parent_id = None
    is_parent_active = False  # Define at function scope

    # --- Apply Filters ---
    
    # Category filter
    if category_id:
        try:
            category = Category.objects.get(pk=category_id, status='active')
            selected_category = category
            
            # Determine the set of category IDs to filter products by
            if category.is_parent:
                # If parent is selected, include products assigned to parent OR any child
                child_ids = category.children.filter(status='active').values_list('id', flat=True)
                
                # Filter products that have:
                # 1. category_id = parent.id OR
                # 2. category_id in child_ids OR
                # 3. child_category_id in child_ids
                products = products.filter(
                    Q(category_id=category.id) |
                    Q(category_id__in=child_ids) |
                    Q(child_category_id__in=child_ids)
                )
                selected_parent_id = category.id
                is_parent_active = True
            else:
                # If subcategory (child) is selected, show products assigned to this child
                # Products can be assigned via category_id OR child_category_id
                products = products.filter(
                    Q(category_id=category.id) | 
                    Q(child_category_id=category.id)
                )
                # Find the parent of the subcategory for sidebar highlighting
                if category.parent:
                    selected_parent_id = category.parent.id
                    is_parent_active = True
        except Category.DoesNotExist:
            category_id = None
    
    # Brand filter
    if brand_id:
        try:
            brand_id_int = int(brand_id)
            products = products.filter(brand_id=brand_id_int)
        except (ValueError, TypeError):
            brand_id = None
    
    # Search query
    if query:
        products = products.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Price range filter
    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except (ValueError, TypeError):
            min_price = None
    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except (ValueError, TypeError):
            max_price = None
    
    # Size filter - handle comma-separated sizes in product
    if size:
        products = products.filter(size__icontains=size)
    
    # Color filter - search in color_data JSONField
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
    parent_cats = Category.objects.filter(
        is_parent=True, 
        status='active'
    ).prefetch_related('children')
    
    brands = Brand.objects.filter(status='active').order_by('title')

    # --- Sizes and colors ---
    sizes_list = ['xs', 's', 'm', 'l', 'xl', '2xl', 'xxl', '3xl', '4xl']
    colors_list = ['c-1', 'c-2', 'c-3', 'c-4', 'c-5', 'c-6', 'c-7', 'c-8', 'c-9'] 

    # --- Wishlist data ---
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    # Convert brand_id to int for template comparison
    selected_brand_id = None
    if brand_id:
        try:
            selected_brand_id = int(brand_id)
        except (ValueError, TypeError):
            pass

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_category': selected_category,
        'selected_parent_id': selected_parent_id,
        'selected_brand_id': selected_brand_id,
        'is_parent_active': is_parent_active,
        
        # Filter values
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'selected_size': size,
        'selected_color': color,
        'sizes_list': sizes_list,
        'colors_list': colors_list,
        'search_query': query,
        'selected_sort': sort_option,
        'wishlisted_ids': wishlisted_ids,
    }

    return render(request, 'shop_all.html', context)



def shop_by_category(request, category_id):
    """
    Display products filtered by category (handles both parent and child categories)
    """
    # Get main or subcategory
    category = get_object_or_404(Category, pk=category_id, status='active')

    # If it's a parent category, include all child categories + itself
    if category.is_parent:
        child_ids = category.children.filter(status='active').values_list('id', flat=True)
        
        # Products can be assigned to:
        # 1. Parent category directly (category_id = parent.id)
        # 2. Child category via category_id
        # 3. Child category via child_category_id
        products = Product.objects.filter(
            Q(category_id=category.id) |
            Q(category_id__in=child_ids) |
            Q(child_category_id__in=child_ids),
            status='active'
        ).distinct()
    else:
        # Subcategory – show products assigned via category_id OR child_category_id
        products = Product.objects.filter(
            Q(category_id=category.id) | 
            Q(child_category_id=category.id),
            status='active'
        ).distinct()

    # Sidebar data
    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')

    # Wishlist data
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_category': category,
        'wishlisted_ids': wishlisted_ids,
    }
    return render(request, 'shop_all.html', context)


def shop_by_brand(request, brand_id):
    """
    Display products filtered by brand
    """
    brand = get_object_or_404(Brand, pk=brand_id, status='active')
    products = Product.objects.filter(brand=brand, status='active')
    
    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')

    # Wishlist data
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_category': None,
        'selected_brand': brand,
        'wishlisted_ids': wishlisted_ids,
    }
    return render(request, 'shop_all.html', context)


def shop_by_color(request, color):
    """
    Display products filtered by color
    """
    products = Product.objects.filter(color_data__icontains=color, status='active')

    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')

    # Wishlist data
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_color': color,
        'selected_category': None,
        'selected_brand': None,
        'selected_size': None,
        'wishlisted_ids': wishlisted_ids,
    }
    return render(request, 'shop_all.html', context)


# --- Shop by Size ---
def shop_by_size(request, size):
    """
    Display products filtered by size
    """
    products = Product.objects.filter(size__icontains=size, status='active')

    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')

    # Wishlist data
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_size': size,
        'selected_category': None,
        'selected_brand': None,
        'selected_color': None,
        'wishlisted_ids': wishlisted_ids,
    }
    return render(request, 'shop_all.html', context)


def shop_by_price(request, min_price, max_price):
    """
    Display products filtered by price range
    """
    products = Product.objects.filter(
        price__gte=min_price, 
        price__lte=max_price, 
        status='active'
    )

    parent_cats = Category.objects.filter(is_parent=True, status='active')
    brands = Brand.objects.filter(status='active')

    # Wishlist data
    if request.user.is_authenticated:
        wishlisted_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    else:
        wishlisted_ids = []

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'brands': brands,
        'selected_price_range': f"{min_price}-{max_price}",
        'selected_category': None,
        'selected_brand': None,
        'selected_color': None,
        'selected_size': None,
        'wishlisted_ids': wishlisted_ids,
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

def wishlist_preview(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')[:3]  # Show only 3
    html = render_to_string('wishlist_preview.html', {'wishlist_items': wishlist_items})
    return JsonResponse({'html': html})


def buy_now_view(request, pk):
    # ✅ Remove any previously applied coupon when entering Buy Now page
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']

    product = get_object_or_404(Product, pk=pk)
    size = request.GET.get('size')
    color = request.GET.get('color')
    quantity = int(request.GET.get('quantity', 1))
    order_total = Decimal(str(product.price)) * Decimal(str(quantity))

    now = timezone.now()

    # ✅ Fetch only valid coupons
    coupons = Coupon.objects.filter(
        is_active=True,
        min_order_amount__lte=order_total,
        start_date__lte=now
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    )

    valid_coupons = []
    for coupon in coupons:
        if coupon.usage_limit > 0 and hasattr(coupon, "used_count"):
            if coupon.used_count >= coupon.usage_limit:
                continue
        if coupon.per_user_limit > 0 and hasattr(coupon, "used_by_user_count"):
            if coupon.used_by_user_count >= coupon.per_user_limit:
                continue
        valid_coupons.append(coupon)

    # ✅ Fetch user's saved addresses (if logged in)
    addresses = []
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-id')

    context = {
        'product': product,
        'selected_size': size,
        'selected_color': color,
        'quantity': quantity,
        'order_total': order_total,
        'coupons': valid_coupons,
        'addresses': addresses,  # ✅ Pass addresses to template
    }

    return render(request, 'buy_now.html', context)

def checkout_view(request):
    """
    Display checkout page with proper shipping calculation.
    """
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        return redirect('shopping_cart')

    subtotal = Decimal('0.00')
    total_shipping = Decimal('0.00')
    all_free_shipping = True
    enriched_items = []

    for item in cart_items:
        product = item.product
        line_total = item.subtotal
        subtotal += line_total

        # ✅ Calculate shipping per product
        shipping_label = getattr(product, 'shipping_label', '')
        shipping_charge = getattr(product, 'shipping_charge', Decimal('0.00'))

        # If product has explicit free shipping
        if shipping_label == 'free' or shipping_charge == 0:
            product_shipping = Decimal('0.00')
        else:
            product_shipping = Decimal(str(shipping_charge))
            all_free_shipping = False

        total_shipping += product_shipping

        enriched_items.append({
            'product': product,
            'quantity': item.quantity,
            'line_total': line_total,
            'shipping_charge': product_shipping,
        })

    # ✅ Automatic Free Shipping condition (only if total >= 1000)
    # if subtotal >= 1000:
    #     total_shipping = Decimal('0.00')
    # ❌ Don’t force free shipping just because all items are labeled free — only skip if subtotal < 1000.

    # ✅ Apply coupon if available
    applied_coupon = request.session.get('applied_coupon')
    discount_amount = Decimal('0.00')
    if applied_coupon:
        discount_amount = Decimal(applied_coupon['discount_amount'])

    total = subtotal + total_shipping - discount_amount

    # ✅ Fetch saved addresses
    addresses = Address.objects.filter(user=request.user)

    context = {
        'cart_items': enriched_items,
        'subtotal': subtotal,
        'shipping_charge': total_shipping,
        'discount_amount': discount_amount,
        'total': total,
        'applied_coupon': applied_coupon,
        'addresses': addresses,
    }

    return render(request, 'checkout.html', context)


@login_required
def account_address(request):
    addresses = Address.objects.filter(user=request.user).order_by('-id')
    return render(request, 'account_address.html', {'addresses': addresses})

@login_required
def account_profile(request):
    return render(request, 'orders/account_profile.html')

@login_required
def add_address(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        street = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        address_type = request.POST.get('address_type')
        is_default = True if request.POST.get('is_default') == 'true' else False

        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            street_address=street,
            city=city,
            state=state,
            zip_code=zip_code,
            address_type=address_type,
            is_default=is_default,
        )
        return redirect('account_address')
    return redirect('account_address')

@login_required
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        return redirect('account_address')  # Redirect to the address list page
    return redirect('account_address')

@login_required
def edit_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        address.full_name = request.POST.get('full_name')
        address.phone = request.POST.get('phone')
        address.street_address = request.POST.get('street_address')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.zip_code = request.POST.get('zip_code')
        address.address_type = request.POST.get('address_type')
        address.is_default = True if request.POST.get('is_default') == 'true' else False
        address.save()
        return redirect('account_address')

    return redirect('account_address')

def faqs_view(request):
   """
    Fetches all active General FAQs, sorted by the 'order' field.
    The template will display them in one long accordion.
    """
    
    # Fetch only active FAQs, ordered simply by the 'order' field
   active_faqs = GeneralFAQ.objects.filter(is_active=True)
    
    # The QuerySet ordering handles the sorting now: .order_by('order', '-created_at')
    
   context = {
        'faqs_list': active_faqs, # Changed context variable name for clarity
    }
    
   return render(request, 'landing_faq.html', context)

def shipping_policy_view(request):
    return render(request, 'shipping_policy.html')

def track_order_view(request):
    return render(request, 'track_order.html')

def return_policy_view(request):
    return render(request, 'return_policy.html')





