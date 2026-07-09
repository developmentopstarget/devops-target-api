# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from api.views import ItemViewSet, MeView, NotificationViewSet
from chat.views import ChatHistoryView
from shop.views import CategoryViewSet, ProductViewSet

def health(request):
    return JsonResponse({"status": "ok"})

router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/", include(router.urls)),
    path("api/me/", MeView.as_view()),
    path("api/chat/history/", ChatHistoryView.as_view()),
    # --- auth endpoints ---
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
]
