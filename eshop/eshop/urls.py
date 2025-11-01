"""
URL configuration for eshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from eshop_app import views as eshop_views
from orders import views as landing_views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_views.index, name='index'),          # Landing page
    path('', include('eshop_app.urls')),                  # eshop_app URLs (note: this might conflict with root ''; adjust if needed)
    path('orders/', include('orders.urls')),              # Orders URLs
    path('admin_dashboard/', eshop_views.admin_dashboard, name='admin_dashboard'),
    path('index/', eshop_views.user_dashboard, name='user_dashboard'),  # Renamed to avoid duplicate 'index' name conflict
    # Password Reset URLs (with fixes: added email_template_name, consistent success_urls, and reverse_lazy for safety)
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             email_template_name='password_reset_email.html',  # Points to your custom email template
             success_url=reverse_lazy('password_reset_done')  # Use reverse_lazy for dynamic resolution
         ), 
         name='password_reset'
    ),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')  # Consistent redirect
         ), 
         name='password_reset_confirm'
    ),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
         name='password_reset_complete'
    ),
    # Add your login URL here if not already in eshop_app.urls or orders.urls (referenced in complete.html)
    # path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
]

# Serve static/media files in development (if DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)