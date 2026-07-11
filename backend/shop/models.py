import random
from decimal import Decimal

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
        verbose_name = "دستهبندی"
        verbose_name_plural = "دستهبندیها"

    def __str__(self):
        return self.name


class Product(models.Model):
    PRICING_MODE_CHOICES = [
        ("fixed", "Fixed"),
        ("on_request", "On Request"),
    ]
    PRODUCT_TYPE_CHOICES = [
        ("physical", "Physical"),
        ("service", "Service"),
    ]
    PRODUCT_CONDITION_CHOICES = [
        ("new", "New"),
        ("used", "Used"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    specs = models.JSONField(default=dict, blank=True)
    pricing_mode = models.CharField(
        max_length=20,
        choices=PRICING_MODE_CHOICES,
        default="fixed",
    )
    type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default="physical",
    )
    condition = models.CharField(
        max_length=20,
        choices=PRODUCT_CONDITION_CHOICES,
        default="new",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

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
    image = models.ImageField(upload_to="products/", null=True, blank=True)
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
        verbose_name = "دیدگاه"
        verbose_name_plural = "دیدگاهها"
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
        verbose_name = "آدرس"
        verbose_name_plural = "آدرسها"

    def __str__(self):
        return f"{self.full_name} — {self.line1}, {self.city}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_default:
                Address.objects.filter(user=self.user, is_default=True).exclude(
                    pk=self.pk
                ).update(is_default=False)


class QuoteRequest(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("quoted", "Quoted"),
        ("approved", "Approved"),
        ("closed", "Closed"),
    ]

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="quote_requests",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quote_requests",
    )
    quantity = models.PositiveIntegerField(default=1)
    contact_phone = models.CharField(max_length=30)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
    )
    agreed_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "درخواست قیمت"
        verbose_name_plural = "درخواستهای قیمت"

    def __str__(self):
        return f"Quote #{self.id} — {self.product.name} ({self.user.username})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        old_agreed_price = None
        if not is_new:
            orig = QuoteRequest.objects.get(pk=self.pk)
            old_status = orig.status
            old_agreed_price = orig.agreed_price

        super().save(*args, **kwargs)

        if self.status == "approved" and (old_status != "approved" or old_agreed_price is None) and self.agreed_price is not None:
            if not hasattr(self, "order") or self.order is None:
                from django.db import transaction
                from .models import Order, OrderItem
                from api.models import Notification

                with transaction.atomic():
                    subtotal = self.agreed_price * self.quantity
                    tax = (Decimal(str(settings.TAX_RATE)) * subtotal).quantize(Decimal("0.01"))
                    total = subtotal + tax

                    order = Order.objects.create(
                        user=self.user,
                        email=self.user.email,
                        status="pending_payment",
                        fulfillment="pickup",
                        shipping_address={},
                        subtotal=subtotal,
                        discount=Decimal("0.00"),
                        delivery_fee=Decimal("0.00"),
                        tax=tax,
                        total=total,
                        promo_code="",
                        quote_request=self,
                    )

                    OrderItem.objects.create(
                        order=order,
                        product=self.product,
                        name=self.product.name,
                        sku=self.product.sku,
                        unit_price=self.agreed_price,
                        quantity=self.quantity,
                        line_total=subtotal,
                    )

                    if self.product.type == "physical":
                        self.product.stock = max(0, self.product.stock - self.quantity)
                        self.product.save(update_fields=["stock"])

                    Notification.objects.create(
                        user=self.user,
                        title="پیش‌فاکتور تأیید شد",
                        message=f"درخواست قیمت شما برای {self.product.name} تأیید شد. شماره سفارش: {order.number}",
                        link=f"/orders/{order.id}",
                    )


ORDER_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("pending_payment", "Pending Payment"),
    ("awaiting_verification", "Awaiting Verification"),
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
    quote_request = models.OneToOneField(
        QuoteRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
    )
    number = models.CharField(
        max_length=20, unique=True, db_index=True, default=generate_order_number, editable=False
    )
    email = models.EmailField()
    status = models.CharField(
        max_length=25, choices=ORDER_STATUS_CHOICES, default="pending_payment", db_index=True
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
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشها"

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if self.pk:
            orig = Order.objects.get(pk=self.pk)
            if self.status == "paid" and orig.status != "paid":
                # Check if there are any manual payments, or if the original status was awaiting_verification
                has_payments = self.payments.exists()
                if has_payments or orig.status == "awaiting_verification":
                    has_approved = self.payments.filter(verification_status="approved").exists()
                    if not has_approved:
                        from django.core.exceptions import ValidationError
                        raise ValidationError(
                            "Cannot mark order as paid: manual payment must be approved first."
                        )
        super().save(*args, **kwargs)


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


class BankAccount(models.Model):
    bank_name = models.CharField(max_length=100, verbose_name="نام بانک")
    card_number = models.CharField(max_length=20, verbose_name="شماره کارت")
    sheba_number = models.CharField(max_length=30, verbose_name="شماره شبا")
    holder_name = models.CharField(max_length=150, verbose_name="نام صاحب حساب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "حساب بانکی"
        verbose_name_plural = "حساب‌های بانکی"
        ordering = ["bank_name", "id"]

    def __str__(self):
        return f"{self.bank_name} - {self.holder_name}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "در انتظار تایید"),
        ("approved", "تایید شده"),
        ("rejected", "رد شده"),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="سفارش",
    )
    receipt_image = models.ImageField(
        upload_to="receipts/",
        null=True,
        blank=True,
        verbose_name="تصویر رسید",
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="شماره پیگیری",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت تایید",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
        verbose_name="تایید شده توسط",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تایید",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Payment #{self.id} for Order {self.order.number} ({self.verification_status})"
