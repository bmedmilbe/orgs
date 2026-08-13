

from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from djoser.serializers import (
    PasswordResetConfirmSerializer,
    SetPasswordSerializer,
    UserCreateSerializer,
)
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.middleware import DomainType
from core.services import UserService

User = get_user_model()



class TenantJWTCreateSerializer(TokenObtainPairSerializer):
    # Flexible field accepting either email or phone
    login_identifier = serializers.CharField(required=True)
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default username field mapping enforced by Simple JWT
        self.fields[self.username_field] = serializers.CharField(required=False)

    @classmethod
    def get_token(cls, user):
        # Generate the standard base token payload
        token = super().get_token(user)

        # Inject custom multi-tenant claims into the encrypted payload
        if hasattr(user, 'tenant') and user.tenant is not None:
            token['tenant_id'] = user.tenant.id # Safe lookup from user instance
            
        return token

    def validate(self, attrs):
        login_identifier = attrs.get("login_identifier")
        password = attrs.get("password")
        request = self.context.get("request")

        # Delegate lookup to TenantEmailOrPhoneBackend via 'username'
        user = authenticate(request=request, username=login_identifier, password=password)

        if not user:
            raise serializers.ValidationError(_("Unable to log in with provided credentials."))

        # Populate the validation payload required by Simple JWT
        data = {}
        refresh = self.get_token(user)
        
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        
        return data




class TenantUserCreateSerializer(UserCreateSerializer):
    phone = serializers.CharField(required=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            User.USERNAME_FIELD,
            "password",
            "phone",
            "first_name",
            "last_name",
            "is_customer",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")

        if not request or not hasattr(request, "tenant") or request.tenant is None:
            raise serializers.ValidationError(
                {"tenant": "A valid tenant context is required to register a user."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        domain_type = getattr(request, "domain_type", DomainType.TENANT)

        # 1. BRIDGE DOMAIN SIGNUP -> customer Creation
        if domain_type == DomainType.BRIDGE:
            return UserService.register_customer_via_bridge(
                user_data=validated_data,
            )

        # 2. PRIVATE TENANT DOMAIN SIGNUP -> Customer Creation
        elif domain_type == DomainType.TENANT:
            return UserService.register_customer_via_tenant(
                request=request,
                user_data=validated_data,
            )

        else:
            raise serializers.ValidationError("Direct user creation is disabled on the Root Domain endpoint.")
    
class TenantSetPasswordSerializer(SetPasswordSerializer):
    """Handles password changes for logged-in users under /auth/users/set_password/"""

    def validate(self, attrs):
        # 1. Run standard Djoser validations (e.g., verifying the current old password)
        attrs = super().validate(attrs)

        request = self.context.get("request")

        # 2. Multi-tenant security check
        if not request or not hasattr(request, "tenant") or request.tenant is None:
            raise serializers.ValidationError(
                {"tenant": "A valid tenant context is required."}
            )

        # 3. Tenant Isolation Check: Verify the logged-in user belongs to the current tenant
        if request.user.tenant != request.tenant:
            raise serializers.ValidationError(
                {"detail": "You do not have permission to modify this resource."}
            )

        return attrs


class TenantPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    """Handles password updates for anonymous 'Forgot Password' links via /auth/users/reset_password_confirm/"""

    def validate(self, attrs):
        # 1. Djoser decodes the UID and token here to find the user instance (self.user)
        attrs = super().validate(attrs)

        request = self.context.get("request")

        # 2. Multi-tenant security check
        if not request or not hasattr(request, "tenant") or request.tenant is None:
            raise serializers.ValidationError(
                {"tenant": "A valid tenant context is required."}
            )

        # 3. Tenant Isolation Check: Block the reset if the target user doesn't belong to the active request tenant
        if hasattr(self, "user") and self.user.tenant != request.tenant:
            raise serializers.ValidationError(
                {"detail": "Invalid token or identifier for this tenant context."}
            )

        return attrs


