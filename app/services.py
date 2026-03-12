from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
import logging

from .models import Address, Cart, CartItem, Order, OrderItem, Payment, BookFormat, Wishlist, Product

# Session key for guest wishlist (product IDs)
WISHLIST_SESSION_KEY = "wishlist"


logger_services = logging.getLogger(__name__)


def send_order_notification_email(order, request=None):
    """Send order notification email to admin/owner when a new order is placed."""
    admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [])
    if not admin_emails:
        logger_services.warning("No admin emails configured for order notifications")
        return False

    if request:
        order_url = request.build_absolute_uri(f'/dashboard/orders/{order.order_number}/')
    else:
        site_domain = getattr(settings, 'SITE_DOMAIN', 'https://kidsshelf.in')
        order_url = f"{site_domain}/dashboard/orders/{order.order_number}/"

    payment_method = "Online Payment"
    if hasattr(order, 'payment'):
        payment_method = order.payment.get_method_display()

    context = {
        'order': order,
        'order_url': order_url,
        'payment_method': payment_method,
        'site_name': 'Kids Shelf',
    }

    html_message = render_to_string('admin/order_notification_email.html', context)
    plain_message = render_to_string('admin/order_notification_email.txt', context)

    try:
        logger_services.info("Sending order notification email for order %s", order.order_number)
        send_mail(
            subject=f'New Order #{order.order_number} - ₹{order.total}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
        logger_services.info("Order notification email sent to %s", admin_emails)
        return True
    except Exception as e:
        logger_services.exception("Error sending order notification email: %s", e)
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
        """✅ ROBUSTNESS: Ensure session exists"""
        if not request.session.session_key:
            request.session.save()
        return request.session.session_key

    @classmethod
    def get_or_create_cart(cls, request):
        """
        Get or create cart: by user if authenticated, by session_key if guest.
        Guest: only use carts with user=None to avoid duplicate ACTIVE carts per session.
        """
        try:
            user = request.user if request.user.is_authenticated else None
            if user:
                cart, _ = Cart.objects.get_or_create(user=user, status=Cart.Status.ACTIVE)
                return cart
            session_key = cls._ensure_session_key(request)
            cart = Cart.objects.filter(
                session_key=session_key, status=Cart.Status.ACTIVE, user__isnull=True
            ).first()
            if not cart:
                cart = Cart.objects.create(session_key=session_key, status=Cart.Status.ACTIVE)
            return cart
        except Exception as e:
            raise CartError(f"Failed to get cart: {str(e)}")

    @classmethod
    def merge_carts(cls, user, session_key):
        """Merge guest cart (session) into user cart; then mark session cart abandoned."""
        if not user or not session_key:
            return
        try:
            session_cart = Cart.objects.get(
                session_key=session_key, status=Cart.Status.ACTIVE, user__isnull=True
            )
        except Cart.DoesNotExist:
            return
        
        try:
            user_cart, _ = Cart.objects.get_or_create(user=user, status=Cart.Status.ACTIVE)
            
            for item in session_cart.items.select_related('product', 'variant').all():
                # ✅ ROBUSTNESS: Skip items with missing variant
                if not item.variant:
                    continue
                
                # ✅ ROBUSTNESS: Skip if variant no longer available
                if not item.variant.is_available():
                    continue
                
                try:
                    cls.add_item(user_cart, item.variant, item.quantity)
                except (StockError, CartError):
                    # ✅ ROBUSTNESS: Continue merging even if one item fails
                    continue
            
            session_cart.status = Cart.Status.ABANDONED
            session_cart.save(update_fields=["status"])
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Cart merge failed: {str(e)}")

    @staticmethod
    def compute_totals(cart):
        """✅ ROBUSTNESS: Calculate totals with error handling"""
        try:
            subtotal = sum(
                item.line_total
                for item in cart.items.select_related("product").all()
            )
            shipping_threshold = getattr(settings, "FREE_SHIPPING_THRESHOLD", 999)
            shipping_fee = getattr(settings, "FLAT_SHIPPING_FEE", 50)
            shipping = 0 if subtotal >= shipping_threshold else shipping_fee
            total = subtotal + shipping
            return CartTotals(subtotal=subtotal, shipping=shipping, total=total)
        except Exception as e:
            logging.getLogger(__name__).error(f"compute_totals failed: {e}", exc_info=True)
            return CartTotals(subtotal=0, shipping=0, total=0)

    @staticmethod
    def add_item(cart, variant, quantity):
        """
        ✅ ROBUSTNESS: Add item to cart with comprehensive validation.
        Raises StockError if item unavailable.
        Raises CartError for other failures.
        """
        if not variant:
            raise CartError("Book format is required.")
        if not variant.is_available():
            raise StockError("This format is out of stock or no longer available.")
        max_qty = getattr(settings, "MAX_CART_QTY", 10)
        try:
            quantity = int(quantity)
            quantity = max(1, min(quantity, max_qty))
        except (TypeError, ValueError):
            raise CartError("Invalid quantity.")
        if not variant.can_fulfill_quantity(quantity):
            raise StockError(
                f"Only {variant.stock_quantity} available. "
                f"You requested {quantity}."
            )
        try:
            product = variant.product
            if not product.is_active:
                raise CartError("This book is no longer available.")
            item = CartItem.objects.filter(cart=cart, variant=variant).first()
            if item:
                new_quantity = min(item.quantity + quantity, max_qty)
                if not variant.can_fulfill_quantity(new_quantity):
                    raise StockError(
                        f"Only {variant.stock_quantity} available. "
                        f"You already have {item.quantity} in cart."
                    )
                item.quantity = new_quantity
                item.unit_price = product.price
                item.save(update_fields=["quantity", "unit_price", "updated_at"])
                return item
            return CartItem.objects.create(
                cart=cart,
                variant=variant,
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )
        except StockError:
            raise
        except CartError:
            raise
        except Exception as e:
            raise CartError(f"Failed to add to cart: {str(e)}")

    @staticmethod
    def update_item(item, quantity):
        """✅ ROBUSTNESS: Update cart item with validation"""
        try:
            if quantity <= 0:
                item.delete()
                return
            if not item.variant:
                raise CartError("Invalid cart item.")
            if not item.variant.is_available():
                raise StockError("This format is no longer available.")
            max_qty = getattr(settings, "MAX_CART_QTY", 10)
            quantity = min(quantity, max_qty)
            if not item.variant.can_fulfill_quantity(quantity):
                raise StockError(
                    f"Only {item.variant.stock_quantity} available. "
                    f"You requested {quantity}."
                )
            item.quantity = quantity
            item.unit_price = item.product.price
            item.save(update_fields=["quantity", "unit_price", "updated_at"])
        except StockError:
            raise
        except CartError:
            raise
        except Exception as e:
            raise CartError(f"Failed to update cart: {str(e)}")

    @staticmethod
    def validate_cart(cart):
        """
        ✅ ROBUSTNESS: Validate all items in cart before checkout.
        Removes invalid items, updates quantities for low stock.
        Returns dict with 'valid' bool and 'errors' list.
        """
        errors = []
        items_to_remove = []
        items_to_update = []
        for item in cart.items.select_related('product', 'variant').all():
            if not item.variant:
                items_to_remove.append(item)
                errors.append(f"{item.product.name}: Format missing")
                continue
            if not item.product.is_active:
                items_to_remove.append(item)
                errors.append(f"{item.product.name}: No longer available")
                continue
            if not item.variant.is_available():
                items_to_remove.append(item)
                errors.append(f"{item.product.name} ({item.get_format_display()}): Out of stock")
                continue
            if item.variant.stock_quantity < item.quantity:
                if item.variant.stock_quantity > 0:
                    items_to_update.append((item, item.variant.stock_quantity))
                    errors.append(
                        f"{item.product.name} ({item.get_format_display()}): "
                        f"Reduced to {item.variant.stock_quantity} (low stock)"
                    )
                else:
                    items_to_remove.append(item)
                    errors.append(f"{item.product.name} ({item.get_format_display()}): Out of stock")
        for item in items_to_remove:
            try:
                item.delete()
            except Exception:
                pass
        for item, new_qty in items_to_update:
            try:
                item.quantity = new_qty
                item.save(update_fields=['quantity'])
            except Exception:
                pass
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'removed_count': len(items_to_remove),
            'updated_count': len(items_to_update)
        }


