
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order, OrderStatusHistory
from .models import Payment
import hashlib
import hmac
import urllib.parse

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def payment_process_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.payment_method == 'vnpay':
        return vnpay_payment(request, order)
    elif order.payment_method == 'momo':
        # Implement MoMo payment here
        messages.error(request, 'MoMo payment chưa được cài đặt')
        return redirect('orders:detail', order_number=order.order_number)
    else:
        messages.error(request, 'Phương thức thanh toán không hợp lệ')
        return redirect('orders:detail', order_number=order.order_number)

def vnpay_payment(request, order):
    # Create payment record
    payment = Payment.objects.create(
        order=order,
        payment_method='vnpay',
        amount=order.total,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
    )
    
    # VNPay parameters
    vnp_params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': settings.VNPAY_TMN_CODE,
        'vnp_Amount': int(order.total * 100),  # VNPay uses smallest unit
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': payment.transaction_id,
        'vnp_OrderInfo': f'Thanh toan don hang {order.order_number}',
        'vnp_OrderType': 'other',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': settings.VNPAY_RETURN_URL,
        'vnp_IpAddr': get_client_ip(request),
        'vnp_CreateDate': timezone.now().strftime('%Y%m%d%H%M%S'),
    }
    
    # Sort parameters
    sorted_params = sorted(vnp_params.items())
    
    # Create query string
    query_string = urllib.parse.urlencode(sorted_params)
    
    # Create secure hash
    hash_data = query_string.encode('utf-8')
    secure_hash = hmac.new(
        settings.VNPAY_HASH_SECRET.encode('utf-8'),
        hash_data,
        hashlib.sha512
    ).hexdigest()
    
    # Add secure hash to URL
    payment_url = f"{settings.VNPAY_URL}?{query_string}&vnp_SecureHash={secure_hash}"
    
    return redirect(payment_url)

@csrf_exempt
def vnpay_return_view(request):
    vnp_params = request.GET.dict()
    
    # Get secure hash
    vnp_secure_hash = vnp_params.pop('vnp_SecureHash', None)
    
    # Sort and create hash
    sorted_params = sorted(vnp_params.items())
    query_string = urllib.parse.urlencode(sorted_params)
    hash_data = query_string.encode('utf-8')
    
    calculated_hash = hmac.new(
        settings.VNPAY_HASH_SECRET.encode('utf-8'),
        hash_data,
        hashlib.sha512
    ).hexdigest()
    
    # Verify hash
    if vnp_secure_hash == calculated_hash:
        transaction_id = vnp_params.get('vnp_TxnRef')
        response_code = vnp_params.get('vnp_ResponseCode')
        
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            order = payment.order
            
            # Save gateway response
            payment.gateway_transaction_id = vnp_params.get('vnp_TransactionNo', '')
            payment.gateway_response = vnp_params
            
            if response_code == '00':
                # Payment successful
                payment.status = 'success'
                payment.completed_at = timezone.now()
                
                order.payment_status = 'paid'
                order.paid_at = timezone.now()
                order.status = 'confirmed'
                order.confirmed_at = timezone.now()
                
                OrderStatusHistory.objects.create(
                    order=order,
                    status='confirmed',
                    note='Thanh toán VNPay thành công',
                )
                
                messages.success(request, f'Thanh toán thành công! Mã đơn hàng: {order.order_number}')
            else:
                # Payment failed
                payment.status = 'failed'
                messages.error(request, 'Thanh toán thất bại!')
            
            payment.save()
            order.save()
            
            return redirect('orders:detail', order_number=order.order_number)
        
        except Payment.DoesNotExist:
            messages.error(request, 'Giao dịch không tồn tại')
            return redirect('home')
    else:
        messages.error(request, 'Chữ ký không hợp lệ')
        return redirect('home')
