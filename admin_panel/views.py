from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
import csv

from products.models import Product, Category, Brand, ProductImage, Review
from orders.models import Order, OrderItem
from accounts.models import User
from products.forms import ProductForm, CategoryForm, BrandForm


# ===================== DASHBOARD =====================
@staff_member_required
def dashboard(request):
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    # Stats
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total'))['total__sum'] or 0
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()
    
    # Today stats
    today = timezone.now().date()
    today_orders = Order.objects.filter(created_at__date=today).count()
    
    # Week revenue
    week_ago = timezone.now() - timedelta(days=7)
    week_revenue = Order.objects.filter(
        created_at__gte=week_ago,
        payment_status='paid'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Revenue data for chart (last 30 days)
    revenue_data = []
    for i in range(29, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        day_revenue = Order.objects.filter(
            created_at__date=date,
            payment_status='paid'
        ).aggregate(Sum('total'))['total__sum'] or 0
        revenue_data.append({
            'date': date.isoformat(),  # Convert to ISO format string
            'revenue': float(day_revenue) if day_revenue else 0
        })
    
    # Order status stats
    order_status_stats = []
    status_data = Order.objects.values('status').annotate(count=Count('id'))
    for item in status_data:
        order_status_stats.append({
            'status': dict(Order.STATUS_CHOICES).get(item['status'], item['status']),
            'count': item['count']
        })
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:10]
    
    # Top products
    top_products = Product.objects.order_by('-sold_count')[:5]
    
    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'today_orders': today_orders,
        'week_revenue': week_revenue,
        'revenue_data': json.dumps(revenue_data, cls=DjangoJSONEncoder),
        'order_status_stats': json.dumps(order_status_stats, cls=DjangoJSONEncoder),
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ===================== PRODUCTS CRUD =====================
@staff_member_required
def products_list(request):
    products = Product.objects.select_related('category', 'brand').prefetch_related('images')
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by brand
    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    # Filter by status
    is_active = request.GET.get('is_active')
    if is_active:
        products = products.filter(is_active=is_active == 'true')
    
    products = products.order_by('-created_at')
    
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'admin_panel/products_list.html', context)


@staff_member_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'reviews'), pk=pk)
    context = {'product': product}
    return render(request, 'admin_panel/product_detail.html', context)


@staff_member_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Handle images
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(i == 0),
                    order=i
                )
            
            messages.success(request, f'Sản phẩm "{product.name}" đã được tạo thành công!')
            return redirect('admin_panel:products_list')
    else:
        form = ProductForm()
    
    context = {'form': form, 'action': 'Thêm'}
    return render(request, 'admin_panel/product_form.html', context)


@staff_member_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                product = form.save()
                
                # Handle new images
                images = request.FILES.getlist('images')
                if images:
                    current_count = product.images.count()
                    for i, image in enumerate(images):
                        ProductImage.objects.create(
                            product=product,
                            image=image,
                            is_primary=(current_count == 0 and i == 0),
                            order=current_count + i
                        )
                
                messages.success(request, f'✅ Sản phẩm "{product.name}" đã được cập nhật thành công!')
                return redirect('admin_panel:product_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'❌ Lỗi khi lưu: {str(e)}')
        else:
            # Hiển thị lỗi validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ {field}: {error}')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'action': 'Cập nhật',
        'existing_images': product.images.all(),
    }
    return render(request, 'admin_panel/product_form.html', context)


@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Đã xóa sản phẩm "{product_name}"!')
        return redirect('admin_panel:products_list')
    
    context = {'product': product}
    return render(request, 'admin_panel/product_confirm_delete.html', context)


@staff_member_required
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    
    status = 'kích hoạt' if product.is_active else 'ẩn'
    messages.success(request, f'Đã {status} sản phẩm "{product.name}"!')
    return redirect('admin_panel:products_list')


# ===================== CATEGORIES CRUD =====================
@staff_member_required
def categories_list(request):
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('-created_at')
    
    context = {'categories': categories}
    return render(request, 'admin_panel/categories_list.html', context)


