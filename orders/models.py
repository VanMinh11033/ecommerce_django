
from django.db import models
from django.utils import timezone
from accounts.models import User
from products.models import Product
import random
import string

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('processing', 'Đang xử lý'),
        ('shipping', 'Đang giao hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
        ('refunded', 'Đã hoàn tiền'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Thanh toán khi nhận hàng'),
        ('vnpay', 'VNPay'),
        ('momo', 'MoMo'),
        ('bank_transfer', 'Chuyển khoản ngân hàng'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Chờ thanh toán'),
        ('paid', 'Đã thanh toán'),
        ('failed', 'Thanh toán thất bại'),
        ('refunded', 'Đã hoàn tiền'),
    ]
    
    # Order info
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    
    # Customer info
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    
    # Shipping info
    shipping_address = models.TextField()
    shipping_ward = models.CharField(max_length=100)
    shipping_district = models.CharField(max_length=100)
    shipping_city = models.CharField(max_length=100)
    shipping_note = models.TextField(blank=True)
    
    # Order details
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=0)
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    notes = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Đơn hàng'
        verbose_name_plural = 'Đơn hàng'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        timestamp = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"ORD{timestamp}{random_str}"
    
    def __str__(self):
        return self.order_number
    
    @property
    def full_shipping_address(self):
        parts = [self.shipping_address, self.shipping_ward, self.shipping_district, self.shipping_city]
        return ', '.join([p for p in parts if p])
    
    @property
    def is_paid(self):
        return self.payment_status == 'paid'
    
    @property
    def can_cancel(self):
        return self.status in ['pending', 'confirmed']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=300)
    product_sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    quantity = models.IntegerField(default=1)
    total = models.DecimalField(max_digits=12, decimal_places=0)
    
    class Meta:
        db_table = 'order_items'
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product_name}"
    
    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_status_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"