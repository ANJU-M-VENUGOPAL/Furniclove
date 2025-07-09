from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Product, ColorVariant,Category
from .forms import ProductForm, ColorVariantForm
from django.core.paginator import Paginator

from furniclove_app.models import Order, OrderItem, OrderAddress, Wallet, Transaction
from admin_panel.models import Product,ColorVariant,Category, Coupon, Return
from decimal import Decimal

from django.utils.timezone import now

from django.views.decorators.http import require_POST
from django.utils import timezone
from django.views.decorators.cache import never_cache

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from decimal import Decimal, InvalidOperation

from .forms import CategoryForm

from django.http import HttpResponse
from weasyprint import HTML
from datetime import datetime
from django.db.models import Sum
import json

from django.db.models import Sum, Count, F
from django.utils.dateparse import parse_date

import pandas as pd


from django.template.loader import get_template
from xhtml2pdf import pisa
import io

from furniclove_app.refund_utils import calculate_refund_for_item 

import logging


logger = logging.getLogger(__name__)

@never_cache
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            request.session.flush()  
            login(request, user)
            
            request.session['is_admin'] = True  
            request.session['user_id'] = user.id  
            
            # Use logger instead of print
            logger.info(f"Admin Login Session Data: {dict(request.session.items())}")  
            
            return redirect('admin_home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'admin_login.html')


@login_required
def admin_home(request):
    # Restrict access to only superusers
    if not request.user.is_superuser:
        return redirect('admin_login')  # Redirect to login if not a superuser
    return render(request, 'admin_home.html')



def admin_dashboard(request):
    # Get filters from GET parameters
    year = request.GET.get('year')
    month = request.GET.get('month')

    order_items = OrderItem.objects.all()

    if year:
        order_items = order_items.filter(order__date__year=year)
    if month:
        order_items = order_items.filter(order__date__month=month)

    # Top 10 products
    top_products = (
        order_items.values('product__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:10]
    )

    # Top 10 categories
    top_categories = (
        order_items.values('product__category__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:10]
    )

    product_labels = [item['product__name'] for item in top_products]
    product_data = [item['total_quantity'] for item in top_products]

    category_labels = [item['product__category__name'] for item in top_categories]
    category_data = [item['total_quantity'] for item in top_categories]

    context = {
    'top_products': list(top_products),
    'top_categories': list(top_categories),
    'year': year,
    'month': month,
    "product_labels": json.dumps(product_labels),
    "product_data": json.dumps(product_data),
    "category_labels": json.dumps(category_labels),
    "category_data": json.dumps(category_data),
    }

    return render(request, 'admin_dashboard.html', context)



# User Management
@login_required
def user_management(request):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')  

    users = User.objects.exclude(is_superuser=True)

    paginator = Paginator(users, 10)  # 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    } 
    return render(request, 'user_management.html', context)



# Block a user (deactivate)
@login_required
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user.is_superuser:
        if user.is_superuser:
            messages.error(request, 'You cannot block the superuser.')
        else:
            user.is_active = False
            user.save()
            messages.success(request, f'{user.username} has been blocked successfully.')
    else:
        messages.error(request, 'You do not have permission to block users.')
    return redirect('user_management')


# Activate a user (reactivate)
@login_required
def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user.is_superuser:
        if user.is_superuser:
            messages.error(request, 'You cannot activate the superuser.')
        else:
            user.is_active = True
            user.save()
            messages.success(request, f'{user.username} has been activated successfully.')
    else:
        messages.error(request, 'You do not have permission to activate users.')
    return redirect('user_management')



# Product Management
@login_required
def product_management(request):
    products = Product.objects.all()

    
    for product in products:
        product.thumbnails = [
            product.thumbnail_1,
            product.thumbnail_2,
            product.thumbnail_3,
            product.thumbnail_4,
        ]

    paginator = Paginator(products, 10)  # 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # paginated products
    }

    return render(request, 'product_management.html', context)



def add_product(request):
    if request.method == "POST":
        # Retrieve form data
        name = request.POST.get("name")
        description = request.POST.get("description")
        category_id = request.POST.get("category")  
        original_price = request.POST.get("original_price")
        offer_percent = request.POST.get("offer_percent", 0)  
        stock = request.POST.get("stock")
        image = request.FILES.get("image")
        thumbnail_1 = request.FILES.get("thumbnail_1")
        thumbnail_2 = request.FILES.get("thumbnail_2")
        thumbnail_3 = request.FILES.get("thumbnail_3")
        thumbnail_4 = request.FILES.get("thumbnail_4")

        # Validation checks
        if not name or not description or not category_id or not original_price or not stock or not image:
            return HttpResponse("All required fields must be filled.", status=400)

        try:
            original_price = float(original_price)
            offer_percent = float(offer_percent) if offer_percent else 0
            stock = int(stock)

            if original_price < 0 or offer_percent < 0 or stock < 0:
                return HttpResponse("Prices, offer, and stock values must be non-negative.", status=400)

        except ValueError:
            return HttpResponse("Invalid numeric values.", status=400)

        category = get_object_or_404(Category, id=category_id)

        product = Product(
            name=name,
            description=description,
            category=category,  
            original_price=original_price,
            offer_percent=offer_percent,
            stock=stock,
            image=image,
            thumbnail_1=thumbnail_1,
            thumbnail_2=thumbnail_2,
            thumbnail_3=thumbnail_3,
            thumbnail_4=thumbnail_4,
        )
        product.save()

        related_ids = request.POST.getlist('related_products')
        for rid in related_ids:
            try:
                related_product = Product.objects.get(id=rid)
                product.related_products.add(related_product)
            except Product.DoesNotExist:
                continue

        return redirect("product_management")  

    categories = Category.objects.all()
    all_products = Product.objects.all()
    return render(request, "add_product.html", {"categories": categories,"all_products": all_products})



def view_product(request, product_id):
    product = Product.objects.get(id=product_id)
    
    thumbnails = []
    for i in range(1, 5):
        thumbnail_field = getattr(product, f'thumbnail_{i}', None)
        if thumbnail_field:
            thumbnails.append(thumbnail_field.url)

    related_products = product.related_products.all()             

    return render(request, 'view_product.html', {
        'product': product,
        'thumbnails': thumbnails,
        'offer_percent': product.offer_percent,
        'related_products': related_products  
    })




def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')

        category_id = request.POST.get('category')
        if category_id:
            product.category = get_object_or_404(Category, id=category_id)

        original_price = request.POST.get('original_price')
        if original_price:
            product.original_price = Decimal(original_price)  

        offer_percent = request.POST.get('offer_percent', 0)
        if offer_percent:
            product.offer_percent = int(offer_percent)  
        product.stock = request.POST.get('stock')

        # Handle image and thumbnails
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        if 'thumbnail_1' in request.FILES:
            product.thumbnail_1 = request.FILES['thumbnail_1']
        if 'thumbnail_2' in request.FILES:
            product.thumbnail_2 = request.FILES['thumbnail_2']
        if 'thumbnail_3' in request.FILES:
            product.thumbnail_3 = request.FILES['thumbnail_3']
        if 'thumbnail_4' in request.FILES:
            product.thumbnail_4 = request.FILES['thumbnail_4']


        product.related_products.clear()  # Clear existing
        related_ids = request.POST.getlist('related_products')
        for rid in related_ids:
            try:
                related_product = Product.objects.get(id=rid)
                product.related_products.add(related_product)
            except Product.DoesNotExist:
                continue


        product.save()

        return redirect('product_management')
    
    all_products = Product.objects.exclude(id=product.id)
    return render(request, 'edit_product.html', {'product': product, 'categories': categories, 'all_products': all_products})

    #return render(request, 'edit_product.html', {'product': product, 'categories': categories})



# block & unblock a product
def block_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False  # Set product as blocked
    product.save()
    return redirect('product_management')



def unblock_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = True  # Set product as active
    product.save()
    return redirect('product_management')



# variant list
def variant_management(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    color_variants = ColorVariant.objects.filter(product=product)
    return render(request, 'variant_management.html', {'product': product, 'color_variants': color_variants})


# add variant
def add_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ColorVariantForm(request.POST, request.FILES)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product  
            variant.save()
            return redirect('view_product', product.id)  
    else:
        form = ColorVariantForm()

    return render(request, 'add_variant.html', {'form': form, 'product': product})



# edit variant
def edit_variant(request, variant_id):
    
    variant = get_object_or_404(ColorVariant, id=variant_id)
    product = variant.product  

    if request.method == 'POST':
        
        form = ColorVariantForm(request.POST, request.FILES, instance=variant)
        if form.is_valid():
            form.save()  
            return redirect('variant_management', product.id)  
    else:
        form = ColorVariantForm(instance=variant)

    return render(request, 'edit_variant.html', {
        'form': form,
        'product': product,
        'variant':variant,
        
    })


# Block & Unblock variant
def block_variant(request, variant_id):  
    variant = get_object_or_404(ColorVariant, id=variant_id)  
    variant.is_active = False  
    variant.save()
    return redirect('product_management')


def unblock_variant(request, variant_id): 
    variant = get_object_or_404(ColorVariant, id=variant_id) 
    variant.is_active = True 
    variant.save()
    return redirect('product_management')



# Category Management
@login_required
def category_management(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('admin_home')

    categories = Category.objects.all()
    paginator = Paginator(categories, 10)  # 10 categories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'category_management.html', {'page_obj': page_obj})



@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        offer_percent = request.POST.get('offer_percent', 0)

        if not name:
            messages.error(request, "Category name is required.")
            return redirect('add_category')

        # Check if the category already exists
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Category '{name}' already exists.")
            return redirect('add_category')

        category = Category(
            name=name,
            description=description,
            offer_percent=int(offer_percent)
        )
        category.save()

        messages.success(request, f"Category '{name}' added successfully.")
        return redirect('category_management')

    return render(request, 'add_category.html')



@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect('category_management')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm(instance=category)

    return render(request, 'edit_category.html', {'form': form, 'category': category})


# delete category
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect('category_management')


# Log out
def admin_logout(request):
    logout(request)
    return redirect('admin_login')  


#order management
@login_required
def order_management(request):
    orders = Order.objects.all().order_by('-date')
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'order_management.html', {'page_obj': page_obj})


# Only the changed section for update_order_status

@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Prevent status change if already Cancelled or Returned
    if order.status in ["Cancelled", "Returned"]:
        messages.error(request, "Cannot change status for cancelled or returned orders.")
        return redirect('order_management')

    if request.method == "POST":
        new_status = request.POST.get("status")
        order.status = new_status

        if new_status == "Delivered":
            for item in order.items.all():
                if item.variant:
                    if item.variant.stock >= item.quantity:
                        item.variant.stock -= item.quantity
                        item.variant.save()
                else:
                    if item.product.stock >= item.quantity:
                        item.product.stock -= item.quantity
                        item.product.save()
            order.payment_status = "Paid"

        elif new_status in ["Pending", "Shipped"]:
            order.payment_status = "Pending"

        elif new_status == "Cancelled":
            if order.payment_status == "Paid":
                user_profile = order.user.userprofile
                wallet, _ = Wallet.objects.get_or_create(user_profile=user_profile)
                refund_amount = sum(item.price * item.quantity for item in order.items.all())
                wallet.balance += refund_amount
                wallet.save()
                Transaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    transaction_type='Credited'
                )
            # Set payment_status to "Refunded" NOT "Failed"
            order.payment_status = "Refunded"

            for item in order.items.all():
                if item.variant:
                    item.variant.stock += item.quantity
                    item.variant.save()
                else:
                    item.product.stock += item.quantity
                    item.product.save()
        order.save()
    return redirect('order_management')


@login_required
def update_payment_status(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        order.payment_status = request.POST.get("payment_status")
        order.save()
    return redirect('order_management')



def order_details_admin(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.status = request.POST.get("status")
        order.payment_status = request.POST.get("payment_status")
        order.save()
        return redirect("order_management")

    order_items = OrderItem.objects.filter(order=order)
    order_address = OrderAddress.objects.filter(order=order).first()

    for item in order_items:
        item.return_obj = Return.objects.filter(order_item=item).first()

    return render(
        request,
        "order_details_admin.html",
        {
            "order": order,
            "order_items": order_items,
            "order_address": order_address,
        },
    )



@require_POST
def process_return(request, return_id):
    return_obj = get_object_or_404(Return, id=return_id)
    new_status = request.POST.get("new_status")
    current_status = return_obj.status

    if new_status in dict(Return.STATUS_CHOICES):
        if new_status == "Refunded" and current_status != "Refunded":
            user_profile = return_obj.order_item.order.user.userprofile
            wallet, created = Wallet.objects.get_or_create(user_profile=user_profile)

            refund_amount = calculate_refund_for_item(
                return_obj.order_item.order,
                return_obj.order_item
            )

            wallet.balance += refund_amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=refund_amount,
                transaction_type='Credited'
            )

            product = return_obj.order_item.product
            product.stock += return_obj.order_item.quantity
            product.save()

        return_obj.status = new_status
        return_obj.processed_at = timezone.now()
        return_obj.save()

        # --- Update order status if all items refunded ---
        order = return_obj.order_item.order
        all_items = order.items.all()
        all_returned = all(Return.objects.filter(order_item=item, status="Refunded").exists() for item in all_items)
        if all_returned:
            order.status = "Returned"
            order.payment_status = "Refunded"
            order.save()
        # --- End of update ---

        messages.success(request, f"Return status updated to {new_status}.")

        try:
            return redirect("admin_order_details", order_id=return_obj.order_item.order.id)
        except Exception as e:
            messages.error(request, f"Redirection failed: {e}")
            return redirect("admin_dashboard")
    else:
        messages.error(request, "Invalid return status selected.")
        return redirect("admin_dashboard")



#coupon management

def coupon_management(request):
    coupons = Coupon.objects.all()
    paginator = Paginator(coupons, 10)  # Show 10 coupons per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'coupon_management.html', {'page_obj': page_obj})



def add_coupon(request):
    if request.method == 'POST':
        try:
            code = request.POST.get('code', '').upper().strip()
            discount_percent = Decimal(request.POST.get('discount_percent', '0'))
            valid_from = parse_datetime(request.POST.get('valid_from'))
            valid_to = parse_datetime(request.POST.get('valid_to'))
            max_usage = int(request.POST.get('max_usage', '0'))
            min_purchase_amount = Decimal(request.POST.get('min_purchase_amount', '0'))

            # Validations
            if not code:
                raise ValidationError("Coupon code is required.")

            if discount_percent <= 0 or discount_percent > 100:
                raise ValidationError("Discount percent must be between 1 and 100.")

            if not valid_from or not valid_to or valid_from >= valid_to:
                raise ValidationError("Please enter valid dates. 'Valid From' should be before 'Valid To'.")

            if max_usage <= 0:
                raise ValidationError("Max usage must be a positive number.")

            if min_purchase_amount < 0:
                raise ValidationError("Minimum purchase amount cannot be negative.")

            # All validations passed
            Coupon.objects.create(
                code=code,
                discount_percent=discount_percent,
                valid_from=valid_from,
                valid_to=valid_to,
                max_usage=max_usage,
                min_purchase_amount=min_purchase_amount
            )
            messages.success(request, "Coupon added successfully.")
            return redirect('coupon_management')

        except ValidationError as e:
            messages.error(request, e.messages[0])
        except (InvalidOperation, ValueError) as e:
            messages.error(request, str(e))

    return render(request, 'add_coupon.html')



def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        try:
            code = request.POST.get('code', '').upper().strip()
            discount_percent = Decimal(request.POST.get('discount_percent', '0'))
            valid_from = parse_datetime(request.POST.get('valid_from'))
            valid_to = parse_datetime(request.POST.get('valid_to'))
            max_usage = int(request.POST.get('max_usage', '0'))
            min_purchase_amount = Decimal(request.POST.get('min_purchase_amount', '0'))

            if not code:
                raise ValidationError("Coupon code is required.")

            if discount_percent <= 0 or discount_percent > 100:
                raise ValidationError("Discount percent must be between 1 and 100.")

            if not valid_from or not valid_to or valid_from >= valid_to:
                raise ValidationError("Please enter valid dates.")

            if max_usage <= 0:
                raise ValidationError("Max usage must be positive.")

            if min_purchase_amount < 0:
                raise ValidationError("Minimum purchase can't be negative.")

            # Save updates
            coupon.code = code
            coupon.discount_percent = discount_percent
            coupon.valid_from = valid_from
            coupon.valid_to = valid_to
            coupon.max_usage = max_usage
            coupon.min_purchase_amount = min_purchase_amount
            coupon.save()

            messages.success(request, "Coupon updated successfully.")
            return redirect('coupon_management')

        except ValidationError as e:
            messages.error(request, e.messages[0])
        except (InvalidOperation, ValueError) as e:
            messages.error(request, str(e))

    return render(request, 'edit_coupon.html', {'coupon': coupon})



def delete_coupon(request, coupon_id):
    if request.method == 'POST':
        coupon = get_object_or_404(Coupon, id=coupon_id)
        coupon.delete()
        messages.success(request, "Coupon deleted successfully.")
    return redirect('coupon_management')



def sales_report(request):
    date_filter = request.GET.get('date')      
    month_filter = request.GET.get('month')    
    year_filter = request.GET.get('year')     

    orders = Order.objects.filter(payment_status='Paid')

    if date_filter:
        date_obj = parse_date(date_filter)
        orders = orders.filter(date__date=date_obj)
    elif month_filter:
        year, month = month_filter.split('-')
        orders = orders.filter(date__year=year, date__month=month)
    elif year_filter:
        orders = orders.filter(date__year=year_filter)

    total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
    total_orders = orders.count()

    total_items_sold = OrderItem.objects.filter(order__in=orders).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

    order_list = orders.order_by('-date').values('id', 'user__username', 'date', 'total', 'status')

    #pagination
    paginator = Paginator(order_list, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_items_sold': total_items_sold,
        'orders': page_obj,      
        'page_obj': page_obj,    
        'date_filter': date_filter or '',
        'month_filter': month_filter or '',
        'year_filter': year_filter or '',
    }

    return render(request, 'sales_report.html', context)



def download_sales_pdf(request):
    
    date_filter = request.GET.get('date')
    month_filter = request.GET.get('month')
    year_filter = request.GET.get('year')

    orders = Order.objects.filter(payment_status='Paid')

    if date_filter:
        date_obj = parse_date(date_filter)
        orders = orders.filter(date__date=date_obj)
    elif month_filter:
        year, month = month_filter.split('-')
        orders = orders.filter(date__year=year, date__month=month)
    elif year_filter:
        orders = orders.filter(date__year=year_filter)

    total_sales = orders.aggregate(total=Sum('final_total'))['total'] or 0
    total_orders = orders.count()
    total_items_sold = OrderItem.objects.filter(order__in=orders).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

    order_list = orders.order_by('-date').values('id', 'user__username', 'date', 'total', 'status')



    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_items_sold': total_items_sold,
        'orders': order_list,
    }

    template = get_template('sales_report_pdf.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode('UTF-8')), dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response




def download_sales_excel(request):
    date_filter = request.GET.get('date')
    month_filter = request.GET.get('month')
    year_filter = request.GET.get('year')

    orders = Order.objects.filter(payment_status='Paid')

    if date_filter:
        date_obj = parse_date(date_filter)
        orders = orders.filter(date__date=date_obj)
    elif month_filter:
        year, month = month_filter.split('-')
        orders = orders.filter(date__year=year, date__month=month)
    elif year_filter:
        orders = orders.filter(date__year=year_filter)

    order_list = orders.order_by('-date').values('id', 'user__username', 'date', 'total', 'status')

    df = pd.DataFrame(order_list)
    df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M')

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales Report')

    return response
