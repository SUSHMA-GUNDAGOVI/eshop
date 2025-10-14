# ecommerce/urls.py
from django.contrib import admin
from django.urls import path , include
from orders import views  # assuming your app is named 'shop'
from .views import ProductListAPI
from .views import CategoryListAPI, SubCategoryListAPI
from django.conf import settings

urlpatterns = [

  # API
    path('banners/', views.banner_api, name='banner_api'),
    path('products/', ProductListAPI.as_view(), name='api-products'),
    path('category/', CategoryListAPI.as_view(), name='api-category'),
    path('subcategory/<int:category_id>/', SubCategoryListAPI.as_view(), name='api-subcategory'),
    path('products-by-category/<int:category_id>/', views.ProductListByCategoryAPI.as_view(), name='api-products-by-category'),

    # Home page
    path('', views.index, name='index'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
     path('shopping_cart/', views.shopping_cart_view, name='shopping_cart'),
     path('cart/remove/', views.remove_from_cart_view, name='remove_from_cart'),
  
    ]

