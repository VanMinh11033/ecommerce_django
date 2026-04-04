from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Brand, Review, Wishlist

def home_view(request):
    """Trang chủ - Hiển thị sản phẩm nổi bật"""
    
    # Lấy 4-8 sản phẩm nổi bật
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category', 'brand').prefetch_related('images')[:8]
    
    # Nếu không có sản phẩm featured, lấy sản phẩm mới nhất
    if not featured_products.exists():
        featured_products = Product.objects.filter(
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').order_by('-created_at')[:8]
    
    context = {
        'featured_products': featured_products,
    }
    
    return render(request, 'home.html', context)

def product_list_view(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    
    # Variables for context
    selected_category = None
    selected_brand = None
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug, is_active=True)
            products = products.filter(category=selected_category)
        except Category.DoesNotExist:
            messages.warning(request, f'Không tìm thấy danh mục "{category_slug}". Hiển thị tất cả sản phẩm.')
    
    # Brand filter
    brand_slug = request.GET.get('brand')
    if brand_slug:
        try:
            selected_brand = Brand.objects.get(slug=brand_slug, is_active=True)
            products = products.filter(brand=selected_brand)
        except Brand.DoesNotExist:
            messages.warning(request, f'Không tìm thấy thương hiệu "{brand_slug}". Hiển thị tất cả sản phẩm.')
    
    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort = request.GET.get('sort', '-created_at')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'popular':
        products = products.order_by('-sold_count', '-view_count')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True, parent=None)
    brands = Brand.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
        'search': search,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
    }
    return render(request, 'products/product_list.html', context)

def product_detail_view(request, slug):
    product = get_object_or_404(Product.objects.select_related('category', 'brand'), slug=slug, is_active=True)
    
    # Increase view count
    product.view_count += 1
    product.save(update_fields=['view_count'])
    
    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:8]
    
    # Reviews
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    
    # Check if user already reviewed
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'user_review': user_review,
    }
    return render(request, 'products/product_detail.html', context)

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    
    # Get subcategories
    subcategories = category.children.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'page_obj': page_obj,
    }
    return render(request, 'products/category.html', context)

@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating,
                'title': title,
                'comment': comment,
            }
        )
        messages.success(request, 'Đánh giá của bạn đã được gửi!')
    
    return redirect('products:detail', slug=slug)

@login_required
def toggle_wishlist(request, slug):
    product = get_object_or_404(Product, slug=slug)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        wishlist_item.delete()
        messages.success(request, 'Đã xóa khỏi danh sách yêu thích')
    else:
        messages.success(request, 'Đã thêm vào danh sách yêu thích')
    
    return redirect('products:detail', slug=slug)

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'products/wishlist.html', {'wishlist_items': wishlist_items})