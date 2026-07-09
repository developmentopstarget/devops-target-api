from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, F, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Category, Product, Review
from .pagination import ProductPagination
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ReviewSerializer,
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
