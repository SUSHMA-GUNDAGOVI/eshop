from django.shortcuts import render
from django.http import JsonResponse
from eshop_app.models import Banner
from .serializers import ProductSerializer
from rest_framework.views import APIView
from eshop_app.models import Product 
from rest_framework.response import Response
from rest_framework import status
from .serializers import CategorySerializer
from eshop_app.models import Category
from rest_framework import serializers
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
# from .models import Product, Order
from eshop_app.models import Product
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


#API
def banner_api(request):
    banners = Banner.objects.filter(status='active')
    banner_list = []
    for banner in banners:
        banner_list.append({
            'id': banner.id,
            'title': banner.title,
            'description': banner.description,
            'image_url': request.build_absolute_uri(banner.photo.url)
        })
    return JsonResponse(banner_list, safe=False)

 
class CategoryListAPI(APIView):
    def get(self, request):
        # Fetch only active main (parent) categories
        categories = Category.objects.filter(status='active', is_parent=True).order_by('title')

        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class SubCategoryListAPI(APIView):
    def get(self, request, category_id):
        subcategories = Category.objects.filter(
            status='active',
            is_parent=False,
            parent_id=category_id
        ).order_by('title')

        serializer = CategorySerializer(subcategories, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class ProductListAPI(APIView):
    def get(self, request):
        # Fetch all active products
        products = Product.objects.filter(status='active').order_by('-created_at')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductListByCategoryAPI(APIView):
    def get(self, request, category_id):
        try:
            # Fetch products where either category OR child_category matches the given category_id
            products = Product.objects.filter(
                Q(category_id=category_id) | Q(child_category_id=category_id),
                status='active'
            ).order_by('-created_at')

            serializer = ProductSerializer(products, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#Landing Page
def index(request):
    filter_type = request.GET.get('filter', 'all')
    products = Product.objects.filter(status='active')
    
    # 1. New Arrivals: Filter for products created in the last 7 days.
    if filter_type == 'new-arrivals':
        products = products.filter(created_at__gte=timezone.now() - timedelta(days=7))
        products = products.order_by('-created_at') # Newest first
        
    # 2. Hot Sales: Filter for products priced under 50.
    elif filter_type == 'hot-sales':
        products = products.filter(price__lt=50)
        products = products.order_by('-price') # Optional: Sort cheapest first, or by title, etc.
        
    # 3. Best Sellers (Default 'all'): Sort by a hypothetical 'sales_count' descending.
    else: # filter_type == 'all'
        # NOTE: You will need to add a 'sales_count' field to your Product model.
        # For now, if you don't have it, keep the original sorting or use a temporary one.
        # products = products.order_by('-sales_count') # IDEAL: Sort by most sold
        products = products.order_by('-created_at') # CURRENT LOGIC: Newest products
    
    print("Active products:", products.count())
    for product in products:
        print(f"Product: {product.title}, Status: {product.status}, Price: {product.price}, Image: {product.photo.url if product.photo else 'No image'}")
        
    context = {'products': products, 'filter_type': filter_type}
    print("Context being sent:", context)
    
    # FIX: You must pass the context dictionary to the render function.
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
    
    # Check if the request is a POST request (from the 'Add to Cart' form)
    if request.method == 'POST':
        
        # 1. Get the product object or return a 404 error
        product = get_object_or_404(Product, pk=product_id)

        # 2. Extract data from the POST request
        # Safely get quantity (default to 1) and selected options
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            # Handle case where quantity isn't a valid number
            quantity = 1
            
        selected_size = request.POST.get('size', 'N/A') # Use a default like 'N/A'
        selected_color = request.POST.get('color', 'N/A') # Use a default like 'N/A'

        # 3. Create a unique identifier for this specific cart item 
        # This key combines the product ID and the selected attributes
        item_key = f"{product_id}-{selected_size}-{selected_color}"

        # 4. Initialize the cart in the session if it doesn't exist
        # 'cart' will be a dictionary of item_key: item_details
        cart = request.session.get('cart', {})
        
        # 5. Add or update the item in the cart
        if item_key in cart:
            # Item already exists, just increase the quantity
            cart[item_key]['quantity'] += quantity
        else:
            # Item is new, add it to the cart dictionary
            cart[item_key] = {
                'product_id': product_id,
                'quantity': quantity,
                # Store price as a string to avoid potential JSON serialization issues 
                # (Decimal types are not JSON serializable by default)
                'price': str(product.price), 
                'title': product.title,
                'size': selected_size,
                'color': selected_color,
            }

        # 6. Save the modified cart back to the session
        request.session['cart'] = cart
        # Mark the session as modified so Django knows to save it to the database/backend
        request.session.modified = True
        
        # 7. Redirect the user back to the product detail page 
        # Use a GET parameter to signal success for the Toastify notification
        product_name = product.title 
        redirect_url = redirect('product_detail', pk=product_id).url
        
        # The f-string syntax safely appends the parameter to the URL
        return redirect(f"{redirect_url}?cart_added={product_name}") 

    # If the request method is not POST (e.g., someone browsed directly to this URL), 
    # just redirect them back to the product detail page.
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


