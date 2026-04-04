from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Cart, CartItem
from products.models import Product

def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # For anonymous users, use session
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart

def cart_view(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'cart/cart.html', context)

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'Đã thêm {product.name} vào giỏ hàng')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'message': 'Đã thêm vào giỏ hàng'
        })
    
    return redirect('cart:view')

@require_POST
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Đã cập nhật giỏ hàng')
    else:
        cart_item.delete()
        messages.success(request, 'Đã xóa sản phẩm khỏi giỏ hàng')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal),
            'item_total': float(cart_item.total_price) if quantity > 0 else 0
        })
    
    return redirect('cart:view')

@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f'Đã xóa {product_name} khỏi giỏ hàng')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal)
        })
    
    return redirect('cart:view')

def clear_cart(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    messages.success(request, 'Đã xóa toàn bộ giỏ hàng')
    return redirect('cart:view')