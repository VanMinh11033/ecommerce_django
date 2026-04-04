from django import forms
from .models import Order

class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=200, label='Họ và tên')
    customer_email = forms.EmailField(label='Email')
    customer_phone = forms.CharField(max_length=15, label='Số điện thoại')
    
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Địa chỉ')
    shipping_ward = forms.CharField(max_length=100, label='Phường/Xã')
    shipping_district = forms.CharField(max_length=100, label='Quận/Huyện')
    shipping_city = forms.CharField(max_length=100, label='Tỉnh/Thành phố')
    shipping_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Ghi chú đơn hàng'
    )
    
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        label='Phương thức thanh toán'
    )