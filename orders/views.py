from django.shortcuts import render, redirect, get_object_or_404
from eshop_app.models import Product, Banner
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from urllib.parse import quote_plus
from django.urls import reverse
from eshop_app.models import Category
from django.contrib.auth.decorators import login_required
from eshop_app.models import Category


def index(request):
    filter_type = request.GET.get('filter', 'all')
    products = Product.objects.filter(status='active')
    
    if filter_type == 'new-arrivals':
        products = products.filter(created_at__gte=timezone.now() - timedelta(days=7)).order_by('-created_at')
    elif filter_type == 'hot-sales':
        products = products.filter(price__lt=50).order_by('-price')
    else:
        products = products.order_by('-created_at')
    
    banners = Banner.objects.all()  # Add this line
    
    context = {
        'products': products,
        'filter_type': filter_type,
        'banners': banners,  # Add this line
    }
    
    return render(request, 'index.html', context)




def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    context = {'product': product}
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


def add_to_cart_view(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
            
        selected_size = request.POST.get('size', 'N/A')
        selected_color = request.POST.get('color', 'N/A')

        # 3. Create a unique identifier for this specific cart item 
        item_key = f"{product_id}-{selected_size}-{selected_color}"

        # 4. Initialize the cart in the session if it doesn't exist
        item_key = f"{product_id}-{selected_size}-{selected_color}"
        cart = request.session.get('cart', {})
        
        if item_key in cart:
            cart[item_key]['quantity'] += quantity
        else:
            cart[item_key] = {
                'product_id': product_id,
                'quantity': quantity,
                'price': str(product.price), 
                'price': str(product.price),
                'title': product.title,
                'size': selected_size,
                'color': selected_color,
            }

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
        redirect_url = redirect('product_detail', pk=product_id).url
        return redirect(f"{redirect_url}?cart_added={product.title}") 

    return redirect('product_detail', pk=product_id)


def shopping_cart_view(request):
    session_cart = request.session.get('cart', {})
    cart_items = []
    cart_subtotal = Decimal('0.00')
    
    for item_key, item_data in session_cart.items():
        product_id = item_data.get('product_id')
        quantity = item_data.get('quantity', 0)
        if quantity <= 0:
            continue
            
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            continue
            
        item_price = Decimal(item_data.get('price', product.price))
        line_total = item_price * quantity
        cart_subtotal += line_total
        
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'size': item_data.get('size', 'N/A'),
            'color': item_data.get('color', 'N/A'),
            'price': item_price,
            'line_total': line_total,
            'item_key': item_key,
        })

    shipping_cost = Decimal('10.00')
    tax_rate = Decimal('0.05')
    tax_amount = (cart_subtotal * tax_rate).quantize(Decimal('0.01'))
    order_total = cart_subtotal + tax_amount + shipping_cost

    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'order_total': order_total,
    }
    
    return render(request, 'shopping_cart.html', context)


def remove_from_cart_view(request):
    if request.method == 'POST':
        item_key = request.POST.get('item_key')
        cart = request.session.get('cart', {})

        if item_key and item_key in cart:
            product_title = cart[item_key].get('title', 'An item') 
            del cart[item_key]
            request.session['cart'] = cart
            request.session.modified = True
            redirect_url = redirect('shopping_cart').url
            return redirect(f"{redirect_url}?cart_removed={product_title}") 

    return redirect('shopping_cart')

def shop_all_products(request):
    # Fetch all products
    products = Product.objects.filter(status='active').order_by('-created_at')

    # Fetch parent categories with their children
    parent_cats = Category.objects.filter(is_parent=True, status='active').prefetch_related('children')

    context = {
        'products': products,
        'parent_cats': parent_cats,
    }

    return render(request, 'shop_all.html', context)


def shop_by_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id, status='active')

    if category.is_parent:
        # Include all child categories' products
        child_ids = category.children.values_list('id', flat=True)
        products = Product.objects.filter(category_id__in=child_ids, status='active')
    else:
        products = Product.objects.filter(category_id=category.id, status='active')

    parent_cats = Category.objects.filter(is_parent=True, status='active').prefetch_related('children')

    context = {
        'products': products,
        'parent_cats': parent_cats,
        'selected_category': category,
    }

    return render(request, 'shop_all.html', context)





