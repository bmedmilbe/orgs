from datetime import date, timedelta

import factory
import factory.fuzzy
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from orgs.models import (
    Customer,
)

from core.models import Client

User = get_user_model()


# ==========================================
# HELPERS
# ==========================================


# ==========================================
# 1. CORE & USER MODULE
# ==========================================


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client

    schema_name = factory.Sequence(lambda n: f"tenant_{n}")
    name = factory.Sequence(lambda n: f"Tenant Corp {n}")
    paid_until = factory.LazyFunction(lambda: date.today() + timedelta(days=365))
    on_trial = True


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    tenant = factory.SubFactory(ClientFactory)

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@tenant.com")
    phone = factory.Sequence(lambda n: f"+23999{n:05d}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    is_customer = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password_to_set = extracted or "password123"
        self.set_password(password_to_set)
        if create:
            self.save()


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer
        django_get_or_create = ["user"]

    user = factory.SubFactory(UserFactory)
    # domain = None

