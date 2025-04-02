from bean_app.models import Cart ,Wishlist # Use CartItem instead of Cart

def cart_context(request):
    cart_item_count = 0  # Default value

    if request.user.is_authenticated:
        cart_item_count = Cart.objects.filter(owner=request.user, is_order_placed=False).count()

    return {'cart_item_count': cart_item_count}



def wishlist_context(request):
    wishlist_count = 0

    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()

    return {'wishlist_count': wishlist_count}