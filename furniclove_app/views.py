from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
import random
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from .forms import SignupForm
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator

from django.core.paginator import Paginator

from admin_panel.models import Product,ColorVariant,Category, Coupon, Return 

from furniclove_app.models import Address, Cart, CartItem, Order, OrderItem, OrderAddress, Wallet, Transaction, Wishlist,Review

from django.contrib.auth import logout

import uuid
from .models import PasswordResetToken
from django.contrib.auth.hashers import make_password

from .models import UserProfile
from .forms import UserProfileForm
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash

import json
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.db.models import Sum
from django.db import transaction

from django.db import IntegrityError

from .forms import ReturnReasonForm

from .models import Wallet
from django.utils import timezone 

from django.utils.timezone import now
from django.db.models import F

from django.views.decorators.cache import never_cache


import razorpay
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

from django.db import transaction as db_transaction
from decimal import Decimal

from .forms import ReviewForm


from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint  

from .refund_utils import calculate_refund_for_item


# Views for different pages
def index(request):
    return render(request, 'index.html')



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            # Generate unique token
            token = str(uuid.uuid4())
            PasswordResetToken.objects.create(user=user, token=token)

            # Send reset email
            reset_link = request.build_absolute_uri(f'/reset-password/{token}/')
            send_mail(
                'Reset Your Password',
                f'Click the link to reset your password: {reset_link}',
                'your_email@example.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, "Password reset link sent to your email.")
        else:
            messages.error(request, "No account found with this email.")

    return render(request, 'forgot_password.html')


def reset_password(request, token):
    reset_entry = PasswordResetToken.objects.filter(token=token).first()

    if not reset_entry:
        messages.error(request, "Invalid or expired token.")
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return render(request, 'reset_password.html', {'token': token})

        reset_entry.user.password = make_password(new_password)
        reset_entry.user.save()
        reset_entry.delete()  # Remove token after reset

        messages.success(request, "Password has been reset successfully. Please login.")
        return redirect('user_login')

    return render(request, 'reset_password.html', {'token': token})



def shop(request):
    category_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort-by', '')
    search_query = request.GET.get('search', '')

    products = Product.objects.filter(is_active=True)

    # Filter by category
    if category_filter:
        products = products.filter(category__name=category_filter)

    # Filter by search
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Apply sorting
    if sort_by == 'a-to-z':
        products = products.order_by('name')
    elif sort_by == 'z-to-a':
        products = products.order_by('-name')
    elif sort_by == 'price-low-to-high':
        products = products.order_by('original_price')
    elif sort_by == 'price-high-to-low':
        products = products.order_by('-original_price')
    elif sort_by == 'discount-low-to-high':
        products = products.order_by('discount_percent')
    elif sort_by == 'discount-high-to-low':
        products = products.order_by('-discount_percent')

    # Calculate discount percent (if not already a model field)
    for product in products:
        if product.original_price and product.discounted_price:
            product.discount_percent = round(((product.original_price - product.discounted_price) / product.original_price) * 100)

    # Pagination
    paginator = Paginator(products, 6)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Product.objects.values_list('category__name', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'category': category_filter,
        'sort_by': sort_by,
        'search_query': search_query,
        'categories': categories,
    }
    return render(request, 'shop.html', context)


def about(request):
    return render(request, 'about.html')


def services(request):
    return render(request, 'services.html')


def contact(request):
    return render(request, 'contact.html')


def otp_view(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        otp_code = request.session.get('otp_code')
        email = request.session.get('otp_email')

        if otp_input == otp_code:
            messages.success(request, "OTP verified successfully!")
            return redirect('user_login')  
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'otp.html')  # Render OTP input page


# Send OTP function
def send_otp(request, user):
    otp = random.randint(100000, 999999)  
    
    # Send OTP via email
    subject = "Your OTP for Signup"
    message = f"Your OTP is {otp}."
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
    
    request.session['otp_code'] = str(otp)
    request.session['otp_email'] = user.email  


def resend_otp(request):
    # Get the user email from the session
    email = request.session.get('otp_email')
    user = User.objects.get(email=email)
    
    # Resend OTP
    send_otp(request, user)
    
    messages.success(request, "OTP resent to your email.")
    return redirect('otp')  # Redirect back to the OTP page



@never_cache
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose another.")
                return render(request, 'signup.html', {'form': form})

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email ID is already used.")
                return render(request, 'signup.html', {'form': form})

            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_superuser = False
            user.is_staff = False
            user.save()

            # OTP 
            send_otp(request, user)

            messages.success(request, "Please check your email for the OTP.")
            return redirect('otp')
        else:
            return render(request, 'signup.html', {'form': form})
    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})



