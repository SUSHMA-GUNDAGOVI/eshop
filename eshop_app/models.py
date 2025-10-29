from django.contrib.auth.models import User, AbstractUser
from django.db import models
from django.conf import settings  # import this
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.text import slugify

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        # Fill username automatically if blank
        if 'username' not in extra_fields or not extra_fields['username']:
            extra_fields['username'] = email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )

    username = models.CharField(max_length=50, unique=True, blank=True, null=True)  
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()  # <-- add this

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

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
    size = models.CharField(max_length=100, blank=True, null=True)
    color_data = models.JSONField(blank=True, null=True, encoder=DjangoJSONEncoder)    
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)

    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default="default")
    stock = models.PositiveIntegerField(default=0)

    shipping_charge = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_free_shipping = models.BooleanField(default=False)

    photo = models.ImageField(upload_to="products/")
    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('inactive', 'Inactive')], default="active")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="products_created")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def _str_(self):
        return self.title

    # ✅ ADD THESE PROPERTIES TO YOUR PRODUCT MODEL:
    @property
    def color_names(self):
        """Return list of color names for template usage"""
        if self.color_data:
            return [color.get('name', '') for color in self.color_data if color.get('name')]
        return []
    
    @property 
    def color_names_string(self):
        """Return color names as comma-separated string"""
        return ','.join(self.color_names)
    
    @property
    def color_map(self):
        """Return a dictionary of color names to hex codes"""
        if self.color_data:
            return {color.get('name', ''): color.get('code', '#cccccc') for color in self.color_data if color.get('name')}
        return {}
    
    def get_color_hex(self, color_name):
        """Get hex code for a color name"""
        color_map = self.color_map
        return color_map.get(color_name, '#cccccc')
    

class ProductMedia(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='product_media/')
    file_type = models.CharField(max_length=20, choices=[('image', 'Image'), ('video', 'Video')])
    is_primary = models.BooleanField(default=False)
    color_name = models.CharField(max_length=50, blank=True, null=True)  # ✅ New field to map media to a color
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-detect file type
        if self.file.name.lower().endswith(('.mp4', '.webm', '.avi', '.mov', '.mkv')):
            self.file_type = 'video'
        else:
            self.file_type = 'image'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.title} - {self.color_name or 'General'} ({self.file_type})"

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
    

class Contact(models.Model):
    # General Description
    description = models.TextField(
        help_text="Short description or introduction for the contact section"
    )

    # Branch 1 Details
    branch1_name = models.CharField(max_length=100, verbose_name="Branch 1 Name")
    branch1_address = models.CharField(max_length=255, verbose_name="Branch 1 Address")
    branch1_phone = models.CharField(max_length=20, verbose_name="Branch 1 Phone")
    branch1_email = models.EmailField(verbose_name="Branch 1 Email")

    # Branch 2 Details
    branch2_name = models.CharField(max_length=100, verbose_name="Branch 2 Name")
    branch2_address = models.CharField(max_length=255, verbose_name="Branch 2 Address")
    branch2_phone = models.CharField(max_length=20, verbose_name="Branch 2 Phone")
    branch2_email = models.EmailField(verbose_name="Branch 2 Email")

    # Meta Info
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contact Information ({self.branch1_name} & {self.branch2_name})"
    

class Blog(models.Model):
    STATUS_CHOICES = (
        (0, 'Draft'),
        (1, 'Published'),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    author_name = models.CharField(max_length=100, default='Admin')
    publish_date = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure uniqueness
            while Blog.objects.filter(slug=self.slug).exists():
                self.slug = f"{slugify(self.title)}-{int(timezone.now().timestamp())}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

class AboutUs(models.Model):
    who_we_are = models.TextField(blank=True, null=True)
    who_we_do = models.TextField(blank=True, null=True)
    why_choose_us = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "About Us Sections"
    
class Team(models.Model):
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    image = models.ImageField(upload_to="team_images/")  # Make sure MEDIA_ROOT is configured
    bio = models.TextField(blank=True, null=True)  # optional short description

    def __str__(self):
        return self.name
    
class Client(models.Model):
    name = models.CharField(max_length=255)  # Optional: client name
    logo = models.ImageField(upload_to='client_logos/')  # Upload folder

    def __str__(self):
        return self.name if self.name else f"Client {self.id}"
    
class Client(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive')
    )
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='client_logos/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)


class GeneralFAQ(models.Model):
    """
    Model for General Frequently Asked Questions (not tied to a product).
    """
    
    question = models.CharField(max_length=255, verbose_name='Question')
    answer = models.TextField(verbose_name='Answer')
    
    # Used for display order
    order = models.IntegerField(default=0, verbose_name='Display Order')
    is_active = models.BooleanField(default=True, verbose_name='Is Active')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'General FAQ'
        verbose_name_plural = 'General FAQs'
        ordering = ['order', '-created_at'] 

    def _str_(self):
        return f"FAQ (Order {self.order}): {self.question[:50]}"
