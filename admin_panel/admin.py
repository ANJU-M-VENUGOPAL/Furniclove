from django.contrib import admin
from .models import Product, ColorVariant,Category, Coupon

from django.contrib.auth.models import User
from furniclove_app.models import UserProfile, Order, OrderItem, Wallet

from .models import Return


class ColorVariantInline(admin.TabularInline):
    model = ColorVariant
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'offer_percent')  # Show category offer
    search_fields = ('name',)
    ordering = ('name',)
    list_filter = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'original_price', 'offer_percent', 'final_offer_percent', 'discounted_price', 'category', 'stock')  # Updated fields
    inlines = [ColorVariantInline]
    filter_horizontal = ('related_products',)

    def discounted_price(self, obj):
        return obj.discounted_price  # Calls the property method in the model

    def final_offer_percent(self, obj):
        return obj.final_offer_percent  # Shows the highest applicable discount

    discounted_price.short_description = "Final Price"
    final_offer_percent.short_description = "Max Discount (%)"


@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color_name', 'stock', 'price_override', 'discounted_price')
    list_filter = ('color_name',)
    search_fields = ('product__name', 'color_name')

    def discounted_price(self, obj):
        return obj.discounted_price  # Calls the property method in the model

    discounted_price.short_description = "Final Price"



class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')
    inlines = [UserProfileInline]  

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)


class OrderItemInline(admin.TabularInline):  
    model = OrderItem
    extra = 1  


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'date', 'status', 'total', 'payment_status', 'payment_method') 
    list_editable = ('status','payment_status')  
    list_filter = ('status', 'payment_status', 'payment_method', 'date')  
    search_fields = ('order_id', 'user__username')
    readonly_fields = ('order_id', 'date')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__order_id', 'product__name')



@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'active', 'max_usage', 'used_count')
    list_filter = ('active', 'valid_from', 'valid_to')
    search_fields = ('code',)
    ordering = ('-valid_from',)



@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'status', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_item__product__name', 'order_item__order__order_id']

