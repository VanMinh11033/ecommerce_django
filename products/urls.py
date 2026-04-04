from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list_view, name='list'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('<slug:slug>/', views.product_detail_view, name='detail'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
    path('<slug:slug>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
]