
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django_tenants.utils import tenant_context
from rest_framework.test import APIRequestFactory

from orgs.models import (
    Budget,
)
from orgs.serializers import (
    AssociationSerializer,
    BlogCategorySerializer,
    BudgetSerializer,
    CatalogItemSerializer,
    CatalogItemSpecificationSerializer,
    CategoryDetailSerializer,
    CustomerSerializer,
    DistrictSerializer,
    ExtraDocSerializer,
    InformationSerializer,
    MessageSerializer,
    PageContentBlockSerializer,
    PageDetailSerializer,
    PartnerSerializer,
    PostDetailSerializer,
    PostListSerializer,
    ReviewSerializer,
    RoleSerializer,
    TeamSerializer,
    VideoSerializer,
    YearGoalSerializer,
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
    MessageFactory,
    PageContentBlockFactory,
    PageFactory,
    PartnerFactory,
    PostDocumentFactory,
    PostFactory,
    PostFileFactory,
    PostImageFactory,
    PostVideoFactory,
    ReviewFactory,
    RoleFactory,
    TeamFactory,
    VideoFactory,
    YearGoalFactory,
    generate_file_json,
)

User = get_user_model()


# ==========================================
# 1. CORE & USER MODULE SERIALIZER TESTS
# ==========================================


class TestCustomerSerializer(TenantAwareTestCase):
    def test_customer_serializer(self):
        with tenant_context(self.tenant):
            customer = CustomerFactory(
                user__username="testuser",
                user__first_name="John",
                user__last_name="Doe",
                user__email="john@example.com",
                user__tenant=self.tenant,
            )
            serializer = CustomerSerializer(customer)
            data = serializer.data

            assert data["id"] == customer.id
            assert data["first_name"] == "John"
            assert data["last_name"] == "Doe"
            assert data["email"] == "john@example.com"


# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER SERIALIZER TESTS
# ==========================================


class TestPageContentBlockSerializer(TenantAwareTestCase):
    def test_page_content_block_serializer(self):
        with tenant_context(self.tenant):
            page = PageFactory()
            block = PageContentBlockFactory(
                page=page,
                block_type="text",
                title="Welcome Section",
                content="<p>Welcome</p>",
                order=1,
            )
            serializer = PageContentBlockSerializer(block)
            data = serializer.data

            assert data["id"] == block.id
            assert data["block_type"] == "text"
            assert data["title"] == "Welcome Section"
            assert data["content"] == "<p>Welcome</p>"
            assert data["order"] == 1


class TestPageDetailSerializer(TenantAwareTestCase):
    def test_page_detail_serializer(self):
        with tenant_context(self.tenant):
            page = PageFactory(title="Home", slug="home", active=True, order=1)
            block1 = PageContentBlockFactory(page=page, block_type="text", order=1)
            block2 = PageContentBlockFactory(page=page, block_type="hero", order=2)

            serializer = PageDetailSerializer(page)
            data = serializer.data

            assert data["id"] == page.id
            assert data["title"] == "Home"
            assert data["slug"] == "home"
            assert data["active"] is True
            assert data["order"] == 1
            assert "blocks" in data
            assert len(data["blocks"]) == 2
            assert data["blocks"][0]["block_type"] == "text"
            assert data["blocks"][1]["block_type"] == "hero"

    def test_page_detail_serializer_only_active_blocks(self):
        with tenant_context(self.tenant):
            page = PageFactory(active=True)
            block1 = PageContentBlockFactory(page=page, block_type="text", order=1)
            # Create an inactive page with blocks
            inactive_page = PageFactory(active=False)
            block2 = PageContentBlockFactory(
                page=inactive_page, block_type="hero", order=2
            )

            serializer = PageDetailSerializer(page)
            data = serializer.data

            # Should only include blocks from active pages
            assert len(data["blocks"]) == 1
            assert data["blocks"][0]["block_type"] == "text"


# ==========================================
# 3. METRICS & GOALS SERIALIZER TESTS
# ==========================================


