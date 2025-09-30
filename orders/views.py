from django.shortcuts import render
from django.http import JsonResponse
from eshop_app.models import Banner
from .serializers import ProductSerializer
from rest_framework.views import APIView
from eshop_app.models import Product 
from rest_framework.response import Response
from rest_framework import status
from .serializers import CategorySerializer
from eshop_app.models import Category
from rest_framework import serializers


def index(request):
    return render(request, 'index.html')

def banner_api(request):
    banners = Banner.objects.filter(status='active')
    banner_list = []
    for banner in banners:
        banner_list.append({
            'id': banner.id,
            'title': banner.title,
            'description': banner.description,
            'image_url': request.build_absolute_uri(banner.photo.url)
        })
    return JsonResponse(banner_list, safe=False)

class ProductListAPI(APIView):
    def get(self, request):
        # Fetch all active products
        products = Product.objects.filter(status='active').order_by('-created_at')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CategoryListAPI(APIView):
    def get(self, request):
        categories = Category.objects.filter(status='active').order_by('title')
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)