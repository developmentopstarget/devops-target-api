from rest_framework import serializers

from .models import Item, Notification, Profile


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "link", "is_read", "created_at"]
        read_only_fields = fields


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    language = serializers.ChoiceField(choices=Profile.LANGUAGE_CHOICES, required=False)
    theme = serializers.ChoiceField(choices=Profile.THEME_CHOICES, required=False)

    def update(self, instance, validated_data):
        for field in ("email", "first_name"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        profile, _ = Profile.objects.get_or_create(user=instance)
        for field in ("language", "theme"):
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()
        return instance

    def to_representation(self, instance):
        profile, _ = Profile.objects.get_or_create(user=instance)
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
            "first_name": instance.first_name,
            "language": profile.language,
            "theme": profile.theme,
        }
