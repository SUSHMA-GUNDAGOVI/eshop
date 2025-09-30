from django.shortcuts import render
from django.http import JsonResponse
from eshop_app.models import Banner

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
