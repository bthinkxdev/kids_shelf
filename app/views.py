from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.utils import timezone

import json
import razorpay
import hmac
import hashlib

from .auth_decorators import LoginRequiredForActionMixin
from .forms import CartAddForm, CartUpdateForm, CheckoutForm, ContactForm, NewsletterForm, ReviewForm
from .models import CartItem, Category, Order, OrderItem, Product, ProductImage, BookFormat, Payment, AgeGroup, Review, Wishlist
from .services import CartError, CartService, OrderService, StockError, WishlistService

from django.db import IntegrityError, transaction
from django.db.models import Count
import logging
logger = logging.getLogger(__name__)


class ProductListView(ListView):
    template_name = "category.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        qs = Product.objects.active().select_related("category")
        
        category = self.request.GET.get("category")
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        format_type = self.request.GET.get("format_type")
        query = self.request.GET.get("q")
        age_group_slugs = self.request.GET.getlist("age_group")    

        if category and category != "all":
            qs = qs.filter(category__slug=category)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if format_type:
            qs = qs.filter(formats__format_type=format_type, formats__is_active=True, formats__stock_quantity__gt=0)
        if age_group_slugs:
            qs = qs.filter(age_groups__slug__in=age_group_slugs, age_groups__is_active=True)
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
            )
        
        return qs.distinct().prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        context["page_title"] = "Shop All Products"
        context["active_page"] = "collection"
        category_slug = self.request.GET.get("category")
        if category_slug and category_slug != "all":
            category = Category.objects.filter(slug=category_slug).first()
            if category:
                context["page_title"] = category.name
        context["filters"] = {
            "category": self.request.GET.get("category", "all"),
            "min_price": self.request.GET.get("min_price", ""),
            "max_price": self.request.GET.get("max_price", ""),
            "format_type": self.request.GET.get("format_type", ""),
            "q": self.request.GET.get("q", ""),
        }
        context["format_options"] = [
            ("hardcover", "Hardcover"),
            ("paperback", "Paperback"),
            ("ebook", "E-Book"),
            ("audiobook", "Audiobook"),
        ]
        # Add age groups for filter
        context["age_groups"] = AgeGroup.objects.filter(is_active=True).order_by('display_order')

        # Track selected age groups for UI state
        context["selected_age_groups"] = self.request.GET.getlist("age_group")
        return context


class HomeView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        age_groups_qs = AgeGroup.objects.filter(is_active=True).order_by('display_order')
        context["age_groups"] = [
            {
                'value': ag.slug,
                'label': ag.name,
                'emoji': ag.emoji or '📚'  
            }
            for ag in age_groups_qs
        ]
        format_qs = BookFormat.objects.filter(is_active=True, stock_quantity__gt=0).order_by("id")
        image_qs = ProductImage.objects.order_by("-is_primary", "id")
        context["featured_products"] = (
            Product.objects.active()
            .filter(is_featured=True)
            .select_related("category")
            .prefetch_related(
                Prefetch("images", queryset=image_qs),
                Prefetch("formats", queryset=format_qs),
                Prefetch("age_groups", queryset=AgeGroup.objects.filter(is_active=True).order_by('display_order')),    
            )[:8]
        )
        context["bestseller_products"] = (
            Product.objects.active()
            .filter(is_bestseller=True)
            .select_related("category")
            .prefetch_related(
                Prefetch("images", queryset=image_qs),
                Prefetch("formats", queryset=format_qs)
            )[:8]
        )
        context["active_page"] = "home"
        return context


