
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django_tenants.utils import tenant_context

from orgs.models import (
    Association,
    BlogCategory,
    Budget,
    Customer,
    Page,
    PageContentBlock,
    Post,
    Review,
)

# ✅ IMPORT: Your base class
from orgs.tests.base import TenantAwareTestCase
from orgs.tests.factories import (
    AssociationFactory,
    AssociationImageFactory,
    BlogCategoryFactory,
    BlogCategoryFactorySingle,
    BudgetFactory,
    CatalogItemFactory,
    CatalogItemSpecificationFactory,
    CategoryFactory,
    CategoryFactorySingle,
    CustomerFactory,
    DistrictFactory,
    ExtraDocFactory,
    ExtraImageFactory,
    InformationFactory,
    MessageFactory,
    PageContentBlockFactory,
    PageFactory,
    PageFactorySingle,
    PartnerFactory,
    PostDocumentFactory,
    PostFactory,
    PostFileFactory,
    PostImageFactory,
    PostVideoFactory,
    ReviewFactory,
    ReviewFactorySingle,
    RoleFactory,
    TeamFactory,
    UserFactory,
    VideoFactory,
    YearGoalFactory,
)

User = get_user_model()


# ==========================================
# 1. CORE & USER MODULE TESTS
# ==========================================


class TestCustomerModel(TenantAwareTestCase):
    def test_customer_creation(self):
        with tenant_context(self.tenant):
            customer = CustomerFactory(
                user__username="testuser", user__tenant=self.tenant, domain=None
            )
            assert customer.user.username == "testuser"
            assert customer.domain is None
            assert (
                str(customer) == f"{customer.user.first_name} {customer.user.last_name}"
            )

    def test_customer_domain_nullable(self):
        with tenant_context(self.tenant):
            customer = CustomerFactory(
                user__username="testuser2", user__tenant=self.tenant, domain=None
            )
            assert customer.domain is None


# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER TESTS
# ==========================================


class TestPageModel(TenantAwareTestCase):
    def test_page_creation(self):
        with tenant_context(self.tenant):
            page = PageFactory(title="Home", slug="home", active=True, order=1)
            assert page.title == "Home"
            assert page.slug == "home"
            assert page.active is True
            assert page.order == 1
            assert str(page) == "Home"

    def test_page_ordering(self):
        with tenant_context(self.tenant):
            PageFactory(title="Home", slug="home", order=1)
            PageFactory(title="About", slug="about", order=2)
            PageFactory(title="Contact", slug="contact", order=0)

            pages = Page.objects.all().order_by("order")
            assert pages[0].order == 0
            assert pages[0].title == "Contact"


class TestPageContentBlockModel(TenantAwareTestCase):
    def test_block_creation(self):
        with tenant_context(self.tenant):
            page = PageFactory()
            block = PageContentBlockFactory(
                page=page,
                block_type="text",
                title="Welcome Section",
                content="<p>Welcome to our site</p>",
                order=1,
            )
            assert block.page.title == page.title
            assert block.block_type == "text"
            assert block.title == "Welcome Section"
            assert block.content == "<p>Welcome to our site</p>"
            assert str(block) == f"{page.title} - text (Welcome Section)"

    def test_block_ordering(self):
        with tenant_context(self.tenant):
            page = PageFactory()
            PageContentBlockFactory(
                page=page, block_type="hero", title="Hero Banner", order=0
            )
            PageContentBlockFactory(
                page=page, block_type="text", title="Text Section", order=1
            )

            blocks = PageContentBlock.objects.filter(page=page).order_by("order")
            assert blocks[0].order == 0
            assert blocks[0].block_type == "hero"
            assert blocks[1].order == 1
            assert blocks[1].block_type == "text"


# ==========================================
# 3. METRICS & GOALS TESTS
# ==========================================


class TestYearGoalModel(TenantAwareTestCase):
    def test_year_goal_creation(self):
        with tenant_context(self.tenant):
            goal = YearGoalFactory(
                year=2025,
                label="Chocolate Produced",
                value=1500.50,
                show_in_dashboard=True,
            )
            assert goal.year == 2025
            assert goal.label == "Chocolate Produced"
            assert goal.value == Decimal("1500.50")
            assert goal.show_in_dashboard is True
            assert str(goal) == "Chocolate Produced (2025): 1500.50"


