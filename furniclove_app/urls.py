
from django.urls import path,include
from furniclove_app import views
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path
from .views import user_login, user_logout

from .views import forgot_password_view, reset_password_view

from .views import profile_update

from .views import add_to_cart, cart_view, update_cart, remove_from_cart, place_order, order_success,user_orders,cancel_order,return_product,check_stock_updates,check_product_stock,razorpay_payment_success, razorpay_payment_failure,apply_coupon,add_address_ajax
from django.utils.timezone import now


urlpatterns = [
    path('', views.index, name='index'),
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),

    
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('add-to-wishlist/<int:product_id>/<int:variant_id>/', views.add_to_wishlist, name='add_to_wishlist_variant'),  
    path('remove-from-wishlist/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    
    path('signup/', views.signup_view, name='signup'),
    path('otp/', views.otp_view, name='otp'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('user_login/', user_login, name='user_login'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),


    path('logout/', user_logout, name='logout'), 


   path('product/<int:product_id>/', views.product_detail, name='product_detail'),


   path('product/<int:product_id>/variant/<int:variant_id>/', views.product_detail, name='product_detail_with_variant'),  # Product with variant
   path('check-product-stock/<int:product_id>/', check_product_stock, name='check_product_stock'),
   path('check-product-stock/<int:product_id>/<int:variant_id>/', check_product_stock, name='check_product_stock_variant'),
   

   path('my-account/', views.my_account, name='my_account'),


   path('address_manage/', views.address_manage, name='address_manage'),
   path('address-selection/', views.address_selection, name='address_selection'),
   path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
   path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
   path('add-address-ajax/', views.add_address_ajax, name='add_address_ajax'),

   
    path('cart/', cart_view, name='cart_view'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Without variant
    path('add/<int:product_id>/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),  # With variant
    path("check-stock-updates/", check_stock_updates, name="check_stock_updates"),

    
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:cart_id>/<int:quantity>/', views.update_cart, name='update_cart'),


   path('checkout/', views.checkout, name='checkout'),
   
     
   path('payment-success/', razorpay_payment_success, name='razorpay_payment_success'),
   path('razorpay-payment-failure/', views.razorpay_payment_failure, name='razorpay_payment_failure'),


   path('wallet/', views.wallet, name='wallet'),
   path('wallet-payment/', views.wallet_payment, name='wallet_payment'),


   path('apply-coupon/', views.apply_coupon, name='apply_coupon'),

   path("place-order/", place_order, name="place_order"),
   path('order-success/<str:order_id>/', order_success, name='order_success'),
   path('user-orders/', user_orders, name='user_orders'),
   path('order-details/<int:order_id>/', views.order_details, name='order_details'),
   path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),

   path('return_product/<int:order_id>/<int:item_id>/', views.return_product, name='return_product'),

   path('product/<int:product_id>/review/', views.submit_review, name='submit_review'),


   path('profile/update/', profile_update, name='profile_update'),
   path('profile/change-password/', views.change_password, name='change_password'),


   path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),

   path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),

]
   




   
    