class ProductDetailView(DetailView):
    template_name = "product.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = Product.objects.prefetch_related("formats")
        if self.request.user.is_staff:
            return qs
        return qs.active()
    
    def get(self, request, *args, **kwargs):
        from django.http import Http404
        
        try:
            self.object = self.get_object()
        except Http404:
            messages.warning(request, "This product is no longer available.")
            return redirect('store:product_list')
        
        # If customer tries to view inactive product
        if not self.object.is_active and not request.user.is_staff:
            messages.warning(request, "This product is currently unavailable.")
            return redirect('store:product_list')
        
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        
        # Get ALL active formats (don't filter by stock here)
        all_formats = product.formats.filter(is_active=True)
        context["formats"] = list(all_formats)
        
        # Check if any format has stock
        context["has_stock"] = all_formats.filter(stock_quantity__gt=0).exists()
        
        context["related_products"] = (
            Product.objects.active()
            .filter(category=product.category)
            .exclude(pk=product.pk)
            .select_related("category")[:4]
        )
        context["add_form"] = CartAddForm(initial={"product_id": product.id, "quantity": 1})
        context["active_page"] = "collection"
        if self.request.user.is_authenticated:
            context["in_wishlist"] = Wishlist.objects.filter(
                user=self.request.user, product=product
            ).exists()
        else:
            context["in_wishlist"] = product.pk in WishlistService.get_guest_ids(
                self.request.session
            )

        # ----- Ratings & Reviews -----
        reviews_qs = (
            Review.objects.filter(
                product=product,
                is_approved=True,
                is_deleted=False,
            )
            .select_related("user", "order")
            .order_by("-created_at")
        )

        # Star breakdown (5★ down to 1★)
        breakdown_raw = reviews_qs.values("rating").annotate(count=Count("id"))
        rating_breakdown = {i: 0 for i in range(5, 0, -1)}
        for row in breakdown_raw:
            r = int(row["rating"])
            if 1 <= r <= 5:
                rating_breakdown[r] = row["count"]

        breakdown_rows = []
        total = product.total_reviews or 0
        for star in range(5, 0, -1):
            count = rating_breakdown.get(star, 0)
            percent = int((count / total) * 100) if total else 0
            breakdown_rows.append({
                "star": star,
                "count": count,
                "percent": percent,
            })

        # Can current user write a review?
        can_review = False
        user_review = None
        if self.request.user.is_authenticated:
            user_review = Review.objects.filter(
                product=product,
                user=self.request.user,
            ).first()
            if not user_review:
                has_delivered_order = OrderItem.objects.filter(
                    order__user=self.request.user,
                    order__status=Order.Status.DELIVERED,
                    product=product,
                ).exists()
                can_review = has_delivered_order

        context["reviews"] = list(reviews_qs)
        context["rating_breakdown"] = rating_breakdown
        context["rating_breakdown_rows"] = breakdown_rows
        context["can_review"] = can_review
        context["user_review"] = user_review
        context["review_form"] = ReviewForm()

        return context

class CartView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = CartService.get_or_create_cart(self.request)
        
        inactive_items = cart.items.filter(product__is_active=False)
        if inactive_items.exists():
            count = inactive_items.count()
            inactive_items.delete()
            messages.warning(
                self.request, 
                f"{count} unavailable item(s) removed from your cart."
            )
        
        items = cart.items.select_related("product", "variant").prefetch_related("product__images").all()
        totals = CartService.compute_totals(cart)
        
        context.update({
            "cart": cart,
            "items": items,
            "totals": totals,
            "update_form": CartUpdateForm(),
            "active_page": "cart",
        })
        return context


class AddToCartView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        form = CartAddForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid cart data.")
            if is_ajax:
                return JsonResponse({"success": False, "error": "Invalid cart data."}, status=400)
            product_id = request.POST.get("product_id")
            if product_id and Product.objects.filter(pk=product_id).exists():
                product = Product.objects.get(pk=product_id)
                return redirect("store:product_detail", slug=product.slug)
            return redirect("store:cart")
        data = form.cleaned_data
        product = get_object_or_404(Product, pk=data["product_id"])
        book_format = BookFormat.objects.filter(
            product=product,
            format_type=data["format_type"],
            is_active=True,
        ).first()
        if not book_format:
            messages.error(request, "Selected format is unavailable.")
            if is_ajax:
                return JsonResponse({"success": False, "error": "Selected variant is unavailable."}, status=400)
            return redirect("store:product_detail", slug=product.slug)
        cart = CartService.get_or_create_cart(request)
        try:
            CartService.add_item(cart, book_format, data["quantity"])
        except (StockError, CartError) as exc:
            messages.error(request, str(exc))
            if is_ajax:
                return JsonResponse({"success": False, "error": str(exc)}, status=400)
        else:
            messages.success(request, "Added to cart.")
            if is_ajax:
                cart_count = cart.items.count()
                return JsonResponse({"success": True, "cart_count": cart_count})
        action = request.POST.get("action", "add")
        if action == "buy":
            return redirect("store:checkout")
        if action == "whatsapp":
            return redirect(f"{reverse_lazy('store:checkout')}?payment=whatsapp")
        return redirect("store:cart")


