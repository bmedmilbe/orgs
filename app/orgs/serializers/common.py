from django.conf import settings
from modeltranslation.translator import translator
from rest_framework import serializers

# Languages the API exposes. Prefer settings.LANGUAGES (Django standard tuple).
# Fallback to your project constant if you keep it separate.
LANGUAGES = getattr(settings, "LANGUAGES", (
    ("pt", "Portuguese"),
    ("fr", "French"),
    ("en", "English"),
))
LANGUAGE_CODES = tuple(code for code, _ in LANGUAGES)
DEFAULT_LANGUAGE = "pt"


def _translated_field_names(model, base_fields):
    """
    Return every `<base>_<lang>` combination for the given base fields,
    using modeltranslation's registered options as the source of truth.

    If modeltranslation has no registration for the model, returns []
    (nothing to expand) — safe no-op.
    """
    opts = translator.get_options_for_model(model)
    registered = set(opts.fields.keys()) if opts else set()
    result = []
    for base in base_fields:
        if base in registered:
            for lang in LANGUAGE_CODES:
                result.append(f"{base}_{lang}")
    return result


class TranslatableFieldsMixin(serializers.Serializer):
    """
    Mixin for WRITE serializers: auto-expands any translatable base field
    into per-language variants (`title` -> `title_pt`, `title_en`, ...).

    Usage:
        class PageWriteSerializer(TranslatableFieldsMixin, serializers.ModelSerializer):
            translatable_fields = ("title", "content")

            class Meta:
                model = Page
                fields = ("id", "slug", "active", "order")  # base only
    """

    #: base field names on the model that are translatable (registered in translation.py)
    translatable_fields: tuple = ()

    def get_fields(self):
        fields = super().get_fields()
        # Rebuild lang-suffixed fields from the *base* fields we declared.
        # We skip the base name itself (it's a virtual field on modeltranslation;
        # including it as a DRF field would be read-only/write-nothing).
        for base in self.translatable_fields:
            # If the ModelSerializer already auto-generated the suffixed fields
            # (some modeltranslation versions do), don't duplicate them.
            for lang in LANGUAGE_CODES:
                name = f"{base}_{lang}"
                if name not in fields:
                    fields[name] = serializers.CharField(
                        required=False, allow_blank=True, allow_null=True
                    )
        return fields

    def get_translatable_field_names(self):
        """All `<base>_<lang>` names generated for this serializer."""
        return _translated_field_names(self.Meta.model, self.translatable_fields)

    def validate(self, attrs):
        attrs = super().validate(attrs) if hasattr(super(), "validate") else attrs

        # Enforce default-language presence on create for each translatable field.
        if self.instance is None:
            missing = {}
            for base in self.translatable_fields:
                key = f"{base}_{DEFAULT_LANGUAGE}"
                if not attrs.get(key):
                    missing[key] = f"{DEFAULT_LANGUAGE.upper()} value is required."
            if missing:
                raise serializers.ValidationError(missing)
        return attrs