@never_cache
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(username=username)
            if not user.is_active:  
                messages.error(request, "You are a blocked user.")  
                return redirect('user_login')
        except User.DoesNotExist:
            pass  

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')

        messages.error(request, "Invalid username or password.")  

    return render(request, 'user_login.html')


# Forgot Password View
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token and send email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(str(user.pk).encode())
            reset_link = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

            subject = "Password Reset Request"
            message = f"Click the link to reset your password: {reset_link}"
            send_mail(subject, message, 'no-reply@example.com', [email])
            
            messages.success(request, "Password reset link has been sent to your email.")
            return redirect('forgot_password')
        
        except User.DoesNotExist:
            messages.error(request, "This email address is not registered.")
    
    return render(request, 'forgot_password.html')



# Reset Password View
def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        
        # Check if token is valid
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST.get('password')
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your password has been reset successfully!")
                return redirect('login')
            
            return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})
        else:
            messages.error(request, "This link has expired or is invalid.")
            return redirect('login')

    except Exception as e:
        messages.error(request, "Invalid reset link.")
        return redirect('login')


def user_logout(request):
    logout(request)
    request.session.flush()  # Clear only user-related session data
    return redirect('user_login')  # Redirect to user login page




@login_required
def profile_update(request):
    try:
        # Ensure the user has a related UserProfile
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # If the user doesn't have a UserProfile, create one
        user_profile = UserProfile(user=request.user)
        user_profile.save()

    # Now handle form submission
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile, user=request.user)

        if form.is_valid():
            new_username = form.cleaned_data.get('username')  # Get the username from form

            # Check if username already exists and is not the current user's username
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                messages.error(request, "This username is already taken. Please choose another one.")
                return redirect('profile_update')

            try:
                form.save()  # Save the form
                messages.success(request, "Profile updated successfully.")
                return redirect('profile_update')
            except IntegrityError:
                messages.error(request, "An error occurred while updating your profile.")
                return redirect('profile_update')
    else:
        form = UserProfileForm(instance=user_profile, user=request.user)

    # Now also pass the wallet to the template, if available
    try:
        wallet = user_profile.wallet  # Access wallet related to the UserProfile
    except Wallet.DoesNotExist:
        wallet = None  # If no wallet exists, set wallet to None
    
    return render(request, 'profile_update.html', {'form': form, 'wallet': wallet})