# ==========================================
# 4. ASSOCIATIONS & NETWORK TESTS
# ==========================================


class TestDistrictModel(TenantAwareTestCase):
    def test_district_creation(self):
        with tenant_context(self.tenant):
            district = DistrictFactory(name="North Region")
            assert district.name == "North Region"
            assert str(district) == "North Region"



class TestAssociationModel(TenantAwareTestCase):
    def test_association_creation(self):
        with tenant_context(self.tenant):
            district = DistrictFactory()
            association = AssociationFactory(
                name="CECAB North", 
                district=district, 
                number_of_associated=150,
                latitude=Decimal("-23.550520"),  
                longitude=Decimal("-46.633309")
            )
            assert association.name == "CECAB North"
            assert association.district.name == district.name
            assert association.number_of_associated == 150
            assert str(association) == "CECAB North"
            
            assert association.latitude == Decimal("-23.550520")
            assert association.longitude == Decimal("-46.633309")

    def test_association_factory_defaults(self):
        """Verifies that the factory automatically generates valid bounding box coordinates."""
        with tenant_context(self.tenant):
            association = AssociationFactory()
            
            assert association.latitude is not None
            assert -90 <= association.latitude <= 90
            
            assert association.longitude is not None
            assert -180 <= association.longitude <= 180

    def test_association_optimized_query(self):
        with tenant_context(self.tenant):
            district = DistrictFactory()
            association = AssociationFactory(district=district)
            queried = Association.objects.optimized().get(id=association.id)
            assert queried.district.name == association.district.name



class TestAssociationImageModel(TenantAwareTestCase):
    def test_association_image_creation(self):
        with tenant_context(self.tenant):
            association = AssociationFactory()
            img = AssociationImageFactory(association=association)
            assert img.association.name == association.name
            assert img.image is not None


# ==========================================
# 5. CATALOGUE & ECO-TOURISM TESTS
# ==========================================


class TestCategoryModel(TenantAwareTestCase):
    def test_category_creation(self):
        with tenant_context(self.tenant):
            category = CategoryFactory(name="Chocolates", slug="chocolates")
            assert category.name == "Chocolates"
            assert category.slug == "chocolates"
            assert str(category) == "Chocolates"


class TestCatalogItemModel(TenantAwareTestCase):
    def test_catalog_item_creation(self):
        with tenant_context(self.tenant):
            category = CategoryFactory()
            catalog_item = CatalogItemFactory(
                category=category,
                name="Dark Chocolate",
                slug="dark-chocolate",
                description="Premium dark chocolate",
                price=Decimal("25.99"),
                is_available=True,
                average_rating=4.50,
                total_reviews=10,
            )
            assert catalog_item.name == "Dark Chocolate"
            assert catalog_item.category.name == category.name
            assert catalog_item.price == Decimal("25.99")
            assert catalog_item.is_available is True
            assert catalog_item.average_rating == Decimal("4.50")
            assert catalog_item.total_reviews == 10
            assert str(catalog_item) == "Dark Chocolate"


