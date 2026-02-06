from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/add/", views.AddToCartView.as_view(), name="cart_add"),
    path("cart/update/", views.UpdateCartItemView.as_view(), name="cart_update"),
    path("cart/remove/<int:item_id>/", views.RemoveCartItemView.as_view(), name="cart_remove"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("checkout/place-order/", views.OrderCreateView.as_view(), name="order_create"),
    path("orders/<slug:order_number>/", views.OrderSuccessView.as_view(), name="order_success"),
    path("orders/", views.OrderHistoryView.as_view(), name="order_history"),
    path("payment/razorpay/verify/", views.RazorpayPaymentVerifyView.as_view(), name="razorpay_verify"),
    path("payment/razorpay/<slug:order_number>/", views.RazorpayPaymentView.as_view(), name="razorpay_payment"),
    path("about/", views.StaticPageView.as_view(template_name="about.html", extra_context={"active_page": "about"}), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("newsletter/subscribe/", views.NewsletterSubscribeView.as_view(), name="newsletter_subscribe"),
    path("privacy/", views.StaticPageView.as_view(template_name="privacy.html", extra_context={"active_page": "privacy"}), name="privacy"),
    path("terms/", views.StaticPageView.as_view(template_name="terms.html", extra_context={"active_page": "terms"}), name="terms"),
    path("refund/", views.StaticPageView.as_view(template_name="refund.html", extra_context={"active_page": "refund"}), name="refund"),
    path("shipping/", views.StaticPageView.as_view(template_name="shipping.html", extra_context={"active_page": "shipping"}), name="shipping"),
]

