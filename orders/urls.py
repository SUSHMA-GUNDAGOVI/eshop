# ecommerce/urls.py
from django.contrib import admin
from django.urls import path , include
from orders import views  # assuming your app is named 'shop'
from django.conf import settings

urlpatterns = [

    # Home page
    path('', views.index, name='index'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('shopping_cart/', views.shopping_cart_view, name='shopping_cart'),
    path('cart/remove/', views.remove_from_cart_view, name='remove_from_cart'),
  
    ]