class TestYearGoalSerializer(TenantAwareTestCase):
    def test_year_goal_serializer(self):
        with tenant_context(self.tenant):
            goal = YearGoalFactory(
                year=2025,
                label="Chocolate Produced",
                value=1500.50,
                show_in_dashboard=True,
            )
            serializer = YearGoalSerializer(goal)
            data = serializer.data

            assert data["id"] == goal.id
            assert data["year"] == 2025
            assert data["label"] == "Chocolate Produced"
            assert data["value"] == "1500.50"
            assert data["show_in_dashboard"] is True


# ==========================================
# 4. ASSOCIATIONS & NETWORK SERIALIZER TESTS
# ==========================================


class TestDistrictSerializer(TenantAwareTestCase):
    def test_district_serializer(self):
        with tenant_context(self.tenant):
            district = DistrictFactory(name="North Region")
            serializer = DistrictSerializer(district)
            data = serializer.data

            assert data["id"] == district.id
            assert data["name"] == "North Region"


class TestAssociationSerializer(TenantAwareTestCase):
    def test_association_serializer(self):
        with tenant_context(self.tenant):
            district = DistrictFactory(name="North Region")
            association = AssociationFactory(
                name="CECAB North", district=district, number_of_associated=150
            )
            serializer = AssociationSerializer(association)
            data = serializer.data

            assert data["id"] == association.id
            assert data["name"] == "CECAB North"
            assert data["district"] == district.id
            assert data["district_name"] == "North Region"
            assert data["number_of_associated"] == 150

    def test_association_serializer_with_gallery_images(self):
        with tenant_context(self.tenant):
            association = AssociationFactory()
            img1 = AssociationImageFactory(association=association)
            img2 = AssociationImageFactory(association=association)

            serializer = AssociationSerializer(association)
            data = serializer.data

            assert "gallery_images" in data
            assert len(data["gallery_images"]) == 2


# ==========================================
# 5. CATALOGUE & ECO-TOURISM SERIALIZER TESTS
# ==========================================


class TestCatalogItemSpecificationSerializer(TenantAwareTestCase):
    def test_specification_serializer(self):
        with tenant_context(self.tenant):
            item = CatalogItemFactory()
            spec = CatalogItemSpecificationFactory(
                item=item, key="Certification", value="Fairtrade"
            )
            serializer = CatalogItemSpecificationSerializer(spec)
            data = serializer.data

            assert data["id"] == spec.id
            assert data["key"] == "Certification"
            assert data["value"] == "Fairtrade"


class TestCatalogItemSerializer(TenantAwareTestCase):
    def test_catalog_item_serializer(self):
        with tenant_context(self.tenant):
            category = CategoryFactory(name="Chocolates")
            item = CatalogItemFactory(
                category=category,
                name="Dark Chocolate",
                slug="dark-chocolate",
                description="Premium dark chocolate",
                price=25.99,
                is_available=True,
            )
            spec = CatalogItemSpecificationFactory(
                item=item, key="Origin", value="Ghana"
            )

            serializer = CatalogItemSerializer(item)
            data = serializer.data

            assert data["id"] == item.id
            assert data["category"] == category.id
            assert data["category_name"] == "Chocolates"
            assert data["name"] == "Dark Chocolate"
            assert data["slug"] == "dark-chocolate"
            assert data["description"] == "Premium dark chocolate"
            assert data["price"] == "25.99"
            assert data["is_available"] is True
            assert "specifications" in data
            assert len(data["specifications"]) == 1
            assert data["specifications"][0]["key"] == "Origin"


class TestCategoryDetailSerializer(TenantAwareTestCase):
    def test_category_detail_serializer(self):
        with tenant_context(self.tenant):
            category = CategoryFactory(name="Chocolates", slug="chocolates")
            item1 = CatalogItemFactory(category=category, name="Dark Chocolate")
            item2 = CatalogItemFactory(category=category, name="Milk Chocolate")

            serializer = CategoryDetailSerializer(category)
            data = serializer.data

            assert data["id"] == category.id
            assert data["name"] == "Chocolates"
            assert data["slug"] == "chocolates"
            assert "items" in data
            assert len(data["items"]) == 2
            assert data["items"][0]["name"] == "Dark Chocolate"
            assert data["items"][1]["name"] == "Milk Chocolate"


# ==========================================
# 6. POSTS, BLOG & NEWS SERIALIZER TESTS
# ==========================================


