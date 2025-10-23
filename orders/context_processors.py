from .models import Cart
from django.db.models import Sum

def cart_total_quantity(request):
    if request.user.is_authenticated:
        total_quantity = Cart.objects.filter(user=request.user).aggregate(
            total=Sum('quantity')
        )['total'] or 0
    else:
        total_quantity = 0
    return {'cart_total_quantity': total_quantity}
