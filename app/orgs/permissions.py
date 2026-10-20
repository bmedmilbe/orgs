"""
Custom permission classes for the CMS + Store API.

Policy:
  - Anyone can perform read-only actions (GET / HEAD / OPTIONS).
  - Only *tenant staff* can mutate data (POST / PUT / PATCH / DELETE).
    "Tenant staff" means: authenticated, `is_staff=True`, and has a
    `Customer` record tied to `request.user` in the *current tenant schema*.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsTenantStaffOrReadOnly(BasePermission):
    """
    Allow anonymous reads; require staff-of-tenant credentials for writes.

    A user qualifies as tenant staff when:
      1. ``request.user.is_authenticated`` is True,
      2. ``request.user.is_staff`` is True,
      3. A ``Customer`` record exists for this user **in the active tenant
         schema** (``Customer`` is a tenant-scoped model, so the query is
         already schema-isolated by django-tenants' search_path).

    The ``request.user.is_anonymous`` short-circuit is kept for clarity and
    to avoid any surprise if DRF is configured with a non-standard auth chain.
    """

    message = (
        "You must be an authenticated tenant staff member to perform "
        "this action."
    )

    def has_permission(self, request, view):
        # 1. Safe methods: everyone (including anonymous) may read.
        if request.method in SAFE_METHODS:
            return True

        # 2. Mutations: must be authenticated.
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # 3. Must be flagged as staff.
        if not getattr(user, "is_staff", False):
            return False

        # 4. Must have a Customer profile in the *current* tenant schema.
        #    `cms_customer` is the reverse OneToOne accessor on the user
        #    (see models.Customer.user -> related_name="cms_customer").
        #    Because Customer lives in the tenant schema, this query is
        #    automatically constrained by django-tenants' search_path.
        return user.cms_customer_set.exists() if hasattr(
            user, "cms_customer_set"
        ) else _has_cms_customer(user)


def _has_cms_customer(user):
    """Helper: reverse OneToOne accessor raises DoesNotExist, not AttributeError."""
    from .models import Customer

    return Customer.objects.filter(user=user).exists()