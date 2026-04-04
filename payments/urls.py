
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('process/<str:order_number>/', views.payment_process_view, name='process'),
    path('vnpay-return/', views.vnpay_return_view, name='vnpay_return'),
]
