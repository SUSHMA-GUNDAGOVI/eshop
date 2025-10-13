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
from django.db.models import Q


def index(request):
    filter_type = request.GET.get('filter', 'all')
    products = Product.objects.filter(status='active')
    if filter_type == 'new-arrivals':
        products = products.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif filter_type == 'hot-sales':
        products = products.filter(price__lt=50)
    products = products.order_by('-created_at')
    print("Active products:", products.count())
    for product in products:
        print(f"Product: {product.title}, Status: {product.status}, Price: {product.price}, Image: {product.photo.url if product.photo else 'No image'}")
    context = {'products': products, 'filter_type': filter_type}
    print("Context being sent:", context)
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

 
class CategoryListAPI(APIView):
    def get(self, request):
        # Fetch only active main (parent) categories
        categories = Category.objects.filter(status='active', is_parent=True).order_by('title')

        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class SubCategoryListAPI(APIView):
    def get(self, request, category_id):
        subcategories = Category.objects.filter(
            status='active',
            is_parent=False,
            parent_id=category_id
        ).order_by('title')

        serializer = CategorySerializer(subcategories, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class ProductListAPI(APIView):
    def get(self, request):
        # Fetch all active products
        products = Product.objects.filter(status='active').order_by('-created_at')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductListByCategoryAPI(APIView):
    def get(self, request, category_id):
        try:
            # Fetch products where either category OR child_category matches the given category_id
            products = Product.objects.filter(
                Q(category_id=category_id) | Q(child_category_id=category_id),
                status='active'
            ).order_by('-created_at')

            serializer = ProductSerializer(products, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ADD THIS FUNCTION - This is what's missing!
def landing_category_product(request, category_id):
    return render(request, 'landing_category_product.html', {'category_id': category_id})   