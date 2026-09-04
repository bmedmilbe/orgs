# core/services.py
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django_tenants.utils import schema_context

from core.middleware import DomainType
from core.models import Client, Domain

User = get_user_model()


class UserService:
    @staticmethod
    @transaction.atomic
    def register_customer_via_bridge(user_data):
        email = user_data.get("email")
        phone = user_data.get("phone")
        username = user_data.get("username")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        # 1. Global Pre-validations
        staff_q = Q(is_superuser=True) | Q(is_staff=True)
        if email and User.objects.filter(staff_q, email=email).exists():
            raise ValidationError(
                {"email": "A staff member with this email address already exists."}
            )
        if phone and User.objects.filter(staff_q, phone=phone).exists():
            raise ValidationError(
                {"phone": "A staff member with this phone number already exists."}
            )

        if email and User.objects.filter(is_customer=True, email=email).exists():
            raise ValidationError(
                {"email": "A customer with this email address already exists."}
            )
        if phone and User.objects.filter(is_customer=True, phone=phone).exists():
            raise ValidationError(
                {"phone": "A customer with this phone number already exists."}
            )

        # 2. Strict Alphanumeric Domain & Schema Generation (No '-' or '_')
        raw_identifier = username or (email.split("@")[0] if email else "customer")
        clean_identifier = (
            "".join(c for c in raw_identifier if c.isalnum()).lower() or "customer"
        )
        clean_identifier = clean_identifier[:5]
        suffix = secrets.token_hex(4)  # Generates pure hex (e.g., 'a1b2c3d4')
        full_domain = f"{clean_identifier}{suffix}.{settings.PUBLIC_DOMAIN}"
        schema_name = f"{clean_identifier}{suffix}"

        # 3. Create Tenant, Domain, and customer User within the PUBLIC schema
        with schema_context("public"):
            while (
                Domain.objects.filter(domain=full_domain).exists()
                or Client.objects.filter(schema_name=schema_name).exists()
            ):
                suffix = secrets.token_hex(4)
                full_domain = f"{clean_identifier}{suffix}.{settings.PUBLIC_DOMAIN}"
                schema_name = f"{clean_identifier}{suffix}"

            # Create Tenant
            display_name = (
                f"{first_name} {last_name}".strip() or username or email or phone
            )
            tenant = Client.objects.create(
                schema_name=schema_name,
                name=f"{display_name}'s Space",
                paid_until=timezone.now().date() + timedelta(days=30),
                on_trial=True,
            )

            # Create Domain
            Domain.objects.create(
                domain=full_domain,
                tenant=tenant,
                is_primary=True,
            )

            # Create customer User
            user = User.objects.create_user(
                email=email,
                username=username or email,
                password=user_data["password"],
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                is_customer=True,
                tenant=tenant,
            )

        return user

    @staticmethod
    def register_customer_via_tenant(request, user_data):
        """
        Private Tenant Domain Signup: Registers an end-customer.
        Validates username uniqueness scoped strictly to request.tenant.
        """
        if getattr(request, "domain_type", None) != DomainType.TENANT:
            raise ValidationError(
                "Customer accounts can only be registered on a customer's private domain."
            )

        tenant = request.tenant
        username = user_data.get("username", user_data.get("email"))

        if user_data.get("is_customer", False):
            raise ValidationError(
                "customers cannot be registered within a private tenant domain."
            )

        # Check username uniqueness for THIS specific tenant space
        if User.objects.filter(tenant=tenant, username=username).exists():
            raise ValidationError(
                {"username": "This username is already taken in this space."}
            )

        user = User.objects.create_user(
            email=user_data["email"],
            username=username,
            password=user_data["password"],
            phone=user_data.get("phone"),
            is_customer=False,
            tenant=tenant,
        )

        return user
