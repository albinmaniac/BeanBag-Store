"""
URL configuration for bean_store project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from bean_app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('signup/',views.SignUpView.as_view(),name='signup'),


    path('otp/verify/',views.OtpVerifyView.as_view(),name="otpverify"),

    path('',views.SignInView.as_view(),name='signin'),

    path('accounts/',include('allauth.urls')),

    path('logout/',views.LogOutView.as_view(),name='logout'),



    path('index/',views.IndexView.as_view(),name='index'),

    path('category/<str:category_name>/', views.CategoryView.as_view(), name='category'),


    path('products/<int:pk>/',views.ProductDetailView.as_view(),name='product-detail'),

    path('product/cart/',views.AddToCartView.as_view(),name='add-cart'),



    path('cart/summary/',views.CartSummaryView.as_view(),name='cart-summary'),

    path('cart/delete/<int:pk>/',views.CartDeleteView.as_view(),name='cart-delete'),



    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),

    path('wishlist/remove/', views.RemoveFromWishlistView.as_view(), name='remove-from-wishlist'),


    path('place/order/',views.PlaceOrderView.as_view(),name='place-order'),

    path('order/summary/',views.OrderSummaryView.as_view(),name='order-summary'),


    path('payment/verify/',views.PaymentVerificationView.as_view(),name='payment-verification'),



    path("beanbag/<int:beanbag_id>/review/add/", views.ReviewCreateView.as_view(), name="review-create"),

    path("review/<int:pk>/edit/", views.ReviewUpdateView.as_view(), name="review-edit"),
    
    path("review/<int:pk>/delete/", views.ReviewDeleteView.as_view(), name="review-delete"),


    path("contact/", views.ContactView.as_view(), name="contact"),


    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)