from django.conf import settings
from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )

    def __str__(self):
        return self.name


class Profile(models.Model):
    LANGUAGE_CHOICES = [("en", "English"), ("fa", "Persian")]
    THEME_CHOICES = [("light", "Light"), ("dark", "Dark")]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default="en")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")

    def __str__(self):
        return f"Profile({self.user})"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.title} — {self.user}"
