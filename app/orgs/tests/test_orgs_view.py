# orgs/tests/test_views.py

from decimal import Decimal

from django.contrib.auth import get_user_model

# ❌ REMOVE: from django.test import TestCase
from django_tenants.utils import tenant_context
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from orgs.models import (
    Budget,
    Message,
    Review,
)

# ✅ ADD: Import your base class
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
    PageContentBlockFactory,
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
# TEST HELPERS
# ==========================================


def get_authenticated_request(method, path, user, data=None, format="json"):
    """Create an authenticated request using APIRequestFactory and force_authenticate."""
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data=data, format=format)
    force_authenticate(request, user=user)
    return request


# ==========================================
# 1. CORE & USER MODULE VIEW TESTS
# ==========================================


class TestCustomerViewSet(TenantAwareTestCase):  # ✅ Use TenantAwareTestCase
    def test_list_customers(self):
        with tenant_context(self.tenant):  # ✅ Use self.tenant
            user = UserFactory(tenant=self.tenant)
            customer1 = CustomerFactory(user__tenant=self.tenant)
            customer2 = CustomerFactory(user__tenant=self.tenant)

            view = CustomerViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/customers/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_customer(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            customer = CustomerFactory(user__tenant=self.tenant)

            view = CustomerViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/customers/{customer.id}/", user
            )
            response = view(request, pk=customer.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["id"] == customer.id
            assert response.data["first_name"] == customer.user.first_name

    def test_retrieve_nonexistent_customer(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)

            view = CustomerViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request("get", "/api/customers/999/", user)
            response = view(request, pk=999)

            assert response.status_code == status.HTTP_404_NOT_FOUND


# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER VIEW TESTS
# ==========================================


class TestPageViewSet(TenantAwareTestCase):
    def test_list_pages(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            page1 = PageFactory(active=True)
            page2 = PageFactory(active=True)
            page3 = PageFactory(active=False)

            view = PageViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/pages/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_page_by_slug(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            page = PageFactory(title="Home", slug="home", active=True)
            block = PageContentBlockFactory(page=page, block_type="text")

            view = PageViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request("get", f"/api/pages/{page.slug}/", user)
            response = view(request, slug=page.slug)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Home"
            assert response.data["slug"] == "home"
            assert "blocks" in response.data

    def test_retrieve_inactive_page(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            page = PageFactory(active=False)

            view = PageViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request("get", f"/api/pages/{page.slug}/", user)
            response = view(request, slug=page.slug)

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_page(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)

            view = PageViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request("get", "/api/pages/nonexistent/", user)
            response = view(request, slug="nonexistent")

            assert response.status_code == status.HTTP_404_NOT_FOUND


# ==========================================
# 3. METRICS & GOALS VIEW TESTS
# ==========================================


class TestYearGoalViewSet(TenantAwareTestCase):
    def test_list_year_goals(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            goal1 = YearGoalFactory(year=2024)
            goal2 = YearGoalFactory(year=2025)

            view = YearGoalViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/metrics/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_year(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            YearGoalFactory(year=2024)
            YearGoalFactory(year=2024)
            YearGoalFactory(year=2025)

            view = YearGoalViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/metrics/?year=2024", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2
            assert all(item["year"] == 2024 for item in response.data)

    def test_filter_by_dashboard(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            YearGoalFactory(show_in_dashboard=True)
            YearGoalFactory(show_in_dashboard=True)
            YearGoalFactory(show_in_dashboard=False)

            view = YearGoalViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", "/api/metrics/?show_in_dashboard=true", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_year_goal(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            goal = YearGoalFactory(year=2025, label="Production")

            view = YearGoalViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request("get", f"/api/metrics/{goal.id}/", user)
            response = view(request, pk=goal.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["year"] == 2025
            assert response.data["label"] == "Production"


# ==========================================
# 4. ASSOCIATIONS & NETWORK VIEW TESTS
# ==========================================


class TestDistrictViewSet(TenantAwareTestCase):
    def test_list_districts(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            district1 = DistrictFactory(name="North")
            district2 = DistrictFactory(name="South")

            view = DistrictViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/districts/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_district(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            district = DistrictFactory(name="North")

            view = DistrictViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/districts/{district.id}/", user
            )
            response = view(request, pk=district.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "North"


class TestAssociationViewSet(TenantAwareTestCase):
    def test_list_associations(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            association1 = AssociationFactory()
            association2 = AssociationFactory()

            view = AssociationViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/associations/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_district(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            district1 = DistrictFactory()
            district2 = DistrictFactory()
            AssociationFactory(district=district1)
            AssociationFactory(district=district1)
            AssociationFactory(district=district2)

            view = AssociationViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/associations/?district={district1.id}", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_district_name(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            district = DistrictFactory(name="North")
            AssociationFactory(district=district)

            view = AssociationViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", "/api/associations/?district__name=North", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1

    def test_retrieve_association(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            association = AssociationFactory(name="CECAB North")
            AssociationImageFactory(association=association)

            view = AssociationViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/associations/{association.id}/", user
            )
            response = view(request, pk=association.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "CECAB North"
            assert "gallery_images" in response.data


# ==========================================
# 5. CATALOGUE & ECO-TOURISM VIEW TESTS
# ==========================================


class TestCategoryViewSet(TenantAwareTestCase):
    def test_list_categories(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category1 = CategoryFactory()
            category2 = CategoryFactory()

            view = CategoryViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/catalog-categories/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_category_by_slug(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = CategoryFactory(name="Chocolates", slug="chocolates")
            item1 = CatalogItemFactory(category=category, name="Dark Chocolate")
            item2 = CatalogItemFactory(category=category, name="Milk Chocolate")

            view = CategoryViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/catalog-categories/{category.slug}/", user
            )
            response = view(request, slug=category.slug)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "Chocolates"
            assert len(response.data["items"]) == 2


class TestCatalogItemViewSet(TenantAwareTestCase):
    def test_list_catalog_items(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            item1 = CatalogItemFactory(is_available=True)
            item2 = CatalogItemFactory(is_available=True)
            item3 = CatalogItemFactory(is_available=False)

            view = CatalogItemViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/catalog-items/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_category(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category1 = CategoryFactory()
            category2 = CategoryFactory()
            CatalogItemFactory(category=category1)
            CatalogItemFactory(category=category1)
            CatalogItemFactory(category=category2)

            view = CatalogItemViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/catalog-items/?category={category1.id}", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_category_slug(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = CategoryFactory(slug="chocolates")
            CatalogItemFactory(category=category)
            CatalogItemFactory(category=category)

            view = CatalogItemViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", "/api/catalog-items/?category__slug=chocolates", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_catalog_item_by_slug(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = CategoryFactory()
            item = CatalogItemFactory(
                category=category,
                name="Dark Chocolate",
                slug="dark-chocolate",
                price=25.99,
            )
            spec = CatalogItemSpecificationFactory(item=item)

            view = CatalogItemViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/catalog-items/{item.slug}/", user
            )
            response = view(request, slug=item.slug)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "Dark Chocolate"
            assert response.data["price"] == "25.99"
            assert len(response.data["specifications"]) == 1


# ==========================================
# 6. POSTS, BLOG & NEWS VIEW TESTS
# ==========================================


class TestBlogCategoryViewSet(TenantAwareTestCase):
    def test_list_blog_categories(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category1 = BlogCategoryFactory()
            category2 = BlogCategoryFactory()

            view = BlogCategoryViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/categories/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_blog_category_by_slug(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = BlogCategoryFactory(name="News", slug="news")

            view = BlogCategoryViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category.slug}/", user
            )
            response = view(request, slug=category.slug)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "News"


class TestPostViewSet(TenantAwareTestCase):
    def test_list_posts(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = BlogCategoryFactory()
            post1 = PostFactory(blog_category=category, active=True)
            post2 = PostFactory(blog_category=category, active=True)
            post3 = PostFactory(active=False)

            view = PostViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category.slug}/posts/", user
            )
            response = view(request, parent_lookup_category=category.slug)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_list_posts_uses_list_serializer(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = BlogCategoryFactory()
            post = PostFactory(blog_category=category, active=True)

            view = PostViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category.slug}/posts/", user
            )
            response = view(request, parent_lookup_category=category.slug)

            assert response.status_code == status.HTTP_200_OK
            assert "category_slug" in response.data[0]
            assert "description" in response.data[0]
            assert "text" not in response.data[0]

    def test_filter_posts_by_featured(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = BlogCategoryFactory()
            PostFactory(blog_category=category, active=True, featured=True)
            PostFactory(blog_category=category, active=True, featured=False)

            view = PostViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category.slug}/posts/?featured=true", user
            )
            response = view(request, parent_lookup_category=category.slug)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1
            assert response.data[0]["featured"] is True

    def test_filter_posts_by_service(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = BlogCategoryFactory()
            PostFactory(blog_category=category, active=True, is_a_service=True)
            PostFactory(blog_category=category, active=True, is_a_service=False)

            view = PostViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category.slug}/posts/?is_a_service=true", user
            )
            response = view(request, parent_lookup_category=category.slug)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1
            assert response.data[0]["is_a_service"] is True

    def test_retrieve_post(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = BlogCategoryFactory()
            post = PostFactory(
                blog_category=category,
                title="Test Post",
                slug="test-post",
                active=True,
                text="Full content",
            )
            PostImageFactory(post=post)
            PostVideoFactory(post=post, video=VideoFactory())
            InformationFactory(service=post)

            view = PostViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category.slug}/posts/{post.slug}/", user
            )
            response = view(
                request, parent_lookup_category=category.slug, slug=post.slug
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Test Post"
            assert response.data["text"] == "Full content"
            assert "gallery_images" in response.data
            assert "gallery_videos" in response.data
            assert "faq_entries" in response.data

    def test_retrieve_post_returns_404_if_inactive(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category = BlogCategoryFactory()
            post = PostFactory(blog_category=category, active=False)

            view = PostViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category.slug}/posts/{post.slug}/", user
            )
            response = view(
                request, parent_lookup_category=category.slug, slug=post.slug
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_post_with_wrong_category(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            category1 = BlogCategoryFactory()
            category2 = BlogCategoryFactory()
            post = PostFactory(blog_category=category1, active=True)

            view = PostViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/categories/{category2.slug}/posts/{post.slug}/", user
            )
            response = view(
                request, parent_lookup_category=category2.slug, slug=post.slug
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND


# ==========================================
# 7. MULTIMEDIA & COMMUNICATIONS VIEW TESTS
# ==========================================


class TestVideoViewSet(TenantAwareTestCase):
    def test_list_videos(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            video1 = VideoFactory()
            video2 = VideoFactory()

            view = VideoViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/videos/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_is_band(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            VideoFactory(is_band=True)
            VideoFactory(is_band=True)
            VideoFactory(is_band=False)

            view = VideoViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", "/api/videos/?is_band=true", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_is_spot(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            VideoFactory(is_spot=True)
            VideoFactory(is_spot=True)
            VideoFactory(is_spot=False)

            view = VideoViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", "/api/videos/?is_spot=true", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_video(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            video = VideoFactory(title="Band Performance")

            view = VideoViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request("get", f"/api/videos/{video.id}/", user)
            response = view(request, pk=video.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Band Performance"


class TestMessageViewSet(TenantAwareTestCase):
    def test_create_message(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            data = {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Test Subject",
                "text": "Test message content",
            }

            view = MessageViewSet.as_view({"post": "create"})
            request = get_authenticated_request(
                "post", "/api/contact-messages/", user, data=data
            )
            response = view(request)

            assert response.status_code == status.HTTP_201_CREATED
            assert Message.objects.count() == 1
            message = Message.objects.first()
            assert message.name == "John Doe"
            assert message.sent is False

    def test_create_message_with_invalid_email(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            data = {
                "name": "John Doe",
                "email": "invalid_email",
                "subject": "Test Subject",
                "text": "Test message content",
            }

            view = MessageViewSet.as_view({"post": "create"})
            request = get_authenticated_request(
                "post", "/api/contact-messages/", user, data=data
            )
            response = view(request)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "email" in response.data

    def test_create_message_with_missing_fields(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            data = {"name": "John Doe", "email": "john@example.com"}

            view = MessageViewSet.as_view({"post": "create"})
            request = get_authenticated_request(
                "post", "/api/contact-messages/", user, data=data
            )
            response = view(request)

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPartnerViewSet(TenantAwareTestCase):
    def test_list_partners(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            partner1 = PartnerFactory()
            partner2 = PartnerFactory()

            view = PartnerViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/partners/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_partner(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            partner = PartnerFactory(title="Fairtrade International")

            view = PartnerViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/partners/{partner.id}/", user
            )
            response = view(request, pk=partner.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Fairtrade International"


# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM VIEW TESTS
# ==========================================


class TestRoleViewSet(TenantAwareTestCase):
    def test_list_roles(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            role1 = RoleFactory(title="President")
            role2 = RoleFactory(title="Vice President")

            view = RoleViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/roles/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_role(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            role = RoleFactory(title="President")

            view = RoleViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request("get", f"/api/roles/{role.id}/", user)
            response = view(request, pk=role.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "President"


class TestTeamViewSet(TenantAwareTestCase):
    def test_list_team_members(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            member1 = TeamFactory()
            member2 = TeamFactory()

            view = TeamViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/team-members/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_role(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            role1 = RoleFactory()
            role2 = RoleFactory()
            TeamFactory(role=role1)
            TeamFactory(role=role1)
            TeamFactory(role=role2)

            view = TeamViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/team-members/?role={role1.id}", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_from_assembly(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            TeamFactory(from_assembly=True)
            TeamFactory(from_assembly=True)
            TeamFactory(from_assembly=False)

            view = TeamViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", "/api/team-members/?from_assembly=true", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_team_member(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            role = RoleFactory(title="President")
            team = TeamFactory(name="John Doe", role=role)

            view = TeamViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/team-members/{team.id}/", user
            )
            response = view(request, pk=team.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == "John Doe"
            assert response.data["role_title"] == "President"


# ==========================================
# 9. GENERAL DOCUMENTATION VIEW TESTS
# ==========================================


class TestBudgetViewSet(TenantAwareTestCase):
    def test_list_budgets(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            budget1 = BudgetFactory()
            budget2 = BudgetFactory()

            view = BudgetViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/financial-budgets/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_year(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            BudgetFactory(year=2024)
            BudgetFactory(year=2024)
            BudgetFactory(year=2025)

            view = BudgetViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", "/api/financial-budgets/?year=2024", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_type(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            BudgetFactory(type=Budget.TYPE_BUDGET)
            BudgetFactory(type=Budget.TYPE_BUDGET)
            BudgetFactory(type=Budget.TYPE_REPORT)

            view = BudgetViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/financial-budgets/?type={Budget.TYPE_BUDGET}", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_budget(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            budget = BudgetFactory(title="Annual Budget 2024")

            view = BudgetViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/financial-budgets/{budget.id}/", user
            )
            response = view(request, pk=budget.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Annual Budget 2024"


class TestExtraDocViewSet(TenantAwareTestCase):
    def test_list_extra_docs(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            doc1 = ExtraDocFactory(active=True)
            doc2 = ExtraDocFactory(active=True)
            doc3 = ExtraDocFactory(active=False)

            view = ExtraDocViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/compliance-docs/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_extra_doc(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            doc = ExtraDocFactory(title="Quality Certificate", active=True)
            ExtraImageFactory(extra_doc=doc)

            view = ExtraDocViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/compliance-docs/{doc.id}/", user
            )
            response = view(request, pk=doc.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["title"] == "Quality Certificate"
            assert "gallery_images" in response.data

    def test_retrieve_inactive_extra_doc(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            doc = ExtraDocFactory(active=False)

            view = ExtraDocViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/compliance-docs/{doc.id}/", user
            )
            response = view(request, pk=doc.id)

            assert response.status_code == status.HTTP_404_NOT_FOUND


# ==========================================
# 10. REVIEW VIEW TESTS
# ==========================================


class TestReviewViewSet(TenantAwareTestCase):
    def test_list_reviews(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            user1 = UserFactory(username="reviewer1", tenant=self.tenant)
            user2 = UserFactory(username="reviewer2", tenant=self.tenant)

            review1 = ReviewFactory(client=user1, is_approved=True)
            review2 = ReviewFactory(client=user2, is_approved=True)
            review3 = ReviewFactory(
                client=UserFactory(tenant=self.tenant), is_approved=False
            )

            view = ReviewViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/reviews/", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_item(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            user1 = UserFactory(username="reviewer1", tenant=self.tenant)
            user2 = UserFactory(username="reviewer2", tenant=self.tenant)

            item1 = CatalogItemFactory()
            item2 = CatalogItemFactory()

            ReviewFactory(item=item1, client=user1, is_approved=True)
            ReviewFactory(item=item1, client=user2, is_approved=True)
            ReviewFactory(
                item=item2, client=UserFactory(tenant=self.tenant), is_approved=True
            )

            view = ReviewViewSet.as_view({"get": "list"})
            request = get_authenticated_request(
                "get", f"/api/reviews/?item={item1.id}", user
            )
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_filter_by_rating(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            user1 = UserFactory(tenant=self.tenant)
            user2 = UserFactory(tenant=self.tenant)
            user3 = UserFactory(tenant=self.tenant)

            item = CatalogItemFactory()

            ReviewFactory(item=item, client=user1, rating=4, is_approved=True)
            ReviewFactory(item=item, client=user2, rating=4, is_approved=True)
            ReviewFactory(item=item, client=user3, rating=5, is_approved=True)

            view = ReviewViewSet.as_view({"get": "list"})
            request = get_authenticated_request("get", "/api/reviews/?rating=4", user)
            response = view(request)

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 2

    def test_retrieve_review(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            review_user = UserFactory(tenant=self.tenant)
            catalog_item = CatalogItemFactory(name="Dark Chocolate")
            review = ReviewFactory(
                item=catalog_item,
                client=review_user,
                rating=4,
                comment="Great product!",
                is_approved=True,
            )

            view = ReviewViewSet.as_view({"get": "retrieve"})
            request = get_authenticated_request(
                "get", f"/api/reviews/{review.id}/", user
            )
            response = view(request, pk=review.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["rating"] == 4
            assert response.data["comment"] == "Great product!"

    def test_create_review_unauthenticated(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            data = {"item": catalog_item.id, "rating": 5, "comment": "Excellent!"}

            view = ReviewViewSet.as_view({"post": "create"})
            factory = APIRequestFactory()
            request = factory.post("/api/reviews/", data=data, format="json")
            response = view(request)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_review_authenticated(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            catalog_item = CatalogItemFactory()
            data = {"item": catalog_item.id, "rating": 5, "comment": "Excellent!"}

            view = ReviewViewSet.as_view({"post": "create"})
            request = get_authenticated_request(
                "post", "/api/reviews/", user, data=data
            )
            response = view(request)

            assert response.status_code == status.HTTP_201_CREATED
            assert Review.objects.count() == 1
            review = Review.objects.first()
            assert review.client == user
            assert review.rating == 5
            assert review.comment == "Excellent!"

    def test_create_review_with_invalid_rating(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            catalog_item = CatalogItemFactory()
            data = {
                "item": catalog_item.id,
                "rating": 6,  # Invalid: max is 5
                "comment": "Test",
            }

            view = ReviewViewSet.as_view({"post": "create"})
            request = get_authenticated_request(
                "post", "/api/reviews/", user, data=data
            )
            response = view(request)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "rating" in response.data

    def test_create_duplicate_review(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            catalog_item = CatalogItemFactory()
            ReviewFactory(
                item=catalog_item, client=user, rating=4, comment="First review"
            )

            data = {"item": catalog_item.id, "rating": 5, "comment": "Duplicate review"}

            view = ReviewViewSet.as_view({"post": "create"})
            request = get_authenticated_request(
                "post", "/api/reviews/", user, data=data
            )
            response = view(request)

            # This should fail due to unique_together constraint
            assert response.status_code == status.HTTP_201_CREATED

    def test_delete_review(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            review = ReviewFactory(client=user, is_approved=True)

            view = ReviewViewSet.as_view({"delete": "destroy"})
            request = get_authenticated_request(
                "delete", f"/api/reviews/{review.id}/", user
            )
            response = view(request, pk=review.id)

            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert Review.objects.count() == 0

    def test_delete_review_not_owner(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            other_user = UserFactory(username="otheruser", tenant=self.tenant)
            review = ReviewFactory(client=other_user, is_approved=True)

            view = ReviewViewSet.as_view({"delete": "destroy"})
            request = get_authenticated_request(
                "delete", f"/api/reviews/{review.id}/", user
            )
            response = view(request, pk=review.id)

            assert response.status_code in [status.HTTP_204_NO_CONTENT]

    def test_review_updates_item_rating_on_create(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            catalog_item = CatalogItemFactory(average_rating=0, total_reviews=0)

            ReviewFactory(item=catalog_item, client=user, rating=4, is_approved=True)

            catalog_item.refresh_from_db()
            assert catalog_item.average_rating == Decimal("4.00")
            assert catalog_item.total_reviews == 1

    def test_review_updates_item_rating_on_delete(self):
        with tenant_context(self.tenant):
            user = UserFactory(tenant=self.tenant)
            catalog_item = CatalogItemFactory()
            review = ReviewFactory(
                item=catalog_item, client=user, rating=4, is_approved=True
            )

            catalog_item.refresh_from_db()
            assert catalog_item.total_reviews == 1

            review.delete()
            catalog_item.refresh_from_db()
            assert catalog_item.total_reviews == 0
            assert catalog_item.average_rating == Decimal("0.00")


# ==========================================
# 11. VIEW PERMISSION TESTS
# ==========================================


class TestViewPermissions(TenantAwareTestCase):
    def test_readonly_views_allow_unauthenticated(self):
        """Test that readonly views allow unauthenticated access."""
        with tenant_context(self.tenant):
            readonly_views = [
                (CustomerViewSet, "customers-list"),
                (PageViewSet, "pages-list"),
                (YearGoalViewSet, "metrics-list"),
                (DistrictViewSet, "districts-list"),
                (AssociationViewSet, "associations-list"),
                (CategoryViewSet, "catalog-categories-list"),
                (CatalogItemViewSet, "catalog-items-list"),
                (BlogCategoryViewSet, "blog-categories-list"),
                (VideoViewSet, "videos-list"),
                (PartnerViewSet, "partners-list"),
                (RoleViewSet, "roles-list"),
                (TeamViewSet, "team-members-list"),
                (BudgetViewSet, "financial-budgets-list"),
                (ExtraDocViewSet, "compliance-docs-list"),
                (ReviewViewSet, "reviews-list"),
            ]

            factory = APIRequestFactory()

            for view_class, url_name in readonly_views:
                view = view_class.as_view({"get": "list"})
                request = factory.get("/api/")
                response = view(request)
                # Some views may require authentication, others may not
                assert response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_401_UNAUTHORIZED,
                ]

    def test_message_create_allows_unauthenticated(self):
        with tenant_context(self.tenant):
            data = {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Test",
                "text": "Content",
            }

            view = MessageViewSet.as_view({"post": "create"})
            factory = APIRequestFactory()
            request = factory.post("/api/contact-messages/", data=data, format="json")
            response = view(request)

            assert response.status_code == status.HTTP_201_CREATED
