from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.models import Notification

from .models import Address, Category, Order, OrderItem, Product, ProductImage, Review, QuoteRequest, BankAccount, Payment

ORDER_PRICING_SETTINGS = {
    "TAX_RATE": 0.08,
    "DELIVERY_FEE": Decimal("9.99"),
    "FREE_DELIVERY_THRESHOLD": Decimal("99"),
}


def make_product(**kwargs):
    category = kwargs.pop("category", None) or Category.objects.get_or_create(
        slug="laptops", defaults={"name": "Laptops"}
    )[0]
    defaults = {
        "name": "Test Laptop",
        "slug": "test-laptop",
        "category": category,
        "brand": "Acme",
        "price": "999.00",
        "sku": "SKU-001",
        "stock": 10,
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


class CategoryModelTests(TestCase):
    def test_str_returns_name(self):
        category = Category.objects.create(name="Laptops", slug="laptops")
        self.assertEqual(str(category), "Laptops")

    def test_parent_child_relationship(self):
        parent = Category.objects.create(name="Components", slug="components")
        child = Category.objects.create(name="GPUs", slug="gpus", parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_slug_must_be_unique(self):
        Category.objects.create(name="Laptops", slug="laptops")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="Laptops Again", slug="laptops")


class ProductModelTests(TestCase):
    def test_str_returns_name(self):
        product = make_product(name="MacBook Air", slug="macbook-air")
        self.assertEqual(str(product), "MacBook Air")

    def test_sku_must_be_unique(self):
        make_product(slug="p1", sku="DUP-SKU")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_product(slug="p2", sku="DUP-SKU")

    def test_in_stock_true_when_stock_positive(self):
        product = make_product(stock=5)
        self.assertTrue(product.in_stock)

    def test_in_stock_false_when_stock_zero(self):
        product = make_product(stock=0)
        self.assertFalse(product.in_stock)

    def test_stock_status_out_of_stock(self):
        product = make_product(stock=0)
        self.assertEqual(product.stock_status, "out-of-stock")

    def test_stock_status_low_stock_at_threshold(self):
        product = make_product(stock=5)
        with self.settings(LOW_STOCK_THRESHOLD=5):
            self.assertEqual(product.stock_status, "low-stock")

    def test_stock_status_in_stock_above_threshold(self):
        product = make_product(stock=6)
        with self.settings(LOW_STOCK_THRESHOLD=5):
            self.assertEqual(product.stock_status, "in-stock")

    def test_aggregate_rating_none_without_reviews(self):
        product = make_product()
        self.assertIsNone(product.aggregate_rating)
        self.assertEqual(product.review_count, 0)

    def test_aggregate_rating_averages_reviews(self):
        product = make_product()
        user_a = User.objects.create_user(username="a", password="pass")
        user_b = User.objects.create_user(username="b", password="pass")
        Review.objects.create(product=product, user=user_a, rating=5)
        Review.objects.create(product=product, user=user_b, rating=3)

        self.assertEqual(product.aggregate_rating, 4.0)
        self.assertEqual(product.review_count, 2)

    def test_pricing_mode_defaults_and_nullable_price(self):
        # Verify defaults
        product = make_product(slug="default-prod", sku="SKU-DEF")
        self.assertEqual(product.pricing_mode, "fixed")
        self.assertEqual(product.type, "physical")
        self.assertEqual(product.condition, "new")
        self.assertIsNotNone(product.price)

        # Verify pricing mode choices and nullable price
        on_request_product = make_product(
            slug="on-req-prod",
            sku="SKU-ONREQ",
            pricing_mode="on_request",
            price=None,
            type="service",
            condition="new"
        )
        self.assertEqual(on_request_product.pricing_mode, "on_request")
        self.assertIsNone(on_request_product.price)
        self.assertEqual(on_request_product.type, "service")


class ProductImageModelTests(TestCase):
    def test_str_includes_product_name_and_order(self):
        product = make_product()
        image = ProductImage.objects.create(product=product, url="https://example.com/a.jpg", order=1)
        self.assertIn(product.name, str(image))


class ReviewModelTests(TestCase):
    def test_str_includes_rating_and_user(self):
        product = make_product()
        user = User.objects.create_user(username="reviewer", password="pass")
        review = Review.objects.create(product=product, user=user, rating=4)
        self.assertIn("4", str(review))
        self.assertIn("reviewer", str(review))

    def test_unique_review_per_user_and_product(self):
        product = make_product()
        user = User.objects.create_user(username="reviewer", password="pass")
        Review.objects.create(product=product, user=user, rating=4)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(product=product, user=user, rating=2)

    def test_same_user_can_review_different_products(self):
        product_a = make_product(slug="a", sku="SKU-A")
        product_b = make_product(slug="b", sku="SKU-B")
        user = User.objects.create_user(username="reviewer", password="pass")

        Review.objects.create(product=product_a, user=user, rating=4)
        Review.objects.create(product=product_b, user=user, rating=2)

        self.assertEqual(Review.objects.filter(user=user).count(), 2)


class ProductListEndpointTests(APITestCase):
    def setUp(self):
        self.laptops = Category.objects.create(name="Laptops", slug="laptops")
        self.monitors = Category.objects.create(name="Monitors", slug="monitors")

        self.p1 = make_product(
            name="Alpha Laptop",
            slug="alpha-laptop",
            sku="SKU-ALPHA",
            category=self.laptops,
            brand="Acme",
            price="1000.00",
            stock=10,
            specs={"ram_gb": 16, "storage_gb": 512},
        )
        self.p2 = make_product(
            name="Beta Laptop",
            slug="beta-laptop",
            sku="SKU-BETA",
            category=self.laptops,
            brand="Zenith",
            price="2000.00",
            stock=0,
            specs={"ram_gb": 32, "storage_gb": 1024},
        )
        self.p3 = make_product(
            name="Gamma Monitor",
            slug="gamma-monitor",
            sku="SKU-GAMMA",
            category=self.monitors,
            brand="Acme",
            price="500.00",
            stock=5,
            specs={},
        )
        self.inactive = make_product(
            name="Hidden Product",
            slug="hidden-product",
            sku="SKU-HIDDEN",
            category=self.monitors,
            price="10.00",
            is_active=False,
        )

        self.url = reverse("product-list")

    def test_list_returns_200_and_excludes_inactive(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"alpha-laptop", "beta-laptop", "gamma-monitor"})

    def test_filter_by_category(self):
        response = self.client.get(self.url, {"category": "monitors"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"gamma-monitor"})

    def test_filter_by_brand(self):
        response = self.client.get(self.url, {"brand": "Acme"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"alpha-laptop", "gamma-monitor"})

    def test_filter_by_ram(self):
        response = self.client.get(self.url, {"ram": "16"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"alpha-laptop"})

    def test_filter_by_storage(self):
        response = self.client.get(self.url, {"storage": "1024"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"beta-laptop"})

    def test_filter_by_price_range(self):
        response = self.client.get(self.url, {"priceMin": "600", "priceMax": "1500"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"alpha-laptop"})

    def test_filter_by_in_stock(self):
        response = self.client.get(self.url, {"inStock": "1"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"alpha-laptop", "gamma-monitor"})

    def test_filter_by_min_rating(self):
        user = User.objects.create_user(username="rater", password="pass")
        Review.objects.create(product=self.p1, user=user, rating=5)

        response = self.client.get(self.url, {"minRating": "4"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"alpha-laptop"})

    def test_search_matches_name(self):
        response = self.client.get(self.url, {"search": "Gamma"})

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"gamma-monitor"})

    def test_sort_price_asc(self):
        response = self.client.get(self.url, {"sort": "price_asc"})

        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(slugs, ["gamma-monitor", "alpha-laptop", "beta-laptop"])

    def test_sort_price_desc(self):
        response = self.client.get(self.url, {"sort": "price_desc"})

        slugs = [item["slug"] for item in response.data["results"]]
        self.assertEqual(slugs, ["beta-laptop", "alpha-laptop", "gamma-monitor"])

    def test_invalid_price_param_is_ignored_not_500(self):
        response = self.client.get(self.url, {"priceMin": "not-a-number"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pagination_page_size_is_12(self):
        for i in range(20):
            make_product(
                name=f"Filler {i}",
                slug=f"filler-{i}",
                sku=f"SKU-FILLER-{i}",
                category=self.laptops,
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 12)
        self.assertEqual(response.data["count"], 23)

    def test_list_response_does_not_leak_sku(self):
        response = self.client.get(self.url)
        for item in response.data["results"]:
            self.assertNotIn("sku", item)


class ProductDetailEndpointTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Laptops", slug="laptops")
        self.product = make_product(
            name="Alpha Laptop",
            slug="alpha-laptop",
            sku="SKU-ALPHA",
            category=self.category,
            description="A fine laptop.",
        )
        ProductImage.objects.create(
            product=self.product, url="https://example.com/a.jpg", order=0, is_primary=True
        )
        self.url = reverse("product-detail", args=["alpha-laptop"])

    def test_detail_returns_200_with_images_and_sku(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sku"], "SKU-ALPHA")
        self.assertEqual(len(response.data["images"]), 1)
        self.assertEqual(response.data["images"][0]["url"], "https://example.com/a.jpg")

    def test_detail_for_inactive_product_returns_404(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_for_missing_slug_returns_404(self):
        response = self.client.get(reverse("product-detail", args=["does-not-exist"]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryEndpointTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Laptops", slug="laptops")
        Category.objects.create(name="Hidden", slug="hidden", is_active=False)

    def test_list_returns_only_active_categories(self):
        response = self.client.get(reverse("category-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = {item["slug"] for item in response.data}
        self.assertEqual(slugs, {"laptops"})

    def test_detail_returns_200(self):
        response = self.client.get(reverse("category-detail", args=["laptops"]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Laptops")


class ProductReviewsEndpointTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Laptops", slug="laptops")
        self.product = make_product(
            name="Alpha Laptop", slug="alpha-laptop", sku="SKU-ALPHA", category=self.category
        )
        self.user = User.objects.create_user(username="reviewer", password="pass")
        self.token = Token.objects.create(user=self.user)
        self.url = reverse("product-reviews", args=["alpha-laptop"])

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_get_reviews_is_public(self):
        Review.objects.create(product=self.product, user=self.user, rating=5, title="Great")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Great")
        self.assertEqual(response.data[0]["user"], "reviewer")

    def test_post_review_requires_authentication(self):
        response = self.client.post(self.url, {"rating": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_review_creates_review(self):
        self.authenticate()

        response = self.client.post(
            self.url, {"rating": 4, "title": "Solid", "body": "Works well"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get()
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 4)

    def test_post_review_rejects_duplicate_from_same_user(self):
        self.authenticate()
        Review.objects.create(product=self.product, user=self.user, rating=3)

        response = self.client.post(self.url, {"rating": 5}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)

    def test_post_review_rejects_rating_out_of_range(self):
        self.authenticate()

        response = self.client.post(self.url, {"rating": 6}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


def make_address(**kwargs):
    defaults = {
        "full_name": "Ada Lovelace",
        "line1": "123 Main St",
        "city": "Springfield",
        "postal_code": "12345",
    }
    defaults.update(kwargs)
    return Address.objects.create(**defaults)


class AddressModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="addruser", password="pass")

    def test_str_includes_name_and_city(self):
        address = make_address(user=self.user)
        self.assertIn("Ada Lovelace", str(address))
        self.assertIn("Springfield", str(address))

    def test_setting_default_unsets_previous_default(self):
        first = make_address(user=self.user, is_default=True, line1="First St")
        second = make_address(user=self.user, is_default=True, line1="Second St")

        first.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

    def test_default_does_not_affect_other_users(self):
        other = User.objects.create_user(username="addrother", password="pass")
        mine = make_address(user=self.user, is_default=True)
        theirs = make_address(user=other, is_default=True)

        mine.refresh_from_db()
        theirs.refresh_from_db()
        self.assertTrue(mine.is_default)
        self.assertTrue(theirs.is_default)


class AddressViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="addrapi", password="pass")
        self.other = User.objects.create_user(username="addrapiother", password="pass")
        self.token = Token.objects.create(user=self.user)
        self.url = reverse("address-list")

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_unauthenticated_list_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_own_addresses(self):
        self.authenticate()
        make_address(user=self.user, label="Home")
        make_address(user=self.other, label="Theirs")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["label"], "Home")

    def test_create_assigns_owner_to_request_user(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "full_name": "Grace Hopper",
                "line1": "1 Compiler Way",
                "city": "Arlington",
                "postal_code": "22201",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        address = Address.objects.get(full_name="Grace Hopper")
        self.assertEqual(address.user, self.user)

    def test_cannot_read_other_users_address(self):
        self.authenticate()
        theirs = make_address(user=self.other)

        response = self.client.get(reverse("address-detail", args=[theirs.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_other_users_address(self):
        self.authenticate()
        theirs = make_address(user=self.other, full_name="Not Yours")

        response = self.client.patch(
            reverse("address-detail", args=[theirs.id]),
            {"full_name": "Hijacked"},
            format="json",
        )

        theirs.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(theirs.full_name, "Not Yours")

    def test_update_own_address(self):
        self.authenticate()
        mine = make_address(user=self.user, full_name="Old Name")

        response = self.client.patch(
            reverse("address-detail", args=[mine.id]),
            {"full_name": "New Name"},
            format="json",
        )

        mine.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mine.full_name, "New Name")

    def test_delete_own_address(self):
        self.authenticate()
        mine = make_address(user=self.user)

        response = self.client.delete(reverse("address-detail", args=[mine.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Address.objects.count(), 0)

    def test_setting_is_default_via_api_unsets_previous(self):
        self.authenticate()
        first = make_address(user=self.user, is_default=True, line1="First St")
        second = make_address(user=self.user, line1="Second St")

        response = self.client.patch(
            reverse("address-detail", args=[second.id]),
            {"is_default": True},
            format="json",
        )

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)


class OrderModelTests(TestCase):
    def test_str_returns_number(self):
        user = User.objects.create_user(username="orderowner", password="pass")
        order = Order.objects.create(
            user=user,
            email=user.email,
            fulfillment="pickup",
            subtotal="10.00",
            total="10.00",
        )
        self.assertEqual(str(order), order.number)

    def test_number_is_auto_generated_and_formatted(self):
        user = User.objects.create_user(username="orderowner2", password="pass")
        order = Order.objects.create(
            user=user,
            email=user.email,
            fulfillment="pickup",
            subtotal="10.00",
            total="10.00",
        )
        self.assertRegex(order.number, r"^DT-\d{6}$")


class OrderViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="orderapi", password="pass", email="orderapi@example.com"
        )
        self.other = User.objects.create_user(username="orderapiother", password="pass")
        self.token = Token.objects.create(user=self.user)
        self.list_url = reverse("order-list")

        self.category = Category.objects.create(name="Laptops", slug="laptops")
        self.product = make_product(
            name="Order Laptop",
            slug="order-laptop",
            sku="SKU-ORDER",
            category=self.category,
            price="100.00",
            stock=10,
        )

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_unauthenticated_list_returns_401(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_create_returns_401(self):
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_pickup_order_recomputes_totals_and_decrements_stock(self):
        self.authenticate()

        with self.settings(**ORDER_PRICING_SETTINGS):
            response = self.client.post(
                self.list_url,
                {
                    "fulfillment": "pickup",
                    "items": [{"product": "order-laptop", "quantity": 2}],
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal"], "200.00")
        self.assertEqual(response.data["discount"], "0.00")
        self.assertEqual(response.data["delivery_fee"], "0.00")
        self.assertEqual(response.data["tax"], "16.00")
        self.assertEqual(response.data["total"], "216.00")
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product"], "order-laptop")

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user, self.user)
        notification = Notification.objects.get(user=self.user)
        self.assertIn(order.number, notification.message)

    def test_delivery_order_requires_address_id(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {
                "fulfillment": "delivery",
                "items": [{"product": "order-laptop", "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("address_id", response.data)

    def test_delivery_order_rejects_other_users_address(self):
        self.authenticate()
        theirs = make_address(user=self.other)

        response = self.client.post(
            self.list_url,
            {
                "fulfillment": "delivery",
                "address_id": theirs.id,
                "items": [{"product": "order-laptop", "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("address_id", response.data)

    def test_delivery_order_below_free_threshold_charges_delivery_fee(self):
        self.authenticate()
        mine = make_address(user=self.user)
        cheap = make_product(
            name="Cheap Mouse", slug="cheap-mouse", sku="SKU-MOUSE", price="50.00", stock=5
        )

        with self.settings(**ORDER_PRICING_SETTINGS):
            response = self.client.post(
                self.list_url,
                {
                    "fulfillment": "delivery",
                    "address_id": mine.id,
                    "items": [{"product": "cheap-mouse", "quantity": 1}],
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal"], "50.00")
        self.assertEqual(response.data["delivery_fee"], "9.99")
        self.assertEqual(response.data["tax"], "4.00")
        self.assertEqual(response.data["total"], "63.99")
        self.assertEqual(response.data["shipping_address"]["full_name"], mine.full_name)

    def test_delivery_order_above_free_threshold_waives_delivery_fee(self):
        self.authenticate()
        mine = make_address(user=self.user)

        with self.settings(**ORDER_PRICING_SETTINGS):
            response = self.client.post(
                self.list_url,
                {
                    "fulfillment": "delivery",
                    "address_id": mine.id,
                    "items": [{"product": "order-laptop", "quantity": 2}],
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["delivery_fee"], "0.00")

    def test_insufficient_stock_rejected_and_stock_unchanged(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {
                "fulfillment": "pickup",
                "items": [{"product": "order-laptop", "quantity": 999}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(Order.objects.count(), 0)

    def test_unknown_product_rejected(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {
                "fulfillment": "pickup",
                "items": [{"product": "does-not-exist", "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_promo_code_rejected(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {
                "fulfillment": "pickup",
                "items": [{"product": "order-laptop", "quantity": 1}],
                "promo_code": "NOTREAL",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("promo_code", response.data)

    def test_valid_promo_code_applies_discount(self):
        self.authenticate()

        with self.settings(**ORDER_PRICING_SETTINGS):
            response = self.client.post(
                self.list_url,
                {
                    "fulfillment": "pickup",
                    "items": [{"product": "order-laptop", "quantity": 1}],
                    "promo_code": "spring10",
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal"], "100.00")
        self.assertEqual(response.data["discount"], "10.00")
        self.assertEqual(response.data["tax"], "7.20")
        self.assertEqual(response.data["total"], "97.20")
        self.assertEqual(response.data["promo_code"], "SPRING10")

    def test_list_returns_only_own_orders(self):
        self.authenticate()
        Order.objects.create(
            user=self.user, email=self.user.email, fulfillment="pickup",
            subtotal="10.00", total="10.00",
        )
        Order.objects.create(
            user=self.other, email=self.other.email, fulfillment="pickup",
            subtotal="20.00", total="20.00",
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_cannot_retrieve_other_users_order(self):
        self.authenticate()
        theirs = Order.objects.create(
            user=self.other, email=self.other.email, fulfillment="pickup",
            subtotal="20.00", total="20.00",
        )

        response = self.client.get(reverse("order-detail", args=[theirs.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_on_request_product_purchase_rejected(self):
        self.authenticate()
        on_req = make_product(
            name="Service Quote",
            slug="service-quote",
            sku="SKU-QUOTE",
            pricing_mode="on_request",
            price=None,
            category=self.category,
            stock=10
        )

        response = self.client.post(
            self.list_url,
            {
                "fulfillment": "pickup",
                "items": [{"product": "service-quote", "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)
        self.assertEqual(Order.objects.count(), 0)


class StripeCheckoutTests(APITestCase):
    def setUp(self):
        from unittest.mock import patch, MagicMock
        self.user = User.objects.create_user(
            username="stripeowner", password="pass", email="stripeowner@example.com"
        )
        self.other = User.objects.create_user(username="stripeother", password="pass")
        self.token = Token.objects.create(user=self.user)
        self.intent_url = reverse("checkout-intent")
        self.webhook_url = reverse("stripe-webhook")

        self.category = Category.objects.create(name="Accessories", slug="accessories")
        self.product = make_product(
            name="Stripe Mouse",
            slug="stripe-mouse",
            sku="SKU-STRIPE-MOUSE",
            category=self.category,
            price="50.00",
            stock=10,
        )

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    @patch("stripe.PaymentIntent.create")
    def test_create_payment_intent_success(self, mock_create):
        from unittest.mock import MagicMock
        self.authenticate()
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            fulfillment="pickup",
            subtotal="50.00",
            total="54.00",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            sku=self.product.sku,
            unit_price=self.product.price,
            quantity=1,
            line_total="50.00",
        )

        mock_intent = MagicMock()
        mock_intent.id = "pi_12345"
        mock_intent.client_secret = "pi_12345_secret_abc123"
        mock_create.return_value = mock_intent

        response = self.client.post(self.intent_url, {"order_id": order.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["client_secret"], "pi_12345_secret_abc123")
        self.assertEqual(response.data["stripe_payment_intent_id"], "pi_12345")

        order.refresh_from_db()
        self.assertEqual(order.stripe_payment_intent_id, "pi_12345")
        mock_create.assert_called_once_with(
            amount=5400,
            currency="usd",
            metadata={
                "order_id": order.id,
                "order_number": order.number,
                "user_id": self.user.id,
            }
        )

    def test_create_payment_intent_missing_order_id(self):
        self.authenticate()
        response = self.client.post(self.intent_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_payment_intent_not_found(self):
        self.authenticate()
        response = self.client.post(self.intent_url, {"order_id": 99999}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_payment_intent_other_users_order(self):
        self.authenticate()
        theirs = Order.objects.create(
            user=self.other,
            email=self.other.email,
            fulfillment="pickup",
            subtotal="50.00",
            total="54.00",
        )
        response = self.client.post(self.intent_url, {"order_id": theirs.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_payment_intent_already_paid(self):
        self.authenticate()
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            fulfillment="pickup",
            subtotal="50.00",
            total="54.00",
            status="paid",
        )
        response = self.client.post(self.intent_url, {"order_id": order.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("stripe.Webhook.construct_event")
    def test_webhook_payment_intent_succeeded(self, mock_construct):
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            fulfillment="pickup",
            subtotal="50.00",
            total="54.00",
            stripe_payment_intent_id="pi_123",
            status="pending_payment",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            sku=self.product.sku,
            unit_price=self.product.price,
            quantity=2,
            line_total="100.00",
        )
        self.product.stock = 8
        self.product.save()

        mock_construct.return_value = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_123"
                }
            }
        }

        response = self.client.post(
            self.webhook_url,
            data="raw_payload",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_sig"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "paid")

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        self.assertTrue(Notification.objects.filter(user=self.user, title="Order paid").exists())

    @patch("stripe.Webhook.construct_event")
    def test_webhook_payment_intent_failed_replenishes_stock(self, mock_construct):
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            fulfillment="pickup",
            subtotal="50.00",
            total="54.00",
            stripe_payment_intent_id="pi_123",
            status="pending_payment",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            sku=self.product.sku,
            unit_price=self.product.price,
            quantity=2,
            line_total="100.00",
        )
        self.product.stock = 8
        self.product.save()

        mock_construct.return_value = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_123"
                }
            }
        }

        response = self.client.post(
            self.webhook_url,
            data="raw_payload",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_sig"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "failed")

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

        self.assertTrue(Notification.objects.filter(user=self.user, title="Order payment failed").exists())

    @patch("stripe.Webhook.construct_event")
    def test_webhook_payment_intent_canceled_replenishes_stock(self, mock_construct):
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            fulfillment="pickup",
            subtotal="50.00",
            total="54.00",
            stripe_payment_intent_id="pi_123",
            status="pending_payment",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            sku=self.product.sku,
            unit_price=self.product.price,
            quantity=3,
            line_total="150.00",
        )
        self.product.stock = 7
        self.product.save()

        mock_construct.return_value = {
            "type": "payment_intent.canceled",
            "data": {
                "object": {
                    "id": "pi_123"
                }
            }
        }

        response = self.client.post(
            self.webhook_url,
            data="raw_payload",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_sig"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

        self.assertTrue(Notification.objects.filter(user=self.user, title="Order payment cancelled").exists())

    @patch("stripe.Webhook.construct_event")
    def test_webhook_invalid_signature(self, mock_construct):
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid signature", "sig")

        response = self.client.post(
            self.webhook_url,
            data="raw_payload",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid_sig"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class QuoteRequestTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quoteuser", password="pass", email="quote@example.com")
        self.token = Token.objects.create(user=self.user)
        self.category = Category.objects.create(name="Services", slug="services")
        self.product = make_product(
            name="Consulting Service",
            slug="consulting",
            sku="SKU-CONS",
            category=self.category,
            price=None,
            pricing_mode="on_request",
            type="service",
        )
        self.url = reverse("quote-list")

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_submit_quote_request_requires_authentication(self):
        response = self.client.post(self.url, {
            "product": self.product.slug,
            "quantity": 2,
            "contact_phone": "+989123456789",
            "message": "Need help with DevOps",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_submit_quote_request_success(self):
        self.authenticate()
        response = self.client.post(self.url, {
            "product": self.product.slug,
            "quantity": 3,
            "contact_phone": "+989123456789",
            "message": "Custom requirements",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuoteRequest.objects.count(), 1)
        quote = QuoteRequest.objects.get()
        self.assertEqual(quote.user, self.user)
        self.assertEqual(quote.product, self.product)
        self.assertEqual(quote.quantity, 3)
        self.assertEqual(quote.contact_phone, "+989123456789")
        self.assertEqual(quote.status, "new")

    def test_read_quote_requests_list_restricted_to_owner(self):
        # Create quote for current user
        QuoteRequest.objects.create(
            user=self.user,
            product=self.product,
            quantity=1,
            contact_phone="+981",
        )
        # Create quote for other user
        other_user = User.objects.create_user(username="otherquote", password="pass")
        QuoteRequest.objects.create(
            user=other_user,
            product=self.product,
            quantity=5,
            contact_phone="+982",
        )

        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only list own quote
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["contact_phone"], "+981")

    def test_quote_approval_generates_order_and_notifications(self):
        # Create a QuoteRequest
        quote = QuoteRequest.objects.create(
            user=self.user,
            product=self.product,
            quantity=2,
            contact_phone="+989123456789",
            message="Test quote approval",
        )

        # Transition to approved with agreed_price
        with self.settings(TAX_RATE=0.08):
            quote.status = "approved"
            quote.agreed_price = Decimal("150.00")
            quote.save()

        # Check Order was generated
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, "pending_payment")
        self.assertEqual(order.fulfillment, "pickup")
        self.assertEqual(order.subtotal, Decimal("300.00")) # 150.00 * 2
        self.assertEqual(order.tax, Decimal("24.00")) # 300 * 0.08
        self.assertEqual(order.total, Decimal("324.00"))
        self.assertEqual(order.quote_request, quote)

        # Check OrderItem was generated
        self.assertEqual(OrderItem.objects.count(), 1)
        item = OrderItem.objects.get()
        self.assertEqual(item.order, order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.unit_price, Decimal("150.00"))
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.line_total, Decimal("300.00"))

        # Check Notification was created
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertIn("تأیید شد", notification.title)
        self.assertIn(order.number, notification.message)

    def test_quote_approval_decrements_stock_only_for_physical_products(self):
        # Service product stock does not decrement (stays 10 or similar)
        service_quote = QuoteRequest.objects.create(
            user=self.user,
            product=self.product,
            quantity=2,
            contact_phone="+98912",
        )
        self.product.stock = 10
        self.product.save()

        service_quote.status = "approved"
        service_quote.agreed_price = Decimal("10.00")
        service_quote.save()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10) # service remains unchanged

        # Physical product stock does decrement
        physical_product = make_product(
            name="Physical Gear",
            slug="gear",
            sku="SKU-GEAR",
            category=self.category,
            price="50.00",
            pricing_mode="fixed",
            type="physical",
            stock=10,
        )

        physical_quote = QuoteRequest.objects.create(
            user=self.user,
            product=physical_product,
            quantity=3,
            contact_phone="+98912",
        )

        physical_quote.status = "approved"
        physical_quote.agreed_price = Decimal("40.00")
        physical_quote.save()

        physical_product.refresh_from_db()
        self.assertEqual(physical_product.stock, 7) # decremented by 3


class IranianPaymentTests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="paymentowner", password="pass", email="owner@example.com")
        self.token = Token.objects.create(user=self.user)
        self.category = Category.objects.create(name="Laptops", slug="laptops")
        self.product = make_product(
            name="Laptop",
            slug="laptop",
            sku="SKU-LAP",
            category=self.category,
            price="100.00",
            stock=10,
        )
        self.order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            fulfillment="pickup",
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
        )
        
        self.bank_account = BankAccount.objects.create(
            bank_name="Melli",
            card_number="6037991234567890",
            sheba_number="IR120170000000123456789012",
            holder_name="Mehdi",
            is_active=True
        )
        
    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_bank_account_list(self):
        self.authenticate()
        response = self.client.get(reverse("bank-account-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["bank_name"], "Melli")

    def test_submit_bank_transfer_success(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from io import BytesIO
        from PIL import Image
        
        self.authenticate()
        
        file_obj = BytesIO()
        image = Image.new("RGBA", size=(1, 1), color=(255, 0, 0))
        image.save(file_obj, "png")
        file_obj.seek(0)
        mock_image = SimpleUploadedFile("receipt.png", file_obj.read(), content_type="image/png")

        response = self.client.post(
            reverse("bank-transfer-submit"),
            {
                "order_id": self.order.id,
                "receipt_image": mock_image,
                "reference_number": "REF-123456"
            },
            format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["status"], "pending")
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "awaiting_verification")

        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.get()
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.reference_number, "REF-123456")
        self.assertEqual(payment.verification_status, "pending")
        self.assertTrue(payment.receipt_image.name.startswith("receipts/"))

        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)

    def test_submit_bank_transfer_invalid_order(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from io import BytesIO
        from PIL import Image
        
        self.authenticate()
        
        file_obj = BytesIO()
        image = Image.new("RGBA", size=(1, 1), color=(255, 0, 0))
        image.save(file_obj, "png")
        file_obj.seek(0)
        mock_image = SimpleUploadedFile("receipt.png", file_obj.read(), content_type="image/png")
        
        response = self.client.post(
            reverse("bank-transfer-submit"),
            {
                "order_id": 99999,
                "receipt_image": mock_image,
                "reference_number": "REF-123"
            },
            format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_paid_transition_validation(self):
        self.order.status = "awaiting_verification"
        self.order.save()

        payment = Payment.objects.create(
            order=self.order,
            reference_number="REF-1",
            verification_status="pending"
        )

        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.order.status = "paid"
            self.order.save()

        payment.verification_status = "approved"
        payment.save()

        self.order.status = "paid"
        self.order.save()
        self.assertEqual(self.order.status, "paid")

    def test_zarinpal_initiate_success(self):
        self.authenticate()
        response = self.client.post(
            reverse("zarinpal-initiate"),
            {"order_id": self.order.id},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("authority", response.data)
        self.assertIn("payment_url", response.data)

    def test_zarinpal_callback_success(self):
        response = self.client.get(
            reverse("zarinpal-callback"),
            {
                "Authority": "zarp-12345",
                "Status": "OK",
                "order_id": self.order.id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.reference_number, "zarp-12345")
        self.assertEqual(payment.verification_status, "approved")

    def test_zarinpal_callback_failure(self):
        response = self.client.get(
            reverse("zarinpal-callback"),
            {
                "Authority": "zarp-12345",
                "Status": "NOK",
                "order_id": self.order.id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "failed")


