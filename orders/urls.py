from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('<str:order_number>/', views.order_detail_view, name='detail'),
    path('<str:order_number>/cancel/', views.cancel_order_view, name='cancel'),
]
