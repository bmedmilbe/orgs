# orgs/tests/base.py

from datetime import date, timedelta

from django.test import TestCase

from orgs.tests.factories import ClientFactory


class TenantAwareTestCase(TestCase):
    """
    Base test class that creates a tenant.
    You must use 'with tenant_context(self.tenant):' in each test.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.tenant = ClientFactory(
            schema_name="test_tenant",
            name="Test Tenant",
            paid_until=date.today() + timedelta(days=365),
            on_trial=True,
        )
        cls.tenant.save()
