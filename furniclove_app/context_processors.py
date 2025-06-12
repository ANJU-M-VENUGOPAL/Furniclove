from .models import Cart
from django.db import models

def cart_item_count(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.cart_items.aggregate(total=models.Sum('quantity'))['total'] or 0
        except Cart.DoesNotExist:
            count = 0
    else:
        count = 0
    return {'cart_item_count': count}