class TestBlogCategorySerializer(TenantAwareTestCase):
    def test_blog_category_serializer(self):
        with tenant_context(self.tenant):
            category = BlogCategoryFactory(name="News", slug="news")
            serializer = BlogCategorySerializer(category)
            data = serializer.data

            assert data["id"] == category.id
            assert data["name"] == "News"
            assert data["slug"] == "news"


class TestInformationSerializer(TenantAwareTestCase):
    def test_information_serializer(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            info = InformationFactory(
                service=post, question="What is this?", information="This is a test"
            )
            serializer = InformationSerializer(info)
            data = serializer.data

            assert data["id"] == info.id
            assert data["question"] == "What is this?"
            assert data["information"] == "This is a test"


class TestPostListSerializer(TenantAwareTestCase):
    def test_post_list_serializer(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory(slug="news")
            post = PostFactory(
                blog_category=blog_category,
                title="Test Post",
                slug="test-post",
                active=True,
                featured=True,
                is_a_service=False,
                is_social_service=True,
                is_to_front=False,
                description="Test description",
            )
            serializer = PostListSerializer(post)
            data = serializer.data

            assert data["id"] == post.id
            assert data["title"] == "Test Post"
            assert data["slug"] == "test-post"
            assert data["category_slug"] == "news"
            assert data["active"] is True
            assert data["featured"] is True
            assert data["is_a_service"] is False
            assert data["is_social_service"] is True
            assert data["is_to_front"] is False
            assert data["description"] == "Test description"
            assert "picture" in data
            assert "date" in data


class TestPostDetailSerializer(TenantAwareTestCase):
    def test_post_detail_serializer(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory(name="News", slug="news")
            post = PostFactory(
                blog_category=blog_category,
                title="Test Post",
                slug="test-post",
                active=True,
                featured=True,
                text="Full content",
                description="Test description",
            )
            image = PostImageFactory(post=post)
            file = PostFileFactory(post=post)
            document = PostDocumentFactory(post=post)
            video = VideoFactory(
                title="Test Video", link="https://youtube.com/watch?v=123"
            )
            post_video = PostVideoFactory(post=post, video=video)
            info = InformationFactory(
                service=post, question="FAQ?", information="Answer"
            )

            serializer = PostDetailSerializer(post)
            data = serializer.data

            assert data["id"] == post.id
            assert data["category"]["name"] == "News"
            assert data["title"] == "Test Post"
            assert data["slug"] == "test-post"
            assert data["active"] is True
            assert data["featured"] is True
            assert data["text"] == "Full content"
            assert data["description"] == "Test description"
            assert "gallery_images" in data
            assert len(data["gallery_images"]) == 1
            assert "gallery_videos" in data
            assert len(data["gallery_videos"]) == 1
            assert data["gallery_videos"][0]["title"] == "Test Video"
            assert data["gallery_videos"][0]["url"] == "https://youtube.com/watch?v=123"
            assert "downloadable_documents" in data
            assert "faq_entries" in data
            assert len(data["faq_entries"]) == 1
            assert data["faq_entries"][0]["question"] == "FAQ?"

    @patch("orgs.serializers.json.load")
    def test_post_detail_serializer_with_parsed_json(self, mock_json_load):
        with tenant_context(self.tenant):
            fake_file = generate_file_json()

            mock_json_load.return_value = {"parsed": "data"}

            post = PostFactory(processed_text_file=fake_file)
            serializer = PostDetailSerializer(post)

            data = serializer.data
            assert "parsed_json_data" in data

    def test_post_detail_serializer_without_processed_file(self):
        with tenant_context(self.tenant):
            post = PostFactory(processed_text_file=None)
            serializer = PostDetailSerializer(post)
            data = serializer.data

            assert data["parsed_json_data"] is None


# ==========================================
# 7. MULTIMEDIA & COMMUNICATIONS SERIALIZER TESTS
# ==========================================


class TestVideoSerializer(TenantAwareTestCase):
    def test_video_serializer(self):
        with tenant_context(self.tenant):
            video = VideoFactory(
                title="Band Performance",
                link="https://youtube.com/watch?v=123",
                is_band=True,
                is_spot=False,
            )
            serializer = VideoSerializer(video)
            data = serializer.data

            assert data["id"] == video.id
            assert data["title"] == "Band Performance"
            assert data["link"] == "https://youtube.com/watch?v=123"
            assert data["is_band"] is True
            assert data["is_spot"] is False
            assert "created_at" in data


class TestMessageSerializer(TenantAwareTestCase):
    def test_message_serializer(self):
        with tenant_context(self.tenant):
            message = MessageFactory(
                name="John Doe",
                email="john@example.com",
                subject="Test Subject",
                text="Test content",
            )
            serializer = MessageSerializer(message)
            data = serializer.data

            assert data["id"] == message.id
            assert data["name"] == "John Doe"
            assert data["email"] == "john@example.com"
            assert data["subject"] == "Test Subject"
            assert data["text"] == "Test content"
            assert data["sent"] is False
            assert "date" in data

    def test_message_serializer_read_only_fields(self):
        with tenant_context(self.tenant):
            data = {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Test",
                "text": "Content",
                "sent": True,  # Should be ignored
            }
            serializer = MessageSerializer(data=data)
            assert serializer.is_valid()
            message = serializer.save()
            assert message.sent is False  # Should default to False


class TestPartnerSerializer(TenantAwareTestCase):
    def test_partner_serializer(self):
        with tenant_context(self.tenant):
            partner = PartnerFactory(title="Fairtrade International")
            serializer = PartnerSerializer(partner)
            data = serializer.data

            assert data["id"] == partner.id
            assert data["title"] == "Fairtrade International"
            assert "picture" in data


# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM SERIALIZER TESTS
# ==========================================


class TestRoleSerializer(TenantAwareTestCase):
    def test_role_serializer(self):
        with tenant_context(self.tenant):
            role = RoleFactory(title="President")
            serializer = RoleSerializer(role)
            data = serializer.data

            assert data["id"] == role.id
            assert data["title"] == "President"


class TestTeamSerializer(TenantAwareTestCase):
    def test_team_serializer(self):
        with tenant_context(self.tenant):
            role = RoleFactory(title="President")
            team = TeamFactory(name="John Doe", role=role, from_assembly=True)
            serializer = TeamSerializer(team)
            data = serializer.data

            assert data["id"] == team.id
            assert data["name"] == "John Doe"
            assert data["role"] == role.id
            assert data["role_title"] == "President"
            assert data["from_assembly"] is True


# ==========================================
# 9. GENERAL DOCUMENTATION SERIALIZER TESTS
# ==========================================


class TestBudgetSerializer(TenantAwareTestCase):
    def test_budget_serializer(self):
        with tenant_context(self.tenant):
            budget = BudgetFactory(
                title="Annual Budget 2024",
                slug="annual-budget-2024",
                year=2024,
                type=Budget.TYPE_BUDGET,
            )
            serializer = BudgetSerializer(budget)
            data = serializer.data

            assert data["id"] == budget.id
            assert data["title"] == "Annual Budget 2024"
            assert data["slug"] == "annual-budget-2024"
            assert data["year"] == 2024
            assert data["type"] == "B"
            assert "text_file" in data
            assert "date" in data


class TestExtraDocSerializer(TenantAwareTestCase):
    def test_extra_doc_serializer(self):
        with tenant_context(self.tenant):
            extra_doc = ExtraDocFactory(
                title="Quality Certificate", slug="quality-cert", active=True
            )
            extra_image = ExtraImageFactory(extra_doc=extra_doc)

            serializer = ExtraDocSerializer(extra_doc)
            data = serializer.data

            assert data["id"] == extra_doc.id
            assert data["title"] == "Quality Certificate"
            assert data["slug"] == "quality-cert"
            assert data["active"] is True
            assert "gallery_images" in data
            assert len(data["gallery_images"]) == 1


# ==========================================
# REVIEW SERIALIZER TESTS
# ==========================================


class TestReviewSerializer(TenantAwareTestCase):
    def test_review_serializer(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory(name="Dark Chocolate")
            user = User.objects.create_user(
                username="reviewer", password="testpass123", first_name="John"
            )
            review = ReviewFactory(
                item=catalog_item,
                client=user,
                rating=4,
                comment="Great product!",
                is_approved=True,
            )
            serializer = ReviewSerializer(review)
            data = serializer.data

            assert data["id"] == review.id
            assert data["item"] == catalog_item.id
            assert data["client_name"] == "John"
            assert data["rating"] == 4
            assert data["comment"] == "Great product!"
            assert "created_at" in data

    def test_review_serializer_validation(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            data = {
                "item": catalog_item.id,
                "rating": 6,  # Invalid: max is 5
                "comment": "Test",
            }
            serializer = ReviewSerializer(data=data)
            assert not serializer.is_valid()
            assert "rating" in serializer.errors

    def test_review_serializer_rating_min_validation(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            data = {
                "item": catalog_item.id,
                "rating": 0,  # Invalid: min is 1
                "comment": "Test",
            }
            serializer = ReviewSerializer(data=data)
            assert not serializer.is_valid()
            assert "rating" in serializer.errors

    def test_review_serializer_create_with_client(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            user = User.objects.create_user(username="reviewer", password="testpass123")

            # Create a mock request with user
            factory = APIRequestFactory()
            request = factory.post("/api/reviews/")
            request.user = user

            data = {"item": catalog_item.id, "rating": 5, "comment": "Excellent!"}
            serializer = ReviewSerializer(data=data, context={"request": request})
            assert serializer.is_valid()
            review = serializer.save()
            assert review.client == user
            assert review.rating == 5
            assert review.comment == "Excellent!"


# ==========================================
# SERIALIZER INTEGRATION TESTS
# ==========================================


class TestSerializerIntegration(TenantAwareTestCase):
    def test_post_detail_serializer_with_all_relations(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory()
            post = PostFactory(blog_category=blog_category)

            # Create all related objects
            PostImageFactory(post=post)
            PostImageFactory(post=post)
            PostFileFactory(post=post)
            PostDocumentFactory(post=post)
            PostVideoFactory(post=post, video=VideoFactory())
            PostVideoFactory(post=post, video=VideoFactory())
            InformationFactory(service=post)
            InformationFactory(service=post)

            serializer = PostDetailSerializer(post)
            data = serializer.data

            assert len(data["gallery_images"]) == 2
            assert len(data["gallery_videos"]) == 2
            assert "downloadable_documents" in data
            assert len(data["faq_entries"]) == 2

    def test_category_detail_serializer_with_items(self):
        with tenant_context(self.tenant):
            category = CategoryFactory()
            for i in range(3):
                CatalogItemFactory(category=category, name=f"Item {i}")

            serializer = CategoryDetailSerializer(category)
            data = serializer.data

            assert len(data["items"]) == 3
            assert data["items"][0]["name"] == "Item 0"

    def test_association_serializer_with_gallery(self):
        with tenant_context(self.tenant):
            association = AssociationFactory()
            for i in range(3):
                AssociationImageFactory(association=association)

            serializer = AssociationSerializer(association)
            data = serializer.data

            assert len(data["gallery_images"]) == 3


# ==========================================
# SERIALIZER FIELD TESTS
# ==========================================


class TestSerializerFields(TenantAwareTestCase):
    def test_customer_serializer_fields(self):
        with tenant_context(self.tenant):
            customer = CustomerFactory(
                user__first_name="John",
                user__last_name="Doe",
                user__email="john@example.com",
                user__tenant=self.tenant,
            )
            serializer = CustomerSerializer(customer)
            data = serializer.data

            expected_fields = ["id", "first_name", "last_name", "email"]
            assert sorted(data.keys()) == sorted(expected_fields)

    def test_post_list_serializer_fields(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            serializer = PostListSerializer(post)
            data = serializer.data

            expected_fields = [
                "id",
                "title",
                "slug",
                "category_slug",
                "picture",
                "active",
                "date",
                "featured",
                "is_a_service",
                "is_social_service",
                "is_to_front",
                "description",
            ]
            assert sorted(data.keys()) == sorted(expected_fields)

    def test_post_detail_serializer_fields(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            serializer = PostDetailSerializer(post)
            data = serializer.data

            expected_fields = [
                "id",
                "category",
                "title",
                "slug",
                "picture",
                "text_file",
                "processed_text_file",
                "active",
                "date",
                "featured",
                "is_a_service",
                "is_social_service",
                "is_to_front",
                "description",
                "text",
                "gallery_images",
                "gallery_videos",
                "downloadable_documents",
                "faq_entries",
                "parsed_json_data",
            ]
            assert sorted(data.keys()) == sorted(expected_fields)
