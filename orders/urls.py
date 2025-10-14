# ecommerce/urls.py
from django.contrib import admin
from django.urls import path , include
from orders import views  # assuming your app is named 'shop'
from .views import ProductListAPI
from .views import CategoryListAPI, SubCategoryListAPI

urlpatterns = [

 # API
    path('banners/', views.banner_api, name='banner_api'),
    path('products/', ProductListAPI.as_view(), name='api-products'),
    path('category/', CategoryListAPI.as_view(), name='api-category'),
    path('subcategory/<int:category_id>/', SubCategoryListAPI.as_view(), name='api-subcategory'),
    path('products-by-category/<int:category_id>/', views.ProductListByCategoryAPI.as_view(), name='api-products-by-category'),


    # Landing page
    path('', views.index, name='index'),
    path('', views.landing_page, name='landing_page'),
    ]