@login_required  
def change_password(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")

        user = request.user  
        if user.check_password(old_password):  
            user.set_password(new_password)  
            user.save()
            update_session_auth_hash(request, user) 
            messages.success(request, "Password changed successfully.")
            return redirect("profile_update")  
            messages.error(request, "Old password is incorrect.")

    return render(request, "profile_update.html")



def product_detail(request, product_id, variant_id=None):
    product = get_object_or_404(Product, id=product_id)
    color_variants = product.color_variants.all()
    selected_variant = None

    if variant_id:
        selected_variant = get_object_or_404(ColorVariant, id=variant_id, product=product)

    # Calculate the discount for the selected variant
    discount_percent_variant = product.offer_percent  
    discount_price_variant = 0
    if selected_variant:
        if selected_variant.price_override:
            original_price_variant = selected_variant.price_override
            discount_price_variant = original_price_variant - (original_price_variant * discount_percent_variant / 100)
        else:
            discount_price_variant = product.original_price - (product.original_price * discount_percent_variant / 100)
    else:
        discount_price_variant = product.original_price - (product.original_price * discount_percent_variant / 100)

    # Calculate the product offer vs. category offer
    category_discount_percent = product.category.offer_percent if product.category.offer_percent else 0

    # Compare and apply the higher discount offer (either product or category)
    if category_discount_percent > discount_percent_variant:
        discount_percent_variant = category_discount_percent
        discount_price_variant = product.original_price - (product.original_price * discount_percent_variant / 100)

    # Category offer logic
    discount_percent_product = 0
    if product.original_price > product.discounted_price:
        discount_price_product = product.original_price - product.discounted_price
        if product.original_price > 0:
            discount_percent_product = (discount_price_product / product.original_price) * 100


    related_products = product.related_products.all()
        

    return render(request, 'product_detail.html', {
        'product': product,
        'color_variants': color_variants,
        'selected_variant': selected_variant,
        'discount_price_variant': discount_price_variant,
        'discount_percent_variant': discount_percent_variant,
        'discount_percent_product': discount_percent_product,
        'related_products': related_products,
    })


@login_required
def my_account(request):
    return render(request, 'my_account.html')


@login_required
def address_manage(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        district = request.POST.get('district')
        state = request.POST.get('state')
        country = request.POST.get('country')
        zipcode = request.POST.get('zipcode')

        Address.objects.create(
            user=request.user,  
            full_name=full_name,
            phone=phone,
            address=address,
            district=district,
            state=state,
            country=country,
            zipcode=zipcode
        )

        messages.success(request, "Address added successfully!")  
        return redirect('address_manage')  
   
    addresses = Address.objects.filter(user=request.user)

    return render(request, 'address_manage.html', {'addresses': addresses})


@login_required
def address_selection(request):
    addresses = Address.objects.filter(user=request.user)  
    return render(request, 'checkout.html', {'addresses': addresses})  




@login_required
def delete_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        address.delete()
        messages.success(request, "Address deleted successfully!")
    except Address.DoesNotExist:
        messages.error(request, "Address not found.")
    return redirect('address_manage') 



@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        address.full_name = request.POST.get("full_name")
        address.phone = request.POST.get("phone")
        address.address = request.POST.get("address")
        address.district = request.POST.get("district")
        address.state = request.POST.get("state")
        address.country = request.POST.get("country")
        address.zipcode = request.POST.get("zipcode")
        address.save()
        
        messages.success(request, "Address updated successfully!")
        return redirect("address_manage")

    return render(request, "edit_address.html", {"address": address})



@csrf_exempt
@login_required
def add_address_ajax(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        district = request.POST.get('district')
        state = request.POST.get('state')
        country = request.POST.get('country')
        zipcode = request.POST.get('zipcode')

        # Basic validation
        if not full_name or not phone or not address:
            return JsonResponse({'success': False, 'error': 'Required fields are missing.'})

        new_address = Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            district=district,
            state=state,
            country=country,
            zipcode=zipcode
        )

        return JsonResponse({
            'success': True,
            'address': {
                'id': new_address.id,
                'full_name': new_address.full_name,
                'phone': new_address.phone,
                'address': new_address.address,
                'district': new_address.district,
                'state': new_address.state,
                'country': new_address.country,
                'zipcode': new_address.zipcode
            }
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})




@login_required(login_url='user_login')
def add_to_cart(request, product_id, variant_id=None):
    user = request.user
    product = get_object_or_404(Product, id=product_id)

    if variant_id:
        variant = get_object_or_404(ColorVariant, id=variant_id, product=product)
        stock_available = variant.stock if variant.stock is not None else 0
    else:
        variant = None
        stock_available = product.stock if product.stock is not None else 0

    if stock_available <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect('cart_view')

    # Get or create cart
    cart, created = Cart.objects.get_or_create(user=user)

    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)

    if not created:
        if cart_item.quantity >= 5:
            messages.warning(request, "Limit reached! A maximum of 5 units per product can be added.")
            return redirect('cart_view')  
        
        if cart_item.quantity + 1 > stock_available:
            messages.error(request, f"Only {stock_available} units available.")
            return redirect('cart_view')

        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, "Item added to cart.")

    else:
        cart_item.quantity = 1
        cart_item.save()
        messages.success(request, "Item added to cart.")
   

    if request.POST.get('from_wishlist') == '1':
        wishlist_item = Wishlist.objects.filter(user=user, product=product, variant=variant).first()
        if wishlist_item:
            wishlist_item.delete()
            messages.success(request, "Removed from wishlist after adding to cart.")

    return redirect('cart_view')



@login_required(login_url='user_login')
def cart_view(request):
    user = request.user
    cart, created = Cart.objects.get_or_create(user=user)
    cart_items = cart.cart_items.select_related('product', 'variant').all()

    total_price = Decimal("0.00")  
    out_of_stock = False  
    discount = Decimal("0.00")

    for item in cart_items:
        if item.variant:
            item.sale_price = item.variant.discounted_price  
            item.discount = item.product.final_offer_percent  
            item.total_price = item.sale_price * item.quantity

            if item.variant.stock == 0:
                out_of_stock = True
        else:
            item.sale_price = item.product.discounted_price  
            item.discount = item.product.final_offer_percent  
            item.total_price = item.sale_price * item.quantity
            
            if item.product.stock == 0:
                out_of_stock = True   
        
        total_price += item.total_price 

    request.session['subtotal'] = str(total_price)  
    
    if cart.coupon and cart.coupon.is_valid() and total_price >= cart.coupon.min_purchase_amount:
        discount = (total_price * cart.coupon.discount_percent) / 100
    else:
        discount = Decimal("0.00")
        if cart.coupon:
            cart.coupon = None
            cart.save()


    if discount > total_price:
        discount = total_price

    discounted_total = total_price - discount

    request.session['discount'] = str(discount)   
    request.session['final_total'] = str(discounted_total)


    # Fetch valid coupons
    valid_coupons = Coupon.objects.filter(
        active=True,
        valid_from__lte=now(),
        valid_to__gte=now(),
        used_count__lt=F('max_usage')
    )
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'final_total': discounted_total,
        'out_of_stock': out_of_stock,
        'coupons': valid_coupons,
        'discount': discount,
        'coupon_code': cart.coupon.code if cart.coupon else None,
        'coupon_discount_percent': cart.coupon.discount_percent if cart.coupon else None,
    })