class UpdateCartItemView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        form = CartUpdateForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid update.")
            return redirect("store:cart")
        cart = CartService.get_or_create_cart(request)
        item = get_object_or_404(CartItem, pk=form.cleaned_data["item_id"], cart=cart)
        try:
            CartService.update_item(item, form.cleaned_data["quantity"])
        except StockError as exc:
            messages.error(request, str(exc))
        return redirect("store:cart")


class RemoveCartItemView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        cart = CartService.get_or_create_cart(request)
        item = get_object_or_404(CartItem, pk=kwargs.get("item_id"), cart=cart)
        item.delete()
        messages.success(request, "Item removed.")
        return redirect("store:cart")


class CheckoutView(TemplateView):
    template_name = "checkout.html"

    def dispatch(self, request, *args, **kwargs):
        cart = CartService.get_or_create_cart(request)
        if not cart.items.exists():
            messages.info(request, "Your cart is empty.")
            return redirect("store:cart")
        inactive_items = cart.items.filter(product__is_active=False)
        if inactive_items.exists():
            inactive_items.delete()
            messages.error(
                request,
                "Some items are no longer available and have been removed. Please review your cart."
            )
            return redirect("store:cart")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = CartService.get_or_create_cart(self.request)
        totals = CartService.compute_totals(cart)
        addresses = []
        default_address = None
        if self.request.user.is_authenticated:
            from .models import Address
            addresses = list(
                Address.objects.filter(
                    user=self.request.user,
                    is_snapshot=False
                ).order_by('-is_default', '-created_at')
            )
            default_address = next((a for a in addresses if a.is_default), addresses[0] if addresses else None)
        payment_method = self.request.GET.get("payment")
        if payment_method not in {"cod", "whatsapp"}:
            payment_method = None
        initial = {"payment": payment_method} if payment_method else {}
        if default_address:
            initial["selected_address"] = default_address.id
        context.update({
            "cart": cart,
            "items": cart.items.select_related("product", "variant").prefetch_related("product__images"),
            "totals": totals,
            "form": CheckoutForm(initial=initial, user=self.request.user if self.request.user.is_authenticated else None),
            "addresses": addresses,
            "default_address": default_address,
            "active_page": "cart",
        })
        return context


class OrderCreateView(FormView):
    form_class = CheckoutForm
    template_name = "checkout.html"

    def dispatch(self, request, *args, **kwargs):
        cart = CartService.get_or_create_cart(request)
        if not cart.items.exists():
            messages.info(request, "Your cart is empty.")
            return redirect("store:cart")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user if self.request.user.is_authenticated else None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = CartService.get_or_create_cart(self.request)
        totals = CartService.compute_totals(cart)
        addresses = []
        default_address = None
        if self.request.user.is_authenticated:
            from .models import Address
            addresses = list(
                Address.objects.filter(
                    user=self.request.user,
                    is_snapshot=False
                ).order_by('-is_default', '-created_at')
            )
            default_address = next((a for a in addresses if a.is_default), addresses[0] if addresses else None)
        context.update({
            "cart": cart,
            "items": cart.items.select_related("product", "variant").prefetch_related("product__images"),
            "totals": totals,
            "addresses": addresses,
            "default_address": default_address,
            "active_page": "cart",
        })
        return context

    def form_valid(self, form):
        cart = CartService.get_or_create_cart(self.request)
        user = self.request.user if self.request.user.is_authenticated else None
        try:
            order = OrderService.create_order(cart, form.cleaned_data, user)
        except (CartError, StockError) as exc:
            messages.error(self.request, str(exc))
            return redirect("store:checkout")
        self.request.session["last_order_number"] = order.order_number
        payment_method = form.cleaned_data.get("payment")
        if payment_method == "razorpay":
            return redirect("store:razorpay_payment", order_number=order.order_number)
        if payment_method == "whatsapp":
            messages.info(self.request, "We will contact you on WhatsApp to confirm your order.")
        return redirect("store:order_success", order_number=order.order_number)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors in the form.")
        return self.render_to_response(self.get_context_data(form=form))


