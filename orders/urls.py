# ecommerce/urls.py
from django.contrib import admin
from django.urls import path , include
from orders import views  # assuming your app is named 'shop'
from .views import ProductListAPI
from .views import CategoryListAPI, SubCategoryListAPI

urlpatterns = [

    #orders app urls
    # Home page
    path('', views.index, name='index'),

    # API
    path('banners/', views.banner_api, name='banner_api'),
    path('products/', ProductListAPI.as_view(), name='api-products'),
    path('category/', CategoryListAPI.as_view(), name='api-category'),
    path('subcategory/<int:category_id>/', SubCategoryListAPI.as_view(), name='api-subcategory'),
    path('products-by-category/<int:category_id>/', views.ProductListByCategoryAPI.as_view(), name='api-products-by-category'),
    path('landing_category_product/<int:category_id>/', views.landing_category_product, name='landing-category-product'),
    ]

