from django.shortcuts import render,redirect,get_object_or_404

from django.core.mail import send_mail

from django.views.generic import View

from django.contrib import messages

from django.contrib.auth import authenticate,login,logout

from django.db.models import Sum,Q,Avg

from django.utils.decorators import method_decorator

from bean_app.decorators import signin_required

from django.views.decorators.cache import never_cache

from django.contrib.auth.mixins import LoginRequiredMixin

from bean_app.forms import SignInForm,SignUpForm,OrderForm,OtpVerifyForm,ReviewForm

from .models import User,Cart,BeanBag,BeanBagVariant,Order,OrderItem,Material,Review,Wishlist

from django.http import HttpResponse,HttpResponseForbidden

from twilio.rest import Client

from django.urls import reverse

from django.conf import settings

from django.contrib.auth.decorators import login_required

import razorpay

decs=[signin_required,never_cache]

from decouple import config

# Create your views here.

key_id=config('key_id')
key_secret=config('key_secret')

TWILIO_ACCOUNT_SID=config('TWILIO_ACCOUNT_SID')
TWILIO_ACCOUNT_SECRET=config('TWILIO_ACCOUNT_SECRET')
TWILIO_PHONENUMBER= config('TWILIO_PHONENUMBER')


def send_otp(user_object):

    user_object.generate_otp()  
    subject = "Verify Your Account ❤️"
    message = f"Your OTP is {user_object.otp}. Use it to verify your account."
    from_email = config('from_email')
    recipient_list = [user_object.email]
    send_mail(subject, message, from_email, recipient_list)

    try:
        account_sid = TWILIO_ACCOUNT_SID
        auth_token = TWILIO_ACCOUNT_SECRET
        twilio_phone = TWILIO_PHONENUMBER  

        client = Client(account_sid, auth_token)


        to_phone = user_object.phone.strip()  
        if not to_phone.startswith("+"):  
            to_phone = "+91" + to_phone  

        message = client.messages.create(
            from_=twilio_phone,
            body=f"Your OTP is {user_object.otp}.",
            to=to_phone
        )
        print(f"SMS sent successfully: {message.sid}")

    except Exception as e:
        print(f"SMS sending failed: {e}")


class SignUpView(View):

    template_name="SignUp.html"

    form_class = SignUpForm

    def get(self,request,*args,**kwargs):

        form_instance = self.form_class()

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self, request, *args, **kwargs):

        form_instance = self.form_class(request.POST)

        if form_instance.is_valid():
            user_object = form_instance.save(commit=False)
            user_object.is_active = False  
            user_object.save()


            send_otp(user_object)

            messages.success(request, "OTP sent to your email & phone. Please verify your account.")
            return redirect("otpverify")  

        return render(request, self.template_name, {"form": form_instance})




class OtpVerifyView(View):

    template_name="otpverify.html"

    form_class=OtpVerifyForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        return render(request,self.template_name,{'form':form_instance})
    
    def post(self, request, *args, **kwargs):

        otp = request.POST.get("otp")

        if not otp:
            messages.error(request, "Please enter the OTP.")
            return render(request, self.template_name)

        print(f"Submitted OTP: {otp}")

        try:

            user_object = User.objects.get(otp=otp)

            user_object.is_active = True
            user_object.is_verified = True
            user_object.otp = None  
            user_object.save()

            messages.success(request, "Your account has been verified. You can now sign in.")
            return redirect("signin")

        except User.DoesNotExist:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, self.template_name)

        
class SignInView(View):

    template_name = "login.html"

    form_class = SignInForm

    def get(self,request,*args,**kwargs):

        form_instance = self.form_class()

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):

        form_instance = self.form_class(request.POST)

        if form_instance.is_valid():

            uname = form_instance.cleaned_data.get("username")

            pwd = form_instance.cleaned_data.get("password")

            user_object = authenticate(request, username=uname,password=pwd)

            if user_object:

                login(request, user_object)

                messages.success(request,"login success")

                # return redirect("index")
                next_url = request.GET.get("next", "index")  # Default redirect to 'index'
                return redirect(next_url)
            else:

                messages.error(request,"invalid username or password")

        return render(request,self.template_name,{"form":form_instance})
    

    
