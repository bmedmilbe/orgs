# core/tests/test_backends.py

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django_tenants.utils import tenant_context

from core.backends import TenantEmailOrPhoneBackend
from core.middleware import DomainType
from core.models import Domain
from core.tests.factories import ClientFactory, UserFactory

User = get_user_model()


class TestTenantEmailOrPhoneBackend(TestCase):
    """Test the custom authentication backend with tenant-aware login."""

    def test_root_domain_login_superuser_success(self):
        """Test that superusers can log in via root domain."""
        # Create tenant and domain
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        root_domain = Domain.objects.create(
            domain="localhost", tenant=root_tenant, is_primary=True
        )

        # Create user
        with tenant_context(root_tenant):
            user = UserFactory(
                username="superuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        # Create request
        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        # Authenticate
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="superuser", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_root_domain_login_staff_success(self):
        """Test that staff users can log in via root domain."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        root_domain = Domain.objects.create(
            domain="localhost", tenant=root_tenant, is_primary=True
        )

        with tenant_context(root_tenant):
            user = UserFactory(
                username="staffuser",
                password="SecurePass123!",
                is_staff=True,
                is_superuser=False,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="staffuser", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_root_domain_login_regular_user_fails(self):
        """Test that regular (non-staff/non-superuser) users cannot log in via root domain."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        Domain.objects.create(domain="localhost", tenant=root_tenant, is_primary=True)

        with tenant_context(root_tenant):
            UserFactory(
                username="regularuser",
                password="SecurePass123!",
                is_superuser=False,
                is_staff=False,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="regularuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_tenant_domain_login_customer(self):
        """Test that customers can log in via tenant domain."""
        tenant1 = ClientFactory(schema_name="tenant1", name="Tenant 1")
        tenant1_domain = Domain.objects.create(
            domain="tenant1.localhost", tenant=tenant1, is_primary=True
        )

        with tenant_context(tenant1):
            # Create a customer user
            customer_user = UserFactory(
                username="customeruser",
                password="SecurePass123!",
                is_customer=True,
                tenant=tenant1,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = tenant1
        request.domain_type = DomainType.TENANT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="customeruser", password="SecurePass123!"
        )

        # Customer should be able to log in via tenant domain
        self.assertTrue(result)

    def test_root_domain_login_by_email(self):
        """Test root domain login using email."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        Domain.objects.create(domain="localhost", tenant=root_tenant, is_primary=True)

        with tenant_context(root_tenant):
            user = UserFactory(
                email="admin@example.com",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, email="admin@example.com", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_root_domain_login_by_phone(self):
        """Test root domain login using phone number."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        Domain.objects.create(domain="localhost", tenant=root_tenant, is_primary=True)

        with tenant_context(root_tenant):
            user = UserFactory(
                phone="+1234567890",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, phone="+1234567890", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_root_domain_login_wrong_password_fails(self):
        """Test root domain login with wrong password."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        Domain.objects.create(domain="localhost", tenant=root_tenant, is_primary=True)

        with tenant_context(root_tenant):
            UserFactory(
                username="superuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="superuser", password="WrongPassword!"
        )

        self.assertIsNone(result)

    def test_root_domain_login_nonexistent_user_fails(self):
        """Test root domain login with non-existent user."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        Domain.objects.create(domain="localhost", tenant=root_tenant, is_primary=True)

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="nonexistent", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_bridge_domain_login_customer_success(self):
        """Test that customers can log in via bridge domain."""
        bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        bridge_domain = Domain.objects.create(
            domain="bridge.localhost", tenant=bridge_tenant, is_primary=True
        )

        with tenant_context(bridge_tenant):
            user = UserFactory(
                username="customeruser",
                password="SecurePass123!",
                is_customer=True,
                tenant=bridge_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = bridge_tenant
        request.domain_type = DomainType.BRIDGE

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="customeruser", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_bridge_domain_login_regular_user_fails(self):
        """Test that regular (non-customer) users cannot log in via bridge domain."""
        bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        bridge_domain = Domain.objects.create(
            domain="bridge.localhost", tenant=bridge_tenant, is_primary=True
        )

        with tenant_context(bridge_tenant):
            UserFactory(
                username="regularuser",
                password="SecurePass123!",
                is_customer=False,
                tenant=bridge_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = bridge_tenant
        request.domain_type = DomainType.BRIDGE

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="regularuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_bridge_domain_login_superuser_fails(self):
        """Test that superusers cannot log in via bridge domain."""
        bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        bridge_domain = Domain.objects.create(
            domain="bridge.localhost", tenant=bridge_tenant, is_primary=True
        )

        with tenant_context(bridge_tenant):
            UserFactory(
                username="superuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                is_customer=False,
                tenant=bridge_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = bridge_tenant
        request.domain_type = DomainType.BRIDGE

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="superuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_bridge_domain_login_by_email(self):
        """Test bridge domain login using email."""
        bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        bridge_domain = Domain.objects.create(
            domain="bridge.localhost", tenant=bridge_tenant, is_primary=True
        )

        with tenant_context(bridge_tenant):
            user = UserFactory(
                email="customer@example.com",
                password="SecurePass123!",
                is_customer=True,
                tenant=bridge_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = bridge_tenant
        request.domain_type = DomainType.BRIDGE

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, email="customer@example.com", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_bridge_domain_login_by_phone(self):
        """Test bridge domain login using phone number."""
        bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        bridge_domain = Domain.objects.create(
            domain="bridge.localhost", tenant=bridge_tenant, is_primary=True
        )

        with tenant_context(bridge_tenant):
            user = UserFactory(
                phone="+9876543210",
                password="SecurePass123!",
                is_customer=True,
                tenant=bridge_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = bridge_tenant
        request.domain_type = DomainType.BRIDGE

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, phone="+9876543210", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_tenant_domain_login_regular_user_success(self):
        """Test that regular users can log in via their tenant domain."""
        tenant1 = ClientFactory(schema_name="tenant1", name="Tenant 1")
        tenant1_domain = Domain.objects.create(
            domain="tenant1.localhost", tenant=tenant1, is_primary=True
        )

        with tenant_context(tenant1):
            user = UserFactory(
                username="tenantuser",
                password="SecurePass123!",
                is_customer=False,
                tenant=tenant1,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = tenant1
        request.domain_type = DomainType.TENANT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="tenantuser", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_tenant_domain_login_wrong_tenant_fails(self):
        """Test that users cannot log in to a tenant they don't belong to."""
        tenant1 = ClientFactory(schema_name="tenant1", name="Tenant 1")
        tenant2 = ClientFactory(schema_name="tenant2", name="Tenant 2")

        tenant1_domain = Domain.objects.create(
            domain="tenant1.localhost", tenant=tenant1, is_primary=True
        )
        tenant2_domain = Domain.objects.create(
            domain="tenant2.localhost", tenant=tenant2, is_primary=True
        )

        with tenant_context(tenant1):
            UserFactory(
                username="tenantuser",
                password="SecurePass123!",
                is_customer=False,
                tenant=tenant1,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = tenant2
        request.domain_type = DomainType.TENANT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="tenantuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_tenant_domain_login_by_email(self):
        """Test tenant domain login using email."""
        tenant1 = ClientFactory(schema_name="tenant1", name="Tenant 1")
        tenant1_domain = Domain.objects.create(
            domain="tenant1.localhost", tenant=tenant1, is_primary=True
        )

        with tenant_context(tenant1):
            user = UserFactory(
                email="user@tenant1.com",
                password="SecurePass123!",
                is_customer=False,
                tenant=tenant1,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = tenant1
        request.domain_type = DomainType.TENANT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, email="user@tenant1.com", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_tenant_domain_login_by_phone(self):
        """Test tenant domain login using phone number."""
        tenant1 = ClientFactory(schema_name="tenant1", name="Tenant 1")
        tenant1_domain = Domain.objects.create(
            domain="tenant1.localhost", tenant=tenant1, is_primary=True
        )

        with tenant_context(tenant1):
            user = UserFactory(
                phone="+5555555555",
                password="SecurePass123!",
                is_customer=False,
                tenant=tenant1,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = tenant1
        request.domain_type = DomainType.TENANT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, phone="+5555555555", password="SecurePass123!"
        )

        self.assertEqual(result, user)

    def test_customer_cannot_login_to_root_domain(self):
        """Test that customers cannot log in to root domain."""
        bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        root_domain = Domain.objects.create(
            domain="localhost", tenant=root_tenant, is_primary=True
        )

        with tenant_context(bridge_tenant):
            UserFactory(
                username="customeruser",
                password="SecurePass123!",
                is_customer=True,
                tenant=bridge_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="customeruser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_superuser_cannot_login_to_bridge_domain(self):
        """Test that superusers cannot log in to bridge domain."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        bridge_domain = Domain.objects.create(
            domain="bridge.localhost", tenant=bridge_tenant, is_primary=True
        )

        with tenant_context(root_tenant):
            UserFactory(
                username="superuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = bridge_tenant
        request.domain_type = DomainType.BRIDGE

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="superuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_authenticate_without_request_returns_none(self):
        """Test that authentication fails without a request object."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")

        with tenant_context(root_tenant):
            UserFactory(
                username="testuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=None, username="testuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_authenticate_without_tenant_returns_none(self):
        """Test that authentication fails without a tenant in request."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")

        with tenant_context(root_tenant):
            UserFactory(
                username="testuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.domain_type = DomainType.ROOT
        # No tenant set

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username="testuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_authenticate_without_identifier_returns_none(self):
        """Test that authentication fails without an identifier."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        root_domain = Domain.objects.create(
            domain="localhost", tenant=root_tenant, is_primary=True
        )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username=None, password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_authenticate_with_unknown_domain_type_returns_none(self):
        """Test that authentication fails with unknown domain type."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        root_domain = Domain.objects.create(
            domain="localhost", tenant=root_tenant, is_primary=True
        )

        with tenant_context(root_tenant):
            UserFactory(
                username="testuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = "UNKNOWN_TYPE"

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username="testuser", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_authenticate_inactive_user_fails(self):
        """Test that inactive users cannot authenticate."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        root_domain = Domain.objects.create(
            domain="localhost", tenant=root_tenant, is_primary=True
        )

        with tenant_context(root_tenant):
            UserFactory(
                username="inactive",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                is_active=False,
                tenant=root_tenant,
            )

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = root_tenant
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username="inactive", password="SecurePass123!"
        )

        self.assertIsNone(result)

    def test_authenticate_multiple_users_same_identifier_fails(self):
        """Test that authentication fails when multiple users share identifier."""
        root_tenant = ClientFactory(schema_name="public", name="Root Tenant")

        tenant_a = ClientFactory(schema_name="test_a", name="Root Tenant")
        tenant_b = ClientFactory(schema_name="test_b", name="Root Tenant")

        root_domain = Domain.objects.create(
            domain="test.localhost", tenant=tenant_a, is_primary=True
        )

        with tenant_context(root_tenant):
            # Create first user
            UserFactory(
                username="duplicate",
                email="duplicate@example.com",
                password="Pass1!",
                is_superuser=True,
                is_staff=True,
                tenant=tenant_a,
            )
            UserFactory(
                username="duplicate2",
                email="duplicate2@example.com",
                password="Pass2!",
                is_superuser=True,
                is_staff=True,
                tenant=tenant_b,
            )

            # Update first user to have the same email
            user1 = User.objects.get(username="duplicate2")
            user1.email = "duplicate@example.com"
            user1.save()

        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = tenant_a
        request.domain_type = DomainType.ROOT

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, email="duplicate@example.com", password="Pass1!"
        )

        self.assertIsNone(result)
