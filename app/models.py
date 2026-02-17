from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import hashlib
import secrets
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg, Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    image = models.ImageField(upload_to="book_categories/", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class AgeGroup(TimeStampedModel):
    """Age groups for book categorization - supports multiple age ranges per book"""
    name = models.CharField(max_length=50, unique=True, help_text="Display name (e.g., '0-2 Years')")
    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    emoji = models.CharField(max_length=10, default='📚', help_text="Emoji for UI display")
    display_order = models.PositiveIntegerField(default=0, db_index=True, help_text="Order for display (lower = first)")
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]
        verbose_name = "Age Group"
        verbose_name_plural = "Age Groups"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def available(self):
        return self.active().filter(formats__is_active=True, formats__stock_quantity__gt=0).distinct()


class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    
    author = models.CharField(max_length=200, db_index=True)
    illustrator = models.CharField(max_length=200, blank=True)
    publisher = models.CharField(max_length=150, blank=True)
    publication_year = models.PositiveIntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True, db_index=True)
    age_groups = models.ManyToManyField(
        'AgeGroup',
        blank=True,
        related_name='products',
        help_text="Select all applicable age groups (e.g., for ages 0-8, select 0-2, 3-5, 6-8)"
    )
    page_count = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    original_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)], 
        blank=True, 
        null=True,
        help_text="MRP/Original price for discount display"
    )
    
    is_featured = models.BooleanField(default=False, db_index=True)
    is_bestseller = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Average star rating from verified reviews (1-5).",
    )
    total_reviews = models.PositiveIntegerField(
        default=0,
        help_text="Total number of approved, non-deleted reviews.",
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["is_active", "is_bestseller"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["author"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def discount_percent(self):
        """
        Calculate discount percentage with full null safety.
        Returns 0 if original_price is missing or invalid.
        """
        if not self.original_price:
            return 0
        if not self.price:
            return 0
        if self.original_price <= self.price:
            return 0
        try:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return round(discount)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0
    
    @property
    def age_range_display(self):
        """
        Returns human-readable age range with full null safety.
        Returns 'All Ages' if no age groups selected.
        """
        if not self.pk:  
            return "Not specified"
        
        try:
            age_groups = self.age_groups.filter(is_active=True).order_by('display_order')
            
            if not age_groups.exists():
                return "All Ages"
            
            names = [ag.name for ag in age_groups]
            
            if len(names) == 1:
                return names[0]
            elif len(names) == 2:
                return f"{names[0]} & {names[1]}"
            else:
                return f"{names[0]} - {names[-1]}"
        except Exception:
            return "All Ages"
    
    def has_available_stock(self):
       
        if not self.pk:
            return False
        
        try:
            return self.formats.filter(
                is_active=True,
                stock_quantity__gt=0
            ).exists()
        except Exception:
            return False
    
    def get_available_formats(self):
        
        if not self.pk:
            return BookFormat.objects.none()
        
        try:
            return self.formats.filter(
                is_active=True,
                stock_quantity__gt=0
            ).order_by('format_type')
        except Exception:
            return BookFormat.objects.none()
    
    def get_primary_image(self):
        
        if not self.pk:
            return None
        
        try:
            primary = self.images.filter(is_primary=True).first()
            if primary and primary.image:
                return primary
            
            first = self.images.filter(image__isnull=False).exclude(image='').first()
            return first
        except Exception:
            return None
    
    def get_primary_image_url(self):
        
        try:
            img = self.get_primary_image()
            if img and img.image:
                return img.image.url
        except Exception:
            pass
        return None
    
    def get_all_image_urls(self):
        
        if not self.pk:
            return []
        
        try:
            urls = []
            for img in self.images.filter(image__isnull=False).exclude(image='').order_by('-is_primary', 'id'):
                if img.image:
                    try:
                        urls.append(img.image.url)
                    except Exception:
                        continue
            return urls
        except Exception:
            return []
    
    def get_total_stock(self):
        
        if not self.pk:
            return 0
        
        try:
            from django.db.models import Sum
            result = self.formats.filter(is_active=True).aggregate(
                total=Sum('stock_quantity')
            )
            return result.get('total') or 0
        except Exception:
            return 0
    
    def get_default_format(self):
        
        if not self.pk:
            return None
        
        try:
            available = self.get_available_formats()
            
            if not available.exists():
                return None
            
            # Try hardcover first
            hardcover = available.filter(format_type='hardcover').first()
            if hardcover:
                return hardcover
            
            # Try paperback next
            paperback = available.filter(format_type='paperback').first()
            if paperback:
                return paperback
            
            # Return first available
            return available.first()
        except Exception:
            return None

    def __str__(self):
        return f"{self.name} by {self.author}"

class ProductImage(TimeStampedModel): 
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="books/")
    is_primary = models.BooleanField(default=False, db_index=True)
    alt_text = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-is_primary", "id"]
        indexes = [
            models.Index(fields=["product", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.product.name} image"


class BookFormat(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="formats")
    sku = models.CharField(max_length=64, unique=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    format_type = models.CharField(
        max_length=20,
        choices=[
            ('hardcover', 'Hardcover'),
            ('paperback', 'Paperback'),
            ('ebook', 'E-Book'),
            ('audiobook', 'Audiobook'),
        ],
        db_index=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "format_type"], name="unique_book_format"),
            models.CheckConstraint(condition=models.Q(stock_quantity__gte=0), name="stock_non_negative"),
        ]
        indexes = [
            models.Index(fields=["product", "is_active", "stock_quantity"]),
        ]

    def is_available(self):
        
        try:
            return self.is_active and self.stock_quantity > 0
        except Exception:
            return False
    
    def can_fulfill_quantity(self, quantity):
        
        try:
            return self.is_active and self.stock_quantity >= quantity
        except Exception:
            return False
    
    def __str__(self):
        try:
            return f"{self.product.name} - {self.get_format_type_display()}"
        except Exception:
            return f"BookFormat #{self.pk}"


class Cart(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ORDERED = "ordered", "Ordered"
        ABANDONED = "abandoned", "Abandoned"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="carts")
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["session_key", "status"]),
        ]

    def __str__(self):
        return f"Cart {self.pk} ({self.status})"

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.select_related("product"))


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="cart_items")
    variant = models.ForeignKey(
        BookFormat, 
        on_delete=models.PROTECT, 
        related_name="cart_items",
        null=True,  
        blank=True  
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def get_format_display(self):
        
        try:
            if self.variant and self.variant.format_type:
                return self.variant.get_format_type_display()
        except Exception:
            pass
        return "Unknown Format"
    
    def has_sufficient_stock(self):
        
        try:
            if not self.variant:
                return False
            return self.variant.stock_quantity >= self.quantity
        except Exception:
            return False
    @property
    def line_total(self):
        try:
            return (self.unit_price or 0) * self.quantity
        except Exception:
            return 0


class Address(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="addresses")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address_line = models.TextField()
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False, db_index=True)
    is_snapshot = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.city}"


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLACED, db_index=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    shipping = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="orders")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    variant = models.ForeignKey(BookFormat, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=200)
    variant_snapshot = models.CharField(max_length=60)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.order.order_number} - {self.product_name}"


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        COD = "cod", "Cash on Delivery"
        WHATSAPP = "whatsapp", "WhatsApp Order"
        RAZORPAY = "razorpay", "Online Payment"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.COD, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    processed_at = models.DateTimeField(blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    def mark_paid(self):
        self.status = self.Status.PAID
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"


class NewsletterSubscription(TimeStampedModel):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.email


class UserProfile(TimeStampedModel):
    """Extended user profile for additional user information"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Profile: {self.user.email}"

class Wishlist(TimeStampedModel):
    """User wishlist for books."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_wishlist",
            ),
        ]
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.product}"