class LogOutView(View):

    def get(self,request,*args,**kwargs):

        logout(request)

        return redirect('signin')
    

class IndexView(View):

    template_name='index.html'

    def get(self,request,*args,**kwargs):

        qs=BeanBag.objects.all()

        return render(request,self.template_name,{'bags':qs})
    

class ProductDetailView(View):

    template_name = 'productdetail.html'

    def get(self, request, *args, **kwargs):
        id = kwargs.get('pk')

        try:
            beanbag = BeanBag.objects.get(id=id)

        except BeanBag.DoesNotExist:

            return HttpResponse("Product not found", status=404)

        variants = BeanBagVariant.objects.filter(beanbag_object=beanbag)

        reviews = beanbag.reviews.all()

        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']

        return render(request, self.template_name, {'product': beanbag,'variants': variants, 'reviews': reviews, 'average_rating': average_rating,})
    

class CategoryView(View):
    
    category_dict = {
        'classic': 'CLASSIC',
        'soccer': 'SOCCER',
        'chairs': 'CHAIRS',
        'refillers': 'REFILLERS',
        'luxury': 'LUXURY'
    }

    def get(self, request, category_name, *args, **kwargs):

        search_query = request.GET.get('search', '')

        if category_name.lower() == "all":
            beanbags = BeanBag.objects.all() 
        else:
            category_code = self.category_dict.get(category_name.lower(), 'CLASSIC')
            beanbags = BeanBag.objects.filter(category=category_code)

        if search_query:
            beanbags = beanbags.filter(title__icontains=search_query) 

        return render(request, 'category.html', {
            'beanbags': beanbags,
            'category': category_name.title(),
            'search_query': search_query
        })



@method_decorator(decs,name="dispatch")
class AddToCartView(View):

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        beanbag_variant_id = request.POST.get("variant")
        beanbag_variant_instance = get_object_or_404(BeanBagVariant, id=beanbag_variant_id)
        
        material_id = request.POST.get("material")
        material_instance = get_object_or_404(Material, id=material_id) if material_id else None

        quantity = int(request.POST.get("quantity", 1))

        if action == "cart":
            existing_item = Cart.objects.filter(
                owner=request.user,
                beanbag_variant_object=beanbag_variant_instance,
                material_object=material_instance,
                is_order_placed=False
            ).first()

            if existing_item:
                existing_item.quantity += quantity  
                existing_item.save()
            else:
                Cart.objects.create(
                    beanbag_variant_object=beanbag_variant_instance,
                    material_object=material_instance,
                    quantity=quantity,
                    owner=request.user
                )
            Wishlist.objects.filter(user=request.user, beanbag_variant=beanbag_variant_instance).delete()

            return redirect("cart-summary")

        elif action == "wishlist":

            existing_item=Wishlist.objects.filter(user=request.user,beanbag_variant=beanbag_variant_instance).exists()

            if not existing_item:

                Wishlist.objects.create(user=request.user,beanbag_variant=beanbag_variant_instance)

            else:

                print("Item Already Exists ")

            return redirect("wishlist")
        
@method_decorator(decs,name="dispatch")
class CartSummaryView(View):
    template_name = 'cart_summary.html'

    def get(self, request, *args, **kwargs):
       
        qs = Cart.objects.filter(owner=request.user, is_order_placed=False)
        
        # Calculate the total cost of all items in the cart
        basket_total = sum([c.item_total() for c in qs])

        return render(request, self.template_name, {'data': qs,'basket_total': basket_total,'cart_item_count': qs.count()})
    
@method_decorator(decs,name="dispatch")
class CartDeleteView(View):

    def post(self, request, *args, **kwargs):
        
        cart_item_id = kwargs.get('pk')

        Cart.objects.filter(id=cart_item_id, owner=request.user).delete()

        return redirect('cart-summary')
    


