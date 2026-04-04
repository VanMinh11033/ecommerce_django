from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_at', 'created_by']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'total', 'payment_method', 'payment_status', 'status', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Thông tin khách hàng', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Địa chỉ giao hàng', {
            'fields': ('shipping_address', 'shipping_ward', 'shipping_district', 'shipping_city', 'shipping_note')
        }),
        ('Chi tiết đơn hàng', {
            'fields': ('subtotal', 'shipping_fee', 'discount_amount', 'total')
        }),
        ('Thanh toán', {
            'fields': ('payment_method', 'payment_status', 'paid_at')
        }),
        ('Ghi chú', {
            'fields': ('notes', 'admin_note')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'price', 'quantity', 'total']
    list_filter = ['order__created_at']

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']