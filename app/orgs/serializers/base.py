from rest_framework import serializers

from .common import TranslatableFieldsMixin


class BaseReadSerializer(serializers.ModelSerializer):
    """Base for read serializers. Read-only by convention."""
    class Meta:
        read_only_fields = "__all__"


class BaseWriteSerializer(TranslatableFieldsMixin, serializers.ModelSerializer):
    """
    Base for write serializers. Handles translation field expansion
    and default-language validation automatically.
    """
