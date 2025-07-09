from django.urls import path
from furniclove_app import views
from django.contrib.auth.decorators import login_required
from .views import (
    user_login, user_logout,profile_update,add_to_cart, cart_view, update_cart, remove_from_cart, order_success, user_orders,
    cancel_order, return_product, check_stock_updates, check_product_stock,
    razorpay_payment_success, razorpay_payment_failure, apply_coupon, add_address_ajax
)

urlpatterns = [
    # General Pages
    path('', views.index, name='index'),
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),

    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('add-to-wishlist/<int:product_id>/<int:variant_id>/', views.add_to_wishlist, name='add_to_wishlist_variant'),
    path('remove-from-wishlist/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('otp/', views.otp_view, name='otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('user-login/', user_login, name='user_login'),
    path('logout/', user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),

    # Products
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/variant/<int:variant_id>/', views.product_detail, name='product_detail_with_variant'),
    path('check-product-stock/<int:product_id>/', check_product_stock, name='check_product_stock'),
    path('check-product-stock/<int:product_id>/<int:variant_id>/', check_product_stock, name='check_product_stock_variant'),

    # Account/Profile
    path('my-account/', views.my_account, name='my_account'),
    path('profile/update/', profile_update, name='profile_update'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # Addresses
    path('address-manage/', views.address_manage, name='address_manage'),
    path('address-selection/', views.address_selection, name='address_selection'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('add-address-ajax/', add_address_ajax, name='add_address_ajax'),

    # Cart
    path('cart/', cart_view, name='cart_view'),
    path('add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('add/<int:product_id>/<int:variant_id>/', add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:cart_id>/<int:quantity>/', update_cart, name='update_cart'),
    path('check-stock-updates/', check_stock_updates, name='check_stock_updates'),

    # Checkout & Payments
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', razorpay_payment_success, name='razorpay_payment_success'),
    path('razorpay-payment-failure/', razorpay_payment_failure, name='razorpay_payment_failure'),

    # Wallet
    path('wallet/', views.wallet, name='wallet'),
    path('wallet-payment/', views.wallet_payment, name='wallet_payment'),

    # Coupons
    path('apply-coupon/', apply_coupon, name='apply_coupon'),

    # Orders
    path('order-success/<str:order_id>/', order_success, name='order_success'),
    path('user-orders/', user_orders, name='user_orders'),
    path('order-details/<int:order_id>/', views.order_details, name='order_details'),
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('return-product/<int:order_id>/<int:item_id>/', return_product, name='return_product'),

    # Reviews
    path('product/<int:product_id>/review/', views.submit_review, name='submit_review'),
    path('submit-review/<int:product_id>/', views.submit_review, name='submit_review'),

    # Invoice
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
]