class OTPRequest(TimeStampedModel):
    """Store OTP requests for email-based authentication"""
    email = models.EmailField(db_index=True)
    otp_hash = models.CharField(max_length=64)  # SHA256 hash of OTP
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    attempts = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_used', 'expires_at']),
            models.Index(fields=['created_at', 'email']),
        ]
    
    def __str__(self):
        return f"OTP for {self.email} - {'Used' if self.is_used else 'Active'}"
    
    @staticmethod
    def hash_otp(otp):
        """Hash OTP using SHA256"""
        return hashlib.sha256(str(otp).encode()).hexdigest()
    
    def verify_otp(self, otp):
        """Verify provided OTP against stored hash"""
        return self.otp_hash == self.hash_otp(otp)
    
    def is_valid(self):
        """Check if OTP is still valid (not expired, not used)"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @classmethod
    def generate_otp(cls):
        """Generate a secure 4-digit OTP"""
        return str(secrets.randbelow(10000)).zfill(4)

class Review(TimeStampedModel):
    """
    Product review from a verified buyer.

    Business rules:
    - Only logged-in users can create reviews (enforced in views).
    - User must have at least one delivered order for the product.
    - One review per (product, user).
    - Rating is 1–5 stars.
    - Reviews can be moderated via is_approved.
    - Reviews are soft-deleted via is_deleted flag.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviews",
        null=True,
        blank=True,
    )
    order = models.ForeignKey(
        "Order",
        on_delete=models.SET_NULL,
        related_name="reviews",
        null=True,
        blank=True,
        help_text="The delivered order that verified this review.",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Only approved reviews are shown on the storefront.",
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft delete flag; deleted reviews are hidden but kept for history.",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_product_user_review",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_between_1_and_5",
            ),
        ]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["is_approved"]),
            models.Index(fields=["product", "is_approved"]),
        ]

    def __str__(self):
        uname = getattr(self.user, "username", "Anonymous")
        return f"Review for {self.product} by {uname} ({self.rating}★)"


def _recompute_product_rating(product_id: int):
    """
    Recompute average_rating and total_reviews for a single product.
    Only considers approved, non-deleted reviews.
    """
    if not product_id:
        return
    qs = Review.objects.filter(
        product_id=product_id,
        is_approved=True,
        is_deleted=False,
    )
    agg = qs.aggregate(
        avg=Avg("rating"),
        cnt=Count("id"),
    )
    Product.objects.filter(pk=product_id).update(
        average_rating=agg["avg"] or 0,
        total_reviews=agg["cnt"] or 0,
    )


@receiver(post_save, sender=Review)
def review_post_save(sender, instance: Review, **kwargs):
    _recompute_product_rating(instance.product_id)


@receiver(post_delete, sender=Review)
def review_post_delete(sender, instance: Review, **kwargs):
    _recompute_product_rating(instance.product_id)