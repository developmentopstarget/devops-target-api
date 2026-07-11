from django.contrib import admin
from django import forms
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from .models import Address, Category, Order, OrderItem, Product, ProductImage, Review, QuoteRequest, BankAccount, Payment


# --- Model Forms for Farsi Labels & Help Texts ---

class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
        help_texts = {
            "name": "نام دسته‌بندی به فارسی (مثال: قطعات سخت‌افزار).",
            "slug": "شناسه در آدرس URL (به انگلیسی و بدون فاصله، مانند: hardware-parts).",
            "parent": "دسته‌بندی والد در ساختار درختی (در صورت وجود).",
            "image": "آدرس تصویر نمایه دسته‌بندی.",
            "order": "ترتیب نمایش این دسته‌بندی.",
            "is_active": "نمایش یا عدم نمایش دسته‌بندی در سایت.",
        }
        labels = {
            "name": "نام دسته‌بندی",
            "slug": "نامک (Slug)",
            "parent": "دسته‌بندی والد",
            "image": "لینک تصویر دسته‌بندی",
            "order": "ترتیب",
            "is_active": "فعال",
        }


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        help_texts = {
            "name": "نام محصول به فارسی (مثال: لپ‌تاپ لنوو مدل ThinkPad).",
            "slug": "نامک یا شناسه URL محصول (به انگلیسی و بدون فاصله، به صورت خودکار ساخته می‌شود).",
            "category": "دسته‌بندی که این محصول در آن قرار می‌گیرد.",
            "brand": "برند سازنده محصول (مثال: Lenovo).",
            "description": "توضیحات تکمیلی و مشخصات متنی کالا.",
            "price": "قیمت فروش محصول (در صورتی که حالت قیمت‌گذاری روی قیمت ثابت باشد).",
            "compare_at_price": "قیمت اولیه جهت نمایش تخفیف (قبل از خط خوردن).",
            "sku": "شناسه انبارداری کالا (یکتا و بدون فاصله).",
            "stock": "تعداد موجودی محصول در انبار.",
            "pricing_mode": "تعیین نوع قیمت‌گذاری: ثابت یا استعلام قیمت (تماس بگیرید).",
            "type": "نوع محصول: فیزیکی (دارای موجودی و ارسال) یا خدمات.",
            "condition": "وضعیت فیزیکی کالا (نو یا دست دوم).",
            "is_active": "نمایش یا عدم نمایش محصول در سایت.",
            "is_featured": "نمایش محصول در بخش پیشنهادات ویژه صفحه اصلی.",
            "specs": "مشخصات فنی محصول به صورت ساختار یافته (JSON).",
        }
        labels = {
            "name": "نام محصول",
            "slug": "نامک (Slug)",
            "category": "دسته‌بندی",
            "brand": "برند",
            "description": "توضیحات",
            "price": "قیمت فروش",
            "compare_at_price": "قیمت مقایسه‌ای",
            "sku": "شناسه انبار کالا (SKU)",
            "stock": "موجودی انبار",
            "pricing_mode": "حالت قیمت‌گذاری",
            "type": "نوع کالا",
            "condition": "وضعیت کلا",
            "is_active": "فعال",
            "is_featured": "ویژه شده",
            "specs": "مشخصات فنی (JSON)",
        }


class ProductImageInlineForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = "__all__"
        help_texts = {
            "image": "فایل تصویر محصول را بارگذاری کنید.",
            "url": "آدرس مستقیم تصویر اینترنتی (در صورت استفاده از لینک خارجی).",
            "alt": "توضیح جایگزین برای سئو و دسترس‌پذیری.",
            "order": "ترتیب نمایش این تصویر در گالری محصول (عدد کوچک‌تر اول نمایش داده می‌شود).",
            "is_primary": "در صورت فعال بودن، این تصویر به عنوان تصویر اصلی محصول استفاده می‌شود.",
        }
        labels = {
            "image": "فایل تصویر",
            "url": "آدرس تصویر (URL)",
            "alt": "توضیح Alt (سئو)",
            "order": "ترتیب نمایش",
            "is_primary": "اصلی",
        }


class ReviewAdminForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = "__all__"
        help_texts = {
            "product": "محصولی که برای آن دیدگاه ثبت شده است.",
            "user": "کاربر ثبت‌کننده دیدگاه.",
            "rating": "امتیاز از ۱ تا ۵ ستاره.",
            "title": "عنوان دیدگاه.",
            "body": "متن دیدگاه کاربر.",
        }
        labels = {
            "product": "محصول",
            "user": "کاربر",
            "rating": "امتیاز",
            "title": "عنوان دیدگاه",
            "body": "متن دیدگاه",
        }


class AddressAdminForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = "__all__"
        help_texts = {
            "user": "کاربر صاحب این نشانی.",
            "label": "عنوان نشانی (مثال: خانه، محل کار).",
            "full_name": "نام و نام خانوادگی تحویل‌گیرنده.",
            "line1": "آدرس دقیق پستی.",
            "line2": "اطلاعات تکمیلی آدرس (مانند واحد، پلاک).",
            "city": "شهر.",
            "postal_code": "کد پستی ۱۰ رقمی.",
            "phone": "شماره تماس تحویل‌گیرنده.",
            "is_default": "آیا نشانی پیش‌فرض کاربر باشد؟",
        }
        labels = {
            "user": "کاربر",
            "label": "برچسب نشانی",
            "full_name": "نام کامل گیرنده",
            "line1": "نشانی (سطر ۱)",
            "line2": "نشانی (سطر ۲)",
            "city": "شهر",
            "postal_code": "کد پستی",
            "phone": "شماره تماس",
            "is_default": "نشانی پیش‌فرض",
        }


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"
        help_texts = {
            "user": "کاربر ثبت‌کننده سفارش.",
            "email": "آدرس ایمیل برای مکاتبات سفارش.",
            "status": "وضعیت فعلی سفارش.",
            "fulfillment": "نحوه تحویل کالا (ارسال یا تحویل حضوری).",
            "shipping_address": "اطلاعات آدرس ارسال در قالب ساختار یافته.",
            "subtotal": "جمع فرعی اقلام سفارش.",
            "discount": "مبلغ تخفیف اعمال شده.",
            "delivery_fee": "هزینه ارسال.",
            "tax": "مبلغ مالیات.",
            "total": "مبلغ کل پرداختی سفارش.",
            "promo_code": "کد تخفیف استفاده شده.",
            "stripe_payment_intent_id": "شناسه تراکنش در درگاه پرداخت.",
            "quote_request": "درخواست قیمت مرجع برای این سفارش (در صورت وجود).",
        }
        labels = {
            "user": "کاربر",
            "email": "ایمیل",
            "status": "وضعیت سفارش",
            "fulfillment": "نحوه تحویل",
            "shipping_address": "آدرس ارسال",
            "subtotal": "جمع اقلام",
            "discount": "میزان تخفیف",
            "delivery_fee": "هزینه ارسال",
            "tax": "مالیات",
            "total": "مبلغ نهایی پرداخت",
            "promo_code": "کد تخفیف",
            "stripe_payment_intent_id": "شناسه پرداخت درگاه",
            "quote_request": "درخواست قیمت مرجع",
        }


class OrderItemInlineForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = "__all__"
        help_texts = {
            "product": "محصول سفارش داده شده.",
            "name": "نام محصول در زمان ثبت سفارش.",
            "sku": "شناسه انبار محصول در زمان ثبت سفارش.",
            "unit_price": "قیمت واحد در زمان ثبت سفارش.",
            "quantity": "تعداد کالا.",
            "line_total": "مبلغ کل برای این قلم کالا.",
        }
        labels = {
            "product": "محصول",
            "name": "نام کالا",
            "sku": "شناسه SKU",
            "unit_price": "قیمت واحد",
            "quantity": "تعداد",
            "line_total": "جمع سطر",
        }


class QuoteRequestAdminForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = "__all__"
        help_texts = {
            "product": "محصولی که برای آن درخواست قیمت ثبت شده است.",
            "user": "کاربری که درخواست قیمت را ثبت کرده است.",
            "quantity": "تعداد درخواستی.",
            "contact_phone": "شماره تلفن تماس مشتری.",
            "message": "پیام یا توضیح مشتری همراه با درخواست.",
            "status": "وضعیت درخواست قیمت (جدید، تماس گرفته شده، قیمت‌گذاری شده، تأیید شده، بسته شده).",
            "agreed_price": "قیمت توافق شده نهایی برای فروش (جهت تأیید درخواست).",
        }
        labels = {
            "product": "محصول",
            "user": "کاربر (مشتری)",
            "quantity": "تعداد",
            "contact_phone": "تلفن تماس",
            "message": "پیام مشتری",
            "status": "وضعیت درخواست",
            "agreed_price": "قیمت توافق شده",
        }


class BankAccountAdminForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = "__all__"
        help_texts = {
            "bank_name": "نام بانک (مثال: بانک ملی، بانک ملت).",
            "card_number": "شماره کارت ۱۶ رقمی (بدون خط تیره).",
            "sheba_number": "شماره شبا (با فرمت IR و بدون خط تیره، ۲۶ کاراکتر).",
            "holder_name": "نام و نام خانوادگی صاحب حساب.",
            "is_active": "فعال یا غیرفعال بودن این حساب جهت دریافت واریزی مشتریان.",
        }
        labels = {
            "bank_name": "نام بانک",
            "card_number": "شماره کارت",
            "sheba_number": "شماره شبا",
            "holder_name": "نام صاحب حساب",
            "is_active": "فعال",
        }


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"
        help_texts = {
            "order": "سفارش مربوط به این پرداخت.",
            "receipt_image": "تصویر فیش یا رسید پرداخت واریز شده.",
            "reference_number": "شماره پیگیری یا کد رهگیری تراکنش بانکی.",
            "verification_status": "وضعیت تایید رسید توسط مدیریت (در انتظار، تایید شده، رد شده).",
            "verified_by": "کاربر مدیری که رسید را بررسی و تایید/رد کرده است.",
            "verified_at": "زمان بررسی و تایید/رد رسید پرداخت.",
        }
        labels = {
            "order": "سفارش",
            "receipt_image": "تصویر رسید",
            "reference_number": "شماره پیگیری",
            "verification_status": "وضعیت تایید",
            "verified_by": "تایید شده توسط",
            "verified_at": "تاریخ تایید",
        }


# --- Django Unfold Admin Configurations ---

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    form = CategoryAdminForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("name", "slug", "parent", "order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")


