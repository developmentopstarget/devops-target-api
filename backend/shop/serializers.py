from collections import Counter
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from api.models import Notification

from .models import Address, Category, Order, OrderItem, Product, ProductImage, Review, QuoteRequest, BankAccount, Payment

# Mirrors the frontend's placeholder promo list (web/src/components/commerce/PromoCode.tsx)
# until a real PromoCode model/admin exists.
PROMO_CODES = {
    "SPRING10": Decimal("0.10"),
    "WELCOME5": Decimal("0.05"),
}


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "image", "order", "is_active"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "url", "image", "alt", "order", "is_primary"]


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    aggregate_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "brand",
            "category",
            "price",
            "compare_at_price",
            "stock",
            "in_stock",
            "stock_status",
            "is_featured",
            "specs",
            "pricing_mode",
            "type",
            "condition",
            "aggregate_rating",
            "review_count",
            "created_at",
        ]

    def get_aggregate_rating(self, obj):
        value = getattr(obj, "avg_rating", None)
        if value is None:
            value = obj.aggregate_rating
        return round(value, 1) if value is not None else None

    def get_review_count(self, obj):
        value = getattr(obj, "reviews_count", None)
        return value if value is not None else obj.review_count


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["sku", "description", "images"]


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "title", "body", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "full_name",
            "line1",
            "line2",
            "city",
            "postal_code",
            "phone",
            "is_default",
        ]
        read_only_fields = ["id"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "name", "sku", "unit_price", "quantity", "line_total"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "number",
            "status",
            "fulfillment",
            "shipping_address",
            "subtotal",
            "discount",
            "delivery_fee",
            "tax",
            "total",
            "promo_code",
            "items",
            "created_at",
        ]
        read_only_fields = fields


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    fulfillment = serializers.ChoiceField(choices=["pickup", "delivery"])
    address_id = serializers.IntegerField(required=False, allow_null=True)
    items = OrderItemInputSerializer(many=True)
    promo_code = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def validate(self, attrs):
        request = self.context["request"]

        address = None
        if attrs["fulfillment"] == "delivery":
            address_id = attrs.get("address_id")
            if not address_id:
                raise serializers.ValidationError(
                    {"address_id": "A delivery address is required."}
                )
            try:
                address = Address.objects.get(id=address_id, user=request.user)
            except Address.DoesNotExist:
                raise serializers.ValidationError({"address_id": "Address not found."})

        promo_code = attrs.get("promo_code", "").strip().upper()
        discount_rate = Decimal("0")
        if promo_code:
            discount_rate = PROMO_CODES.get(promo_code)
            if discount_rate is None:
                raise serializers.ValidationError({"promo_code": "Invalid or expired code."})

        attrs["promo_code"] = promo_code
        attrs["_address"] = address
        attrs["_discount_rate"] = discount_rate
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        address = validated_data["_address"]
        discount_rate = validated_data["_discount_rate"]
        items_data = validated_data["items"]
        fulfillment = validated_data["fulfillment"]
        promo_code = validated_data["promo_code"]

        slugs = [item["product"] for item in items_data]

        with transaction.atomic():
            products = {
                product.slug: product
                for product in Product.objects.select_for_update().filter(
                    slug__in=slugs, is_active=True
                )
            }

            missing = [slug for slug in slugs if slug not in products]
            if missing:
                raise serializers.ValidationError(
                    {"items": f"Unknown or inactive product(s): {', '.join(missing)}"}
                )

            requested_quantities = Counter()
            for item in items_data:
                requested_quantities[item["product"]] += item["quantity"]

            subtotal = Decimal("0")
            line_items = []
            for item in items_data:
                product = products[item["product"]]
                quantity = item["quantity"]
                total_requested = requested_quantities[item["product"]]
                if product.stock < total_requested:
                    raise serializers.ValidationError(
                        {
                            "items": (
                                f"Insufficient stock for {product.name} "
                                f"(have {product.stock}, requested total of {total_requested})."
                            )
                        }
                    )
                if product.pricing_mode == "on_request" or product.price is None:
                    raise serializers.ValidationError(
                        {"items": f"Product {product.name} is quote-only and cannot be purchased directly."}
                    )
                line_total = product.price * quantity
                subtotal += line_total
                line_items.append((product, quantity, line_total))

            discount = (subtotal * discount_rate).quantize(Decimal("0.01"))

            if fulfillment == "pickup":
                delivery_fee = Decimal("0.00")
            else:
                delivery_fee = (
                    Decimal("0.00")
                    if subtotal >= settings.FREE_DELIVERY_THRESHOLD
                    else settings.DELIVERY_FEE
                )

            tax = (Decimal(str(settings.TAX_RATE)) * (subtotal - discount)).quantize(
                Decimal("0.01")
            )
            total = subtotal - discount + delivery_fee + tax

            shipping_address = {}
            if address:
                shipping_address = {
                    "full_name": address.full_name,
                    "line1": address.line1,
                    "line2": address.line2,
                    "city": address.city,
                    "postal_code": address.postal_code,
                    "phone": address.phone,
                }

            order = Order.objects.create(
                user=request.user,
                email=request.user.email,
                fulfillment=fulfillment,
                shipping_address=shipping_address,
                subtotal=subtotal,
                discount=discount,
                delivery_fee=delivery_fee,
                tax=tax,
                total=total,
                promo_code=promo_code,
            )

            for product, quantity, line_total in line_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    name=product.name,
                    sku=product.sku,
                    unit_price=product.price,
                    quantity=quantity,
                    line_total=line_total,
                )
                product.stock -= quantity
                product.save(update_fields=["stock"])

            Notification.objects.create(
                user=request.user,
                title="Order placed",
                message=f"Your order {order.number} has been placed.",
                link=f"/orders/{order.id}",
            )

        return order


class QuoteRequestSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="slug", queryset=Product.objects.filter(is_active=True))
    product_name = serializers.CharField(source="product.name", read_only=True)
    user = serializers.CharField(source="user.username", read_only=True)
    order_id = serializers.IntegerField(source="order.id", read_only=True, allow_null=True)
    order_number = serializers.CharField(source="order.number", read_only=True, allow_null=True)

    class Meta:
        model = QuoteRequest
        fields = [
            "id",
            "product",
            "product_name",
            "user",
            "quantity",
            "contact_phone",
            "message",
            "status",
            "agreed_price",
            "order_id",
            "order_number",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "agreed_price",
            "order_id",
            "order_number",
            "created_at",
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id", "bank_name", "card_number", "sheba_number", "holder_name", "is_active"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "receipt_image",
            "reference_number",
            "verification_status",
            "verified_at",
            "created_at",
        ]
        read_only_fields = ["id", "verification_status", "verified_at", "created_at"]


class BankTransferSubmitSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    receipt_image = serializers.ImageField(required=True)
    reference_number = serializers.CharField(max_length=100, required=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        try:
            order = Order.objects.get(id=attrs["order_id"], user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError({"order_id": "Order not found."})

        if order.status == "paid":
            raise serializers.ValidationError({"order_id": "Order has already been paid."})

        if order.status in ["ready", "shipped", "delivered", "refunded"]:
            raise serializers.ValidationError({"order_id": f"Order is in status '{order.status}' and cannot be paid."})

        attrs["_order"] = order
        return attrs

    def create(self, validated_data):
        order = validated_data["_order"]
        with transaction.atomic():
            order.status = "awaiting_verification"
            order.save(update_fields=["status"])

            payment = Payment.objects.create(
                order=order,
                receipt_image=validated_data["receipt_image"],
                reference_number=validated_data["reference_number"],
                verification_status="pending",
            )

            from api.models import Notification
            if order.user:
                Notification.objects.create(
                    user=order.user,
                    title="رسید پرداخت ثبت شد",
                    message=f"رسید پرداخت شما برای سفارش {order.number} ثبت شد و در حال بررسی است.",
                    link=f"/orders/{order.id}",
                )

        return payment
