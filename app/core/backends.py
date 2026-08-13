# core/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from core.middleware import DomainType

User = get_user_model()


class TenantEmailOrPhoneBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (
            username
            or kwargs.get("email")
            or kwargs.get("phone")
            or kwargs.get(User.USERNAME_FIELD)
        )
        if not identifier or not request or not hasattr(request, "tenant"):
            return None

        domain_type = getattr(request, "domain_type", None)
        
        current_tenant = request.tenant

        # Base query for lookup by email, phone, or username
        lookup = Q(email=identifier) | Q(phone=identifier) | Q(username=identifier)

        try:
            # =================================================================
            # RULE 2A: PUBLIC / ROOT DOMAIN LOGIN
            # Only superusers/staff belonging to the public/root tenant
            # =================================================================
            if domain_type == DomainType.ROOT:
             
                user = User.objects.get(
                    lookup,
                    Q(is_superuser=True) | Q(is_staff = True)
                )
               
                

            # =================================================================
            # RULE 2B: BRIDGE DOMAIN LOGIN
            # Only registered customers (is_customer = True) can authenticate
            # =================================================================
            elif domain_type == DomainType.BRIDGE:
                user = User.objects.get(
                    lookup,
                    is_customer=True
                )

            # =================================================================
            # RULE 2C: PRIVATE TENANT DOMAIN LOGIN
            # Only end-customers (is_customer = False) matching THIS specific tenant
            # =================================================================
            elif domain_type == DomainType.TENANT:
                user = User.objects.get(
                    lookup,
                    tenant=current_tenant,
                    # is_customer=False  # customers are BLOCKED from authenticating here
                )

            else:
                return None

            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        return None