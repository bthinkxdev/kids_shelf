from .services import CartService
from .models import Wishlist
from .services import WishlistService

def cart_context(request):
    cart = CartService.get_or_create_cart(request)
    return {
        "cart_count": cart.items.count(),  
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