class ProductImageInline(TabularInline):
    model = ProductImage
    form = ProductImageInlineForm
    extra = 1
    readonly_fields = ("image_preview",)
    fields = ("image", "url", "image_preview", "alt", "order", "is_primary")

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; object-fit: contain; border-radius: 6px; border: 1px solid #ddd;" />',
                obj.image.url,
            )
        elif obj.url:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; object-fit: contain; border-radius: 6px; border: 1px solid #ddd;" />',
                obj.url,
            )
        return "بدون تصویر"

    image_preview.short_description = "پیش‌نمایش تصویر"


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    form = ProductAdminForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = (
        "name",
        "sku",
        "category",
        "brand",
        "price",
        "compare_at_price",
        "stock",
        "stock_status_display",
        "pricing_mode",
        "type",
        "condition",
        "is_active",
        "is_featured",
        "created_at",
    )
    list_filter = ("is_active", "is_featured", "category", "brand", "pricing_mode", "type", "condition")
    search_fields = ("name", "sku", "slug", "brand")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [ProductImageInline]

    @admin.display(description="وضعیت موجودی")
    def stock_status_display(self, obj):
        status = obj.stock_status
        if status == "out-of-stock":
            return "ناموجود"
        elif status == "low-stock":
            return "موجودی اندک"
        return "موجود"


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    form = ReviewAdminForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("product", "user", "rating", "title", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__username", "title", "body")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    form = AddressAdminForm
    compressed_fields = True
    warn_unsaved_form = True
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


@admin.register(QuoteRequest)
class QuoteRequestAdmin(ModelAdmin):
    form = QuoteRequestAdminForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = (
        "id",
        "product",
        "user",
        "quantity",
        "contact_phone",
        "status",
        "agreed_price",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "id",
        "product__name",
        "user__username",
        "user__email",
        "contact_phone",
        "message",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    actions = ["approve_quotes"]

    @action(description="تأیید درخواست‌های انتخاب شده (نیازمند قیمت توافقی)", icon="check_circle")
    def approve_quotes(self, request, queryset):
        count = 0
        for quote in queryset:
            if quote.status != "approved" and quote.agreed_price is not None:
                quote.status = "approved"
                quote.save()
                count += 1
        self.message_user(
            request, f"تعداد {count} درخواست قیمت با موفقیت تأیید و سفارش پیش‌پرداخت ایجاد شد."
        )


class OrderItemInline(TabularInline):
    model = OrderItem
    form = OrderItemInlineForm
    extra = 0
    readonly_fields = ("product", "name", "sku", "unit_price", "quantity", "line_total")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(TabularInline):
    model = Payment
    form = PaymentAdminForm
    extra = 0
    fields = ("receipt_image", "image_preview", "reference_number", "verification_status", "verified_by", "verified_at")
    readonly_fields = ("image_preview", "verified_by", "verified_at")

    def image_preview(self, obj):
        if obj.receipt_image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px; object-fit: contain; border-radius: 6px; border: 1px solid #ddd;" />',
                obj.receipt_image.url,
            )
        return "بدون تصویر"

    image_preview.short_description = "پیش‌نمایش رسید"


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    form = OrderAdminForm
    compressed_fields = True
    warn_unsaved_form = True
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
    readonly_fields = ("number", "quote_request", "created_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [OrderItemInline, PaymentInline]
    actions = [
        "mark_paid",
        "mark_preparing",
        "mark_shipped",
        "mark_delivered",
        "mark_cancelled",
    ]

    @action(description="تغییر وضعیت به پرداخت شده", icon="check_circle")
    def mark_paid(self, request, queryset):
        count = 0
        from django.core.exceptions import ValidationError
        for order in queryset:
            try:
                order.status = "paid"
                order.save()
                count += 1
            except ValidationError as e:
                self.message_user(request, f"خطا در سفارش {order.number}: {e.message}", level="ERROR")
        if count:
            self.message_user(request, f"تعداد {count} سفارش با موفقیت به وضعیت پرداخت شده تغییر یافت.")

    @action(description="تغییر وضعیت به در حال آماده‌سازی", icon="build")
    def mark_preparing(self, request, queryset):
        queryset.update(status="preparing")

    @action(description="تغییر وضعیت به ارسال شده", icon="local_shipping")
    def mark_shipped(self, request, queryset):
        queryset.update(status="shipped")

    @action(description="تغییر وضعیت به تحویل داده شده", icon="task_alt")
    def mark_delivered(self, request, queryset):
        queryset.update(status="delivered")

    @action(description="تغییر وضعیت به لغو شده", icon="cancel")
    def mark_cancelled(self, request, queryset):
        queryset.update(status="cancelled")


@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    form = BankAccountAdminForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("bank_name", "holder_name", "card_number", "sheba_number", "is_active")
    list_filter = ("is_active",)
    search_fields = ("bank_name", "holder_name", "card_number", "sheba_number")
    ordering = ("bank_name", "id")


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    form = PaymentAdminForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = (
        "id",
        "order",
        "reference_number",
        "verification_status",
        "receipt_preview",
        "verified_by",
        "verified_at",
        "created_at",
    )
    list_filter = ("verification_status", "created_at")
    search_fields = ("order__number", "reference_number", "order__user__username")
    readonly_fields = ("verified_by", "verified_at", "created_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["approve_payments", "reject_payments"]

    def receipt_preview(self, obj):
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 50px; max-width: 50px; object-fit: contain; border-radius: 4px; border: 1px solid #ddd;" /></a>',
                obj.receipt_image.url,
                obj.receipt_image.url,
            )
        return "بدون تصویر"
    receipt_preview.short_description = "پیش‌نمایش رسید"

    @action(description="تأیید پرداخت‌های انتخاب شده و ثبت سفارش به عنوان پرداخت‌شده", icon="check_circle")
    def approve_payments(self, request, queryset):
        from django.utils import timezone
        from django.db import transaction
        from api.models import Notification
        
        count = 0
        for payment in queryset:
            if payment.verification_status != "approved":
                with transaction.atomic():
                    payment.verification_status = "approved"
                    payment.verified_by = request.user
                    payment.verified_at = timezone.now()
                    payment.save()
                    
                    order = payment.order
                    order.status = "paid"
                    order.save()
                    
                    if order.user:
                        Notification.objects.create(
                            user=order.user,
                            title="رسید پرداخت تایید شد",
                            message=f"پرداخت سفارش {order.number} تایید شد و سفارش در حال آماده‌سازی است.",
                            link=f"/orders/{order.id}",
                        )
                count += 1
        self.message_user(
            request, f"تعداد {count} پرداخت با موفقیت تایید شد و وضعیت سفارش‌های مربوطه به 'پرداخت شده' تغییر یافت."
        )

    @action(description="رد پرداخت‌های انتخاب شده و ثبت سفارش به عنوان ناموفق", icon="cancel")
    def reject_payments(self, request, queryset):
        from django.utils import timezone
        from django.db import transaction
        from api.models import Notification
        
        count = 0
        for payment in queryset:
            if payment.verification_status != "rejected":
                with transaction.atomic():
                    payment.verification_status = "rejected"
                    payment.verified_by = request.user
                    payment.verified_at = timezone.now()
                    payment.save()
                    
                    order = payment.order
                    order.status = "failed"
                    order.save()
                    
                    if order.user:
                        Notification.objects.create(
                            user=order.user,
                            title="رسید پرداخت رد شد",
                            message=f"پرداخت سفارش {order.number} رد شد. لطفا رسید جدیدی آپلود نمایید.",
                            link=f"/orders/{order.id}",
                        )
                count += 1
        self.message_user(
            request, f"تعداد {count} پرداخت رد شد و وضعیت سفارش‌های مربوطه به 'ناموفق' تغییر یافت."
        )