@staff_member_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Danh mục "{category.name}" đã được tạo!')
            return redirect('admin_panel:categories_list')
    else:
        form = CategoryForm()
    
    context = {'form': form, 'action': 'Thêm'}
    return render(request, 'admin_panel/category_form.html', context)


@staff_member_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Danh mục "{category.name}" đã được cập nhật!')
            return redirect('admin_panel:categories_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {'form': form, 'category': category, 'action': 'Cập nhật'}
    return render(request, 'admin_panel/category_form.html', context)


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        if category.products.exists():
            messages.error(request, f'Không thể xóa danh mục "{category.name}" vì còn sản phẩm!')
            return redirect('admin_panel:categories_list')
        
        category_name = category.name
        category.delete()
        messages.success(request, f'Đã xóa danh mục "{category_name}"!')
        return redirect('admin_panel:categories_list')
    
    context = {'category': category}
    return render(request, 'admin_panel/category_confirm_delete.html', context)


# ===================== BRANDS CRUD =====================
@staff_member_required
def brands_list(request):
    brands = Brand.objects.annotate(
        product_count=Count('products')
    ).order_by('-created_at')
    
    context = {'brands': brands}
    return render(request, 'admin_panel/brands_list.html', context)


@staff_member_required
def brand_create(request):
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Thương hiệu "{brand.name}" đã được tạo!')
            return redirect('admin_panel:brands_list')
        else:
            # Hiển thị lỗi nếu form không valid
            messages.error(request, 'Có lỗi trong form. Vui lòng kiểm tra lại!')
    else:
        form = BrandForm()
    
    context = {'form': form, 'action': 'Thêm'}
    return render(request, 'admin_panel/brand_form.html', context)


@staff_member_required
def brand_edit(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Thương hiệu "{brand.name}" đã được cập nhật!')
            return redirect('admin_panel:brands_list')
    else:
        form = BrandForm(instance=brand)
    
    context = {'form': form, 'brand': brand, 'action': 'Cập nhật'}
    return render(request, 'admin_panel/brand_form.html', context)


@staff_member_required
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    
    if request.method == 'POST':
        if brand.products.exists():
            messages.error(request, f'Không thể xóa thương hiệu "{brand.name}" vì còn sản phẩm!')
            return redirect('admin_panel:brands_list')
        
        brand_name = brand.name
        brand.delete()
        messages.success(request, f'Đã xóa thương hiệu "{brand_name}"!')
        return redirect('admin_panel:brands_list')
    
    context = {'brand': brand}
    return render(request, 'admin_panel/brand_confirm_delete.html', context)


# ===================== ORDERS MANAGEMENT =====================
@staff_member_required
def orders_list(request):
    orders = Order.objects.select_related('user').prefetch_related('items')
    
    # Search
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search) |
            Q(customer_email__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by payment status
    payment_status = request.GET.get('payment_status')
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    
    orders = orders.order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'order_statuses': Order.STATUS_CHOICES,
        'payment_statuses': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'admin_panel/orders_list.html', context)


@staff_member_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product', 'status_history'),
        order_number=order_number
    )
    
    context = {
        'order': order,
        'order_items': order.items.all(),
        'status_history': order.status_history.all().order_by('-created_at'),
        'available_statuses': Order.STATUS_CHOICES,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'admin_panel/order_detail.html', context)


@staff_member_required
def order_update_status(request, order_number):
    from django.utils import timezone
    from orders.models import OrderStatusHistory
    
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('status_history'),
        order_number=order_number
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        note = request.POST.get('note', '')
        
        if new_status in dict(Order.STATUS_CHOICES):
            # Cập nhật trạng thái
            old_status = order.status
            order.status = new_status
            
            # Cập nhật timestamp tương ứng
            now = timezone.now()
            if new_status == 'confirmed':
                order.confirmed_at = now
            elif new_status == 'shipping':
                order.shipped_at = now
            elif new_status == 'delivered':
                order.delivered_at = now
            elif new_status == 'cancelled':
                order.cancelled_at = now
            
            order.save()
            
            # Tạo lịch sử
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                note=note,
                created_by=request.user
            )
            
            messages.success(request, f'Đã cập nhật trạng thái đơn hàng #{order.order_number}!')
            return redirect('admin_panel:order_detail', order_number=order_number)
        else:
            messages.error(request, 'Trạng thái không hợp lệ!')
    
    # GET request - hiển thị form
    context = {
        'order': order,
        'available_statuses': Order.STATUS_CHOICES,
        'status_history': order.status_history.all().order_by('-created_at'),
    }
    return render(request, 'admin_panel/order_update_status.html', context)


