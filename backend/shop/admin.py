from django.contrib import admin

from .models import Address, Category, Product, ProductImage, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "brand",
        "price",
        "compare_at_price",
        "stock",
        "stock_status",
        "is_active",
        "is_featured",
        "created_at",
    )
    list_filter = ("is_active", "is_featured", "category", "brand")
    search_fields = ("name", "sku", "slug", "brand")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [ProductImageInline]

    @admin.display(description="Stock status")
    def stock_status(self, obj):
        return obj.stock_status


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "title", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__username", "title", "body")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "postal_code", "label", "is_default")
    list_filter = ("is_default", "city")
    search_fields = (
        "full_name",
        "user__username",
        "user__email",
        "line1",
        "city",
        "postal_code",
    )
    ordering = ("-is_default", "-id")
