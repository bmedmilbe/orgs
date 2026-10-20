"""Sanity tests for URL registration — no DB, no fixtures, no schema."""
from django.urls import reverse
from django_tenants.utils import tenant_context

from orgs.tests.base import TenantAwareTestCase
from orgs.tests.factories import BlogCategoryFactory


class TestUrlReversal(TenantAwareTestCase):
    def test_root_routes_reverse(self):
        for name in [
            "customers-list", "pages-list", "metrics-list",
            "districts-list", "associations-list",
            "catalog-categories-list", "catalog-items-list",
            "videos-list", "contact-messages-list", "partners-list",
            "roles-list", "team-members-list",
            "financial-budgets-list", "compliance-docs-list",
            "blog-categories-list", "reviews-list",
        ]:
            url = reverse(f"orgs:{name}")
            assert url.startswith("/api/orgs/")

    def test_nested_category_posts_reverses(self):
        with tenant_context(self.tenant):
            BlogCategoryFactory(slug="news")
            url = reverse("orgs:category-posts-list", kwargs={"category_slug": "news"})
            
            assert url == "/api/orgs/categories/news/posts/"