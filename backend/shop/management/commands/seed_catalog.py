from django.core.management.base import BaseCommand
from shop.models import Category, Product

# Full nested Persian category taxonomy (Niavaran)
TAXONOMY = [
    {
        "name": "کامپیوتر",
        "slug": "computers",
        "order": 0,
        "children": [
            {"name": "مانیتور", "slug": "monitors", "order": 0},
            {"name": "مادربورد", "slug": "motherboards", "order": 1},
            {"name": "CPU", "slug": "cpu", "order": 2},
            {"name": "RAM", "slug": "ram", "order": 3},
            {"name": "کارت گرافیک", "slug": "gpu", "order": 4},
            {"name": "هارد اینترنال/اکسترنال", "slug": "hard-drives", "order": 5},
            {"name": "SSD", "slug": "ssd", "order": 6},
            {"name": "درایو نوری", "slug": "optical-drives", "order": 7},
            {"name": "پاور", "slug": "power-supplies", "order": 8},
            {"name": "کیس", "slug": "pc-cases", "order": 9},
            {"name": "فن CPU/کیس", "slug": "fans", "order": 10},
            {"name": "کارت صدا", "slug": "sound-cards", "order": 11},
        ],
    },
    {
        "name": "لپ‌تاپ",
        "slug": "laptops",
        "order": 1,
        "children": [
            {"name": "لپ‌تاپ", "slug": "laptop-devices", "order": 0},
            {"name": "کیف", "slug": "laptop-bags", "order": 1},
            {"name": "آداپتور", "slug": "laptop-adapters", "order": 2},
            {"name": "فن زیرلپ‌تاپ", "slug": "cooling-pads", "order": 3},
        ],
    },
    {
        "name": "لوازم جانبی موبایل و تبلت",
        "slug": "mobile-accessories",
        "order": 2,
        "children": [
            {"name": "شارژر", "slug": "mobile-chargers", "order": 0},
            {"name": "کابل", "slug": "mobile-cables", "order": 1},
            {"name": "محافظ صفحه", "slug": "screen-protectors", "order": 2},
            {"name": "قاب", "slug": "mobile-cases", "order": 3},
            {"name": "هندزفری/هدست", "slug": "mobile-headsets", "order": 4},
            {"name": "پاوربانک", "slug": "powerbanks", "order": 5},
            {"name": "پایه", "slug": "mobile-stands", "order": 6},
            {"name": "شارژر فندکی", "slug": "car-chargers", "order": 7},
            {"name": "کابل/مبدل", "slug": "mobile-adapters", "order": 8},
            {"name": "اسپیکر همراه", "slug": "portable-speakers", "order": 9},
            {"name": "ساعت هوشمند", "slug": "smartwatches", "order": 10},
        ],
    },
    {
        "name": "تجهیزات جانبی کامپیوتر",
        "slug": "peripherals",
        "order": 3,
        "children": [
            {"name": "موس/کیبورد/پد", "slug": "mice-keyboards", "order": 0},
            {"name": "میکروفن", "slug": "microphones", "order": 1},
            {"name": "وب‌کم", "slug": "webcams", "order": 2},
            {"name": "اسپیکر", "slug": "speakers", "order": 3},
            {"name": "فلش", "slug": "flash-drives", "order": 4},
            {"name": "رم‌ریدر", "slug": "card-readers", "order": 5},
            {"name": "کارت حافظه", "slug": "memory-cards", "order": 6},
            {"name": "کیف/باکس هارد", "slug": "hd-cases", "order": 7},
            {"name": "هاب USB", "slug": "usb-hubs", "order": 8},
            {"name": "بلوتوث", "slug": "bluetooth-adapters", "order": 9},
            {"name": "هدفون/هدست", "slug": "headphones", "order": 10},
        ],
    },
    {
        "name": "تجهیزات شبکه",
        "slug": "networking",
        "order": 4,
        "children": [
            {"name": "مودم/روتر", "slug": "modems-routers", "order": 0},
            {"name": "اکسس‌پوینت", "slug": "access-points", "order": 1},
            {"name": "رنج‌اکستندر", "slug": "range-extenders", "order": 2},
            {"name": "مودم 4G", "slug": "4g-modems", "order": 3},
            {"name": "کارت شبکه", "slug": "network-cards", "order": 4},
            {"name": "سوئیچ/هاب", "slug": "network-switches", "order": 5},
            {"name": "کابل شبکه", "slug": "network-cables", "order": 6},
            {"name": "اسپلیتر", "slug": "splitters", "order": 7},
            {"name": "کیستون", "slug": "keystones", "order": 8},
            {"name": "سوکت", "slug": "network-sockets", "order": 9},
            {"name": "کابل/سوکت تلفن", "slug": "phone-cables", "order": 10},
        ],
    },
    {
        "name": "فروش ویژه",
        "slug": "special-sale",
        "order": 5,
        "children": [],
    },
    {
        "name": "خدمات",
        "slug": "services",
        "order": 6,
        "children": [
            {"name": "نصب سیستم‌عامل", "slug": "os-installation", "order": 0},
            {"name": "آنتی‌ویروس", "slug": "antivirus", "order": 1},
            {"name": "خدمات نرم‌افزاری موبایل", "slug": "mobile-software-services", "order": 2},
            {"name": "ساخت ایمیل/اپل‌آیدی", "slug": "apple-id-creation", "order": 3},
            {"name": "نرم‌افزار تخصصی", "slug": "specialized-software", "order": 4},
            {"name": "ارسال پیامک", "slug": "sms-services", "order": 5},
            {"name": "سیستم گیمینگ/رندر", "slug": "custom-pc-assembly", "order": 6},
            {"name": "طراحی سایت", "slug": "web-design", "order": 7},
        ],
    },
    {
        "name": "ماشین‌های اداری",
        "slug": "office-machines",
        "order": 7,
        "children": [
            {"name": "پرینتر", "slug": "printers", "order": 0},
            {"name": "کارتریج", "slug": "cartridges", "order": 1},
        ],
    },
    {
        "name": "تجهیزات کارکرده (موبایل و تبلت)",
        "slug": "used-mobile-tablet",
        "order": 8,
        "children": [],
    },
    {
        "name": "دوربین مدار بسته",
        "slug": "cctv",
        "order": 9,
        "children": [],
    },
    {
        "name": "دزدگیر",
        "slug": "alarms",
        "order": 10,
        "children": [],
    },
]

