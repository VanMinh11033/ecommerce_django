from django.db import models
from orders.models import Order
import random
import string

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'COD'),
        ('vnpay', 'VNPay'),
        ('momo', 'MoMo'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Gateway response
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        prefix = self.payment_method.upper()
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        return f"{prefix}_{random_str}"
    
    def __str__(self):
        return f"{self.transaction_id} - {self.order.order_number}"