class OrderSuccessView(DetailView):
    template_name = "success.html"
    context_object_name = "order"
    slug_url_kwarg = "order_number"
    slug_field = "order_number"

    def get_queryset(self):
        return Order.objects.select_related("address", "payment").prefetch_related("items")

    def dispatch(self, request, *args, **kwargs):
        order_number = kwargs.get("order_number")
        order = get_object_or_404(Order, order_number=order_number)
        if request.user.is_authenticated:
            if order.user and order.user != request.user:
                return HttpResponseForbidden()
        else:
            if request.session.get("last_order_number") != order_number:
                return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "orders"
        return context


class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = "orders.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("address", "payment")
            .prefetch_related("items")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "orders"
        return context


class ContactView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("store:contact")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Thanks for reaching out! We will respond soon.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contact"
        return context


class StaticPageView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.extra_context and "active_page" in self.extra_context:
            context["active_page"] = self.extra_context["active_page"]
        return context


class NewsletterSubscribeView(FormView):
    form_class = NewsletterForm
    success_url = reverse_lazy("store:home")

    def get_success_url(self):
        return self.request.META.get("HTTP_REFERER", str(self.success_url))

    def form_valid(self, form):
        email = form.cleaned_data["email"].lower()
        try:
            subscription, created = form._meta.model.objects.get_or_create(email=email)
        except IntegrityError:
            subscription = form._meta.model.objects.filter(email=email).first()
            created = False
            if not subscription:
                messages.error(self.request, "Could not complete subscription. Please try again.")
                return redirect(self.get_success_url())
        if not created and not subscription.is_active:
            subscription.is_active = True
            subscription.save(update_fields=["is_active"])
        messages.success(self.request, "Thanks for subscribing!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please enter a valid email.")
        return redirect(self.get_success_url())

def _can_access_order(request, order):
    """Allow access if order belongs to user or guest session matches."""
    if order.user is None:
        return request.session.get("last_order_number") == order.order_number
    return request.user.is_authenticated and order.user == request.user