PRODUCTS = [
    {"slug": "macbook-air-13-m3", "name": 'MacBook Air 13" M3', "spec": "8-core · 16GB · 512GB", "category": "laptop-devices", "brand": "Apple", "ram": 16, "storage": 512, "price": "1199.00", "compare_at_price": "1299.00", "stock": 40, "is_featured": True, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "asus-rog-strix-g16", "name": "ASUS ROG Strix G16", "spec": "RTX 4060 · i7 · 16GB", "category": "laptop-devices", "brand": "ASUS", "ram": 16, "storage": 512, "price": "1349.00", "compare_at_price": None, "stock": 4, "is_featured": True, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "nvidia-rtx-4070-ti", "name": "NVIDIA RTX 4070 Ti", "spec": "12GB GDDR6X · triple fan", "category": "gpu", "brand": "NVIDIA", "ram": None, "storage": None, "price": "799.00", "compare_at_price": "869.00", "stock": 25, "is_featured": True, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "dell-ultrasharp-27-4k", "name": 'Dell UltraSharp 27" 4K', "spec": "IPS · USB-C · 60Hz", "category": "monitors", "brand": "Dell", "ram": None, "storage": None, "price": "549.00", "compare_at_price": None, "stock": 0, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "aurora-ryzen-7-gaming-pc", "name": "Aurora Ryzen 7 Gaming PC", "spec": "RTX 4070 · 32GB · 1TB", "category": "computers", "brand": "Aurora", "ram": 32, "storage": 1024, "price": "1499.00", "compare_at_price": "1699.00", "stock": 3, "is_featured": True, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "samsung-990-pro-2tb", "name": "Samsung 990 Pro 2TB NVMe", "spec": "PCIe 4.0 · 7450MB/s", "category": "ssd", "brand": "Samsung", "ram": None, "storage": 2048, "price": "169.00", "compare_at_price": "199.00", "stock": 60, "is_featured": True, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "logitech-mx-keys-s-combo", "name": "Logitech MX Keys S Combo", "spec": "Keyboard + MX Master 3S", "category": "mice-keyboards", "brand": "Logitech", "ram": None, "storage": None, "price": "199.00", "compare_at_price": None, "stock": 30, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "corsair-vengeance-32gb-ddr5", "name": "Corsair Vengeance 32GB DDR5", "spec": "6000MHz · CL30 · RGB", "category": "ram", "brand": "Corsair", "ram": 32, "storage": None, "price": "114.00", "compare_at_price": "139.00", "stock": 50, "is_featured": True, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "macbook-pro-14-m3-pro", "name": 'MacBook Pro 14" M3 Pro', "spec": "11-core · 18GB · 1TB", "category": "laptop-devices", "brand": "Apple", "ram": 16, "storage": 1024, "price": "1999.00", "compare_at_price": None, "stock": 18, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "asus-zenbook-14-oled", "name": "ASUS Zenbook 14 OLED", "spec": "Ryzen 7 · 16GB · 1TB", "category": "laptop-devices", "brand": "ASUS", "ram": 16, "storage": 1024, "price": "1049.00", "compare_at_price": "1199.00", "stock": 4, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "dell-xps-15", "name": "Dell XPS 15", "spec": "i7 · 16GB · 512GB · RTX", "category": "laptop-devices", "brand": "Dell", "ram": 16, "storage": 512, "price": "1699.00", "compare_at_price": None, "stock": 22, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "lenovo-thinkpad-x1-carbon", "name": "Lenovo ThinkPad X1 Carbon", "spec": "i7 · 16GB · 1TB", "category": "laptop-devices", "brand": "Lenovo", "ram": 16, "storage": 1024, "price": "1549.00", "compare_at_price": "1749.00", "stock": 15, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "asus-rog-zephyrus-g14", "name": "ASUS ROG Zephyrus G14", "spec": "RTX 4060 · Ryzen 9 · 16GB", "category": "laptop-devices", "brand": "ASUS", "ram": 16, "storage": 512, "price": "1599.00", "compare_at_price": None, "stock": 5, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "hp-spectre-x360-14", "name": "HP Spectre x360 14", "spec": "i7 · 16GB · 1TB · 2-in-1", "category": "laptop-devices", "brand": "HP", "ram": 16, "storage": 1024, "price": "1299.00", "compare_at_price": "1449.00", "stock": 27, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "msi-prestige-16-studio", "name": "MSI Prestige 16 Studio", "spec": "i7 · 32GB · RTX 4050", "category": "laptop-devices", "brand": "MSI", "ram": 32, "storage": 512, "price": "1399.00", "compare_at_price": None, "stock": 0, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "macbook-air-15-m3", "name": 'MacBook Air 15" M3', "spec": "8-core · 16GB · 512GB", "category": "laptop-devices", "brand": "Apple", "ram": 16, "storage": 512, "price": "1499.00", "compare_at_price": None, "stock": 33, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "razer-blade-14", "name": "Razer Blade 14", "spec": "RTX 4070 · Ryzen 9 · 32GB", "category": "laptop-devices", "brand": "Razer", "ram": 32, "storage": 2048, "price": "2199.00", "compare_at_price": "2399.00", "stock": 5, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "acer-swift-go-14", "name": "Acer Swift Go 14", "spec": "i5 · 8GB · 256GB", "category": "laptop-devices", "brand": "Acer", "ram": 8, "storage": 256, "price": "799.00", "compare_at_price": None, "stock": 41, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},
    {"slug": "lenovo-legion-slim-5", "name": "Lenovo Legion Slim 5", "spec": "RTX 4060 · Ryzen 7 · 16GB", "category": "laptop-devices", "brand": "Lenovo", "ram": 16, "storage": 512, "price": "1249.00", "compare_at_price": "1399.00", "stock": 19, "is_featured": False, "pricing_mode": "fixed", "type": "physical", "condition": "new"},

    # Services (set to on_request)
    {"slug": "os-installation-service", "name": "نصب سیستم‌عامل (ویندوز/مک)", "spec": "نصب انواع ویندوز و مکینتاش همراه با درایورها و نرم‌افزارهای کاربردی", "category": "os-installation", "brand": "Niavaran", "ram": None, "storage": None, "price": None, "compare_at_price": None, "stock": 9999, "is_featured": True, "pricing_mode": "on_request", "type": "service", "condition": "new"},
    {"slug": "web-design-service", "name": "طراحی سایت اختصاصی", "spec": "طراحی انواع سایت‌های فروشگاهی، شرکتی و شخصی با سئو اولیه", "category": "web-design", "brand": "Niavaran", "ram": None, "storage": None, "price": None, "compare_at_price": None, "stock": 9999, "is_featured": True, "pricing_mode": "on_request", "type": "service", "condition": "new"},
    {"slug": "custom-pc-assembly-service", "name": "اسمبل سیستم‌های گیمینگ و رندرینگ", "spec": "مشاوره تخصصی، قطعه‌شناسی و اسمبل حرفه‌ای سیستم‌های رندرینگ و بازی", "category": "custom-pc-assembly", "brand": "Niavaran", "ram": None, "storage": None, "price": None, "compare_at_price": None, "stock": 9999, "is_featured": False, "pricing_mode": "on_request", "type": "service", "condition": "new"},
    {"slug": "antivirus-installation-service", "name": "نصب و فعال‌سازی آنتی‌ویروس", "spec": "نصب آنتی‌ویروس اورجینال با لایسنس یک‌ساله معتبر", "category": "antivirus", "brand": "ESET", "ram": None, "storage": None, "price": None, "compare_at_price": None, "stock": 9999, "is_featured": False, "pricing_mode": "on_request", "type": "service", "condition": "new"},
]


