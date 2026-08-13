from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

# ==========================================
# CUSTOM QUERYSETS FOR OPTIMIZED FETCHING
# ==========================================


# 1. Custom QuerySet for User chainable methods
class UserQuerySet(models.QuerySet):
    def with_tenant(self):
        """Fetch User with tenant Client relationship via single SQL JOIN."""
        return self.select_related("tenant")


# 2. Inherit from Django's UserManager so create_user() and create_superuser() are preserved
class CustomUserManager(UserManager.from_queryset(UserQuerySet)):
    pass



class User(AbstractUser):
    # Username is scoped per-tenant via Meta constraints
    username = models.CharField(max_length=150, unique=False)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_customer = models.BooleanField(default=False)
    tenant = models.ForeignKey(
        "Client", on_delete=models.CASCADE, null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        constraints = [
            # 1. Per-tenant uniqueness constraints
            models.UniqueConstraint(
                fields=["email", "tenant"],
                name="unique_email_per_tenant",
                condition=models.Q(email__isnull=False, is_customer=False),
            ),
            models.UniqueConstraint(
                fields=["phone", "tenant"],
                name="unique_phone_per_tenant",
                condition=models.Q(phone__isnull=False, is_customer=False),
            ),
            models.UniqueConstraint(
                fields=["username", "tenant"],
                name="unique_username_per_tenant",
            ),

            # 2. Single customer per tenant
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(is_customer=True),
                name="unique_single_customer_per_tenant",
            ),

            # 3. GLOBAL uniqueness for customers across all tenants
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(is_customer=True, email__isnull=False),
                name="unique_customer_email_global",
            ),
            models.UniqueConstraint(
                fields=["phone"],
                condition=models.Q(is_customer=True, phone__isnull=False),
                name="unique_customer_phone_global",
            ),
        ]

    def clean(self):
        super().clean()
        if self.is_customer and self.tenant_id:
            existing_customer = User.objects.filter(tenant=self.tenant, is_customer=True).exclude(pk=self.pk)
            if existing_customer.exists():
                raise ValidationError("A customer already exists for this tenant schema.")
            
class Client(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until = models.DateField()
    on_trial = models.BooleanField()
    created_on = models.DateField(auto_now_add=True)


class Domain(DomainMixin):
    pass