@login_required(login_url='user_login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart_view')



@login_required(login_url='user_login')
def update_cart(request, cart_id, quantity):
    if request.method == "POST":
        try:
            with transaction.atomic():
                new_quantity = int(quantity)  

                cart_item = get_object_or_404(CartItem.objects.select_for_update(), id=cart_id, cart__user=request.user)

               
                stock_available = getattr(cart_item.variant, 'stock', None) or cart_item.product.stock or 0

               
                if new_quantity > 5:
                    return JsonResponse({'success': False, 'message': "Limit reached! Maximum 5 units per product."}, status=400)

                # Check stock availability
                if new_quantity > stock_available:
                    return JsonResponse({'success': False, 'message': f"Only {stock_available} units available."}, status=400)

                print(f"Before update: {cart_item.product.name}, Quantity in DB: {cart_item.quantity}")
                cart_item.quantity = new_quantity
                cart_item.save()
                print(f"After update: {cart_item.product.name}, New Quantity in DB: {cart_item.quantity}")

                # total price calculation
                total_price = cart_item.cart.total_price() if callable(cart_item.cart.total_price) else cart_item.cart.total_price

                return JsonResponse({'success': True, 'total_price': total_price, 'updated_quantity': cart_item.quantity})

        except Exception as e:
            print("Error in update_cart:", str(e))  
            return JsonResponse({'success': False, 'message': f"Something went wrong: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': "Invalid request."}, status=400)


@login_required
def checkout(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    delivery_charge = Decimal("50.00")
    # Always start with zeros, never use session for these
    subtotal = Decimal("0.00")
    discount = Decimal("0.00")
    final_total = Decimal("0.00")
    total = Decimal("0.00")
    
    
    try:
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        coupon_code = cart.coupon.code if cart.coupon else None
        coupon_discount_percent = cart.coupon.discount_percent if cart.coupon else None


        subtotal = sum(
            (item.sale_price if hasattr(item, "sale_price") else (
                item.variant.discounted_price if (item.variant and hasattr(item.variant, "discounted_price") and item.variant.discounted_price)
                else (item.product.discounted_price if hasattr(item.product, "discounted_price") and item.product.discounted_price
                else item.product.original_price)
            )) * item.quantity
            for item in cart_items
        )

        if cart.coupon:
            coupon_code = cart.coupon.code
            coupon_discount_percent = cart.coupon.discount_percent
            discount = (Decimal(cart.coupon.discount_percent) / Decimal(100)) * subtotal
        else:
            coupon_code = None
            coupon_discount_percent = None
            discount = Decimal("0.00")

            for key in ['coupon_id', 'discount', 'final_total']:
                request.session.pop(key, None)
        
        final_total = subtotal - discount
        total = final_total + delivery_charge

    except Cart.DoesNotExist:
        cart = None
        cart_items = CartItem.objects.none()
        subtotal = Decimal("0.00")
        discount = Decimal("0.00")
        final_total = Decimal("0.00")
        total = Decimal("0.00")
        coupon_code = None
        coupon_discount_percent = None
        
    if request.method == "POST":
        selected_address_id = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        selected_address = Address.objects.filter(id=selected_address_id, user=user).first()
        if not selected_address:
            return JsonResponse({'error': 'Invalid address selection.'}, status=400)

        request.session["selected_address_id"] = selected_address_id

        # Razorpay
        if payment_method == "Razorpay":
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            try:
                razorpay_order = client.order.create({
                    "amount": int(total * 100),  # Amount in paise
                    "currency": "INR",
                    "payment_capture": "1"
                })

                request.session["razorpay_order_id"] = razorpay_order["id"]

                return JsonResponse({
                    "razorpay_order_id": razorpay_order["id"],
                    "total_amount": float(total)
                })

            except razorpay.errors.BadRequestError as e:
                messages.error(request, f"Razorpay Error: {str(e)}")
                return redirect('checkout')

        # COD
        elif payment_method == "COD":
            if total >= 1000:
                messages.error(request, "COD is available only for orders below ₹1000.")
                return redirect("checkout")
            
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    subtotal=subtotal,
                    discount=discount,
                    final_total=final_total,
                    payment_method="COD", 
                    status="Pending",
                    payment_status="Pending",
                    delivery_charge=delivery_charge,
                    total=total,
                    coupon=cart.coupon if hasattr(cart, "coupon") else None,
                )

                OrderAddress.objects.create(
                    order=order,
                    full_name=selected_address.full_name,
                    phone=selected_address.phone,
                    address=selected_address.address,
                    district=selected_address.district,
                    state=selected_address.state,
                    country=selected_address.country,
                    zipcode=selected_address.zipcode
                )

                
                for item in cart_items:
                    # Get the per-unit sale price
                    if hasattr(item, "sale_price"):
                        unit_price = item.sale_price
                    elif item.variant and hasattr(item.variant, "discounted_price") and item.variant.discounted_price:
                        unit_price = item.variant.discounted_price
                    elif hasattr(item.product, 'discounted_price') and item.product.discounted_price:
                        unit_price = item.product.discounted_price
                    else:
                        unit_price = item.product.original_price

                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=unit_price  # <--- CORRECT: per-unit price
                    )    

                if cart_items.exists():
                    cart_items.delete()
                cart.delete()

                # Clear session values
                for key in ['subtotal', 'discount', 'final_total']:
                    request.session.pop(key, None)

            return redirect('order_success', order_id=order.id)

        # Wallet
        elif payment_method == "Wallet":
            user_profile = user.userprofile
            wallet_balance = user_profile.wallet.balance if hasattr(user_profile, 'wallet') else 0

            if wallet_balance >= total:
                user_profile.wallet.balance -= total
                user_profile.wallet.save()

                with transaction.atomic():
                    order = Order.objects.create(
                        user=user,
                        subtotal=subtotal,
                        discount=discount,
                        final_total=final_total,
                        payment_method="Wallet",
                        status="Pending",
                        payment_status="Paid", 
                        delivery_charge=delivery_charge,
                        total=total,
                        coupon=cart.coupon if hasattr(cart, "coupon") else None,
                    )

                    OrderAddress.objects.create(
                        order=order,
                        full_name=selected_address.full_name,
                        phone=selected_address.phone,
                        address=selected_address.address,
                        district=selected_address.district,
                        state=selected_address.state,
                        country=selected_address.country,
                        zipcode=selected_address.zipcode
                    )

                    for item in cart_items:
                        # Get the per-unit sale price
                        if hasattr(item, "sale_price"):
                            unit_price = item.sale_price
                        elif item.variant and hasattr(item.variant, "discounted_price") and item.variant.discounted_price:
                            unit_price = item.variant.discounted_price
                        elif hasattr(item.product, 'discounted_price') and item.product.discounted_price:
                            unit_price = item.product.discounted_price
                        else:
                            unit_price = item.product.original_price

                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            variant=item.variant,
                            quantity=item.quantity,
                            price=unit_price  # <--- CORRECT: per-unit price
                        )    

                    if cart_items.exists():
                        cart_items.delete()
                    cart.delete()

                    for key in ['subtotal', 'discount', 'final_total']:
                        request.session.pop(key, None)

                messages.success(request, "Your order was placed successfully using Wallet payment.")
                return redirect('order_success', order_id=order.id)
            else:
                messages.error(request, "Insufficient wallet balance.")
                return redirect('checkout')

    return render(request, 'checkout.html', {
        'addresses': addresses,
        'cart_items': cart_items,
        'discount': discount,
        'final_total': final_total,  
        'delivery_charge': delivery_charge,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'total': total,
        'subtotal': subtotal,
        'coupon_code': coupon_code,
        'coupon_discount_percent': coupon_discount_percent,
        'cart':cart,
        
    })



