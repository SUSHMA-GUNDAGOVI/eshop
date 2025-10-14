from django.contrib import admin
from django.urls import path, include
from eshop_app import views   # adjust app name if needed
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path("" ,views.home, name='index'),  # Home page
    path("", views.login_view, name="home"),
    path("login/", views.login_view, name="login"),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path("register/", views.register, name="register"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("user/dashboard/", views.user_dashboard, name="user_dashboard"),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('banners/add/', views.add_banner, name='add_banner'),
    path('banners/list/', views.banner_list, name='banner_list'),
    path('banners/edit/<int:id>/', views.edit_banner, name='edit_banner'),
    path('banners/delete/<int:id>',views.banner_delete, name="banner_delete"),
    path('category/list/', views.category_list, name='category_list'),
    path('category/add/', views.category_add, name='category_add'),
    path("category/edit/<int:pk>/", views.category_edit, name="category_edit"),
    path("category/delete/<int:pk>/", views.category_delete, name="category_delete"),
    path('brands/list/', views.brand_list, name='brand_list'),
    path('brands/add/', views.brand_add, name='brand_add'),
    path('brands/edit/<int:pk>/', views.brand_edit, name='brand_edit'),
    path('brands/delete/<int:pk>/', views.brand_delete, name='brand_delete'),
    path("products/list/", views.product_list, name="product_list"),
    path("products/add/", views.product_add, name="product_add"),
    path("products/edit/<int:pk>/", views.product_edit, name="product_edit"),
    path('products/toggle-status/<int:pk>/', views.product_toggle_status, name='product_toggle_status'),    
    path("products/delete/<int:pk>/", views.product_delete, name="product_delete"),
    path("ajax/get-child-categories/", views.get_child_categories, name="get_child_categories"),
    path("coupons/list/", views.coupon_list, name="coupon_list"),
    path("coupons/add/", views.coupon_add, name="coupon_add"),
    path("coupons/edit/<int:pk>/", views.coupon_edit, name="coupon_edit"),
    path("coupons/delete/<int:pk>/", views.coupon_delete, name="coupon_delete"),
    path('users/list/', views.users_list, name='user_list'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'), 
     path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('settings/', views.settings_view, name='settings'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('vendors/list/', views.vendor_list, name='vendor_list'),       
    path('vendors/add/', views.add_vendor, name='vendor_add'),     
    # 2. Status Toggle Path (Crucial for the clickable badge)
]
