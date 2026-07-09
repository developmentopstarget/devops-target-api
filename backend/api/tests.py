from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Item, Notification


class HealthCheckTests(APITestCase):
    def test_health_returns_200_and_ok(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})


class ItemViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.token = Token.objects.create(user=self.user)
        self.url = reverse("item-list")

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_unauthenticated_get_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_items_returns_200_with_own_items(self):
        self.authenticate()
        Item.objects.create(name="Alpha", owner=self.user)
        Item.objects.create(name="Beta", owner=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_item_response_fields_shape(self):
        self.authenticate()
        Item.objects.create(name="Alpha", owner=self.user)

        response = self.client.get(self.url)
        item = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(item["name"], "Alpha")
        self.assertIn("id", item)
        self.assertIn("created_at", item)
        self.assertNotIn("owner", item)

    def test_create_item_returns_201(self):
        self.authenticate()

        response = self.client.post(self.url, {"name": "Gamma"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Gamma")
        self.assertEqual(Item.objects.count(), 1)

    def test_create_item_missing_name_returns_400(self):
        self.authenticate()

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_authenticated_user_sees_only_own_items(self):
        self.authenticate()
        other = User.objects.create_user(username="other", password="pass")
        Item.objects.create(name="Mine", owner=self.user)
        Item.objects.create(name="Theirs", owner=other)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Mine")

    def test_authenticated_user_does_not_see_other_users_items(self):
        self.authenticate()
        other = User.objects.create_user(username="other2", password="pass")
        Item.objects.create(name="NotMine", owner=other)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_item_assigns_owner_to_request_user(self):
        self.authenticate()

        response = self.client.post(self.url, {"name": "Owned"}, format="json")
        item = Item.objects.get(name="Owned")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(item.owner, self.user)

class MeViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="meuser",
            password="pass",
            email="me@example.com",
        )
        self.token = Token.objects.create(user=self.user)
        self.url = "/api/me/"

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_unauthenticated_get_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_returns_200(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_exactly_safe_fields(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(
            set(response.data.keys()),
            {"id", "username", "email", "first_name", "language", "theme"},
        )
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["username"], "meuser")
        self.assertEqual(response.data["email"], "me@example.com")

    def test_get_returns_default_profile_prefs(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.data["language"], "en")
        self.assertEqual(response.data["theme"], "light")

    def test_patch_updates_first_name_and_email(self):
        self.authenticate()
        response = self.client.patch(
            self.url,
            {"first_name": "Ada", "email": "ada@example.com"},
            format="json",
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Ada")
        self.assertEqual(response.data["email"], "ada@example.com")
        self.assertEqual(self.user.first_name, "Ada")
        self.assertEqual(self.user.email, "ada@example.com")

    def test_patch_updates_profile_prefs(self):
        self.authenticate()
        response = self.client.patch(
            self.url,
            {"language": "fa", "theme": "dark"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["language"], "fa")
        self.assertEqual(response.data["theme"], "dark")

        second = self.client.get(self.url)
        self.assertEqual(second.data["language"], "fa")
        self.assertEqual(second.data["theme"], "dark")

    def test_patch_rejects_invalid_theme(self):
        self.authenticate()
        response = self.client.patch(self.url, {"theme": "neon"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("theme", response.data)

    def test_patch_unauthenticated_returns_401(self):
        response = self.client.patch(self.url, {"first_name": "Ada"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class NotificationViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="notifyuser", password="pass")
        self.other = User.objects.create_user(username="notifyother", password="pass")
        self.token = Token.objects.create(user=self.user)
        self.url = reverse("notification-list")

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_unauthenticated_list_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_sees_only_own_notifications(self):
        self.authenticate()
        Notification.objects.create(
            user=self.user,
            title="Mine",
            message="Visible notification",
        )
        Notification.objects.create(
            user=self.other,
            title="Theirs",
            message="Hidden notification",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Mine")

    def test_notification_response_fields_shape(self):
        self.authenticate()
        Notification.objects.create(
            user=self.user,
            title="Shape",
            message="Check fields",
            link="/items",
        )

        response = self.client.get(self.url)
        notification = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(notification.keys()),
            {"id", "title", "message", "link", "is_read", "created_at"},
        )
        self.assertEqual(notification["title"], "Shape")
        self.assertEqual(notification["link"], "/items")
        self.assertFalse(notification["is_read"])

    def test_mark_read_marks_own_notification_as_read(self):
        self.authenticate()
        notification = Notification.objects.create(
            user=self.user,
            title="Unread",
            message="Mark me",
        )

        response = self.client.post(
            reverse("notification-mark-read", args=[notification.id])
        )

        notification.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(notification.is_read)
        self.assertTrue(response.data["is_read"])

    def test_mark_read_does_not_allow_other_users_notification(self):
        self.authenticate()
        notification = Notification.objects.create(
            user=self.other,
            title="Private",
            message="Not yours",
        )

        response = self.client.post(
            reverse("notification-mark-read", args=[notification.id])
        )

        notification.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(notification.is_read)

    def test_mark_all_read_marks_only_own_unread_notifications(self):
        self.authenticate()
        mine = Notification.objects.create(
            user=self.user,
            title="Mine",
            message="Read me",
        )
        theirs = Notification.objects.create(
            user=self.other,
            title="Theirs",
            message="Stay unread",
        )

        response = self.client.post(reverse("notification-mark-all-read"))

        mine.refresh_from_db()
        theirs.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated"], 1)
        self.assertTrue(mine.is_read)
        self.assertFalse(theirs.is_read)

    def test_creating_item_creates_notification(self):
        self.authenticate()
        response = self.client.post(reverse("item-list"), {"name": "Notebook"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.title, "Item created")
        self.assertIn("Notebook", notification.message)
        self.assertEqual(notification.link, "/items")
        self.assertFalse(notification.is_read)
