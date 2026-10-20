"""
ViewSet test suite for the orgs app.

Mirrors the pattern from ``test_orgs_models.py``:

* ``TenantAwareTestCase`` + ``with tenant_context(self.tenant):`` per test.
* Factories from ``orgs.tests.factories``. No fixtures, no setUp.
* Views are dispatched **directly** with ``ViewSet.as_view({...})`` and
  ``APIRequestFactory`` — no ``reverse()``, no URL resolution.
* Simple ``assert x == y`` assertions with ``response.status_code``.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django_tenants.utils import tenant_context
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from orgs.models import Message, Review
from orgs.tests.base import TenantAwareTestCase
from orgs.tests.factories import (
    AssociationFactory,
    AssociationImageFactory,
    BlogCategoryFactory,
    BudgetFactory,
    CatalogItemFactory,
    CatalogItemSpecificationFactory,
    CategoryFactory,
    CustomerFactory,
    DistrictFactory,
    ExtraDocFactory,
    ExtraImageFactory,
    InformationFactory,
    PageFactory,
    PartnerFactory,
    PostFactory,
    PostImageFactory,
    PostVideoFactory,
    ReviewFactory,
    RoleFactory,
    TeamFactory,
    UserFactory,
    VideoFactory,
    YearGoalFactory,
)
from orgs.views import (
    AssociationViewSet,
    BlogCategoryViewSet,
    BudgetViewSet,
    CatalogItemViewSet,
    CategoryViewSet,
    CustomerViewSet,
    DistrictViewSet,
    ExtraDocViewSet,
    MessageViewSet,
    PageViewSet,
    PartnerViewSet,
    PostViewSet,
    ReviewViewSet,
    RoleViewSet,
    TeamViewSet,
    VideoViewSet,
    YearGoalViewSet,
)

User = get_user_model()


# ==========================================
# HELPERS
# ==========================================
def make_request(method, path, user=None, data=None):
    """
    Build an authenticated (or anonymous) DRF request.

    ``user=None`` produces an anonymous request — used to verify the
    anonymous-read policy on public endpoints.
    """
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data=data, format="json")
    if user is not None:
        force_authenticate(request, user=user)
    return request


def _tenant_user(tenant, **kwargs):
    """Create a user bound to the given tenant (factories require it)."""
    return UserFactory(tenant=tenant, **kwargs)


# ==========================================
# 1. CORE & USER MODULE
# ==========================================
class TestCustomerViewSet(TenantAwareTestCase):
    def test_list_customers_anonymous_allowed(self):
        with tenant_context(self.tenant):
            CustomerFactory(user__tenant=self.tenant)
            CustomerFactory(user__tenant=self.tenant)

            view = CustomerViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/customers/"))

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_customer(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant)
            customer = CustomerFactory(user__tenant=self.tenant)

            view = CustomerViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/customers/{customer.id}/"),
                pk=customer.id,
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.data["id"] == customer.id

    def test_retrieve_nonexistent_returns_404(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant)
            view = CustomerViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", "/api/customers/999/", user=user), pk=999
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND


# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER
# ==========================================
class TestPageViewSet(TenantAwareTestCase):
    def test_anonymous_list_returns_active_only(self):
        with tenant_context(self.tenant):
            PageFactory(active=True)
            PageFactory(active=True)
            PageFactory(active=False)

            view = PageViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/pages/"))

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_by_slug(self):
        with tenant_context(self.tenant):
            page = PageFactory(slug="home", active=True)

            view = PageViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/pages/{page.slug}/"), slug=page.slug
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.data["slug"] == "home"

    

    def test_anonymous_cannot_create(self):
        with tenant_context(self.tenant):
            payload = {"slug": "x", "title_pt": "X", "active": True, "order": 1}
            view = PageViewSet.as_view({"post": "create"})
            response = view(make_request("post", "/api/pages/", data=payload))
            assert response.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            )


# ==========================================
# 3. METRICS & GOALS
# ==========================================
class TestYearGoalViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            YearGoalFactory()
            YearGoalFactory()

            view = YearGoalViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/metrics/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_year(self):
        with tenant_context(self.tenant):
            YearGoalFactory(year=2024)
            YearGoalFactory(year=2024)
            YearGoalFactory(year=2025)

            view = YearGoalViewSet.as_view({"get": "list"})
            request = make_request("get", "/api/metrics/?year=2024")
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2
            assert all(item["year"] == 2024 for item in response.data)

    def test_filter_by_dashboard_flag(self):
        with tenant_context(self.tenant):
            YearGoalFactory(show_in_dashboard=True)
            YearGoalFactory(show_in_dashboard=False)

            view = YearGoalViewSet.as_view({"get": "list"})
            request = make_request(
                "get", "/api/metrics/?show_in_dashboard=true"
            )
            response = view(request)
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1


# ==========================================
# 4. DISTRICTS & ASSOCIATIONS
# ==========================================
class TestDistrictViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            DistrictFactory()
            DistrictFactory()

            view = DistrictViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/districts/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve(self):
        with tenant_context(self.tenant):
            district = DistrictFactory(name="North")

            view = DistrictViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/districts/{district.id}/"),
                pk=district.id,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "North"


class TestAssociationViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            AssociationFactory()
            AssociationFactory()

            view = AssociationViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/associations/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_district(self):
        with tenant_context(self.tenant):
            d1 = DistrictFactory()
            d2 = DistrictFactory()
            AssociationFactory(district=d1)
            AssociationFactory(district=d1)
            AssociationFactory(district=d2)

            view = AssociationViewSet.as_view({"get": "list"})
            request = make_request(
                "get", f"/api/associations/?district={d1.id}"
            )
            response = view(request)
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_with_images(self):
        with tenant_context(self.tenant):
            association = AssociationFactory(
                name="CECAB North"
            )
            AssociationImageFactory(
                association=association
            )

            view = AssociationViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/associations/{association.id}/"),
                pk=association.id,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "CECAB North"


# ==========================================
# 5. CATALOGUE
# ==========================================
class TestCategoryViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            CategoryFactory()
            CategoryFactory()

            view = CategoryViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/catalog-categories/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_by_slug(self):
        with tenant_context(self.tenant):
            category = CategoryFactory(
                name="Chocolates", slug="chocolates"
            )
            CatalogItemFactory(category=category)
            CatalogItemFactory(category=category)

            view = CategoryViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request(
                    "get", f"/api/catalog-categories/{category.slug}/"
                ),
                slug=category.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "Chocolates"


class TestCatalogItemViewSet(TenantAwareTestCase):
    def test_anonymous_list_only_available(self):
        with tenant_context(self.tenant):
            CatalogItemFactory(is_available=True)
            CatalogItemFactory(is_available=True)
            CatalogItemFactory(is_available=False)

            view = CatalogItemViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/catalog-items/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_category(self):
        with tenant_context(self.tenant):
            cat_a = CategoryFactory()
            cat_b = CategoryFactory()
            CatalogItemFactory(category=cat_a)
            CatalogItemFactory(category=cat_a)
            CatalogItemFactory(category=cat_b)

            view = CatalogItemViewSet.as_view({"get": "list"})
            response = view(
                make_request(
                    "get", f"/api/catalog-items/?category={cat_a.id}"
                )
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_by_slug_with_specs(self):
        with tenant_context(self.tenant):
            category = CategoryFactory()
            item = CatalogItemFactory(
                category=category,
                name="Dark Chocolate",
                slug="dark-chocolate",
                price=Decimal("25.99"),
                
            )
            CatalogItemSpecificationFactory(
                item=item
            )

            view = CatalogItemViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request(
                    "get", f"/api/catalog-items/{item.slug}/"
                ),
                slug=item.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "Dark Chocolate"

    def test_anonymous_cannot_create(self):
        with tenant_context(self.tenant):
            category = CategoryFactory()
            payload = {
                "category": category.pk,
                "name_pt": "Trufa",
                "slug": "trufa",
                "description_pt": "Doce",
            }
            view = CatalogItemViewSet.as_view({"post": "create"})
            response = view(make_request("post", "/api/catalog-items/", data=payload))
            assert response.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            )


# ==========================================
# 6. POSTS, BLOG & NEWS (nested under category)
# ==========================================
class TestBlogCategoryViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            BlogCategoryFactory()
            BlogCategoryFactory()

            view = BlogCategoryViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/categories/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_by_slug(self):
        with tenant_context(self.tenant):
            cat = BlogCategoryFactory(
                name="News", slug="news"
            )

            view = BlogCategoryViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/categories/{cat.slug}/"),
                slug=cat.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "News"


class TestPostViewSet(TenantAwareTestCase):
    def test_nested_list_filters_by_category(self):
        with tenant_context(self.tenant):
            cat_a = BlogCategoryFactory()
            cat_b = BlogCategoryFactory()
            PostFactory(blog_category=cat_a, active=True)
            PostFactory(blog_category=cat_a, active=True)
            PostFactory(blog_category=cat_b, active=True)

            view = PostViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", f"/api/categories/{cat_a.slug}/posts/"),
                parent_lookup_category=cat_a.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_anonymous_list_hides_inactive(self):
        with tenant_context(self.tenant):
            cat = BlogCategoryFactory()
            PostFactory(blog_category=cat, active=True)
            PostFactory(blog_category=cat, active=False)

            view = PostViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", f"/api/categories/{cat.slug}/posts/"),
                parent_lookup_category=cat.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1

    def test_filter_by_featured(self):
        with tenant_context(self.tenant):
            cat = BlogCategoryFactory()
            PostFactory(
                blog_category=cat, active=True, featured=True,
                
            )
            PostFactory(
                blog_category=cat, active=True, featured=False,
                
            )

            view = PostViewSet.as_view({"get": "list"})
            response = view(
                make_request(
                    "get", f"/api/categories/{cat.slug}/posts/?featured=true"
                ),
                parent_lookup_category=cat.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1

    def test_retrieve_full_post(self):
        with tenant_context(self.tenant):
            cat = BlogCategoryFactory()
            post = PostFactory(
                blog_category=cat,
                title="Test Post",
                slug="test-post",
                active=True,
                text="Full content",
                
            )
            PostImageFactory(post=post)
            PostVideoFactory(
                post=post,
                video=VideoFactory(),
                
            )
            InformationFactory(service=post)

            view = PostViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request(
                    "get", f"/api/categories/{cat.slug}/posts/{post.slug}/"
                ),
                parent_lookup_category=cat.slug,
                slug=post.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Test Post"

    def test_retrieve_inactive_returns_404(self):
        with tenant_context(self.tenant):
            cat = BlogCategoryFactory()
            post = PostFactory(
                blog_category=cat, active=False
            )

            view = PostViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request(
                    "get", f"/api/categories/{cat.slug}/posts/{post.slug}/"
                ),
                parent_lookup_category=cat.slug,
                slug=post.slug,
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_with_wrong_category_returns_404(self):
        with tenant_context(self.tenant):
            cat_a = BlogCategoryFactory()
            cat_b = BlogCategoryFactory()
            post = PostFactory(
                blog_category=cat_a, active=True
            )

            view = PostViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request(
                    "get", f"/api/categories/{cat_b.slug}/posts/{post.slug}/"
                ),
                parent_lookup_category=cat_b.slug,
                slug=post.slug,
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND


# ==========================================
# 7. MULTIMEDIA & COMMUNICATIONS
# ==========================================
class TestVideoViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            VideoFactory()
            VideoFactory()

            view = VideoViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/videos/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_is_band(self):
        with tenant_context(self.tenant):
            VideoFactory(is_band=True)
            VideoFactory(is_band=True)
            VideoFactory(is_band=False)

            view = VideoViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", "/api/videos/?is_band=true")
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_is_spot(self):
        with tenant_context(self.tenant):
            VideoFactory(is_spot=True)
            VideoFactory(is_spot=False)

            view = VideoViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", "/api/videos/?is_spot=true")
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1

    def test_retrieve(self):
        with tenant_context(self.tenant):
            video = VideoFactory(
                title="Band Performance"
            )

            view = VideoViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/videos/{video.id}/"), pk=video.id
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Band Performance"

    def test_anonymous_cannot_write(self):
        with tenant_context(self.tenant):
            payload = {
                "title_pt": "V",
                "link": "https://x",
                "created_at": "2024-01-01",
            }
            view = VideoViewSet.as_view({"post": "create"})
            response = view(make_request("post", "/api/videos/", data=payload))
            assert response.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            )


class TestMessageViewSet(TenantAwareTestCase):
    def test_anonymous_can_submit_message(self):
        with tenant_context(self.tenant):
            payload = {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Hello",
                "text": "Content",
            }
            view = MessageViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/contact-messages/", data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert Message.objects.count() == 1

    def test_invalid_email_returns_400(self):
        with tenant_context(self.tenant):
            payload = {
                "name": "John",
                "email": "not-an-email",
                "subject": "Hi",
                "text": "Content",
            }
            view = MessageViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/contact-messages/", data=payload)
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "email" in response.data

    def test_missing_fields_returns_400(self):
        with tenant_context(self.tenant):
            payload = {"name": "John"}
            view = MessageViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/contact-messages/", data=payload)
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPartnerViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            PartnerFactory()
            PartnerFactory()

            view = PartnerViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/partners/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve(self):
        with tenant_context(self.tenant):
            partner = PartnerFactory(
                title="Fairtrade International"
            )

            view = PartnerViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/partners/{partner.id}/"),
                pk=partner.id,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Fairtrade International"


# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM
# ==========================================
class TestRoleViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            RoleFactory()
            RoleFactory()

            view = RoleViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/roles/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve(self):
        with tenant_context(self.tenant):
            role = RoleFactory(title="President")

            view = RoleViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/roles/{role.id}/"), pk=role.id
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "President"


class TestTeamViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            TeamFactory()
            TeamFactory()

            view = TeamViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/team-members/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_role(self):
        with tenant_context(self.tenant):
            role_a = RoleFactory()
            role_b = RoleFactory()
            TeamFactory(role=role_a)
            TeamFactory(role=role_a)
            TeamFactory(role=role_b)

            view = TeamViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", f"/api/team-members/?role={role_a.id}")
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_from_assembly(self):
        with tenant_context(self.tenant):
            TeamFactory(from_assembly=True)
            TeamFactory(from_assembly=True)
            TeamFactory(from_assembly=False)

            view = TeamViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", "/api/team-members/?from_assembly=true")
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2


# ==========================================
# 9. GENERAL DOCUMENTATION
# ==========================================
class TestBudgetViewSet(TenantAwareTestCase):
    def test_anonymous_list(self):
        with tenant_context(self.tenant):
            BudgetFactory()
            BudgetFactory()

            view = BudgetViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/financial-budgets/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_year(self):
        with tenant_context(self.tenant):
            BudgetFactory(year=2024)
            BudgetFactory(year=2024)
            BudgetFactory(year=2025)

            view = BudgetViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", "/api/financial-budgets/?year=2024")
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_type(self):
        with tenant_context(self.tenant):
            BudgetFactory(type="B")
            BudgetFactory(type="B")
            BudgetFactory(type="R")

            view = BudgetViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", "/api/financial-budgets/?type=B")
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2


class TestExtraDocViewSet(TenantAwareTestCase):
    def test_anonymous_list_hides_inactive(self):
        with tenant_context(self.tenant):
            ExtraDocFactory(active=True)
            ExtraDocFactory(active=True)
            ExtraDocFactory(active=False)

            view = ExtraDocViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/compliance-docs/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_with_images(self):
        with tenant_context(self.tenant):
            doc = ExtraDocFactory(
                title="Quality Certificate",
                active=True,
                
            )
            ExtraImageFactory(extra_doc=doc)

            view = ExtraDocViewSet.as_view({"get": "retrieve"})
            response = view(
                make_request("get", f"/api/compliance-docs/{doc.id}/"),
                pk=doc.id,
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Quality Certificate"


# ==========================================
# 10. REVIEWS
# ==========================================
class TestReviewViewSet(TenantAwareTestCase):
    def test_anonymous_list_approved_only(self):
        with tenant_context(self.tenant):
            user_a = _tenant_user(self.tenant, username="reviewer_a")
            user_b = _tenant_user(self.tenant, username="reviewer_b")
            item = CatalogItemFactory()
            ReviewFactory(
                item=item, client=user_a, is_approved=True,
                
            )
            ReviewFactory(
                item=item, client=user_b, is_approved=False,
                
            )

            view = ReviewViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/reviews/"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1

    def test_filter_by_item(self):
        with tenant_context(self.tenant):
            user_a = _tenant_user(self.tenant, username="ra")
            user_b = _tenant_user(self.tenant, username="rb")
            user_c = _tenant_user(self.tenant, username="rc")
            item_a = CatalogItemFactory()
            item_b = CatalogItemFactory()
            ReviewFactory(
                item=item_a, client=user_a
            )
            ReviewFactory(
                item=item_a, client=user_b
            )
            ReviewFactory(
                item=item_b, client=user_c
            )

            view = ReviewViewSet.as_view({"get": "list"})
            response = view(
                make_request("get", f"/api/orgs/catalog-items/{item_a.id}/reviews/"), catalog_item_pk=item_a.id
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_rating(self):
        with tenant_context(self.tenant):
            user_a = _tenant_user(self.tenant, username="r1")
            user_b = _tenant_user(self.tenant, username="r2")
            user_c = _tenant_user(self.tenant, username="r3")
            item = CatalogItemFactory()
            ReviewFactory(
                item=item, client=user_a, rating=4,
                
            )
            ReviewFactory(
                item=item, client=user_b, rating=4,
                
            )
            ReviewFactory(
                item=item, client=user_c, rating=5,
                
            )

            view = ReviewViewSet.as_view({"get": "list"})
            response = view(make_request("get", "/api/reviews/?rating=4"))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_create_unauthenticated_returns_401(self):
        with tenant_context(self.tenant):
            item = CatalogItemFactory()
            payload = {"item": item.id, "rating": 5, "comment": "Great"}
            view = ReviewViewSet.as_view({"post": "create"})
            response = view(make_request("post", "/api/reviews/", data=payload))
            assert response.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            )

    def test_create_authenticated(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant)
            item = CatalogItemFactory()
            payload = {"item": item.id, "rating": 5, "comment": "Great"}

            view = ReviewViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", f"/api/catalog-items/{item.id}/reviews/", user=user, data=payload),
                item_pk=item.id

            )
            print(response.data)
            assert response.status_code == status.HTTP_201_CREATED
            assert Review.objects.count() == 1
            review = Review.objects.first()
            assert review.client_id == user.id
            assert review.rating == 5

    def test_create_with_invalid_rating_returns_400(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant)
            item = CatalogItemFactory()
            payload = {"item": item.id, "rating": 6, "comment": "Too high"}

            view = ReviewViewSet.as_view({"post": "create"})
           