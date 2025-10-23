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
    path('shop/brand/<int:brand_id>/', views.shop_by_brand, name='shop_by_brand'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='orders_edit_profile'),
    path('contact/', views.landing_contact, name='landing_contact'),
    path('blog/', views.landing_blog, name='landing_blog'),
    path('blog/<slug:slug>/', views.landing_blog_detail, name='landing_blog_detail'),
    path('about-us/', views.landing_about_us, name='landing_about_us'),
    path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
]
