from core.models import User
from django.utils import timezone
from django_tenants.test.cases import TenantTestCase


class TestHTTP(TenantTestCase):

    @staticmethod
    def get_test_schema_name():
        """Forces django-tenants to use 'bridge' instead of 'test' for the schema"""
        return "bridge"

    @staticmethod
    def get_test_tenant_domain():
        """Forces django-tenants to use 'bridge.localhost' instead of 'tenant.test.com'"""
        return "bridge.localhost"

    @classmethod
    def setup_tenant(cls, tenant):
        """Populates fields required by model on the auto-generated test tenant"""
        tenant.name = "Bridge"
        tenant.paid_until = timezone.now()
        tenant.on_trial = False
        tenant.created_on = timezone.now()
        return tenant

    def setUp(self):
        super().setUp()
        
        # self.tenant and self.domain are automatically built by TenantTestCase
        self.bridge_tenant = self.tenant
        self.bridge_domain = self.domain

    def test_bridge(self):
        # These assertions will now pass flawlessly
        self.assertEqual(self.bridge_tenant.schema_name, "bridge")
        self.assertEqual(self.bridge_domain.domain, "bridge.localhost")

    def test_create_user_from_bridge_and_allocate_new_tenant(self):
        # Given
        main_client_data = {
            "username": "main_client",            
            "email": "main_client@gmail.com",            
            "password": "SecurePassword123!",
            "phone": "+1234567890",
            "first_name": "John",
            "last_name": "Doe",
            "is_customer": True
        }
        main_client_url = "/api/auth/users/"

        # Act - HTTP_HOST routes the request to the correct schema automatically
        main_client_response = self.client.post(main_client_url,
                                                 main_client_data, 
                                                 HTTP_HOST=self.bridge_domain.domain)

        main_user = User.objects.get(pk=main_client_response.data["id"])

        # Then
        self.assertEqual(main_client_response.status_code, 201)
        self.assertEqual(main_user.is_customer, True)
        self.assertNotEqual(main_user.tenant, self.bridge_tenant)