def order_success(request, order_id):
    try:
        if order_id.isdigit():
            order = Order.objects.get(id=order_id)
        else:
            order = Order.objects.get(order_id=order_id)

        razorpay_payment_id = request.GET.get('razorpay_payment_id', '')

        if order.payment_method == "Razorpay" and razorpay_payment_id:
            order.razorpay_payment_id = razorpay_payment_id
            order.payment_status = "Paid"
            order.save()

        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

        return render(request, 'order_success.html', {'order': order})

    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)


#order details
@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-date')

    # Paginate orders
    paginator = Paginator(orders, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'user_orders.html', {'page_obj': page_obj})



@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_address = OrderAddress.objects.filter(order=order).first()
    order.refresh_from_db()

    order_items = OrderItem.objects.filter(order=order)
    for item in order_items:
        item.subtotal = item.quantity * item.price  
        item.return_obj = Return.objects.filter(order_item=item).first()

    razorpay_payment_id = order.razorpay_payment_id if order.payment_method == 'Razorpay' else None

    # Get coupon info if attached to order
    coupon = getattr(order, "coupon", None) if hasattr(order, "coupon") else None
    coupon_code = coupon.code if coupon else None
    coupon_discount_percent = coupon.discount_percent if coupon else None
    coupon_discount = order.discount  # this is the discount amount

    original_total = order.subtotal + order.delivery_charge

    context = {
        'order': order,
        'order_address': order_address,
        'order_items': order_items,
        'razorpay_payment_id': razorpay_payment_id,
        'original_total': original_total,
        'coupon_code': coupon_code,
        'coupon_discount_percent': coupon_discount_percent,
        'coupon_discount': coupon_discount,
    }
    return render(request, 'order_details.html', context)