@staff_member_required
def order_update_payment(request, order_number):
    """Cập nhật thanh toán chi tiết"""
    from django.utils import timezone
    
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        amount_received = request.POST.get('amount_received')
        actual_payment_method = request.POST.get('actual_payment_method')
        transaction_ref = request.POST.get('transaction_ref', '')
        payment_note = request.POST.get('payment_note', '')
        
        if payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
            # Cập nhật trạng thái thanh toán
            order.payment_status = payment_status
            
            # Nếu thanh toán thành công
            if payment_status == 'paid':
                order.paid_at = timezone.now()
                
                # Tạo ghi chú chi tiết
                note_parts = []
                if amount_received:
                    note_parts.append(f"Số tiền: {amount_received}₫")
                if actual_payment_method:
                    note_parts.append(f"Phương thức: {actual_payment_method}")
                if transaction_ref:
                    note_parts.append(f"Mã GD: {transaction_ref}")
                if payment_note:
                    note_parts.append(f"Ghi chú: {payment_note}")
                
                # Lưu vào admin_note
                if note_parts:
                    payment_info = " | ".join(note_parts)
                    if order.admin_note:
                        order.admin_note += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] THANH TOÁN: {payment_info}"
                    else:
                        order.admin_note = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] THANH TOÁN: {payment_info}"
            
            order.save()
            
            messages.success(
                request, 
                f'✅ Đã cập nhật thanh toán: {order.get_payment_status_display()}!'
            )
            return redirect('admin_panel:order_detail', order_number=order_number)
        else:
            messages.error(request, 'Trạng thái thanh toán không hợp lệ!')
    
    # GET request - hiển thị form
    context = {
        'order': order,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
        'payment_history': [],  # Có thể thêm model PaymentHistory sau
    }
    return render(request, 'admin_panel/order_update_payment.html', context)


@staff_member_required
def order_delete(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        if order.status not in ['pending', 'cancelled']:
            messages.error(request, 'Chỉ có thể xóa đơn hàng đang chờ hoặc đã hủy!')
            return redirect('admin_panel:orders_list')
        
        order.delete()
        messages.success(request, f'Đã xóa đơn hàng #{order_number}!')
        return redirect('admin_panel:orders_list')
    
    context = {'order': order}
    return render(request, 'admin_panel/order_confirm_delete.html', context)


# ===================== CUSTOMERS MANAGEMENT =====================
@staff_member_required
def customers_list(request):
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total')
    ).order_by('-date_joined')
    
    # Search
    search = request.GET.get('search')
    if search:
        customers = customers.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'admin_panel/customers_list.html', context)


@staff_member_required
def customer_detail(request, pk):
    customer = get_object_or_404(User.objects.prefetch_related('orders'), pk=pk)
    
    orders = customer.orders.all().order_by('-created_at')
    total_spent = orders.aggregate(Sum('total'))['total__sum'] or 0
    
    context = {
        'customer': customer,
        'orders': orders,
        'total_spent': total_spent,
    }
    return render(request, 'admin_panel/customer_detail.html', context)


