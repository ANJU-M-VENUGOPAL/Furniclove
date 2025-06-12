from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

import uuid



def generate_order_id():
    return str(uuid.uuid4())[:8]  # Take only the first 8 characters of UUID


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    offer_percent = models.IntegerField(default=0)  # Category-wide offer %

    def __str__(self):
        return self.name



class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default="No description available.")
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    thumbnail_1 = models.ImageField(upload_to='product_images/', blank=True, null=True)
    thumbnail_2 = models.ImageField(upload_to='product_images/', blank=True, null=True)
    thumbnail_3 = models.ImageField(upload_to='product_images/', blank=True, null=True)
    thumbnail_4 = models.ImageField(upload_to='product_images/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    offer_percent = models.IntegerField(default=0)  
    related_products = models.ManyToManyField('self', blank=True)

    @property
    def final_offer_percent(self):
        """Returns the maximum discount available (either product offer or category offer)."""
        return max(self.offer_percent, self.category.offer_percent)

    @property
    def discounted_price(self):
        """Calculates the final price after applying the best available discount."""
        discount = self.final_offer_percent
        if discount > 0:
            return self.original_price - (self.original_price * discount / 100)
        return self.original_price  # No discount applied

    def __str__(self):
        return self.name



class ColorVariant(models.Model):
    product = models.ForeignKey(Product, related_name='color_variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=7)
    main_image = models.ImageField(upload_to='variant_images/')
    thumbnail_1 = models.ImageField(upload_to='variant_images/', blank=True, null=True)
    thumbnail_2 = models.ImageField(upload_to='variant_images/', blank=True, null=True)
    thumbnail_3 = models.ImageField(upload_to='variant_images/', blank=True, null=True)
    thumbnail_4 = models.ImageField(upload_to='variant_images/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="If different from the product's original price"
    )

    @property
    def discounted_price(self):
        base_price = self.price_override if self.price_override else self.product.original_price
        discount = self.product.final_offer_percent  # Use the highest offer available
        if discount > 0:
            return base_price - (base_price * discount / 100)
        return base_price  # No discount applied

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"



class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="Discount percentage")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    max_usage = models.PositiveIntegerField(default=1, help_text="Maximum number of times the coupon can be used")
    used_count = models.PositiveIntegerField(default=0, help_text="Times the coupon has been used")
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def is_valid(self):
        """Check if the coupon is valid based on date, usage, and active status."""
        return (
            self.active and
            self.valid_from <= now() <= self.valid_to and
            self.used_count < self.max_usage
        )

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"


class Return(models.Model):
    STATUS_CHOICES = [
        ("Requested", "Requested"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Refunded", "Refunded"),
           ]

    order_item = models.OneToOneField('furniclove_app.OrderItem', on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Requested")
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # 🆕 add this

    def __str__(self):
        return f"Return for {self.order_item.product.name}"
