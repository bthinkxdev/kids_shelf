from .services import CartService


def cart_context(request):
    cart = CartService.get_or_create_cart(request)
    return {
        "cart_count": sum(item.quantity for item in cart.items.all()),
    }

