


from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Products Management - FULL CRUD
    path('products/', views.products_list, name='products_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:pk>/toggle-active/', views.product_toggle_active, name='product_toggle_active'),
    
    # Categories Management - FULL CRUD
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Brands Management - FULL CRUD
    path('brands/', views.brands_list, name='brands_list'),
    path('brands/create/', views.brand_create, name='brand_create'),
    path('brands/<int:pk>/edit/', views.brand_edit, name='brand_edit'),
    path('brands/<int:pk>/delete/', views.brand_delete, name='brand_delete'),
    
    # Orders Management
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/update-status/', views.order_update_status, name='order_update_status'),
    path('orders/<str:order_number>/update-payment/', views.order_update_payment, name='order_update_payment'),
    path('orders/<str:order_number>/delete/', views.order_delete, name='order_delete'),
    
    # Customers Management
    path('customers/', views.customers_list, name='customers_list'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/toggle-active/', views.customer_toggle_active, name='customer_toggle_active'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Reviews Management
    path('reviews/', views.reviews_list, name='reviews_list'),
    path('reviews/<int:pk>/approve/', views.review_approve, name='review_approve'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.reports_export, name='reports_export'),
]