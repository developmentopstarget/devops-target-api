# backend/config/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from api.views import ItemViewSet, MeView, NotificationViewSet
from chat.views import ChatHistoryView
from shop.views import (
    AddressViewSet, CategoryViewSet, OrderViewSet, ProductViewSet,
    CreatePaymentIntentView, StripeWebhookView, QuoteRequestViewSet,
    BankAccountListView, SubmitBankTransferView, ZarinpalInitiateView, ZarinpalCallbackView
)

def health(request):
    return JsonResponse({"status": "ok"})

router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"addresses", AddressViewSet, basename="address")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"quotes", QuoteRequestViewSet, basename="quote")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/", include(router.urls)),
    path("api/me/", MeView.as_view()),
    path("api/chat/history/", ChatHistoryView.as_view()),
    path("api/checkout/intent/", CreatePaymentIntentView.as_view(), name="checkout-intent"),
    path("api/webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
    # --- Iranian Payments ---
    path("api/payments/bank-accounts/", BankAccountListView.as_view(), name="bank-account-list"),
    path("api/payments/bank-transfer/", SubmitBankTransferView.as_view(), name="bank-transfer-submit"),
    path("api/payments/zarinpal/initiate/", ZarinpalInitiateView.as_view(), name="zarinpal-initiate"),
    path("api/payments/zarinpal/callback/", ZarinpalCallbackView.as_view(), name="zarinpal-callback"),
    # --- auth endpoints ---
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