class RazorpayPaymentView(View):
    """Handle Razorpay payment initialization. Supports guest (session last_order_number)."""

    def post(self, request, *args, **kwargs):
        try:
            order_number = request.POST.get('order_number')
            if not order_number or not str(order_number).strip():
                return JsonResponse({'status': 'error', 'message': 'Order number required'}, status=400)
            order_number = str(order_number).strip()
            logger.info("POST request for order: %s", order_number)
            order = Order.objects.select_related('address', 'user').get(order_number=order_number)
            if not _can_access_order(request, order):
                logger.warning("Unauthorized access attempt for order %s", order_number)
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'method': Payment.Method.RAZORPAY,
                    'amount': order.total,
                    'status': Payment.Status.PENDING
                }
            )
            client = razorpay.Client(auth=(settings.RZP_CLIENT_ID, settings.RZP_CLIENT_SECRET))
            razorpay_order = client.order.create({
                'amount': int(order.total * 100),
                'currency': 'INR',
                'payment_capture': 1
            })
            payment.razorpay_order_id = razorpay_order['id']
            payment.save(update_fields=['razorpay_order_id'])
            customer_email = order.address.email or (getattr(request.user, 'email', '') or '')
            return JsonResponse({
                'status': 'success',
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': settings.RZP_CLIENT_ID,
                'amount': int(order.total * 100),
                'order_number': order.order_number,
                'customer_name': order.address.full_name,
                'customer_email': customer_email,
                'customer_phone': order.address.phone,
            })
        except Order.DoesNotExist:
            logger.error("Order not found: %s", order_number or "(missing)")
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
        except Exception as e:
            logger.error("Payment initialization error: %s", e, exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def get(self, request, *args, **kwargs):
        try:
            order_number = kwargs.get('order_number')
            order = Order.objects.select_related('address', 'user').get(order_number=order_number)
            if not _can_access_order(request, order):
                return HttpResponseForbidden()
            context = {'order': order, 'razorpay_key_id': settings.RZP_CLIENT_ID}
            return self.render_to_response(context)
        except Order.DoesNotExist:
            return redirect('store:checkout')

    def render_to_response(self, context):
        from django.shortcuts import render
        return render(self.request, 'razorpay_payment.html', context)



class RazorpayPaymentVerifyView(View):
    """Verify Razorpay payment signature. Works for guest and authenticated (no user check)."""

    def post(self, request, *args, **kwargs):
        try:
            if not request.body:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Request body required',
                }, status=400)
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON',
                }, status=400)
            razorpay_order_id = data.get('razorpay_order_id') or ''
            razorpay_payment_id = data.get('razorpay_payment_id') or ''
            razorpay_signature = data.get('razorpay_signature') or ''
            if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing payment verification data',
                }, status=400)
            logger.info(
                "Payment verification attempt - Order: %s, Payment: %s",
                razorpay_order_id, razorpay_payment_id
            )
            payment = Payment.objects.select_related('order').get(
                razorpay_order_id=razorpay_order_id
            )
            signature_data = f"{razorpay_order_id}|{razorpay_payment_id}"
            signature_check = hmac.new(
                settings.RZP_CLIENT_SECRET.encode(),
                signature_data.encode(),
                hashlib.sha256
            ).hexdigest()
            if signature_check == razorpay_signature:
                if payment.status != Payment.Status.PAID:
                    payment.razorpay_payment_id = razorpay_payment_id
                    payment.razorpay_signature = razorpay_signature
                    payment.status = Payment.Status.PAID
                    payment.processed_at = timezone.now()
                    payment.save(update_fields=[
                        'status', 'processed_at', 'razorpay_payment_id', 'razorpay_signature'
                    ])
                    logger.info(
                        "Payment successful - Order: %s, Payment: %s",
                        payment.order.order_number, razorpay_payment_id
                    )
                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment verified successfully',
                    'order_number': payment.order.order_number
                })
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=['status'])
            logger.warning("Signature mismatch for order %s", razorpay_order_id)
            return JsonResponse({
                'status': 'error',
                'message': 'Payment signature verification failed'
            }, status=400)
        except Payment.DoesNotExist:
            logger.error("Payment record not found for order: %s", razorpay_order_id)
            return JsonResponse({
                'status': 'error',
                'message': 'Payment record not found'
            }, status=404)
        except Exception as e:
            logger.error("Payment verification error: %s", e, exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f'Payment verification error: {str(e)}'
            }, status=500)
        