class Command(BaseCommand):
    help = "Seed nested categories and products mirroring the frontend placeholder catalog."

    def handle(self, *args, **options):
        categories_by_slug = {}
        total_cats = 0

        for parent_data in TAXONOMY:
            parent_category, created = Category.objects.update_or_create(
                slug=parent_data["slug"],
                defaults={
                    "name": parent_data["name"],
                    "order": parent_data["order"],
                    "parent": None,
                    "is_active": True,
                },
            )
            categories_by_slug[parent_data["slug"]] = parent_category
            total_cats += 1
            self.stdout.write(
                f"{'Created' if created else 'Updated'} parent category: {parent_category.name}"
            )

            for child_data in parent_data.get("children", []):
                child_category, created = Category.objects.update_or_create(
                    slug=child_data["slug"],
                    defaults={
                        "name": child_data["name"],
                        "order": child_data["order"],
                        "parent": parent_category,
                        "is_active": True,
                    },
                )
                categories_by_slug[child_data["slug"]] = child_category
                total_cats += 1
                self.stdout.write(
                    f"  - {'Created' if created else 'Updated'} child category: {child_category.name}"
                )

        for entry in PRODUCTS:
            sku = "DT-" + entry["slug"].upper().replace("-", "")[:20]
            specs = {"spec": entry["spec"]}
            if entry["ram"] is not None:
                specs["ram_gb"] = entry["ram"]
            if entry["storage"] is not None:
                specs["storage_gb"] = entry["storage"]

            product, created = Product.objects.update_or_create(
                slug=entry["slug"],
                defaults={
                    "name": entry["name"],
                    "category": categories_by_slug[entry["category"]],
                    "brand": entry["brand"],
                    "price": entry["price"],
                    "compare_at_price": entry["compare_at_price"],
                    "sku": sku,
                    "stock": entry["stock"],
                    "is_active": True,
                    "is_featured": entry["is_featured"],
                    "specs": specs,
                    "pricing_mode": entry.get("pricing_mode", "fixed"),
                    "type": entry.get("type", "physical"),
                    "condition": entry.get("condition", "new"),
                },
            )
            self.stdout.write(
                f"{'Created' if created else 'Updated'} product: {product.name} ({product.pricing_mode})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {total_cats} categories and {len(PRODUCTS)} products."
            )
        )
