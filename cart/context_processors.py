from .models import Cart

def cart_items_count(request):
    """Add cart items count to all templates"""
    count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.total_items
        except Cart.DoesNotExist:
            pass
    else:
        # For anonymous users using session
        cart_session = request.session.get('cart', {})
        count = sum(item['quantity'] for item in cart_session.values())
    
    return {'cart_items_count': count}