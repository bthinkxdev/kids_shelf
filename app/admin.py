from django.contrib import admin

from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    ContactMessage,
    NewsletterSubscription,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductImage,
    BookFormat,
    AgeGroup
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = BookFormat
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_featured", "is_bestseller", "is_active")
    list_filter = ("category", "is_featured", "is_bestseller", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    inlines = [ProductImageInline, ProductVariantInline]
    filter_horizontal = ('age_groups',)

@admin.register(AgeGroup)
class AgeGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "emoji", "display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("display_order", "is_active")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "status", "updated_at")
    list_filter = ("status",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "variant", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user_or_guest", "guest_email", "status", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("order_number", "user__username", "user__email", "address__email")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("address", "user")

    def user_or_guest(self, obj):
        if obj.user_id is None:
            return "Guest Order"
        return str(obj.user)
    user_or_guest.short_description = "Customer"

    def guest_email(self, obj):
        if not obj.address_id:
            return ""
        return obj.address.email or obj.address.phone or ""
    guest_email.short_description = "Email / Phone"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "quantity", "unit_price")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "city", "state", "is_snapshot")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "status", "amount", "processed_at")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_resolved", "created_at")
    list_filter = ("is_resolved",)


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
