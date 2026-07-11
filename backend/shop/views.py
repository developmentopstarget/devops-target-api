from decimal import Decimal, InvalidOperation
import stripe

from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Notification
from .models import Address, Category, Order, Product, Review, QuoteRequest, BankAccount, Payment
from .pagination import ProductPagination
from .serializers import (
    AddressSerializer,
    CategorySerializer,
    OrderCreateSerializer,
    OrderSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ReviewSerializer,
    QuoteRequestSerializer,
    BankAccountSerializer,
    BankTransferSubmitSerializer,
)


def _to_decimal(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _to_int_list(values):
    result = []
    for value in values:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    permission_classes = [AllowAny]
    pagination_class = ProductPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def get_queryset(self):
        params = self.request.query_params
        qs = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images")
            .annotate(
                avg_rating=Avg("reviews__rating"),
                reviews_count=Count("reviews", distinct=True),
            )
        )

        categories = params.getlist("category")
        if categories:
            qs = qs.filter(category__slug__in=categories)

        brands = params.getlist("brand")
        if brands:
            qs = qs.filter(brand__in=brands)

        ram_values = _to_int_list(params.getlist("ram"))
        if ram_values:
            qs = qs.filter(specs__ram_gb__in=ram_values)

        storage_values = _to_int_list(params.getlist("storage"))
        if storage_values:
            qs = qs.filter(specs__storage_gb__in=storage_values)

        price_min = _to_decimal(params.get("priceMin"))
        if price_min is not None:
            qs = qs.filter(price__gte=price_min)

        price_max = _to_decimal(params.get("priceMax"))
        if price_max is not None:
            qs = qs.filter(price__lte=price_max)

        min_rating = _to_decimal(params.get("minRating"))
        if min_rating is not None:
            qs = qs.filter(avg_rating__gte=min_rating)

        if params.get("inStock") == "1":
            qs = qs.filter(stock__gt=0)

        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(brand__icontains=search)
                | Q(description__icontains=search)
            )

        sort = params.get("sort")
        if sort == "price_asc":
            qs = qs.order_by("price", "id")
        elif sort == "price_desc":
            qs = qs.order_by("-price", "id")
        elif sort == "newest":
            qs = qs.order_by("-created_at", "-id")
        elif sort == "rating":
            qs = qs.order_by(F("avg_rating").desc(nulls_last=True), "-id")
        else:
            qs = qs.order_by("-is_featured", "-created_at", "-id")

        return qs

    @action(
        detail=True,
        methods=["get", "post"],
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def reviews(self, request, slug=None):
        product = self.get_object()

        if request.method == "GET":
            reviews = product.reviews.select_related("user")
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        if Review.objects.filter(product=product, user=request.user).exists():
            return Response(
                {"detail": "You have already reviewed this product."},
                status=400,
            )

        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, user=request.user)
        return Response(serializer.data, status=201)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items", "items__product"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=201)


