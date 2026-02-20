from .services import CartService
from .models import Wishlist
from .services import WishlistService

# URL names where the bottom cart popup should be hidden
HIDE_CART_POPUP_URL_NAMES = frozenset({
    "cart", "checkout", "order_create", "order_success",
    "razorpay_payment", "razorpay_verify",
})


def cart_context(request):
    cart = CartService.get_or_create_cart(request)
    url_name = None
    if getattr(request, "resolver_match", None):
        url_name = getattr(request.resolver_match, "url_name", None)
    hide_cart_popup = url_name in HIDE_CART_POPUP_URL_NAMES
    return {
        "cart_count": cart.items.count(),
        "hide_cart_popup": hide_cart_popup,
    }

def wishlist_count(request):
    try:
        if request.user.is_authenticated:
            count = Wishlist.objects.filter(user=request.user).count()
        else:
            count = len(WishlistService.get_guest_ids(request.session))
        return {'wishlist_count': count}
    except Exception:
        return {'wishlist_count': 0}