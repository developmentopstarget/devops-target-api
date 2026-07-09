import random

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    image = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    specs = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def stock_status(self):
        if self.stock <= 0:
            return "out-of-stock"
        if self.stock <= settings.LOW_STOCK_THRESHOLD:
            return "low-stock"
        return "in-stock"

    @property
    def aggregate_rating(self):
        result = self.reviews.aggregate(avg=models.Avg("rating"))["avg"]
        return round(result, 1) if result is not None else None

    @property
    def review_count(self):
        return self.reviews.count()


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    url = models.URLField(blank=True)
    alt = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.product.name} image #{self.order}"


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"], name="unique_review_per_user_product"
            )
        ]

    def __str__(self):
        return f"{self.product.name} — {self.rating}★ by {self.user}"


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(max_length=50, blank=True)
    full_name = models.CharField(max_length=150)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=30, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-id"]
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.full_name} — {self.line1}, {self.city}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_default:
                Address.objects.filter(user=self.user, is_default=True).exclude(
                    pk=self.pk
                ).update(is_default=False)


ORDER_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("pending_payment", "Pending Payment"),
    ("paid", "Paid"),
    ("failed", "Failed"),
    ("preparing", "Preparing"),
    ("ready", "Ready"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
    ("refunded", "Refunded"),
]

FULFILLMENT_CHOICES = [
    ("pickup", "Pickup"),
    ("delivery", "Delivery"),
]


def generate_order_number():
    for _ in range(20):
        candidate = f"DT-{random.randint(100000, 999999)}"
        if not Order.objects.filter(number=candidate).exists():
            return candidate
    raise RuntimeError("Could not generate a unique order number")


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    number = models.CharField(
        max_length=20, unique=True, db_index=True, default=generate_order_number, editable=False
    )
    email = models.EmailField()
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="pending_payment", db_index=True
    )
    fulfillment = models.CharField(max_length=10, choices=FULFILLMENT_CHOICES)
    shipping_address = models.JSONField(default=dict, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    promo_code = models.CharField(max_length=30, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} x{self.quantity} ({self.order.number})"
