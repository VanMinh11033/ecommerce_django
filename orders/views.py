from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Order, OrderItem, OrderStatusHistory
from cart.views import get_or_create_cart
from .forms import CheckoutForm

@login_required
def checkout_view(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items:
        messages.warning(request, 'Giỏ hàng trống')
        return redirect('cart:view')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order = Order.objects.create(
                user=request.user,
                customer_name=form.cleaned_data['customer_name'],
                customer_email=form.cleaned_data['customer_email'],
                customer_phone=form.cleaned_data['customer_phone'],
                shipping_address=form.cleaned_data['shipping_address'],
                shipping_ward=form.cleaned_data['shipping_ward'],
                shipping_district=form.cleaned_data['shipping_district'],
                shipping_city=form.cleaned_data['shipping_city'],
                shipping_note=form.cleaned_data.get('shipping_note', ''),
                payment_method=form.cleaned_data['payment_method'],
                subtotal=cart.subtotal,
                shipping_fee=30000,  # Fixed shipping fee
                total=cart.subtotal + 30000,
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_sku=item.product.sku or '',
                    price=item.product.price,
                    quantity=item.quantity,
                )
                
                # Update product stock and sold count
                item.product.stock -= item.quantity
                item.product.sold_count += item.quantity
                item.product.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                note='Đơn hàng đã được tạo',
            )
            
            # Clear cart
            cart_items.delete()
            
            # Redirect to payment
            if order.payment_method in ['vnpay', 'momo']:
                return redirect('payments:process', order_number=order.order_number)
            else:
                messages.success(request, f'Đặt hàng thành công! Mã đơn hàng: {order.order_number}')
                return redirect('orders:detail', order_number=order.order_number)
    else:
        # Pre-fill form with user data
        initial_data = {
            'customer_name': request.user.get_full_name(),
            'customer_email': request.user.email,
            'customer_phone': request.user.phone,
            'shipping_address': request.user.address,
            'shipping_ward': request.user.ward,
            'shipping_district': request.user.district,
            'shipping_city': request.user.city,
        }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'shipping_fee': 30000,
        'total': cart.subtotal + 30000,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = order.items.select_related('product').all()
    status_history = order.status_history.all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_history': status_history,
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def cancel_order_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.can_cancel:
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            note='Khách hàng hủy đơn hàng',
            created_by=request.user,
        )
        
        # Restore product stock
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.sold_count -= item.quantity
                item.product.save()
        
        messages.success(request, 'Đơn hàng đã được hủy')
    else:
        messages.error(request, 'Không thể hủy đơn hàng này')
    
    return redirect('orders:detail', order_number=order_number)