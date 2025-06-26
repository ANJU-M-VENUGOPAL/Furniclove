from django.db import models
from django.contrib.auth.models import User
from admin_panel.models import Product , ColorVariant, Coupon 
from django.utils.timezone import now 
import uuid
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError

from django.db.models import Sum, F

import random
import string

from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Wallet(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_profile.user.username}'s Wallet"



class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=(('Credited', 'Credited'), ('Debited', 'Debited')))
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"{self.transaction_type} ₹{self.amount} on {self.created_at}"



class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)   

    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)



class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey('admin_panel.Coupon', null=True, blank=True, on_delete=models.SET_NULL)


    def total_price(self):
        total = sum(item.subtotal() for item in self.cart_items.all())

        # Apply coupon discount if present and valid
        if self.coupon and self.coupon.is_valid():
            if total >= self.coupon.min_purchase_amount:  
                discount = (total * self.coupon.discount_percent) / 100
                total -= discount

        return total

    def __str__(self):
        return f"Cart for {self.user.username}"     




class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)  # Add this field
    quantity = models.PositiveIntegerField(default=0)
    
    def subtotal(self):
        # Check if the variant exists and has a discounted price
        if self.variant and self.variant.discounted_price is not None:
            price = self.variant.discounted_price
        # Check if the product has a discounted price
        elif self.product.discounted_price is not None:
            price = self.product.discounted_price
        # Use the original price if no discount is available
        else:
            price = self.product.original_price or 0

        # Calculate subtotal by multiplying the price with quantity
        return price * self.quantity


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    district = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.full_name}, {self.address}, {self.district}, {self.state}, {self.country}, {self.zipcode}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Failed', 'Failed'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('Razorpay', 'Razorpay Payment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    razorpay_payment_id = models.CharField(max_length=50, blank=True, null=True) 
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=50.00) #delivery charge
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)


    
    @property
    def order_id(self):
        return f"ORD{self.id:06d}"  

    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)  # Add this field
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of order

    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order: {self.order.order_id})"


    @property
    def is_returnable(self):
        """Checks if the product in this order can be returned (within 10 days of purchase)."""
        return self.order.date >= timezone.now() - timedelta(days=10)

    def subtotal(self):
        return self.quantity * self.price    
      


class OrderAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="order_address")  
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    district = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.full_name}, {self.address}, {self.district}, {self.state}, {self.country}, {self.zipcode}"



class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'variant')  # Prevent duplicates

    def __str__(self):
        if self.variant:
            return f"{self.user.username} - {self.product.name} ({self.variant.color_name})"
        return f"{self.user.username} - {self.product.name}"
  
    

class Review(models.Model):
    RATING_CHOICES = [(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Prevents duplicate reviews

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"
