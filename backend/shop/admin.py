from django.contrib import admin

from .models import Address, Category, Order, OrderItem, Product, ProductImage, Review


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


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "name", "sku", "unit_price", "quantity", "line_total")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "user",
        "status",
        "fulfillment",
        "total",
        "created_at",
    )
    list_filter = ("status", "fulfillment", "created_at")
    search_fields = ("number", "email", "user__username", "user__email")
    readonly_fields = ("number", "created_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [OrderItemInline]
    actions = [
        "mark_paid",
        "mark_preparing",
        "mark_shipped",
        "mark_delivered",
        "mark_cancelled",
    ]

    @admin.action(description="Mark selected orders as paid")
    def mark_paid(self, request, queryset):
        queryset.update(status="paid")

    @admin.action(description="Mark selected orders as preparing")
    def mark_preparing(self, request, queryset):
        queryset.update(status="preparing")

    @admin.action(description="Mark selected orders as shipped")
    def mark_shipped(self, request, queryset):
        queryset.update(status="shipped")

    @admin.action(description="Mark selected orders as delivered")
    def mark_delivered(self, request, queryset):
        queryset.update(status="delivered")

    @admin.action(description="Mark selected orders as cancelled")
    def mark_cancelled(self, request, queryset):
        queryset.update(status="cancelled")
