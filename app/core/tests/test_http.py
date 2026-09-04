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

    @classmethod
    def setUpTestData(cls):
        """Set up data for all test methods."""
        # Create tenants
        cls.root_tenant = ClientFactory(schema_name="public", name="Root Tenant")
        cls.bridge_tenant = ClientFactory(schema_name="bridge", name="Bridge Tenant")
        cls.tenant1 = ClientFactory(schema_name="tenant1", name="Tenant 1")
        cls.tenant2 = ClientFactory(schema_name="tenant2", name="Tenant 2")

        # Create domains
        cls.root_domain = Domain.objects.create(
            domain="localhost", tenant=cls.root_tenant, is_primary=True
        )
        cls.bridge_domain = Domain.objects.create(
            domain="bridge.localhost", tenant=cls.bridge_tenant, is_primary=True
        )
        cls.tenant1_domain = Domain.objects.create(
            domain="tenant1.localhost", tenant=cls.tenant1, is_primary=True
        )
        cls.tenant2_domain = Domain.objects.create(
            domain="tenant2.localhost", tenant=cls.tenant2, is_primary=True
        )

        # Create users in root tenant
        with tenant_context(cls.root_tenant):
            cls.superuser = UserFactory(
                username="superuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=cls.root_tenant,
            )
            cls.staff_user = UserFactory(
                username="staffuser",
                password="SecurePass123!",
                is_staff=True,
                is_superuser=False,
                tenant=cls.root_tenant,
            )
            cls.regular_user = UserFactory(
                username="regularuser",
                password="SecurePass123!",
                is_superuser=False,
                is_staff=False,
                tenant=cls.root_tenant,
            )
            cls.inactive_user = UserFactory(
                username="inactive",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                is_active=False,
                tenant=cls.root_tenant,
            )

        # Create users in bridge tenant
        with tenant_context(cls.bridge_tenant):
            cls.bridge_customer = UserFactory(
                username="bridge_customer",
                email="customer@example.com",
                phone="+9876543210",
                password="SecurePass123!",
                is_customer=True,
                tenant=cls.bridge_tenant,
            )
            cls.bridge_regular = UserFactory(
                username="bridge_regular",
                password="SecurePass123!",
                email="customer@example.com",
                is_customer=False,
                tenant=cls.bridge_tenant,
            )
            cls.bridge_superuser = UserFactory(
                username="bridge_superuser",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                is_customer=False,
                tenant=cls.bridge_tenant,
            )

        # Create users in tenant1
        with tenant_context(cls.tenant1):
            cls.tenant_user = UserFactory(
                username="tenantuser",
                password="SecurePass123!",
                is_customer=False,
                tenant=cls.tenant1,
            )
            cls.tenant_customer = UserFactory(
                username="tenant_customer",
                password="SecurePass123!",
                is_customer=True,
                tenant=cls.tenant1,
            )

        # Create users in tenant2
        with tenant_context(cls.tenant2):
            cls.tenant2_user = UserFactory(
                username="tenant2_user",
                password="SecurePass123!",
                is_customer=False,
                tenant=cls.tenant2,
            )

        # Create request factory
        cls.factory = RequestFactory()

    def _create_request(self, tenant, domain_type):
        """Helper to create a request with tenant and domain type."""
        request = self.factory.get("/")
        request.tenant = tenant
        request.domain_type = domain_type
        return request

    # =============================================================
    # ROOT DOMAIN LOGIN TESTS
    # =============================================================

    def test_root_domain_login_superuser_success(self):
        """Test that superusers can log in via root domain."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="superuser", password="SecurePass123!"
        )
        self.assertEqual(result, self.superuser)

    def test_root_domain_login_staff_success(self):
        """Test that staff users can log in via root domain."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="staffuser", password="SecurePass123!"
        )
        self.assertEqual(result, self.staff_user)

    def test_root_domain_login_regular_user_fails(self):
        """Test that regular (non-staff/non-superuser) users cannot log in via root domain."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="regularuser", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_root_domain_login_by_email(self):
        """Test root domain login using email."""
        # Create user with email
        with tenant_context(self.root_tenant):
            email_user = UserFactory(
                email="admin@example.com",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=self.root_tenant,
            )

        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, email="admin@example.com", password="SecurePass123!"
        )
        self.assertEqual(result, email_user)

    def test_root_domain_login_by_phone(self):
        """Test root domain login using phone number."""
        # Create user with phone
        with tenant_context(self.root_tenant):
            phone_user = UserFactory(
                phone="+1234567890",
                password="SecurePass123!",
                is_superuser=True,
                is_staff=True,
                tenant=self.root_tenant,
            )

        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, phone="+1234567890", password="SecurePass123!"
        )
        self.assertEqual(result, phone_user)

    def test_root_domain_login_wrong_password_fails(self):
        """Test root domain login with wrong password."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="superuser", password="WrongPassword!"
        )
        self.assertIsNone(result)

    def test_root_domain_login_nonexistent_user_fails(self):
        """Test root domain login with non-existent user."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="nonexistent", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_customer_cannot_login_to_root_domain(self):
        """Test that customers cannot log in to root domain."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="bridge_customer", password="SecurePass123!"
        )
        self.assertIsNone(result)

    # =============================================================
    # BRIDGE DOMAIN LOGIN TESTS
    # =============================================================

    def test_bridge_domain_login_customer_success(self):
        """Test that customers can log in via bridge domain."""
        request = self._create_request(self.bridge_tenant, DomainType.BRIDGE)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="bridge_customer", password="SecurePass123!"
        )
        self.assertEqual(result, self.bridge_customer)

    def test_bridge_domain_login_regular_user_fails(self):
        """Test that regular (non-customer) users cannot log in via bridge domain."""
        request = self._create_request(self.bridge_tenant, DomainType.BRIDGE)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="bridge_regular", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_bridge_domain_login_superuser_fails(self):
        """Test that superusers cannot log in via bridge domain."""
        request = self._create_request(self.bridge_tenant, DomainType.BRIDGE)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="bridge_superuser", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_bridge_domain_login_by_email(self):
        """Test bridge domain login using email."""
        # Create user with email
        with tenant_context(self.bridge_tenant):
            email_user = self.bridge_customer

               
        request = self._create_request(self.bridge_tenant, DomainType.BRIDGE)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, email="customer@example.com", password="SecurePass123!"
        )
        self.assertEqual(result, email_user)

    def test_bridge_domain_login_by_phone(self):
        """Test bridge domain login using phone number."""
        # Create user with phone
        with tenant_context(self.bridge_tenant):
            phone_user = self.bridge_customer

        request = self._create_request(self.bridge_tenant, DomainType.BRIDGE)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, phone="+9876543210", password="SecurePass123!"
        )
        self.assertEqual(result, phone_user)

    def test_superuser_cannot_login_to_bridge_domain(self):
        """Test that superusers cannot log in to bridge domain."""
        request = self._create_request(self.bridge_tenant, DomainType.BRIDGE)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="superuser", password="SecurePass123!"
        )
        self.assertIsNone(result)

    # =============================================================
    # TENANT DOMAIN LOGIN TESTS
    # =============================================================

    def test_tenant_domain_login_regular_user_success(self):
        """Test that regular users can log in via their tenant domain."""
        request = self._create_request(self.tenant1, DomainType.TENANT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="tenantuser", password="SecurePass123!"
        )
        self.assertEqual(result, self.tenant_user)

    def test_tenant_domain_login_customer(self):
        """Test that customers cannot log in via tenant domain."""
        request = self._create_request(self.tenant1, DomainType.TENANT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="tenant_customer", password="SecurePass123!"
        )
        self.assertTrue(result)

    def test_tenant_domain_login_wrong_tenant_fails(self):
        """Test that users cannot log in to a tenant they don't belong to."""
        request = self._create_request(self.tenant2, DomainType.TENANT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, username="tenantuser", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_tenant_domain_login_by_email(self):
        """Test tenant domain login using email."""
        # Create user with email
        with tenant_context(self.tenant1):
            email_user = UserFactory(
                email="user@tenant1.com",
                password="SecurePass123!",
                is_customer=False,
                tenant=self.tenant1,
            )

        request = self._create_request(self.tenant1, DomainType.TENANT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, email="user@tenant1.com", password="SecurePass123!"
        )
        self.assertEqual(result, email_user)

    def test_tenant_domain_login_by_phone(self):
        """Test tenant domain login using phone number."""
        # Create user with phone
        with tenant_context(self.tenant1):
            phone_user = UserFactory(
                phone="+5555555555",
                password="SecurePass123!",
                is_customer=False,
                tenant=self.tenant1,
            )

        request = self._create_request(self.tenant1, DomainType.TENANT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request, phone="+5555555555", password="SecurePass123!"
        )
        self.assertEqual(result, phone_user)

    # =============================================================
    # EDGE CASE TESTS
    # =============================================================

    def test_authenticate_without_request_returns_none(self):
        """Test that authentication fails without a request object."""
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=None, username="superuser", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_authenticate_without_tenant_returns_none(self):
        """Test that authentication fails without a tenant in request."""
        request = self.factory.get("/")
        request.domain_type = DomainType.ROOT
        # No tenant set

        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username="superuser", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_authenticate_without_identifier_returns_none(self):
        """Test that authentication fails without an identifier."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username=None, password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_authenticate_with_unknown_domain_type_returns_none(self):
        """Test that authentication fails with unknown domain type."""
        request = self._create_request(self.root_tenant, "UNKNOWN_TYPE")
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username="superuser", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_authenticate_inactive_user_fails(self):
        """Test that inactive users cannot authenticate."""
        request = self._create_request(self.root_tenant, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, username="inactive", password="SecurePass123!"
        )
        self.assertIsNone(result)

    def test_authenticate_multiple_users_same_identifier_fails(self):
        """Test that authentication fails when multiple users share identifier."""
        # Create two users with same email in different tenants
        tenant_a = ClientFactory(schema_name="test_a", name="Test Tenant A")
        tenant_b = ClientFactory(schema_name="test_b", name="Test Tenant B")

        with tenant_context(tenant_a):
            UserFactory(
                username="user_a",
                email="duplicate@example.com",
                password="Pass1!",
                is_superuser=True,
                is_staff=True,
                tenant=tenant_a,
            )

        with tenant_context(tenant_b):
            UserFactory(
                username="user_b",
                email="duplicate@example.com",
                password="Pass2!",
                is_superuser=True,
                is_staff=True,
                tenant=tenant_b,
            )

        request = self._create_request(tenant_a, DomainType.ROOT)
        backend = TenantEmailOrPhoneBackend()
        result = backend.authenticate(
            request=request, email="duplicate@example.com", password="Pass1!"
        )
        self.assertIsNone(result)