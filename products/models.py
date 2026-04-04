from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from accounts.models import User

class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Danh mục'
        verbose_name_plural = 'Danh mục'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:category', args=[self.slug])


class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ THÊM

    class Meta:
        db_table = 'brands'
        verbose_name = 'Thương hiệu'
        verbose_name_plural = 'Thương hiệu'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField()
    specifications = models.JSONField(default=dict, blank=True)  # Lưu thông số kỹ thuật
    price = models.DecimalField(max_digits=12, decimal_places=0)
    compare_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    
    # Stats
    view_count = models.IntegerField(default=0)
    sold_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Sản phẩm'
        verbose_name_plural = 'Sản phẩm'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:detail', args=[self.slug])
    
    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int((1 - (self.price / self.compare_price)) * 100)
        return 0
    
    @property
    def in_stock(self):
        return self.stock > 0
    
    @property
    def rating_average(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'product_images'
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set other images as non-primary
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Đánh giá'
        verbose_name_plural = 'Đánh giá'
        ordering = ['-created_at']
        unique_together = [['product', 'user']]
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}*"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wishlists'
        unique_together = [['user', 'product']]
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"