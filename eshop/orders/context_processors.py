
def cart_count(request):
    """
    Calculates the total quantity of items in the session cart 
    and makes it available in all templates.
    """
    cart = request.session.get('cart', {})
    cart_total_quantity = 0
    
    # Sum the 'quantity' from every item in the cart dictionary
    for item in cart.values():
        try:
            cart_total_quantity += item.get('quantity', 0)
        except TypeError:
            # Handle case where quantity might not be an integer (if stored as string)
            pass 
            
    return {
        'cart_total_quantity': cart_total_quantity
    }