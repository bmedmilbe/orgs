from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

import factory
import factory.fuzzy
from core.models import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import slugify
from factory.django import DjangoModelFactory
from PIL import Image

from orgs.models import (
    Association,
    AssociationImage,
    BlogCategory,
    Budget,
    CatalogItem,
    CatalogItemSpecification,
    Category,
    Customer,
    District,
    ExtraDoc,
    ExtraImage,
    Information,
    Message,
    Page,
    PageContentBlock,
    Partner,
    Post,
    PostDocument,
    PostFile,
    PostImage,
    PostVideo,
    Review,
    Role,
    Team,
    Video,
    YearGoal,
)

User = get_user_model()


# ==========================================
# HELPERS
# ==========================================


def generate_image():
    """Generate a genuine tiny image in memory using Pillow."""
    buffer = BytesIO()
    img = Image.new("RGB", (10, 10), color="white")
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(
        name="test_image.jpg", content=buffer.read(), content_type="image/jpeg"
    )


def generate_file_json():
    """Generate a genuine json."""

    return SimpleUploadedFile(
        name="test_data.json", content=b"{}", content_type="application/json"
    )


def generate_doc(title="text.docx"):
    """Generate a mock document file."""
    return SimpleUploadedFile(
        f"{title}",
        b"fake_doc_content",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ==========================================
# 1. CORE & USER MODULE
# ==========================================


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client
        django_get_or_create = ["schema_name"]

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


# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER MODULE
# ==========================================


class PageFactory(DjangoModelFactory):
    class Meta:
        model = Page
        django_get_or_create = ["slug"]

    title = factory.Sequence(lambda n: f"Page {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    active = True
    order = factory.Sequence(lambda n: n)


class PageFactorySingle(DjangoModelFactory):
    class Meta:
        model = Page

    title = factory.Sequence(lambda n: f"Page {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    active = True
    order = factory.Sequence(lambda n: n)


class PageContentBlockFactory(DjangoModelFactory):
    class Meta:
        model = PageContentBlock

    page = factory.SubFactory(PageFactory)
    block_type = factory.fuzzy.FuzzyChoice(["text", "hero", "process"])
    title = factory.Sequence(lambda n: f"Block {n}")
    content = factory.Faker("paragraph")
    image = factory.LazyFunction(generate_image)
    order = factory.Sequence(lambda n: n)


# ==========================================
# 3. METRICS & GOALS MODULE
# ==========================================


class YearGoalFactory(DjangoModelFactory):
    class Meta:
        model = YearGoal

    year = factory.fuzzy.FuzzyInteger(2020, 2030)
    label = factory.Faker("word")
    value = factory.LazyFunction(
        lambda: Decimal(str(round(factory.fuzzy.FuzzyDecimal(0, 10000).fuzz(), 2)))
    )
    show_in_dashboard = True


# ==========================================
# 4. ASSOCIATIONS & NETWORK MODULE
# ==========================================


class DistrictFactory(DjangoModelFactory):
    class Meta:
        model = District

    name = factory.Sequence(lambda n: f"District {n}")


class AssociationFactory(DjangoModelFactory):
    class Meta:
        model = Association

    name = factory.Sequence(lambda n: f"Association {n}")
    registered = factory.LazyFunction(lambda: date.today() - timedelta(days=365))
    address = factory.Faker("address")
    number_of_associated = factory.fuzzy.FuzzyInteger(10, 500)
    picture = factory.LazyFunction(generate_image)
    district = factory.SubFactory(DistrictFactory)


class AssociationImageFactory(DjangoModelFactory):
    class Meta:
        model = AssociationImage

    association = factory.SubFactory(AssociationFactory)
    image = factory.LazyFunction(generate_image)


# ==========================================
# 5. CATALOGUE & ECO-TOURISM MODULE
# ==========================================


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ["slug"]

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class CategoryFactorySingle(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class CatalogItemFactory(DjangoModelFactory):
    class Meta:
        model = CatalogItem

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Item {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    description = factory.Faker("paragraph")
    price = factory.fuzzy.FuzzyDecimal(10, 1000)
    is_available = True
    picture = factory.LazyFunction(generate_image)
    average_rating = factory.fuzzy.FuzzyDecimal(0, 5)
    total_reviews = factory.fuzzy.FuzzyInteger(0, 100)


class CatalogItemSpecificationFactory(DjangoModelFactory):
    class Meta:
        model = CatalogItemSpecification

    item = factory.SubFactory(CatalogItemFactory)
    key = factory.Sequence(lambda n: f"Specification {n}")
    value = factory.Faker("word")


# ==========================================
# 6. POSTS, BLOG & NEWS MODULE
# ==========================================


class BlogCategoryFactory(DjangoModelFactory):
    class Meta:
        model = BlogCategory
        django_get_or_create = ["slug"]

    name = factory.Sequence(lambda n: f"Blog Category {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class BlogCategoryFactorySingle(DjangoModelFactory):
    class Meta:
        model = BlogCategory

    name = factory.Sequence(lambda n: f"Blog Category {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class PostFactory(DjangoModelFactory):
    class Meta:
        model = Post

    blog_category = factory.SubFactory(BlogCategoryFactory)
    title = factory.Sequence(lambda n: f"Post {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    picture = factory.LazyFunction(generate_image)
    text_file = factory.LazyFunction(generate_doc)
    processed_text_file = None
    active = True
    featured = False
    is_a_service = False
    is_social_service = False
    is_to_front = False
    description = factory.Faker("paragraph")
    text = factory.Faker("paragraph")

    # Multilingual fields
    text_file_pt = None
    text_file_en = None
    text_file_fr = None
    processed_text_file_pt = None
    processed_text_file_en = None
    processed_text_file_fr = None


class PostDocumentFactory(DjangoModelFactory):
    class Meta:
        model = PostDocument

    post = factory.SubFactory(PostFactory)
    document = factory.LazyFunction(generate_doc)


class PostFileFactory(DjangoModelFactory):
    class Meta:
        model = PostFile

    post = factory.SubFactory(PostFactory)
    file = factory.LazyFunction(generate_doc)


class PostImageFactory(DjangoModelFactory):
    class Meta:
        model = PostImage

    picture = factory.LazyFunction(generate_image)
    post = factory.SubFactory(PostFactory)


# ==========================================
# 7. MULTIMEDIA & COMMUNICATIONS MODULE
# ==========================================


class VideoFactory(DjangoModelFactory):
    class Meta:
        model = Video

    title = factory.Sequence(lambda n: f"Video {n}")
    link = factory.Faker("url")
    picture = factory.LazyFunction(generate_image)
    is_band = False
    is_spot = False
    created_at = factory.LazyFunction(lambda: date.today() - timedelta(days=30))


class PostVideoFactory(DjangoModelFactory):
    class Meta:
        model = PostVideo

    video = factory.SubFactory(VideoFactory)
    post = factory.SubFactory(PostFactory)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    name = factory.Faker("name")
    email = factory.Faker("email")
    subject = factory.Faker("sentence")
    text = factory.Faker("paragraph")
    sent = False


# ==========================================
# PARTNER MODULE
# ==========================================


class PartnerFactory(DjangoModelFactory):
    class Meta:
        model = Partner

    title = factory.Sequence(lambda n: f"Partner {n}")
    picture = factory.LazyFunction(generate_image)


# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM MODULE
# ==========================================


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role

    title = factory.Sequence(lambda n: f"Role {n}")


class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Faker("name")
    image = factory.LazyFunction(generate_image)
    role = factory.SubFactory(RoleFactory)
    from_assembly = False


# ==========================================
# 9. GENERAL DOCUMENTATION MODULE
# ==========================================


class BudgetFactory(DjangoModelFactory):
    class Meta:
        model = Budget

    title = factory.Sequence(lambda n: f"Budget {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    text_file = factory.LazyFunction(generate_doc)
    year = factory.fuzzy.FuzzyInteger(2020, 2030)
    type = factory.fuzzy.FuzzyChoice(
        [Budget.TYPE_BUDGET, Budget.TYPE_REPORT, Budget.TYPE_LAW]
    )


class ExtraDocFactory(DjangoModelFactory):
    class Meta:
        model = ExtraDoc

    title = factory.Sequence(lambda n: f"Extra Doc {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    picture = factory.LazyFunction(generate_image)
    text_file = factory.LazyFunction(generate_doc)
    active = True


class ExtraImageFactory(DjangoModelFactory):
    class Meta:
        model = ExtraImage

    picture = factory.LazyFunction(generate_image)
    extra_doc = factory.SubFactory(ExtraDocFactory)


class InformationFactory(DjangoModelFactory):
    class Meta:
        model = Information

    service = factory.SubFactory(PostFactory)
    question = factory.Sequence(lambda n: f"Question {n}?")
    information = factory.Faker("paragraph")


# ==========================================
# REVIEW MODEL
# ==========================================


class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review
        django_get_or_create = ["item", "client"]

    item = factory.SubFactory(CatalogItemFactory)
    client = factory.SubFactory(UserFactory)
    rating = factory.fuzzy.FuzzyInteger(1, 5)
    comment = factory.Faker("paragraph")
    is_approved = True


class ReviewFactorySingle(DjangoModelFactory):
    class Meta:
        model = Review

    item = factory.SubFactory(CatalogItemFactory)
    client = factory.SubFactory(UserFactory)
    rating = factory.fuzzy.FuzzyInteger(1, 5)
    comment = factory.Faker("paragraph")
    is_approved = True


# ==========================================
# HELPER FACTORIES FOR COMPLEX SCENARIOS
# ==========================================


class PostWithAllRelationsFactory(PostFactory):
    """Factory that creates a post with all related objects."""

    @factory.post_generation
    def with_images(self, create, extracted, **kwargs):
        if not create:
            return
        count = extracted or 3
        for _ in range(count):
            PostImageFactory(post=self)

    @factory.post_generation
    def with_files(self, create, extracted, **kwargs):
        if not create:
            return
        count = extracted or 2
        for _ in range(count):
            PostFileFactory(post=self)

    @factory.post_generation
    def with_documents(self, create, extracted, **kwargs):
        if not create:
            return
        count = extracted or 2
        for _ in range(count):
            PostDocumentFactory(post=self)

    @factory.post_generation
    def with_videos(self, create, extracted, **kwargs):
        if not create:
            return
        count = extracted or 1
        for _ in range(count):
            PostVideoFactory(post=self)

    @factory.post_generation
    def with_informations(self, create, extracted, **kwargs):
        if not create:
            return
        count = extracted or 3
        for _ in range(count):
            InformationFactory(service=self)


class CatalogItemWithReviewsFactory(CatalogItemFactory):
    """Factory that creates a catalog item with reviews."""

    @factory.post_generation
    def with_reviews(self, create, extracted, **kwargs):
        if not create:
            return
        count = extracted or 5
        for i in range(count):
            user = UserFactory(username=f"reviewer_{i}")
            ReviewFactory(
                item=self,
                client=user,
                rating=factory.fuzzy.FuzzyInteger(1, 5),
                is_approved=True,
            )


class AssociationWithImagesFactory(AssociationFactory):
    """Factory that creates an association with images."""

    @factory.post_generation
    def with_images(self, create, extracted, **kwargs):
        if not create:
            return
        count = extracted or 3
        for _ in range(count):
            AssociationImageFactory(association=self)
