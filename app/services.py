from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from .models import Address, Cart, CartItem, Order, OrderItem, Payment, BookFormat


def send_order_notification_email(order, request=None):
    """Send order notification email to admin/owner when a new order is placed."""
    admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [])
    if not admin_emails:
        print("No admin emails configured for order notifications")
        return False
    
    if request:
        order_url = request.build_absolute_uri(f'/dashboard/orders/{order.order_number}/')
    else:
        site_domain = getattr(settings, 'SITE_DOMAIN', 'https://queenorange.shop')
        order_url = f"{site_domain}/dashboard/orders/{order.order_number}/"

    payment_method = "Cash on Delivery"
    if hasattr(order, 'payment'):
        payment_method = order.payment.get_method_display()
    
    context = {
        'order': order,
        'order_url': order_url,
        'payment_method': payment_method,
        'site_name': 'Golden Elegance',
    }
    
    html_message = render_to_string('admin/order_notification_email.html', context)
    plain_message = render_to_string('admin/order_notification_email.txt', context)
    
    try:
        print(f"Sending order notification email for order {order.order_number}...")
        send_mail(
            subject=f'New Order #{order.order_number} - ₹{order.total}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Order notification email sent successfully to {admin_emails}")
        return True
    except Exception as e:
        print(f"Error sending order notification email: {e}")
        import traceback
        traceback.print_exc()
        return False


class CartError(Exception):
    pass


class StockError(CartError):
    pass


@dataclass
class CartTotals:
    subtotal: object
    shipping: object
    total: object


class CartService:
    @staticmethod
    def _ensure_session_key(request):
        if not request.session.session_key:
            request.session.save()
        return request.session.session_key

    @classmethod
    def get_or_create_cart(cls, request):
        user = request.user if request.user.is_authenticated else None
        if user:
            cart, _ = Cart.objects.get_or_create(user=user, status=Cart.Status.ACTIVE)
            return cart
        session_key = cls._ensure_session_key(request)
        cart, _ = Cart.objects.get_or_create(session_key=session_key, status=Cart.Status.ACTIVE)
        return cart

    @classmethod
    def merge_carts(cls, user, session_key):
        if not user or not session_key:
            return
        try:
            session_cart = Cart.objects.get(session_key=session_key, status=Cart.Status.ACTIVE)
        except Cart.DoesNotExist:
            return
        user_cart, _ = Cart.objects.get_or_create(user=user, status=Cart.Status.ACTIVE)
        for item in session_cart.items.all():
            cls.add_item(user_cart, item.variant, item.quantity)
        session_cart.status = Cart.Status.ABANDONED
        session_cart.save(update_fields=["status"])

    @staticmethod
    def compute_totals(cart):
        subtotal = sum(item.line_total for item in cart.items.select_related("product"))
        shipping_threshold = getattr(settings, "FREE_SHIPPING_THRESHOLD", 999)
        shipping_fee = getattr(settings, "FLAT_SHIPPING_FEE", 50)
        shipping = 0 if subtotal >= shipping_threshold else shipping_fee
        total = subtotal + shipping
        return CartTotals(subtotal=subtotal, shipping=shipping, total=total)

    @staticmethod
    def add_item(cart, variant, quantity):
        if not variant.is_active or variant.stock_quantity <= 0:
            raise StockError("This item is out of stock.")
        max_qty = getattr(settings, "MAX_CART_QTY", 10)
        quantity = max(1, min(quantity, max_qty))
        if quantity > variant.stock_quantity:
            raise StockError("Requested quantity exceeds available stock.")
        item = CartItem.objects.filter(cart=cart, variant=variant).first()
        if item:
            new_quantity = min(item.quantity + quantity, max_qty)
            if new_quantity > variant.stock_quantity:
                raise StockError("Requested quantity exceeds available stock.")
            item.quantity = new_quantity
            item.unit_price = variant.product.price
            item.save(update_fields=["quantity", "unit_price", "updated_at"])
            return item
        return CartItem.objects.create(
            cart=cart,
            variant=variant,
            product=variant.product,
            quantity=quantity,
            unit_price=variant.product.price,
        )

    @staticmethod
    def update_item(item, quantity):
        if quantity <= 0:
            item.delete()
            return
        max_qty = getattr(settings, "MAX_CART_QTY", 10)
        quantity = min(quantity, max_qty)
        if quantity > item.variant.stock_quantity:
            raise StockError("Requested quantity exceeds available stock.")
        item.quantity = quantity
        item.unit_price = item.variant.product.price
        item.save(update_fields=["quantity", "unit_price", "updated_at"])


class OrderService:
    @staticmethod
    def _generate_order_number():
        while True:
            order_number = f"QO{get_random_string(8).upper()}"
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number

    @classmethod
    @transaction.atomic
    def create_order(cls, cart, form_data, user=None):
        items = (
            cart.items.select_related("variant", "product")
            .select_for_update(of=("self", "variant"))
            .all()
        )
        if not items:
            raise CartError("Cart is empty.")

        for item in items:
            if item.quantity > item.variant.stock_quantity:
                raise StockError(f"{item.product.name} is out of stock.")

        # Handle address - either use existing or create snapshot
        selected_address_id = form_data.get('selected_address')
        use_new_address = form_data.get('use_new_address', False)
        
        if selected_address_id and not use_new_address:
            # Create snapshot of existing address
            try:
                existing_address = Address.objects.get(pk=selected_address_id, user=user, is_snapshot=False)
                address = Address.objects.create(
                    user=user,
                    full_name=existing_address.full_name,
                    phone=existing_address.phone,
                    email=existing_address.email,
                    address_line=existing_address.address_line,
                    city=existing_address.city,
                    state=existing_address.state,
                    pincode=existing_address.pincode,
                    is_snapshot=True,
                )
            except Address.DoesNotExist:
                raise CartError("Selected address not found.")
        else:
            # Create new snapshot address
            address = Address.objects.create(
                user=cart.user if cart.user else None,
                full_name=form_data["full_name"],
                phone=form_data["phone"],
                email=form_data.get("email", ""),
                address_line=form_data["address_line"],
                city=form_data["city"],
                state=form_data["state"],
                pincode=form_data["pincode"],
                is_snapshot=True,
            )

        totals = CartService.compute_totals(cart)
        order_number = cls._generate_order_number()
        order = Order.objects.create(
            user=cart.user if cart.user else None,
            order_number=order_number,
            subtotal=totals.subtotal,
            shipping=totals.shipping,
            total=totals.total,
            address=address,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                product_name=item.product.name,
                variant_snapshot=item.variant.get_format_type_display(),
                unit_price=item.unit_price,
                quantity=item.quantity,
            )
            BookFormat.objects.filter(pk=item.variant_id).update(
                stock_quantity=F("stock_quantity") - item.quantity
            )

        Payment.objects.create(
            order=order,
            method=form_data.get("payment", Payment.Method.COD),
            amount=totals.total,
        )

        cart.status = Cart.Status.ORDERED
        cart.save(update_fields=["status"])
        cart.items.all().delete()

        # Send order notification email to admin/owner
        send_order_notification_email(order)

        return order