@staff_member_required
def customer_edit(request, pk):
    customer = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        # Update basic info
        customer.first_name = request.POST.get('first_name', '')
        customer.last_name = request.POST.get('last_name', '')
        customer.email = request.POST.get('email', '')
        customer.phone = request.POST.get('phone', '')
        customer.address = request.POST.get('address', '')
        customer.city = request.POST.get('city', '')
        customer.district = request.POST.get('district', '')
        customer.ward = request.POST.get('ward', '')
        customer.save()
        
        messages.success(request, f'Đã cập nhật thông tin khách hàng!')
        return redirect('admin_panel:customer_detail', pk=pk)
    
    context = {'customer': customer}
    return render(request, 'admin_panel/customer_form.html', context)


@staff_member_required
def customer_toggle_active(request, pk):
    customer = get_object_or_404(User, pk=pk)
    customer.is_active = not customer.is_active
    customer.save()
    
    status = 'kích hoạt' if customer.is_active else 'vô hiệu hóa'
    messages.success(request, f'Đã {status} tài khoản "{customer.username}"!')
    return redirect('admin_panel:customers_list')


@staff_member_required
def customer_delete(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    
    if request.method == 'POST':
        if customer.orders.exists():
            messages.error(request, 'Không thể xóa khách hàng đã có đơn hàng!')
            return redirect('admin_panel:customers_list')
        
        username = customer.username
        customer.delete()
        messages.success(request, f'Đã xóa khách hàng "{username}"!')
        return redirect('admin_panel:customers_list')
    
    context = {'customer': customer}
    return render(request, 'admin_panel/customer_confirm_delete.html', context)


# ===================== REVIEWS MANAGEMENT =====================
@staff_member_required
def reviews_list(request):
    reviews = Review.objects.select_related('product', 'user').order_by('-created_at')
    
    # Filter
    is_approved = request.GET.get('is_approved')
    if is_approved:
        reviews = reviews.filter(is_approved=is_approved == 'true')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'admin_panel/reviews_list.html', context)


@staff_member_required
def review_approve(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = not review.is_approved
    review.save()
    
    status = 'duyệt' if review.is_approved else 'hủy duyệt'
    messages.success(request, f'Đã {status} đánh giá!')
    return redirect('admin_panel:reviews_list')


@staff_member_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, 'Đã xóa đánh giá!')
    return redirect('admin_panel:reviews_list')


# ===================== REPORTS =====================
@staff_member_required
def reports(request):
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = Order.objects.filter(payment_status='paid')
    
    if start_date:
        orders = orders.filter(created_at__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__lte=end_date)
    
    # Revenue stats
    total_revenue = orders.aggregate(Sum('total'))['total__sum'] or 0
    total_orders = orders.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Revenue by category
    revenue_by_category = []
    for category in Category.objects.all():
        cat_revenue = OrderItem.objects.filter(
            order__in=orders,
            product__category=category
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        if cat_revenue > 0:
            revenue_by_category.append({
                'category': category.name,
                'revenue': cat_revenue
            })
    
    # Top products
    top_products = Product.objects.annotate(
        revenue=Sum('orderitem__total')
    ).order_by('-revenue')[:10]
    
    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'revenue_by_category': revenue_by_category,
        'top_products': top_products,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_panel/reports.html', context)


@staff_member_required
def reports_export(request):
    # Export to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Mã đơn', 'Khách hàng', 'Tổng tiền', 'Trạng thái', 'Ngày tạo'])
    
    orders = Order.objects.all().order_by('-created_at')
    for order in orders:
        writer.writerow([
            order.order_number,
            order.customer_name,
            order.total,
            order.get_status_display(),
            order.created_at.strftime('%d/%m/%Y %H:%M')
        ])
    
    return response
@staff_member_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                product = form.save()
                images = request.FILES.getlist('images')
                if images:
                    current_count = product.images.count()
                    for i, image in enumerate(images):
                        ProductImage.objects.create(
                            product=product,
                            image=image,
                            is_primary=(current_count == 0 and i == 0),
                            order=current_count + i
                        )
                messages.success(request, f'✅ Sản phẩm "{product.name}" đã được cập nhật!')
                return redirect('admin_panel:product_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'❌ Lỗi: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ {field}: {error}')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'action': 'Cập nhật',
        'existing_images': product.images.all(),
    }
    return render(request, 'admin_panel/product_form.html', context)