class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"order_id": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status == "paid":
            return Response({"detail": "This order has already been paid."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status in ["failed", "cancelled", "refunded"]:
            return Response({"detail": "This order is cancelled or failed and cannot be paid."}, status=status.HTTP_400_BAD_REQUEST)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            amount_cents = int(order.total * 100)
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                metadata={
                    "order_id": order.id,
                    "order_number": order.number,
                    "user_id": request.user.id,
                },
            )

            order.stripe_payment_intent_id = intent.id
            order.save(update_fields=["stripe_payment_intent_id"])

            return Response({
                "client_secret": intent.client_secret,
                "stripe_payment_intent_id": intent.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        if not sig_header:
            return Response({"detail": "Missing Stripe-Signature header"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response({"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        event_type = event.get("type")
        data_object = event.get("data", {}).get("object", {})
        intent_id = data_object.get("id")

        if not intent_id:
            return Response({"detail": "Missing PaymentIntent ID"}, status=status.HTTP_400_BAD_REQUEST)

        if event_type == "payment_intent.succeeded":
            with transaction.atomic():
                try:
                    order = Order.objects.select_for_update().get(stripe_payment_intent_id=intent_id)
                except Order.DoesNotExist:
                    return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

                if order.status != "paid":
                    order.status = "paid"
                    order.save(update_fields=["status"])

                    if order.user:
                        Notification.objects.create(
                            user=order.user,
                            title="Order paid",
                            message=f"Payment for order {order.number} was successful.",
                            link=f"/orders/{order.id}",
                        )
            return Response({"status": "success", "detail": "Order marked as paid"}, status=status.HTTP_200_OK)

        elif event_type in ["payment_intent.payment_failed", "payment_intent.canceled"]:
            with transaction.atomic():
                try:
                    order = Order.objects.select_for_update().get(stripe_payment_intent_id=intent_id)
                except Order.DoesNotExist:
                    return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

                if order.status in ["failed", "cancelled", "refunded"]:
                    return Response({"status": "ignored", "detail": "Order already in terminal state"}, status=status.HTTP_200_OK)

                new_status = "cancelled" if event_type == "payment_intent.canceled" else "failed"
                order.status = new_status
                order.save(update_fields=["status"])

                # Replenish stock safely
                items = order.items.filter(product__isnull=False).select_related("product")
                product_ids = [item.product.id for item in items]
                if product_ids:
                    product_ids.sort()
                    products_locked = {
                        p.id: p
                        for p in Product.objects.select_for_update().filter(id__in=product_ids)
                    }
                    for item in items:
                        product = products_locked.get(item.product.id)
                        if product:
                            product.stock += item.quantity
                            product.save(update_fields=["stock"])

                if order.user:
                    event_name = "cancelled" if event_type == "payment_intent.canceled" else "failed"
                    Notification.objects.create(
                        user=order.user,
                        title=f"Order payment {event_name}",
                        message=f"Payment for order {order.number} {event_name}.",
                        link=f"/orders/{order.id}",
                    )
            return Response({"status": "success", "detail": f"Order marked as {new_status} and stock replenished"}, status=status.HTTP_200_OK)

        return Response({"status": "ignored", "detail": "Unhandled event type"}, status=status.HTTP_200_OK)


class QuoteRequestViewSet(viewsets.ModelViewSet):
    serializer_class = QuoteRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuoteRequest.objects.filter(user=self.request.user).select_related("product", "user", "order")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BankAccountListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        accounts = BankAccount.objects.filter(is_active=True)
        serializer = BankAccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitBankTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BankTransferSubmitSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(
            {
                "detail": "Bank transfer payment receipt submitted successfully.",
                "payment_id": payment.id,
                "status": payment.verification_status,
            },
            status=status.HTTP_201_CREATED,
        )


class ZarinpalInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"order_id": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status == "paid":
            return Response({"detail": "This order has already been paid."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status in ["failed", "cancelled", "refunded"]:
            return Response({"detail": "This order is cancelled or failed and cannot be paid."}, status=status.HTTP_400_BAD_REQUEST)

        # Stub Zarinpal payment initiation
        import random
        authority = f"zarp-{random.randint(1000000, 9999999)}"
        return Response({
            "status": "success",
            "authority": authority,
            "payment_url": f"https://sandbox.zarinpal.com/pg/StartPay/{authority}"
        }, status=status.HTTP_200_OK)


class ZarinpalCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        authority = request.query_params.get("Authority")
        status_param = request.query_params.get("Status")  # "OK" or "NOK"
        order_id = request.query_params.get("order_id")

        if not authority or not order_id:
            return Response({"detail": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if status_param == "OK":
            with transaction.atomic():
                if order.status != "paid":
                    order.status = "paid"
                    order.save(update_fields=["status"])

                    Payment.objects.create(
                        order=order,
                        reference_number=authority,
                        verification_status="approved",
                    )

                    if order.user:
                        Notification.objects.create(
                            user=order.user,
                            title="پرداخت موفق زارین‌پال",
                            message=f"پرداخت سفارش {order.number} از طریق درگاه زارین‌پال تایید شد.",
                            link=f"/orders/{order.id}",
                        )
            return Response({"status": "paid", "message": "Payment verified successfully."}, status=status.HTTP_200_OK)
        else:
            if order.status == "pending_payment":
                order.status = "failed"
                order.save(update_fields=["status"])
            return Response({"status": "failed", "message": "Payment was cancelled or failed."}, status=status.HTTP_400_BAD_REQUEST)