@method_decorator(decs,name='dispatch')
class WishlistView(View):

    template_name = "wishlist.html"

    def get(self, request, *args, **kwargs):

        print("Logged-in user:", request.user)

        wishlist_items = Wishlist.objects.filter(user=request.user)

        print("Wishlist items in view:", wishlist_items)

        return render(request, self.template_name, {"wishlist_items": wishlist_items})

@method_decorator(decs,name="dispatch")
class RemoveFromWishlistView(View):

    def post(self, request, *args, **kwargs):

        beanbag_variant_id = request.POST.get('variant_id')

        Wishlist.objects.filter(user=request.user, beanbag_variant_id=beanbag_variant_id).delete()

        return redirect('wishlist')


@method_decorator(decs,name="dispatch")
class PlaceOrderView(View):
    template_name = 'place_order.html'
    form_class = OrderForm

    def get(self, request, *args, **kwargs):
        form_instance = self.form_class()
        qs = Cart.objects.filter(owner=request.user, is_order_placed=False)
        basket_total = sum([c.item_total() for c in qs])

        return render(request, self.template_name, {'form': form_instance, 'cartitems': qs, 'total': basket_total})
    
    def post(self, request, *args, **kwargs):
        form_instance = self.form_class(request.POST)
        form_instance.instance.customer = request.user

        if form_instance.is_valid():
            order_object = form_instance.save()

            cart_items = Cart.objects.filter(owner=request.user, is_order_placed=False)
            for item in cart_items:
                OrderItem.objects.create(
                    order_object=order_object,
                    beanbag_variant_object=item.beanbag_variant_object,
                    quantity=item.quantity,
                    price=item.beanbag_variant_object.price
                )
                item.is_order_placed = True
                item.save()

            payment_method = request.POST.get('payment_method')  
            print(f"Payment method: {payment_method}")  

            if payment_method == 'ONLINE':
                print("Rendering payment page") 
                client = razorpay.Client(auth=(key_id, key_secret))
                data = {"amount": order_object.order_total() * 100, "currency": "INR", "receipt": f"order_{order_object.id}"}
                payment = client.order.create(data=data)

                rzp_id = payment.get('id')
                order_object.rzp_order_id = rzp_id
                order_object.save()

                context = {
                    'key_id': key_id,
                    'amount': order_object.order_total(),
                    'order_id': order_object.rzp_order_id
                }
                return render(request, 'payment.html', context)
            
            else:  
                messages.success(request, "Your order has been placed successfully!")
                print("Redirecting to index...")  
                return redirect('cart-summary')  

        print("Form validation failed:", form_instance.errors)
        return render(request, self.template_name, {
            'form': form_instance,
            'cartitems': Cart.objects.filter(owner=request.user, is_order_placed=False),
            'total': sum([c.item_total() for c in Cart.objects.filter(owner=request.user, is_order_placed=False)]),
            'errors': form_instance.errors
        })

@method_decorator(decs,name="dispatch")
class OrderSummaryView(View):

    template_name='order_summary.html'

    def get(self,request,*args,**kwargs):
        
        qs=Order.objects.filter(customer=request.user)

        return render(request,self.template_name,{'orders':qs})
    

    
@method_decorator(decs, name="dispatch")  
class PaymentVerificationView(View):
    def post(self, request, *args, **kwargs):
        client = razorpay.Client(auth=(key_id, key_secret))
        rzp_order_id = request.POST.get('razorpay_order_id')

        print(rzp_order_id, '.....')

        try:

            client.utility.verify_payment_signature(request.POST)

            # Fetch the order and update is_paid
            order = Order.objects.filter(rzp_order_id=rzp_order_id).first()  # ✅ Fetch the actual order
            if order:
                order.is_paid = True
                order.save()

                # Send payment confirmation email
                self.send_payment_email(order)
            else:
                print("Order not found")

        except razorpay.errors.SignatureVerificationError:
            print('Payment Failed')

        return redirect('order-summary')

    def send_payment_email(self, order):

        subject = "Payment Successful - Your Order Confirmation"
        message = f"""
        Hi {order.customer.username},

        Your payment of ₹{order.order_total()} has been received.

        Order ID: {order.id}

        Payment Method: Razorpay

        Your item will receive in 3-4 Business Days 

        Thank you for shopping with us!

        Regards,
        Anughar ks
        Marketing team,BeanBag Store Team
        """
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [order.customer.email],  
            fail_silently=False,
        )
        