@login_required
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)

        if order.status in ['Shipped', 'Delivered']:
            return HttpResponse("You cannot cancel a shipped or delivered order.", status=400)

        # Only refund if order was paid and not already cancelled/refunded
        if order.payment_status == "Paid" and order.status != "Cancelled":
            if order.payment_method in ["Wallet", "Razorpay"]:
                # Refund to wallet
                user_profile = request.user.userprofile
                wallet, _ = Wallet.objects.get_or_create(user_profile=user_profile)
                wallet.balance += order.total
                wallet.save()

                # Log wallet transaction
                wallet.transactions.create(
                    amount=order.total,
                    transaction_type='Credited',
                    description=f"Refund for cancelled order {order.order_id}"
                )

        # Change order status to "Cancelled"
        order.status = 'Cancelled'
        # Change payment status to "Failed" or maybe "Refunded"
        order.payment_status = 'Refunded'
        order.save()
        return redirect('user_orders')

    except Order.DoesNotExist:
        return redirect('user_orders')



@login_required
def return_product(request, order_id, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order_id=order_id)
    order = item.order

    if request.method == 'POST':
        form = ReturnReasonForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']

            # Only create Return object, do NOT credit wallet here
            Return.objects.create(order_item=item, reason=reason, status="Requested")

            messages.success(request, "Return request submitted. Awaiting admin approval.")
            return redirect('order_details', order_id=order_id)
    return redirect('order_details', order_id=order_id)




@login_required
def wallet(request):
    wallet, created = Wallet.objects.get_or_create(user_profile=request.user.userprofile)
    transactions = wallet.transactions.all().order_by('-created_at')

    # Filters
    amount = request.GET.get('amount')
    date = request.GET.get('date')

    if amount:
        transactions = transactions.filter(amount__icontains=amount)
    if date:
        transactions = transactions.filter(created_at__date=date)

    # Pagination
    paginator = Paginator(transactions, 15)  # 5 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'balance': wallet.balance,
        'page_obj': page_obj,
    }
    return render(request, 'wallet.html', context)



@login_required
def wallet_payment(request):
    if request.method == 'POST':
        user_profile = request.user.userprofile
        wallet = Wallet.objects.get(user_profile=user_profile)
        cart = Cart.objects.filter(user=request.user).first()

        if not cart:
            return JsonResponse({'success': False, 'message': 'Cart is empty.'})

        cart_items = CartItem.objects.filter(cart=cart)
        subtotal = sum(
            (item.sale_price if hasattr(item, "sale_price") else (
                item.variant.discounted_price if (item.variant and hasattr(item.variant, "discounted_price") and item.variant.discounted_price)
                else (item.product.discounted_price if hasattr(item.product, "discounted_price") and item.product.discounted_price
                else item.product.original_price)
            )) * item.quantity
            for item in cart_items
        )

        if cart.coupon:
            discount = (Decimal(cart.coupon.discount_percent) / Decimal(100)) * subtotal
        else:
            discount = Decimal("0.00")
        final_total = subtotal - discount
        delivery_charge = Decimal("50.00")
        total = final_total + delivery_charge

        if wallet.balance < total:
            return JsonResponse({'success': False, 'message': 'Not enough wallet balance.'})

        try:
            with transaction.atomic():
                wallet.balance -= total
                wallet.save()

                order = Order.objects.create(
                    user=request.user,
                    subtotal=subtotal,
                    discount=discount,
                    final_total=final_total,
                    delivery_charge=delivery_charge,
                    total=total,
                    payment_status="Paid",
                    payment_method="Wallet",
                    coupon=cart.coupon if hasattr(cart, "coupon") else None,
                )

                for item in cart_items:
                    # Get the per-unit sale price
                    if hasattr(item, "sale_price"):
                        unit_price = item.sale_price
                    elif item.variant and hasattr(item.variant, "discounted_price") and item.variant.discounted_price:
                        unit_price = item.variant.discounted_price
                    elif hasattr(item.product, 'discounted_price') and item.product.discounted_price:
                        unit_price = item.product.discounted_price
                    else:
                        unit_price = item.product.original_price

                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=unit_price  
                    )    

                address_id = request.session.get("selected_address_id")
                if address_id:
                    address = get_object_or_404(Address, id=address_id)
                    OrderAddress.objects.create(
                        order=order,
                        full_name=address.full_name,
                        phone=address.phone,
                        address=address.address,
                        district=address.district,
                        state=address.state,
                        country=address.country,
                        zipcode=address.zipcode
                    )

                wallet.transactions.create(
                    amount=total,
                    transaction_type='Debited'
                )

                cart_items.delete()
                cart.delete()
                for key in ['subtotal', 'discount', 'final_total']:
                    request.session.pop(key, None)
                request.session.modified = True

            return JsonResponse({'success': True, 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Payment failed: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})



