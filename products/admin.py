from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, Review, Wishlist

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_featured', 'is_bestseller', 'category', 'brand', 'created_at']
    search_fields = ['name', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ['view_count', 'sold_count']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('category', 'brand', 'name', 'slug', 'sku')
        }),
        ('Mô tả', {
            'fields': ('description', 'specifications')
        }),
        ('Giá & Kho', {
            'fields': ('price', 'compare_price', 'cost_price', 'stock')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Trạng thái', {
            'fields': ('is_active', 'is_featured', 'is_bestseller', 'is_new')
        }),
        ('Thống kê', {
            'fields': ('view_count', 'sold_count'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'order']
    list_filter = ['is_primary']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['product__name', 'user__username']
    actions = ['approve_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Duyệt đánh giá"

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