class WishlistService:
    """Session-based wishlist for guests; merge into DB on login."""
    WISHLIST_MAX_ITEMS = 50

    @staticmethod
    def get_guest_ids(session):
        """Return list of product IDs from session (max WISHLIST_MAX_ITEMS, no duplicates)."""
        ids = session.get(WISHLIST_SESSION_KEY) or []
        if not isinstance(ids, list):
            ids = []
        seen = set()
        out = []
        for x in ids:
            try:
                pk = int(x)
                if pk not in seen and len(out) < WishlistService.WISHLIST_MAX_ITEMS:
                    seen.add(pk)
                    out.append(pk)
            except (TypeError, ValueError):
                continue
        return out

    @staticmethod
    def set_guest_ids(session, ids):
        """Store product IDs in session (cap at WISHLIST_MAX_ITEMS)."""
        ids = [int(x) for x in ids[:WishlistService.WISHLIST_MAX_ITEMS] if x is not None]
        session[WISHLIST_SESSION_KEY] = list(dict.fromkeys(ids))
        session.modified = True

    @classmethod
    def merge_into_user(cls, request, user):
        """Merge session wishlist into user's DB wishlist; clear session wishlist."""
        ids = cls.get_guest_ids(request.session)
        if not ids:
            return
        valid_ids = set(
            Product.objects.filter(pk__in=ids, is_active=True).values_list("pk", flat=True)
        )
        for product_id in valid_ids:
            try:
                Wishlist.objects.get_or_create(user=user, product_id=product_id)
            except Exception:
                continue
        request.session.pop(WISHLIST_SESSION_KEY, None)
        request.session.modified = True


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
        if cart.status != Cart.Status.ACTIVE:
            raise CartError("This cart has already been used to place an order.")
        items = list(
            cart.items.select_related("variant", "product")
            .select_for_update(of=("self",))
            .all()
        )
        if not items:
            raise CartError("Cart is empty.")

        # Lock variant rows to prevent concurrent stock deduction (race condition)
        variant_ids = [item.variant_id for item in items if item.variant_id]
        if variant_ids:
            BookFormat.objects.select_for_update().filter(pk__in=variant_ids).exists()

        for item in items:
            # Check variant exists
            if not item.variant:
                raise CartError(f"{item.product.name}: Format missing. Please remove and re-add.")
            
            # Check product is active
            if not item.product.is_active:
                raise CartError(f"{item.product.name}: No longer available.")
            
            # Check variant is available
            if not item.variant.is_available():
                raise StockError(f"{item.product.name} ({item.get_format_display()}): Out of stock.")
            
            # Check quantity
            if not item.variant.can_fulfill_quantity(item.quantity):
                available = item.variant.stock_quantity
                raise StockError(
                    f"{item.product.name} ({item.get_format_display()}): "
                    f"Only {available} available, you have {item.quantity} in cart."
                )

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
            method=form_data.get("payment", Payment.Method.RAZORPAY),
            amount=totals.total,
        )

        cart.status = Cart.Status.ORDERED
        cart.save(update_fields=["status"])
        cart.items.all().delete()

        # Send order notification email to admin/owner
        send_order_notification_email(order)

        return order

