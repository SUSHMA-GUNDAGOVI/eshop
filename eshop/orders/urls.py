from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('shopping_cart/', views.shopping_cart_view, name='shopping_cart'),
    path('cart/remove/', views.remove_from_cart_view, name='remove_from_cart'),
    path('shop/', views.shop_all_products, name='shop_all'),
    path('shop/category/<int:category_id>/', views.shop_by_category, name='shop_by_category'),
]