class ProductReviewCreateView(LoginRequiredForActionMixin, View):
    """
    POST endpoint to create a product review from a verified buyer.
    Rules:
    - Must be logged in.
    - Must have at least one delivered order for this product.
    - One review per (product, user).
    - Rating 1-5.
    """

    http_method_names = ["post"]

    def post(self, request, product_id: int, *args, **kwargs):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not request.user.is_authenticated:
            login_url = f"{reverse('auth:login')}?next={request.build_absolute_uri()}"
            if is_ajax:
                return JsonResponse(
                    {
                        "success": False,
                        "login_required": True,
                        "login_url": login_url,
                        "error": "Login required to write a review.",
                    },
                    status=403,
                )
            return redirect(login_url)

        product = get_object_or_404(Product, pk=product_id, is_active=True)

        form = ReviewForm(request.POST)
        if not form.is_valid():
            error_text = "; ".join(
                [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
            ) or "Invalid review data."
            if is_ajax:
                return JsonResponse({"success": False, "error": error_text}, status=400)
            messages.error(request, "Invalid review data.")
            return redirect("store:product_detail", slug=product.slug)

        # Must have a delivered order for this product
        delivered_item = (
            OrderItem.objects.select_related("order")
            .filter(
                order__user=request.user,
                order__status=Order.Status.DELIVERED,
                product=product,
            )
            .order_by("-order__created_at")
            .first()
        )
        if not delivered_item:
            msg = "You can only review books you have received (delivered orders only)."
            if is_ajax:
                return JsonResponse({"success": False, "error": msg}, status=403)
            messages.error(request, msg)
            return redirect("store:product_detail", slug=product.slug)

        # Prevent duplicate review
        if Review.objects.filter(product=product, user=request.user).exists():
            msg = "You have already reviewed this book."
            if is_ajax:
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("store:product_detail", slug=product.slug)

        try:
            with transaction.atomic():
                Review.objects.create(
                    product=product,
                    user=request.user,
                    order=delivered_item.order,
                    rating=form.cleaned_data["rating"],
                    title=form.cleaned_data.get("title", "").strip(),
                    comment=form.cleaned_data.get("comment", "").strip(),
                )
        except IntegrityError:
            msg = "You have already reviewed this book."
            if is_ajax:
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("store:product_detail", slug=product.slug)
        except Exception as exc:
            logger.error("Error creating review: %s", exc, exc_info=True)
            msg = "Could not submit your review. Please try again."
            if is_ajax:
                return JsonResponse({"success": False, "error": msg}, status=500)
            messages.error(request, msg)
            return redirect("store:product_detail", slug=product.slug)

        if is_ajax:
            return JsonResponse({"success": True, "message": "Thank you for your review!"})
        messages.success(request, "Thank you for your review!")
        return redirect("store:product_detail", slug=product.slug)
    
class WishlistToggleView(View):
    """POST: toggle product in wishlist. Works for guest (session) and authenticated user."""

    def post(self, request):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        product_id = None
        if request.content_type and "application/json" in request.content_type:
            try:
                data = json.loads(request.body)
                product_id = data.get("product_id")
            except (json.JSONDecodeError, TypeError):
                pass
        if product_id is None:
            product_id = request.POST.get("product_id")

        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return JsonResponse({"success": False, "error": "Invalid product"}, status=400)

        product = Product.objects.filter(pk=product_id, is_active=True).first()
        if not product:
            return JsonResponse({"success": False, "error": "Product not found"}, status=404)

        if request.user.is_authenticated:
            wishlist, created = Wishlist.objects.get_or_create(
                user=request.user,
                product=product,
            )
            if not created:
                wishlist.delete()
                added = False
            else:
                added = True
            count = Wishlist.objects.filter(user=request.user).count()
        else:
            ids = WishlistService.get_guest_ids(request.session)
            if product_id in ids:
                ids = [x for x in ids if x != product_id]
                added = False
            else:
                if len(ids) >= WishlistService.WISHLIST_MAX_ITEMS:
                    return JsonResponse(
                        {"success": False, "error": "Wishlist limit reached (max 50)."},
                        status=400,
                    )
                ids = ids + [product_id]
                added = True
            WishlistService.set_guest_ids(request.session, ids)
            count = len(ids)

        return JsonResponse({"success": True, "added": added, "count": count})


class WishlistIdsView(View):
    """GET: return wishlist product IDs for marking hearts on product cards. Guest = session."""

    def get(self, request):
        try:
            if request.user.is_authenticated:
                product_ids = list(
                    Wishlist.objects.filter(user=request.user)
                    .filter(product__is_active=True)
                    .values_list("product_id", flat=True)
                )
            else:
                product_ids = WishlistService.get_guest_ids(request.session)
            return JsonResponse({"product_ids": product_ids})
        except Exception as e:
            logger.exception("WishlistIdsView: %s", e)
            return JsonResponse({"product_ids": []})


class WishlistPageView(TemplateView):
    """Wishlist page: saved books. Authenticated = DB; guest = session product IDs."""

    template_name = "wishlist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            wishlist_items = (
                Wishlist.objects.filter(
                    user=self.request.user,
                    product__is_active=True,
                )
                .select_related("product", "product__category")
                .prefetch_related("product__images", "product__formats")
                .order_by("-created_at")
            )
            context["wishlist_products"] = [item.product for item in wishlist_items]
        else:
            ids = WishlistService.get_guest_ids(self.request.session)
            if not ids:
                context["wishlist_products"] = []
            else:
                context["wishlist_products"] = list(
                    Product.objects.active()
                    .filter(pk__in=ids)
                    .select_related("category")
                    .prefetch_related("images", "formats")
                    .order_by("-created_at")
                )
        context["active_page"] = "wishlist"
        return context