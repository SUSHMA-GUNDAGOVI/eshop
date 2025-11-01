from rest_framework import serializers
from eshop_app.models import Product,Category
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.title', read_only=True)
    child_category_name = serializers.CharField(source='child_category.title', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'summary', 'description', 'is_featured',
            'category', 'category_name',
            'child_category', 'child_category_name',
            'price', 'discount', 'size',
            'brand', 'brand_name',
            'condition', 'stock', 'photo', 'photo_url',
            'status', 'created_at',
        ]

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and hasattr(obj.photo, 'url'):
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

class CategorySerializer(serializers.ModelSerializer):
    parent_title = serializers.CharField(source='parent.title', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'title',
            'summary',
            'is_parent',
            'parent',
            'parent_title',
            'photo',
            'photo_url',
            'status',
            'created_at',
        ]

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None