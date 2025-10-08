from django.contrib.auth.models import User, AbstractUser
from django.db import models
from django.conf import settings  # import this
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )

    # Remove username auto-generation — we’ll use email for login
    username = models.CharField(max_length=50, unique=True, blank=True, null=True)  

    email = models.EmailField(unique=True)  # used for login
    first_name = models.CharField(max_length=50)  # full name split
    last_name = models.CharField(max_length=50, blank=True, null=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    USERNAME_FIELD = 'email'  # login with email
    REQUIRED_FIELDS = ['first_name', 'last_name']  # will be required if using createsuperuser

    def save(self, *args, **kwargs):
        # ensure username is always filled (use email if not provided)
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email  # easier for admin panel
    
class Banner(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='banners/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive')
)

class Category(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    is_parent = models.BooleanField(default=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='children')
    photo = models.ImageField(upload_to='category_photos/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Brand(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Product(models.Model):
    CONDITION_CHOICES = [
        ("default", "Default"),
        ("new", "New"),
        ("hot", "Hot"),
    ]

    title = models.CharField(max_length=200)
    summary = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    child_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="child_products")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.PositiveIntegerField(default=0)  # % value
    size = models.CharField(max_length=50, blank=True, null=True)  # "S,M,L"

    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)

    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default="default")
    stock = models.PositiveIntegerField(default=0)

    photo = models.ImageField(upload_to="products/")
    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('inactive', 'Inactive')], default="active")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="products_created")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("percent", "Percentage"),
        ("fixed", "Fixed Amount"),
    )

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="percent")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    per_user_limit = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code
    
class SiteSettings(models.Model):
    short_des = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)

    def __str__(self):
        return "Site Settings"
    
def upload_to_profile(instance, filename):
    return f"profile_photos/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to=upload_to_profile, blank=True, null=True)

    def __str__(self):
        return self.user.email  # or self.user.username
