from rest_framework import serializers


class ParentScopeMixin:
    """
    Resolves a parent scope ID from the view's URL kwargs (preferred)
    or a direct serializer context value.
    """

    def get_parent_id(self, key: str):
        view = self.context.get("view")
        if view is not None and hasattr(view, "kwargs"):
            kwargs = view.kwargs or {}
            if key in kwargs:
                return kwargs[key]
            alt = key.replace("-", "_")
            if alt in kwargs:
                return kwargs[alt]

        direct = self.context.get(key)
        if direct is not None:
            return direct

        raise serializers.ValidationError(
            {key: f"Missing required URL scope parameter '{key}'."}
        )


class ScopedWriteSerializer(ParentScopeMixin, serializers.ModelSerializer):
    """
    Base for child serializers whose parent FK comes from the URL.
    Subclasses declare `scope_kwarg` (e.g. 'page_pk') and `scope_field`
    (e.g. 'page'), then get create/update/validate for free.
    """
    scope_kwarg: str = ""
    scope_field: str = ""

    def validate(self, attrs):
        self.get_parent_id(self.scope_kwarg)
        return super().validate(attrs)

    def create(self, validated_data):
        parent_id = self.get_parent_id(self.scope_kwarg)
        return self.Meta.model.objects.create(
            **{f"{self.scope_field}_id": parent_id}, **validated_data
        )

    def update(self, instance, validated_data):
        self.get_parent_id(self.scope_kwarg)
        return super().update(instance, validated_data)