@method_decorator(decs,name="dispatch")
class ReviewCreateView(View):
    template_name = "review_form.html"

    def get_has_purchased(self, user, beanbag):
        """Helper method to check if the user has purchased the beanbag."""
        beanbag_variants = BeanBagVariant.objects.filter(beanbag_object=beanbag)
        return OrderItem.objects.filter(order_object__customer=user, beanbag_variant_object__in=beanbag_variants).exists()

    def get(self, request, beanbag_id, *args, **kwargs):
        beanbag = get_object_or_404(BeanBag, id=beanbag_id)

        if not self.get_has_purchased(request.user, beanbag):
            messages.error(request, "❌ You can only review products you have purchased.")
            return redirect(reverse("product-detail", kwargs={"pk": beanbag_id}))  # Redirect instead of just refreshing

        form = ReviewForm()
        return render(request, self.template_name, {"form": form, "beanbag": beanbag})


    def post(self, request, beanbag_id, *args, **kwargs):
        beanbag = get_object_or_404(BeanBag, id=beanbag_id)

        if not self.get_has_purchased(request.user, beanbag):
            messages.error(request, "❌ You can only review products you have purchased.")
            return redirect(reverse("product-detail", kwargs={"pk": beanbag_id}))

        # Prevent duplicate reviews
        if Review.objects.filter(beanbag=beanbag, user=request.user).exists():
            messages.error(request, "❌ You have already reviewed this product.")
            return redirect(reverse("product-detail", kwargs={"pk": beanbag_id}))

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.beanbag = beanbag
            review.user = request.user
            review.save()
            messages.success(request, "✅ Review added successfully!")
            return redirect(reverse("product-detail", kwargs={"pk": beanbag_id}))

        return render(request, self.template_name, {"form": form, "beanbag": beanbag})

@method_decorator(decs,name="dispatch")
class ReviewUpdateView(LoginRequiredMixin, View):
    template_name = "review_edit.html"

    def get(self, request, pk, *args, **kwargs):
        """Handle GET request to show the review edit form"""
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user:
            return HttpResponseForbidden("❌ You are not allowed to edit this review.")

        form = ReviewForm(instance=review)
        return render(request, self.template_name, {"form": form, "review": review})

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request to update the review"""
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user:
            return HttpResponseForbidden("❌ You are not allowed to edit this review.")

        form = ReviewForm(request.POST, instance=review)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Your review has been updated successfully!")
            return redirect(reverse("product-detail", kwargs={"pk": review.beanbag.id}))

        return render(request, self.template_name, {"form": form, "review": review})

@method_decorator(decs,name="dispatch")
class ReviewDeleteView(LoginRequiredMixin, View):


    def post(self, request, pk, *args, **kwargs):
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user:
            return HttpResponseForbidden("❌ You are not allowed to delete this review.")

        review.delete()
        messages.success(request, "✅ Your review has been deleted successfully!")

        return redirect(reverse("product-detail", kwargs={"pk": review.beanbag.id}))
    

@method_decorator(decs,name="dispatch")
class ContactView(View):

    template_name = "contact.html"

    def get(self, request):
        """Handles GET requests and displays the contact page."""
        return render(request, self.template_name)

    def post(self, request):
        """Handles POST requests for contact form submission."""
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if name and email and message:
            # Example: Send an email (Optional)
            send_mail(
                subject=f"New Contact Form Submission from {name}",
                message=f"Message: {message}\n\nFrom: {name} ({email})",
                from_email=config('from_email'),
                recipient_list=config('recipient_list'),  # Set CONTACT_EMAIL in settings
            )

            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact")  # Redirect to contact page after submission
        else:
            messages.error(request, "Please fill out all fields correctly.")

        return render(request, self.template_name)
    
