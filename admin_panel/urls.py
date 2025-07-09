from django.urls import path
from . import views
from .views import admin_login, admin_logout
from admin_panel.views import (
    order_management, update_order_status, update_payment_status, order_details_admin
)

urlpatterns = [
    # Admin Auth
    path('', admin_login, name='admin_login'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('admin/logout/', admin_logout, name='admin_logout'),

    # User Management
    path('user-management/', views.user_management, name='user_management'),
    path('block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('activate-user/<int:user_id>/', views.activate_user, name='activate_user'),

    # Product Management
    path('product-management/', views.product_management, name='product_management'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('view-product/<int:product_id>/', views.view_product, name='view_product'),
    path('block-product/<int:product_id>/', views.block_product, name='block_product'),
    path('unblock-product/<int:product_id>/', views.unblock_product, name='unblock_product'),

    # Variant Management
    path('product/<int:product_id>/variants/', views.variant_management, name='variant_management'),
    path('product/<int:product_id>/add-variant/', views.add_variant, name='add_variant'),
    path('variant/<int:variant_id>/edit/', views.edit_variant, name='edit_variant'),
    path('block-variant/<int:variant_id>/', views.block_variant, name='block_variant'),
    path('unblock-variant/<int:variant_id>/', views.unblock_variant, name='unblock_variant'),

    # Category Management
    path('category-management/', views.category_management, name='category_management'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),

    # Orders
    path('order-management/', order_management, name='order_management'),
    path('order/update-status/<int:order_id>/', update_order_status, name='update_order_status'),
    path('order/update-payment/<int:order_id>/', update_payment_status, name='update_payment_status'),
    path('admin/order/details/<int:order_id>/', order_details_admin, name='admin_order_details'),
    path('admin/return/process/<int:return_id>/', views.process_return, name='process_return'),

    # Coupons
    path('coupons/', views.coupon_management, name='coupon_management'),
    path('add-coupon/', views.add_coupon, name='add_coupon'),
    path('edit-coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete-coupon/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    # Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Sales Reports
    path('sales-report/', views.sales_report, name='sales_report'),
    path('sales-report/download-pdf/', views.download_sales_pdf, name='download_sales_pdf'),
    path('sales-report/download-excel/', views.download_sales_excel, name='download_sales_excel'),
]