def check_stock_updates(request):
    # Only check the current user's cart items!
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
    except Cart.DoesNotExist:
        cart_items = []

    items = []
    for item in cart_items:
        stock = item.variant.stock if item.variant else item.product.stock  
        items.append({
            "id": item.id,
            "stock": stock,
        })

    return JsonResponse({"items": items})



def check_product_stock(request, product_id, variant_id=None):
    try:
        if variant_id:
            variant = ColorVariant.objects.get(id=variant_id)
            stock = variant.stock
        else:
            product = Product.objects.get(id=product_id)
            stock = product.stock
        
        return JsonResponse({"stock": stock})
    
    except (Product.DoesNotExist, ColorVariant.DoesNotExist):
        return JsonResponse({"error": "Product not found"}, status=404)
    


@login_required
def razorpay_payment_success(request):
    payment_id = request.GET.get("payment_id")
    order_id = request.session.get("razorpay_order_id")

    if not payment_id or not order_id:
        messages.error(request, "Invalid payment details.")
        return redirect('checkout')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        payment = client.payment.fetch(payment_id)
        if payment['status'] in ["authorized", "captured"]:
            if payment['status'] == "authorized":
                client.payment.capture(payment_id, payment['amount'])

            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart_items = CartItem.objects.filter(cart=cart)
                subtotal = sum(
                    (item.sale_price if hasattr(item, "sale_price") else (
                        item.variant.discounted_price if (item.variant and hasattr(item.variant, "discounted_price") and item.variant.discounted_price)
                        else (item.product.discounted_price if hasattr(item.product, "discounted_price") and item.product.discounted_price
                        else item.product.original_price)
                    )) * item.quantity
                    for item in cart_items
                )
                if cart.coupon:
                    discount = (Decimal(cart.coupon.discount_percent) / Decimal(100)) * subtotal
                else:
                    discount = Decimal("0.00")
                final_total = subtotal - discount
                delivery_charge = Decimal("50.00")
                total = final_total + delivery_charge
                

                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user,
                        subtotal=subtotal,
                        discount=discount,
                        final_total=final_total,
                        delivery_charge=delivery_charge,
                        total=total,
                        payment_status="Paid",
                        payment_method="Razorpay",
                        razorpay_payment_id=payment_id,
                        coupon=cart.coupon if hasattr(cart, "coupon") else None,
                    )

                    for item in cart_items:
                        # Get the per-unit sale price
                        if hasattr(item, "sale_price"):
                            unit_price = item.sale_price
                        elif item.variant and hasattr(item.variant, "discounted_price") and item.variant.discounted_price:
                            unit_price = item.variant.discounted_price
                        elif hasattr(item.product, 'discounted_price') and item.product.discounted_price:
                            unit_price = item.product.discounted_price
                        else:
                            unit_price = item.product.original_price

                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            variant=item.variant,
                            quantity=item.quantity,
                            price=unit_price  # CORRECT: per-unit price!
                        )

                    address_id = request.session.get("selected_address_id")
                    if address_id:
                        address = get_object_or_404(Address, id=address_id)
                        OrderAddress.objects.create(
                            order=order,
                            full_name=address.full_name,
                            phone=address.phone,
                            address=address.address,
                            district=address.district,
                            state=address.state,
                            country=address.country,
                            zipcode=address.zipcode
                        )

                    if hasattr(cart, 'coupon') and cart.coupon:
                        apply_coupon_usage(request)

                    cart_items.delete()
                    cart.delete()
                    for key in ['subtotal', 'discount', 'final_total']:
                        request.session.pop(key, None)
                    request.session.modified = True

                    messages.success(request, "Payment captured successfully! Your order has been placed.")
                    return redirect('order_success', order_id=order.id)
            else:
                messages.error(request, "Cart is empty. Please add items before payment.")
                return redirect('cart_view')
        else:
            messages.error(request, "Payment failed. Please try again.")
            return redirect('razorpay_payment_failure')

    except razorpay.errors.BadRequestError as e:
        messages.error(request, f"Razorpay Error: {str(e)}")
        return redirect('checkout')
    except Exception as e:
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('cart_view')



