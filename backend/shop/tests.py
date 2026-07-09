from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Category, Product, ProductImage, Review


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