class TestCatalogItemSpecificationModel(TenantAwareTestCase):
    def test_specification_creation(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            spec = CatalogItemSpecificationFactory(
                item=catalog_item, key="Certification", value="Fairtrade"
            )
            assert spec.item.name == catalog_item.name
            assert spec.key == "Certification"
            assert spec.value == "Fairtrade"


# ==========================================
# 6. POSTS, BLOG & NEWS TESTS
# ==========================================


class TestBlogCategoryModel(TenantAwareTestCase):
    def test_blog_category_creation(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory(name="News", slug="news")
            assert blog_category.name == "News"
            assert blog_category.slug == "news"
            assert str(blog_category) == "News"


class TestPostModel(TenantAwareTestCase):
    def test_post_creation(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory()
            post = PostFactory(
                blog_category=blog_category,
                title="Test Post",
                slug="test-post",
                active=True,
                featured=True,
                is_social_service=True,
            )
            assert post.title == "Test Post"
            assert post.slug == "test-post"
            assert post.active is True
            assert post.featured is True
            assert post.is_social_service is True
            assert str(post) == "Test Post"

    def test_post_optimized_query(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory()
            post = PostFactory(blog_category=blog_category)
            queried = Post.objects.optimized().get(id=post.id)
            assert queried.blog_category.name == post.blog_category.name

    def test_post_multilingual_fields(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory()
            post = PostFactory(
                blog_category=blog_category,
                title="Multilingual Post",
                slug="multilingual-post",
                text_file_pt=SimpleUploadedFile("pt.docx", b"pt_content"),
                text_file_en=SimpleUploadedFile("en.docx", b"en_content"),
                text_file_fr=SimpleUploadedFile("fr.docx", b"fr_content"),
            )
            assert post.text_file_pt is not None
            assert post.text_file_en is not None
            assert post.text_file_fr is not None
            assert "pt/" in post.text_file_pt.name
            assert "en/" in post.text_file_en.name
            assert "fr/" in post.text_file_fr.name


class TestPostDocumentModel(TenantAwareTestCase):
    def test_post_document_creation(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            doc = PostDocumentFactory(post=post)
            assert doc.post.title == post.title
            assert doc.document is not None


class TestPostFileModel(TenantAwareTestCase):
    def test_post_file_creation(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            file = PostFileFactory(post=post)
            assert file.post.title == post.title
            assert file.file is not None


class TestPostImageModel(TenantAwareTestCase):
    def test_post_image_creation(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            post_image = PostImageFactory(post=post)
            assert post_image.post.title == post.title
            assert post_image.picture is not None


# ==========================================
# 7. MULTIMEDIA & COMMUNICATIONS TESTS
# ==========================================


class TestVideoModel(TenantAwareTestCase):
    def test_video_creation(self):
        with tenant_context(self.tenant):
            video = VideoFactory(
                title="CECAB Band Performance",
                link="https://youtube.com/watch?v=123",
                is_band=True,
                is_spot=False,
            )
            assert video.title == "CECAB Band Performance"
            assert video.link == "https://youtube.com/watch?v=123"
            assert video.is_band is True
            assert video.is_spot is False
            assert str(video) == "CECAB Band Performance"


class TestPostVideoModel(TenantAwareTestCase):
    def test_post_video_creation(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            video = VideoFactory()
            post_video = PostVideoFactory(post=post, video=video)
            assert post_video.post.title == post.title
            assert post_video.video.title == video.title


class TestMessageModel(TenantAwareTestCase):
    def test_message_creation(self):
        with tenant_context(self.tenant):
            message = MessageFactory(
                name="John Doe",
                email="john@example.com",
                subject="Test Subject",
                text="Test message content",
            )
            assert message.name == "John Doe"
            assert message.email == "john@example.com"
            assert message.subject == "Test Subject"
            assert message.text == "Test message content"
            assert message.sent is False
            assert str(message) == "John Doe"


# ==========================================
# PARTNER MODULE TESTS
# ==========================================


class TestPartnerModel(TenantAwareTestCase):
    def test_partner_creation(self):
        with tenant_context(self.tenant):
            partner = PartnerFactory(title="Fairtrade International")
            assert partner.title == "Fairtrade International"
            assert str(partner) == "Fairtrade International"


# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM TESTS
# ==========================================


class TestRoleModel(TenantAwareTestCase):
    def test_role_creation(self):
        with tenant_context(self.tenant):
            role = RoleFactory(title="President")
            assert role.title == "President"
            assert str(role) == "President"


class TestTeamModel(TenantAwareTestCase):
    def test_team_creation(self):
        with tenant_context(self.tenant):
            role = RoleFactory(title="President")
            team = TeamFactory(name="John Doe", role=role, from_assembly=True)
            assert team.name == "John Doe"
            assert team.role.title == role.title
            assert team.from_assembly is True
            assert str(team) == "John Doe - President"

    def test_team_unique_together(self):
        with tenant_context(self.tenant):
            role = RoleFactory()
            TeamFactory(name="John Doe", role=role, from_assembly=True)
            with pytest.raises(IntegrityError):
                TeamFactory(name="John Doe", role=role, from_assembly=False)


# ==========================================
# 9. GENERAL DOCUMENTATION TESTS
# ==========================================


class TestBudgetModel(TenantAwareTestCase):
    def test_budget_creation(self):
        with tenant_context(self.tenant):
            budget = BudgetFactory(
                title="Annual Budget 2024",
                slug="annual-budget-2024",
                year=2024,
                type=Budget.TYPE_BUDGET,
            )
            assert budget.title == "Annual Budget 2024"
            assert budget.year == 2024
            assert budget.type == "B"
            assert str(budget) == "Annual Budget 2024"


class TestExtraDocModel(TenantAwareTestCase):
    def test_extra_doc_creation(self):
        with tenant_context(self.tenant):
            extra_doc = ExtraDocFactory(
                title="Quality Certificate", slug="quality-cert", active=True
            )
            assert extra_doc.title == "Quality Certificate"
            assert extra_doc.active is True
            assert str(extra_doc) == "Quality Certificate"


class TestExtraImageModel(TenantAwareTestCase):
    def test_extra_image_creation(self):
        with tenant_context(self.tenant):
            extra_doc = ExtraDocFactory()
            extra_image = ExtraImageFactory(extra_doc=extra_doc)
            assert extra_image.extra_doc.title == extra_doc.title
            assert extra_image.picture is not None


class TestInformationModel(TenantAwareTestCase):
    def test_information_creation(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            info = InformationFactory(
                service=post,
                question="What is this service?",
                information="This service provides...",
            )
            assert info.service.title == post.title
            assert info.question == "What is this service?"
            assert info.information == "This service provides..."
            assert str(info) == "What is this service?"


# ==========================================
# REVIEW MODEL TESTS
# ==========================================


class TestReviewModel(TenantAwareTestCase):
    def test_review_creation(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            user = UserFactory(
                username="reviewer", password="testpass123", tenant=self.tenant
            )
            review = ReviewFactory(
                item=catalog_item,
                client=user,
                rating=4,
                comment="Great product!",
                is_approved=True,
            )
            assert review.item.name == catalog_item.name
            assert review.client.username == "reviewer"
            assert review.rating == 4
            assert review.comment == "Great product!"
            assert review.is_approved is True
            assert str(review) == f"Review by reviewer on {catalog_item.name} (4/5)"

    def test_review_unique_together(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            user = UserFactory(
                username="reviewer", password="testpass123", tenant=self.tenant
            )
            ReviewFactorySingle(
                item=catalog_item, client=user, rating=5, comment="First review"
            )
            with pytest.raises(IntegrityError):
                ReviewFactorySingle(
                    item=catalog_item, client=user, rating=3, comment="Duplicate review"
                )

    def test_review_updates_item_rating(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory(average_rating=0, total_reviews=0)
            user1 = UserFactory(
                username="reviewer1", password="testpass123", tenant=self.tenant
            )
            user2 = UserFactory(
                username="reviewer2", password="testpass123", tenant=self.tenant
            )

            ReviewFactory(
                item=catalog_item,
                client=user1,
                rating=4,
                comment="Good",
                is_approved=True,
            )
            catalog_item.refresh_from_db()
            assert catalog_item.average_rating == Decimal("4.00")
            assert catalog_item.total_reviews == 1

            ReviewFactory(
                item=catalog_item,
                client=user2,
                rating=5,
                comment="Excellent!",
                is_approved=True,
            )
            catalog_item.refresh_from_db()
            assert catalog_item.average_rating == Decimal("4.50")
            assert catalog_item.total_reviews == 2

    def test_review_only_counts_approved_reviews(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            user = UserFactory(
                username="reviewer", password="testpass123", tenant=self.tenant
            )
            ReviewFactory(
                item=catalog_item,
                client=user,
                rating=2,
                comment="Not approved",
                is_approved=False,
            )
            catalog_item.refresh_from_db()
            assert catalog_item.total_reviews == 0
            assert catalog_item.average_rating == Decimal("0.00")

    def test_review_delete_updates_item(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            user = UserFactory(
                username="reviewer", password="testpass123", tenant=self.tenant
            )
            review = ReviewFactory(
                item=catalog_item,
                client=user,
                rating=4,
                comment="Great!",
                is_approved=True,
            )
            catalog_item.refresh_from_db()
            assert catalog_item.total_reviews == 1

            review.delete()
            catalog_item.refresh_from_db()
            assert catalog_item.total_reviews == 0
            assert catalog_item.average_rating == Decimal("0.00")


class TestReviewModelCounting(TenantAwareTestCase):
    def test_review_multiple_ratings(self):
        # Define your test cases inside a dictionary or list of tuples
        test_cases = [
            {"ratings": [5, 4, 3], "expected_avg": 4.0, "expected_count": 3},
            {"ratings": [5, 5], "expected_avg": 5.0, "expected_count": 2},
            {"ratings": [1], "expected_avg": 1.0, "expected_count": 1},
        ]

        with tenant_context(self.tenant):
            for count, case in enumerate(test_cases, start=1):
                catalog_item = CatalogItemFactory()

                for i, rating in enumerate(case["ratings"]):
                    user = UserFactory(
                        username=f"reviewer_{i}_{count}_{rating}",
                        email=f"reviewer@hot_{i}_{count}_{rating}.com",
                        password="testpass123",
                        tenant=self.tenant,
                    )
                    ReviewFactory(
                        item=catalog_item,
                        client=user,
                        rating=rating,
                        comment=f"Review {i}",
                        is_approved=True,
                    )

                catalog_item.refresh_from_db()

                from decimal import Decimal

                assert catalog_item.average_rating == Decimal(str(case["expected_avg"]))
                assert catalog_item.total_reviews == case["expected_count"]


# ==========================================
# RELATIONSHIP AND INTEGRATION TESTS
# ==========================================


class TestRelationships(TenantAwareTestCase):
    def test_page_content_block_relationship(self):
        with tenant_context(self.tenant):
            page = PageFactory()
            PageContentBlockFactory(
                page=page, block_type="text", title="Block 1", order=1
            )
            PageContentBlockFactory(
                page=page, block_type="hero", title="Block 2", order=2
            )

            blocks = page.blocks.all()
            assert blocks.count() == 2
            assert blocks[0].title == "Block 1"
            assert blocks[1].title == "Block 2"

    def test_catalog_item_specification_relationship(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            CatalogItemSpecificationFactory(
                item=catalog_item, key="Certification", value="Fairtrade"
            )
            CatalogItemSpecificationFactory(
                item=catalog_item, key="Origin", value="Ghana"
            )

            specs = catalog_item.specifications.all()
            assert specs.count() == 2

    def test_association_image_relationship(self):
        with tenant_context(self.tenant):
            association = AssociationFactory()
            AssociationImageFactory(association=association)
            AssociationImageFactory(association=association)

            images = association.cms_images.all()
            assert images.count() == 2

    def test_post_video_relationship(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            video = VideoFactory()
            PostVideoFactory(post=post, video=video)
            PostVideoFactory(post=post, video=VideoFactory())

            assert post.post_videos.count() == 2
            assert video.post_videos.count() == 1

    def test_information_post_relationship(self):
        with tenant_context(self.tenant):
            post = PostFactory()
            InformationFactory(service=post, question="Q1", information="A1")
            InformationFactory(service=post, question="Q2", information="A2")

            assert post.informations.count() == 2


# ==========================================
# CUSTOM QUERYSET TESTS
# ==========================================


class TestCustomQuerySets(TenantAwareTestCase):
    def test_customer_optimized_queryset(self):
        with tenant_context(self.tenant):
            CustomerFactory(user__username="testuser", user__tenant=self.tenant)
            queryset = Customer.objects.optimized()
            assert queryset is not None
            assert queryset.count() > 0

    def test_association_optimized_queryset(self):
        with tenant_context(self.tenant):
            AssociationFactory()
            queryset = Association.objects.optimized()
            assert queryset is not None
            assert queryset.count() > 0

    def test_post_optimized_queryset(self):
        with tenant_context(self.tenant):
            PostFactory()
            queryset = Post.objects.optimized()
            assert queryset is not None
            assert queryset.count() > 0


# ==========================================
# MODEL FIELD AND CONSTRAINT TESTS
# ==========================================


class TestModelConstraints(TenantAwareTestCase):
    def test_slug_uniqueness_page(self):
        with tenant_context(self.tenant):
            PageFactorySingle(title="Test", slug="test-slug")
            with pytest.raises(Exception):
                PageFactorySingle(title="Test Duplicate", slug="test-slug")

    def test_slug_uniqueness_category(self):
        with tenant_context(self.tenant):
            CategoryFactorySingle(name="Test", slug="test-slug")
            with pytest.raises(Exception):
                CategoryFactorySingle(name="Test Duplicate", slug="test-slug")

    def test_slug_uniqueness_blog_category(self):
        with tenant_context(self.tenant):
            BlogCategoryFactorySingle(name="Test", slug="test-slug")
            with pytest.raises(Exception):
                BlogCategoryFactorySingle(name="Test Duplicate", slug="test-slug")


# ==========================================
# FILE UPLOAD FIELD TESTS
# ==========================================


class TestFileUploads(TenantAwareTestCase):
    def test_image_file_upload(self):
        with tenant_context(self.tenant):
            category = CategoryFactory()
            item = CatalogItemFactory(
                category=category,
                name="Test Item",
                slug="test-item",
                description="Test description",
            )
            
            item_pictures = item.pictures.all()
            
            assert item_pictures.exists()
            assert len(item_pictures) == 2  
            
            feature_picture = item_pictures.filter(is_feature=True).first()
            assert feature_picture is not None
            
            assert feature_picture.picture is not None
            assert feature_picture.picture.name.startswith("orgs_api/cms/catalog/")


    def test_document_file_upload(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory()
            post = PostFactory(
                blog_category=blog_category, title="Test Post", slug="test-post"
            )
            assert post.text_file is not None
            assert post.text_file.name.startswith("orgs_api/cms/posts/documents/")

    def test_multilingual_file_uploads(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory()
            post = PostFactory(
                blog_category=blog_category,
                title="Test Post",
                slug="test-post",
                text_file_pt=SimpleUploadedFile("pt.docx", b"pt_content"),
                text_file_en=SimpleUploadedFile("en.docx", b"en_content"),
                text_file_fr=SimpleUploadedFile("fr.docx", b"fr_content"),
            )
            assert post.text_file_pt is not None
            assert post.text_file_en is not None
            assert post.text_file_fr is not None
            assert "pt/" in post.text_file_pt.name
            assert "en/" in post.text_file_en.name
            assert "fr/" in post.text_file_fr.name


# ==========================================
# EDGE CASES AND BOUNDARY TESTS
# ==========================================


class TestEdgeCases(TenantAwareTestCase):
    def test_year_goal_decimal_precision(self):
        with tenant_context(self.tenant):
            goal = YearGoalFactory(
                year=2025, label="Production", value=Decimal("1234.57")
            )
            assert goal.value == Decimal("1234.57")

    def test_catalog_item_null_price(self):
        with tenant_context(self.tenant):
            category = CategoryFactory()
            item = CatalogItemFactory(
                category=category,
                name="Free Item",
                slug="free-item",
                description="Free item description",
                price=None,
            )
            assert item.price is None

    def test_post_blank_description(self):
        with tenant_context(self.tenant):
            blog_category = BlogCategoryFactory()
            post = PostFactory(
                blog_category=blog_category,
                title="Post without description",
                slug="no-description",
                description="",
            )
            assert post.description == ""

    def test_review_min_max_rating(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            user1 = UserFactory(
                username="reviewer1", password="testpass123", tenant=self.tenant
            )
            user2 = UserFactory(
                username="reviewer2", password="testpass123", tenant=self.tenant
            )

            review1 = ReviewFactory(
                item=catalog_item, client=user1, rating=1, comment="Minimum rating"
            )
            assert review1.rating == 1

            review2 = ReviewFactory(
                item=catalog_item, client=user2, rating=5, comment="Maximum rating"
            )
            assert review2.rating == 5


# ==========================================
# PERFORMANCE AND OPTIMIZATION TESTS
# ==========================================


class TestPerformance(TenantAwareTestCase):
    def test_bulk_create_reviews(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            users = []
            for i in range(10):
                user = UserFactory(
                    username=f"bulk_user_{i}",
                    password="testpass123",
                    tenant=self.tenant,
                )
                users.append(user)

            reviews = [
                Review(
                    item=catalog_item,
                    client=user,
                    rating=4,
                    comment=f"Bulk review {i}",
                    is_approved=True,
                )
                for i, user in enumerate(users)
            ]

            Review.objects.bulk_create(reviews)

            catalog_item.refresh_from_db()
            review = Review.objects.filter(item=catalog_item).first()
            if review:
                review.update_item_rating()

            catalog_item.refresh_from_db()
            assert catalog_item.total_reviews == 10


# ==========================================
# MODEL META CLASS TESTS
# ==========================================


class TestModelMeta(TenantAwareTestCase):
    def test_page_meta_ordering(self):
        with tenant_context(self.tenant):
            PageFactory(title="Home", slug="home", order=3)
            PageFactory(title="About", slug="about", order=1)
            PageFactory(title="Contact", slug="contact", order=2)

            pages = Page.objects.all()
            assert pages[0].title == "About"
            assert pages[1].title == "Contact"
            assert pages[2].title == "Home"

    def test_review_meta_ordering(self):
        with tenant_context(self.tenant):
            catalog_item = CatalogItemFactory()
            user1 = UserFactory(
                username="reviewer1", password="testpass123", tenant=self.tenant
            )
            user2 = UserFactory(
                username="reviewer2", password="testpass123", tenant=self.tenant
            )
            review1 = ReviewFactory(
                item=catalog_item,
                client=user1,
                rating=4,
                comment="First review",
                is_approved=True,
            )
            review2 = ReviewFactory(
                item=catalog_item,
                client=user2,
                rating=5,
                comment="Newer review",
                is_approved=True,
            )

            reviews = Review.objects.all()
            assert reviews[0].id == review2.id
            assert reviews[1].id == review1.id

    def test_blog_category_meta_plural(self):
        assert BlogCategory._meta.verbose_name_plural == "Blog Categories"


# ==========================================
# TEST COVERAGE FOR ALL STRING REPRESENTATIONS
# ==========================================


class TestStringRepresentations(TenantAwareTestCase):
    def test_all_model_str_methods(self):
        with tenant_context(self.tenant):
            # Create all objects using factories
            customer = CustomerFactory(
                user__username="testuser", user__tenant=self.tenant
            )
            page = PageFactory()
            district = DistrictFactory()
            association = AssociationFactory(district=district)
            category = CategoryFactory()
            catalog_item = CatalogItemFactory(category=category)
            blog_category = BlogCategoryFactory()
            post = PostFactory(blog_category=blog_category)
            video = VideoFactory()
            message = MessageFactory()
            role = RoleFactory()
            team = TeamFactory(role=role)
            budget = BudgetFactory()
            info = InformationFactory(service=post)
            review_user = UserFactory(
                username="reviewer", password="testpass123", tenant=self.tenant
            )
            review = ReviewFactory(
                item=catalog_item, client=review_user, rating=4, comment="Great!"
            )

            # Test all str() methods
            assert (
                str(customer) == f"{customer.user.first_name} {customer.user.last_name}"
            )
            assert str(page) == page.title
            assert str(association) == association.name
            assert str(catalog_item) == catalog_item.name
            assert str(post) == post.title
            assert str(video) == video.title
            assert str(message) == message.name
            assert str(team) == f"{team.name} - {team.role}"
            assert str(budget) == budget.title
            assert str(info) == info.question
            assert (
                str(review)
                == f"Review by {review_user.username} on {catalog_item.name} ({review.rating}/5)"
            )