def razorpay_payment_failure(request):
    """ Handle failed payments with a custom message """

    payment_id = request.GET.get("razorpay_payment_id", "")

    messages.error(request, f"Payment failed. Please try again. (Payment ID: {payment_id})")

    return render(request, 'payment_failed.html', {
        'payment_id': payment_id
    })




def apply_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get("coupon", "").strip().upper()
        cart = Cart.objects.get(user=request.user)

        # User submits empty coupon field: clear coupon!
        if not coupon_code:
            cart.coupon = None
            cart.save()
            subtotal = Decimal(sum(item.subtotal() for item in cart.cart_items.all()))
            request.session['final_total'] = str(subtotal)
            request.session['discount'] = str(Decimal("0.00"))
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'final_total': f"Rs.{subtotal:.2f}"
                })
            return redirect('cart_view')

        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if not coupon.is_valid():
                cart.coupon = None  # Ensure coupon is cleared for invalid/expired
                cart.save()
                return JsonResponse({'success': False, 'error': 'Coupon expired, inactive, or exceeded usage'})

            if coupon.discount_percent <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid discount value'})

            subtotal = Decimal(sum(item.subtotal() for item in cart.cart_items.all()))
            if subtotal < coupon.min_purchase_amount:
                return JsonResponse({'success': False, 'error': f'Minimum purchase amount is Rs.{coupon.min_purchase_amount}'})
            
            cart.coupon = coupon
            cart.save()

            discount_amount = (coupon.discount_percent / Decimal(100)) * subtotal
            final_total = subtotal - discount_amount

            request.session['coupon_id'] = coupon.id
            request.session['final_total'] = str(final_total.quantize(Decimal('0.01')))
            request.session['discount'] = str(discount_amount.quantize(Decimal('0.01')))

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'final_total': f"Rs.{final_total:.2f}"
                })

            return redirect('cart_view')

        except Coupon.DoesNotExist:
            cart.coupon = None  # Clear coupon if invalid code
            cart.save()
            return JsonResponse({'success': False, 'error': 'Invalid coupon code'})

    return redirect('cart_view')


def apply_coupon_usage(request):
    coupon_id = request.session.get("coupon_id")
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon.used_count = F('used_count') + 1
            coupon.save()
            coupon.refresh_from_db()
            del request.session["coupon_id"]
        except Coupon.DoesNotExist:
            pass





def add_to_wishlist(request, product_id, variant_id=None):
    """Add product with or without variant to wishlist"""
    
    # Get the product
    product = get_object_or_404(Product, id=product_id)

    # Check for color variant if provided
    variant = None
    if variant_id:
        variant = get_object_or_404(ColorVariant, id=variant_id)

    # Add to wishlist or prevent duplicates
    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product,
        variant=variant
    )
    
    if created:
        messages.success(request, "Added to wishlist successfully!")
    else:
        messages.info(request, "Item is already in your wishlist.")

    return redirect('wishlist')



def wishlist(request):
    """Display wishlist items"""
    wishlist_items = Wishlist.objects.filter(user=request.user)
    
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'wishlist.html', context)    



def remove_from_wishlist(request, item_id):
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    wishlist_item.delete()
    messages.success(request, "Removed from wishlist successfully.")
    return redirect('wishlist')



@login_required
def submit_review(request, product_id):
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        user = request.user
        product = get_object_or_404(Product, id=product_id)

        # Prevent duplicate reviews: update if exists, else create
        review, created = Review.objects.update_or_create(
            user=user,
            product=product,
            defaults={'rating': rating, 'comment': comment}
        )

        return JsonResponse({
            'success': True,
            'user': user.username,
            'rating': rating,
            'comment': comment,
            'created': created,
        })

    return JsonResponse({'success': False}, status=400)



def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    order_address = OrderAddress.objects.filter(order=order).first()

    coupon = getattr(order, "coupon", None)
    coupon_code = coupon.code if coupon else None
    coupon_discount_percent = coupon.discount_percent if coupon else None
    coupon_discount = order.discount if hasattr(order, 'discount') else None

    html_string = render_to_string('invoice_template.html', {
        'order': order,
        'order_items': order_items,
        'order_address': order_address,
        'user': request.user,
        'coupon_code': coupon_code,
        'coupon_discount_percent': coupon_discount_percent,
        'coupon_discount': coupon_discount,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.pdf"'

    weasyprint.HTML(string=html_string).write_pdf(response)

    return response


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)