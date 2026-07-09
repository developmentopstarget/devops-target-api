from rest_framework import serializers

from .models import Address, Category, Product, ProductImage, Review


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "image", "order", "is_active"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "url", "alt", "order", "is_primary"]


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
