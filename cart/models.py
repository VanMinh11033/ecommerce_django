from django.db import models
from accounts.models import User
from products.models import Product

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carts'
    
    def __str__(self):
        return f"Cart {self.id}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total(self):
        return self.subtotal


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart_items'
        unique_together = [['cart', 'product']]
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.product.price * self.quantity