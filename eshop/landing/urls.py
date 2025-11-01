from django.contrib import admin
from django.urls import path, include
from landing import views

#landing app urls

urlpatterns = [
    path('', views.index, name='landing_index'),
]
