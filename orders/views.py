from django.shortcuts import render, redirect, get_object_or_404
from eshop_app.models import Product, Banner
from django.utils import timezone
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


def index(request):
    filter_type = request.GET.get('filter', 'all')
    
    # All active products
    all_products = Product.objects.filter(status='active')
    
    # Only featured products for the banner (3 most recent)
    featured_products = Product.objects.filter(is_featured=True, status='active').order_by('-created_at')[:3]

    # Apply filters for main product listing
    if filter_type == 'new-arrivals':
        all_products = all_products.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')
    elif filter_type == 'hot-sales':
        all_products = all_products.filter(price__lt=50).order_by('-price')
    else:
        all_products = all_products.order_by('-created_at')

    # Slice for homepage: 3 rows, 3 products per row = 9 products
    homepage_products = all_products[:9]

    # Fetch banners if needed
    banners = Banner.objects.all()
    
    context = {
        'products': homepage_products,       # only 9 products for homepage
        'total_products_count': all_products.count(),  # to show Read More button
        'filter_type': filter_type,
        'banners': banners,
        'featured_products': featured_products,
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


def add_to_cart_view(request, product_id):
    """
    Handles adding a product and its options (quantity, size, color) to the cart 
    stored in the user's session.
    """
    if request.method == 'POST':
        
        # 1. Get the product object or return a 404 error
        product = get_object_or_404(Product, pk=product_id)

        # 2. Extract data from the POST request
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
            
        selected_size = request.POST.get('size', 'N/A')
        selected_color = request.POST.get('color', 'N/A')

        # 3. Create a unique identifier for this specific cart item 
        item_key = f"{product_id}-{selected_size}-{selected_color}"

        # 4. Initialize the cart in the session if it doesn't exist
        cart = request.session.get('cart', {})
        
        # 5. Add or update the item in the cart
        if item_key in cart:
            cart[item_key]['quantity'] += quantity
        else:
            cart[item_key] = {
                'product_id': product_id,
                'quantity': quantity,
                'price': str(product.price), 
                'title': product.title,
                'size': selected_size,
                'color': selected_color,
            }

        # 6. Save the modified cart back to the session
        request.session['cart'] = cart
        request.session.modified = True
        
        # 7. Redirect the user back to the product detail page (FIXED)
        
        # A. Safely encode the product name for the URL
        product_name_encoded = quote_plus(product.title) # 👈 Correct encoding
        
        # B. Get the base URL
        redirect_url = reverse('product_detail', kwargs={'pk': product_id}) 
        
        # C. Redirect with the correctly encoded parameter
        return redirect(f"{redirect_url}?cart_added={product_name_encoded}") 

    # If the request method is not POST, redirect back.
    return redirect('product_detail', pk=product_id)


def shopping_cart_view(request):
    """
    Renders the shopping cart page, processing items stored in the session.
    """
    # 1. Get the cart data from the session
    # Defaults to an empty dictionary if the cart doesn't exist
    session_cart = request.session.get('cart', {})
    
    cart_items = []
    cart_subtotal = Decimal('0.00')
    
    # 2. Iterate through the session cart to fetch product details and calculate totals
    for item_key, item_data in session_cart.items():
        
        # item_key looks like "4-L-Blue"
        product_id = item_data.get('product_id')
        print(product_id)
        quantity = item_data.get('quantity', 0)
        
        # Skip if quantity is 0 or less
        if quantity <= 0:
            continue
            
        try:
            # Fetch the actual Product object from the database
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            # Handle case where the product may have been deleted
            # You might want to remove this item from the session cart here,
            # but for simplicity, we'll just skip it for now.
            continue
            
        # Get the price (ensure it's treated as a Decimal for calculations)
        # We stored the price as a string in add_to_cart_view to avoid serialization issues
        item_price = Decimal(item_data.get('price', product.price))
        
        # Calculate line total
        line_total = item_price * quantity
        cart_subtotal += line_total
        
        # 3. Compile the enriched item data for the template
        cart_items.append({
            'product': product,          # The full Product object
            'quantity': quantity,
            'size': item_data.get('size', 'N/A'),
            'color': item_data.get('color', 'N/A'),
            'price': item_price,
            'line_total': line_total,
            # Pass the unique key to help with update/remove views later
            'item_key': item_key,
        })

    # 4. Calculate final totals (e.g., tax, shipping)
    # NOTE: You will need to define your own logic for these values!
    shipping_cost = Decimal('10.00')  # Example fixed shipping
    tax_rate = Decimal('0.05')        # Example 5% tax
    
    tax_amount = (cart_subtotal * tax_rate).quantize(Decimal('0.01'))
    order_total = cart_subtotal + tax_amount + shipping_cost

    # 5. Prepare the context dictionary
    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'order_total': order_total,
    }
    
    # 6. Render the template
    return render(request, 'shopping_cart.html', context)


def remove_from_cart_view(request):
    """
    Removes a specific item from the session cart based on item_key
    and redirects with a parameter for Toastify notification.
    """
    if request.method == 'POST':
        item_key = request.POST.get('item_key')
        cart = request.session.get('cart', {})

        if item_key and item_key in cart:
            try:
                # Get the product title before deletion for the toast message
                product_title = cart[item_key].get('title', 'An item') 
                
                # Remove the item dictionary from the cart
                del cart[item_key]
                
                # Save the modified cart back to the session
                request.session['cart'] = cart
                request.session.modified = True

                # Redirect back to the shopping cart page with a success parameter
                redirect_url = redirect('shopping_cart').url
                
                # Use a specific message to display in Toastify
                return redirect(f"{redirect_url}?cart_removed={product_title}") 
                
            except Exception as e:
                # Should handle critical error if session or key logic fails
                print(f"Error removing item: {e}")
                pass # Fall through to default redirect

    # If item removal fails or request is not POST, redirect to the cart page
    return redirect('shopping_cart')


def shop_all_products(request):
    query = request.GET.get('q', '')  # Search term
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    size = request.GET.get('size')
    color = request.GET.get('color')
    sort_option = request.GET.get('sort')  # ✅ New field for sorting

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
    sizes_list = ['xs','s','m','l','xl','2xl','xxl','3xl','4xl']
    colors_list = ['c-1','c-2','c-3','c-4','c-5','c-6','c-7','c-8','c-9']

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
        'selected_sort': sort_option,  # ✅ Add this to remember selection
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