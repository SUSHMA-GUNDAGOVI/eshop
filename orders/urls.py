# ecommerce/urls.py
from django.contrib import admin
from django.urls import path
from orders import views  # assuming your app is named 'shop'
from .views import ProductListAPI
from .views import CategoryListAPI

urlpatterns = [

    # Home page
    path('', views.index, name='index'),

    # API
    path('banners/', views.banner_api, name='banner_api'),
    path('products/', ProductListAPI.as_view(), name='api-products'),
    path('category/', CategoryListAPI.as_view(), name='api-category'),
    
]

