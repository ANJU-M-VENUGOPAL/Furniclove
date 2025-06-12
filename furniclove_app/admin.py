from django.contrib import admin
from .models import Cart, CartItem, Review

admin.site.register(Cart)
admin.site.register(CartItem)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    search_fields = ['product__name', 'user__username']
