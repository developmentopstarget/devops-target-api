from django.core.management.base import BaseCommand

from shop.models import Category, Product

CATEGORIES = [
    {"slug": "laptops", "name": "Laptops", "order": 0},
    {"slug": "desktops-pcs", "name": "Desktops & PCs", "order": 1},
    {"slug": "components", "name": "Components", "order": 2},
    {"slug": "monitors", "name": "Monitors", "order": 3},
    {"slug": "peripherals", "name": "Peripherals", "order": 4},
    {"slug": "networking", "name": "Networking", "order": 5},
]

# Mirrors devops-target-web's src/data/products.ts placeholder catalog
# (dealsOfTheWeek + additionalCatalogProducts) so integration data matches.
PRODUCTS = [
    {"slug": "macbook-air-13-m3", "name": 'MacBook Air 13" M3', "spec": "8-core · 16GB · 512GB", "category": "laptops", "brand": "Apple", "ram": 16, "storage": 512, "price": "1199.00", "compare_at_price": "1299.00", "stock": 40, "is_featured": True},
    {"slug": "asus-rog-strix-g16", "name": "ASUS ROG Strix G16", "spec": "RTX 4060 · i7 · 16GB", "category": "laptops", "brand": "ASUS", "ram": 16, "storage": 512, "price": "1349.00", "compare_at_price": None, "stock": 4, "is_featured": True},
    {"slug": "nvidia-rtx-4070-ti", "name": "NVIDIA RTX 4070 Ti", "spec": "12GB GDDR6X · triple fan", "category": "components", "brand": "NVIDIA", "ram": None, "storage": None, "price": "799.00", "compare_at_price": "869.00", "stock": 25, "is_featured": True},
    {"slug": "dell-ultrasharp-27-4k", "name": 'Dell UltraSharp 27" 4K', "spec": "IPS · USB-C · 60Hz", "category": "monitors", "brand": "Dell", "ram": None, "storage": None, "price": "549.00", "compare_at_price": None, "stock": 0, "is_featured": False},
    {"slug": "aurora-ryzen-7-gaming-pc", "name": "Aurora Ryzen 7 Gaming PC", "spec": "RTX 4070 · 32GB · 1TB", "category": "desktops-pcs", "brand": "Aurora", "ram": 32, "storage": 1024, "price": "1499.00", "compare_at_price": "1699.00", "stock": 3, "is_featured": True},
    {"slug": "samsung-990-pro-2tb", "name": "Samsung 990 Pro 2TB NVMe", "spec": "PCIe 4.0 · 7450MB/s", "category": "components", "brand": "Samsung", "ram": None, "storage": 2048, "price": "169.00", "compare_at_price": "199.00", "stock": 60, "is_featured": True},
    {"slug": "logitech-mx-keys-s-combo", "name": "Logitech MX Keys S Combo", "spec": "Keyboard + MX Master 3S", "category": "peripherals", "brand": "Logitech", "ram": None, "storage": None, "price": "199.00", "compare_at_price": None, "stock": 30, "is_featured": False},
    {"slug": "corsair-vengeance-32gb-ddr5", "name": "Corsair Vengeance 32GB DDR5", "spec": "6000MHz · CL30 · RGB", "category": "components", "brand": "Corsair", "ram": 32, "storage": None, "price": "114.00", "compare_at_price": "139.00", "stock": 50, "is_featured": True},
    {"slug": "macbook-pro-14-m3-pro", "name": 'MacBook Pro 14" M3 Pro', "spec": "11-core · 18GB · 1TB", "category": "laptops", "brand": "Apple", "ram": 16, "storage": 1024, "price": "1999.00", "compare_at_price": None, "stock": 18, "is_featured": False},
    {"slug": "asus-zenbook-14-oled", "name": "ASUS Zenbook 14 OLED", "spec": "Ryzen 7 · 16GB · 1TB", "category": "laptops", "brand": "ASUS", "ram": 16, "storage": 1024, "price": "1049.00", "compare_at_price": "1199.00", "stock": 4, "is_featured": False},
    {"slug": "dell-xps-15", "name": "Dell XPS 15", "spec": "i7 · 16GB · 512GB · RTX", "category": "laptops", "brand": "Dell", "ram": 16, "storage": 512, "price": "1699.00", "compare_at_price": None, "stock": 22, "is_featured": False},
    {"slug": "lenovo-thinkpad-x1-carbon", "name": "Lenovo ThinkPad X1 Carbon", "spec": "i7 · 16GB · 1TB", "category": "laptops", "brand": "Lenovo", "ram": 16, "storage": 1024, "price": "1549.00", "compare_at_price": "1749.00", "stock": 15, "is_featured": False},
    {"slug": "asus-rog-zephyrus-g14", "name": "ASUS ROG Zephyrus G14", "spec": "RTX 4060 · Ryzen 9 · 16GB", "category": "laptops", "brand": "ASUS", "ram": 16, "storage": 512, "price": "1599.00", "compare_at_price": None, "stock": 5, "is_featured": False},
    {"slug": "hp-spectre-x360-14", "name": "HP Spectre x360 14", "spec": "i7 · 16GB · 1TB · 2-in-1", "category": "laptops", "brand": "HP", "ram": 16, "storage": 1024, "price": "1299.00", "compare_at_price": "1449.00", "stock": 27, "is_featured": False},
    {"slug": "msi-prestige-16-studio", "name": "MSI Prestige 16 Studio", "spec": "i7 · 32GB · RTX 4050", "category": "laptops", "brand": "MSI", "ram": 32, "storage": 512, "price": "1399.00", "compare_at_price": None, "stock": 0, "is_featured": False},
    {"slug": "macbook-air-15-m3", "name": 'MacBook Air 15" M3', "spec": "8-core · 16GB · 512GB", "category": "laptops", "brand": "Apple", "ram": 16, "storage": 512, "price": "1499.00", "compare_at_price": None, "stock": 33, "is_featured": False},
    {"slug": "razer-blade-14", "name": "Razer Blade 14", "spec": "RTX 4070 · Ryzen 9 · 32GB", "category": "laptops", "brand": "Razer", "ram": 32, "storage": 2048, "price": "2199.00", "compare_at_price": "2399.00", "stock": 5, "is_featured": False},
    {"slug": "acer-swift-go-14", "name": "Acer Swift Go 14", "spec": "i5 · 8GB · 256GB", "category": "laptops", "brand": "Acer", "ram": 8, "storage": 256, "price": "799.00", "compare_at_price": None, "stock": 41, "is_featured": False},
    {"slug": "lenovo-legion-slim-5", "name": "Lenovo Legion Slim 5", "spec": "RTX 4060 · Ryzen 7 · 16GB", "category": "laptops", "brand": "Lenovo", "ram": 16, "storage": 512, "price": "1249.00", "compare_at_price": "1399.00", "stock": 19, "is_featured": False},
]


class Command(BaseCommand):
    help = "Seed categories and products mirroring the frontend placeholder catalog."

    def handle(self, *args, **options):
        categories_by_slug = {}
        for entry in CATEGORIES:
            category, created = Category.objects.update_or_create(
                slug=entry["slug"],
                defaults={"name": entry["name"], "order": entry["order"]},
            )
            categories_by_slug[entry["slug"]] = category
            self.stdout.write(
                f"{'Created' if created else 'Updated'} category: {category.name}"
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
                },
            )
            self.stdout.write(
                f"{'Created' if created else 'Updated'} product: {product.name}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} products."
            )
        )
