"""
Single-file DRF serializer test suite for the CMS API.

Design notes
------------
* No ``setUp`` / ``setUpTestData``: every record is created locally via
  ``factory_boy`` factories inside each test. This keeps each test
  self-contained and resilient to cross-test contamination.
* ``TranslatablePayloadFactory`` helper generates ``<field>_<lang>``
  dictionaries from ``LANGUAGE_CODES`` so adding a language to the project
  settings extends every test automatically.
* ``build_context`` mirrors the context produced by a nested-router view:
  a ``view`` object with ``.kwargs`` plus a ``request`` when needed.
"""


import uuid
from datetime import date

import factory
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django_tenants.test.cases import TenantTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from orgs.models import (
    Association,
    AssociationImage,
    BlogCategory,
    Budget,
    CatalogItem,
    CatalogItemPicture,
    CatalogItemSpecification,
    Category,
    District,
    ExtraDoc,
    ExtraImage,
    Information,
    Message,
    Page,
    PageContentBlock,
    Partner,
    Post,
    PostImage,
    Review,
    Role,
    Team,
    Video,
    YearGoal,
)
from orgs.serializers.common import DEFAULT_LANGUAGE, LANGUAGE_CODES
from orgs.serializers.serializers import (
    AssociationImageWriteSerializer,
    AssociationSerializer,
    AssociationWriteSerializer,
    BudgetWriteSerializer,
    CatalogItemPictureWriteSerializer,
    CatalogItemSerializer,
    CatalogItemSpecificationWriteSerializer,
    CatalogItemWriteSerializer,
    ExtraDocWriteSerializer,
    ExtraImageWriteSerializer,
    InformationWriteSerializer,
    MessageWriteSerializer,
    PageContentBlockWriteSerializer,
    PageSerializer,
    PageWriteSerializer,
    PartnerWriteSerializer,
    PostImageWriteSerializer,
    PostSerializer,
    PostWriteSerializer,
    ReviewSerializer,
    ReviewWriteSerializer,
    RoleWriteSerializer,
    TeamWriteSerializer,
    VideoWriteSerializer,
    YearGoalWriteSerializer,
)

# ---------------------------------------------------------------------------
# Factories (shared, DRY) — declared once, reused everywhere.
# ---------------------------------------------------------------------------
User = get_user_model()





def _tr(prefix: str) -> dict[str, str]:
    """Build {prefix_lang: 'value'} dicts from project LANGUAGE_CODES."""
    tr = {
        f"{prefix}_{lang}": f"{prefix.capitalize()} {lang}"
        for lang in LANGUAGE_CODES
    }
    tr[prefix] = f"{prefix.capitalize()} Default"
    return tr



# class ClientFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = Client

#     schema_name = factory.Sequence(lambda n: f"test_tenant_{n}")
#     name = "Test Tenant"
#     on_trial = False
#     paid_until = factory.LazyFunction(lambda: date(2099, 12, 31))


# @contextmanager
# def isolated_tenant(tenant_test_case):
#     """
#     Create a fresh tenant + domain, then enter its schema for the
#     duration of the block. Yields the tenant instance for reference.
#     """
#     from customers.models import Domain  # tenant apps

#     tenant = ClientFactory()
#     tenant.save()

#     domain = Domain()
#     domain.domain = f"{tenant.schema_name}.localhost"
#     domain.tenant = tenant
#     domain.is_primary = True
#     domain.save()

#     with tenant_context(tenant):
#         yield tenant

#     # Cleanup is handled by django-tenants' TransactionTestCase base.
dummy_picture = SimpleUploadedFile(
    name="test_picture.jpg",
    content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b",  # A minimal valid 1x1 pixel GIF binary string
    content_type="image/jpeg",
)




class MultiTenantSerializerTest(TenantTestCase):
    """
    Base for all serializer tests.

    Subclasses are expected to wrap each test body in:
        with isolated_tenant(self):
            ...body...

    ``TenantTestCase`` provides the public schema; the isolated_tenant
    context manager migrates into the test's schema. This satisfies the
    "no setUp database" rule while staying schema-safe.
    """

    @classmethod
    def setup_tenant(cls, tenant):
        """
        Overrides django-tenants internal hook to populate custom fields
        before cls.tenant.save() is invoked during setUpClass.
        """
        tenant.name = "Default Test Tenant"
        tenant.schema_name = f"schema_{uuid.uuid4().hex[:8]}"
        tenant.paid_until = date(2099, 12, 31)
        tenant.on_trial = False
        return tenant

    # def make_factory_context(self):
    #     """Expose a short alias so tests read cleanly."""
    #     return isolated_tenant(self)


# ---------------------------------------------------------------------------
# Factories — declared once, reused everywhere. All .create() calls must
# run inside an active tenant_context (enforced by the caller).
# ---------------------------------------------------------------------------
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = "Test"
    last_name = "User"


class DistrictFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = District

    name = factory.Sequence(lambda n: f"District {n}")


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    slug = factory.Sequence(lambda n: f"cat-{n}")

    @factory.post_generation
    def translated_name(self, create, _extracted, **kwargs):
        self.name_pt = kwargs.get("name_pt", f"Category {self.pk}")


class BlogCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogCategory

    slug = factory.Sequence(lambda n: f"blog-{n}")

    @factory.post_generation
    def translated_name(self, create, _extracted, **kwargs):
        self.name_pt = kwargs.get("name_pt", f"Blog {self.pk}")


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    slug = factory.Sequence(lambda n: f"page-{n}")


class PageContentBlockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PageContentBlock

    page = factory.SubFactory(PageFactory)
    block_type = "text"


class YearGoalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = YearGoal

    year = 2025
    value = 100


class AssociationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Association

    registered = "2024-01-01"
    address_pt = "Rua Principal"
    number_of_associated = 10
    picture = dummy_picture
    district = factory.SubFactory(DistrictFactory)


class AssociationImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AssociationImage

    association = factory.SubFactory(AssociationFactory)
    image = "img.jpg"


class CatalogItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CatalogItem

    category = factory.SubFactory(CategoryFactory)
    slug = factory.Sequence(lambda n: f"item-{n}")
    description_pt = "Descrição"
    price = "10.00"


class CatalogItemPictureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CatalogItemPicture

    catalog_item = factory.SubFactory(CatalogItemFactory)
    picture = "pic.jpg"


class CatalogItemSpecificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CatalogItemSpecification

    item = factory.SubFactory(CatalogItemFactory)
    key_pt = "Certificação"
    value_pt = "Fairtrade"


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    slug = factory.Sequence(lambda n: f"post-{n}")
    picture = "post.jpg"
    title_pt = "Título"
    blog_category = factory.SubFactory(BlogCategoryFactory)


class PostImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PostImage

    post = factory.SubFactory(PostFactory)
    picture = "post-image.jpg"


class BudgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Budget

    slug = factory.Sequence(lambda n: f"budget-{n}")
    text_file = "budget.pdf"
    year = 2024
    type = "B"
    title_pt = "Orçamento"


class ExtraDocFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExtraDoc

    slug = factory.Sequence(lambda n: f"extra-{n}")
    text_file = "extra.pdf"
    title_pt = "Extra"


class ExtraImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExtraImage

    extra_doc = factory.SubFactory(ExtraDocFactory)
    picture = "extra.jpg"


class InformationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Information

    service = factory.SubFactory(PostFactory)
    question_pt = "Pergunta?"
    information_pt = "Resposta."


class VideoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Video

    title_pt = "Vídeo"
    link = "https://youtu.be/abc"
    created_at = "2024-01-01"


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    name = "Ana"
    email = "ana@example.com"
    subject = "Hello"
    text = "World"


class PartnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partner

    title = "Fairtrade"
    picture = "partner.jpg"


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    title_pt = "Diretor"


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f"Member {n}")
    role = factory.SubFactory(RoleFactory)
    image = "team.jpg"


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    item = factory.SubFactory(CatalogItemFactory)
    client = factory.SubFactory(UserFactory)
    rating = 5
    comment = "Great"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def build_context(request=None, **url_kwargs):
    """Mimic nested-router context: view.kwargs + request."""
    class _FakeView:
        pass

    view = _FakeView()
    view.kwargs = url_kwargs
    return {"request": request, "view": view, **url_kwargs}


def authed_request(user):
    request = APIRequestFactory().post("/")
    force_authenticate(request, user=user)
    return request


def anon_request():
    request = APIRequestFactory().post("/")
    request.user = AnonymousUser()
    return request


# ---------------------------------------------------------------------------
# Page / PageContentBlock
# ---------------------------------------------------------------------------
class PageSerializerTests(MultiTenantSerializerTest):
    
    def test_create_page_with_all_translations(self):
            payload = {"slug": "home", "active": True, "order": 1, **_tr("title"), "title":"Default"}
            serializer = PageWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            page = serializer.save()
            page.refresh_from_db()
            for lang in LANGUAGE_CODES:
                assert getattr(page, f"title_{lang}") == payload[f"title_{lang}"]

    def test_create_page_missing_default_language_raises(self):
        
            payload = {
                "slug": "home", "active": True, "order": 1, "title_en": "Home",
            }
            serializer = PageWriteSerializer(data=payload)
            with pytest.raises(ValidationError) as exc_info:
                serializer.is_valid(raise_exception=True)
            assert "title" in exc_info.value.detail

                

    def test_partial_update_preserves_other_languages(self):
        
            page = PageFactory(title_pt="Início", title_en="Home", title_fr="Accueil")
            serializer = PageWriteSerializer(
                page, data={"title_en": "Main"}, partial=True
            )
            assert serializer.is_valid(), serializer.errors

            serializer.save()
            page.refresh_from_db()
            assert page.title_en == "Main"
            assert page.title_pt == "Início"
            assert page.title_fr == "Accueil"

    def test_read_nests_blocks_and_flattens_translations(self):
        
            page = PageFactory(title_pt="Início")
            PageContentBlockFactory(page=page, title_pt="Bloco", content_pt="Conteúdo")

            data = PageSerializer(page).data
            assert data["slug"] == page.slug
            assert data["title"] == "Início"
            assert len(data["blocks"]) == 1
            assert data["blocks"][0]["title"] == "Bloco"


class PageContentBlockSerializerTests(MultiTenantSerializerTest):
    def test_create_block_pulls_page_from_context(self):
        
            page = PageFactory()
            payload = {
                "block_type": "text", "order": 1,
                **_tr("title"), **_tr("content"),
            }
            serializer = PageContentBlockWriteSerializer(
                data=payload, context=build_context(page_pk=page.pk)
            )
            assert serializer.is_valid(), serializer.errors

            block = serializer.save()
            block.refresh_from_db()
            assert block.page_id == page.pk

    def test_create_block_ignores_page_from_payload(self):
        
            page = PageFactory()
            other = PageFactory()
            payload = {
                "page": other.pk, "block_type": "text", "order": 1,
                **_tr("title"), **_tr("content"),
            }
            serializer = PageContentBlockWriteSerializer(
                data=payload, context=build_context(page_pk=page.pk)
            )
            assert serializer.is_valid(), serializer.errors

            block = serializer.save()
            block.refresh_from_db()
            assert block.page_id == page.pk  # URL wins

    def test_create_block_missing_scope_raises(self):
        
            payload = {
                "block_type": "text", "order": 1,
                **_tr("title"), **_tr("content"),
            }
            serializer = PageContentBlockWriteSerializer(data=payload, context={})
            assert not serializer.is_valid()
            assert "page_pk" in serializer.errors

    def test_create_block_missing_default_language_raises(self):
        
            page = PageFactory()
            payload = {"block_type": "text", "order": 1, "title_en": "EN only"}
            serializer = PageContentBlockWriteSerializer(
                data=payload, context=build_context(page_pk=page.pk)
            )
            assert not serializer.is_valid()
            assert f"title_{DEFAULT_LANGUAGE}" in serializer.errors


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
class YearGoalSerializerTests(MultiTenantSerializerTest):
    def test_create_year_goal_with_translations(self):
        
            payload = {"year": 2025, "value": "1200.50", **_tr("label")}
            serializer = YearGoalWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            goal = serializer.save()
            goal.refresh_from_db()
            for lang in LANGUAGE_CODES:
                assert getattr(goal, f"label_{lang}") == payload[f"label_{lang}"]

    def test_create_year_goal_missing_default_label_raises(self):
        
            serializer = YearGoalWriteSerializer(
                data={"year": 2025, "value": "10", "label_en": "Only"}
            )
            assert not serializer.is_valid()
            assert f"label_{DEFAULT_LANGUAGE}" in serializer.errors


# ---------------------------------------------------------------------------
# Associations
# ---------------------------------------------------------------------------
class AssociationSerializerTests(MultiTenantSerializerTest):
    def test_create_with_translations(self):
        
            district = DistrictFactory()
            payload = {
                "registered": "2024-01-01",
                "number_of_associated": 42,
                "district": district.pk,
                "latitude": "0.123",
                "longitude": "10.456",
                "name":"name",
                "address":"address",
                "picture" : dummy_picture,  
                **_tr("name"), **_tr("address"),
            }
            serializer = AssociationWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            assoc = serializer.save()
            assoc.refresh_from_db()
            assert assoc.number_of_associated == 42
            assert assoc.district_id == district.pk

    def test_latitude_out_of_range_raises(self):
        
            district = DistrictFactory()
            payload = {
                "registered": "2024-01-01",
                "number_of_associated": 1,
                "district": district.pk,
                "latitude": "999.0",
                **_tr("name"), **_tr("address"),
            }
            serializer = AssociationWriteSerializer(data=payload)
            assert not serializer.is_valid()
            assert "latitude" in serializer.errors

    def test_read_nests_district_and_images(self):
        
            assoc = AssociationFactory(name_pt="CECAB")
            AssociationImageFactory(association=assoc)

            data = AssociationSerializer(assoc).data
            assert data["name"] == "CECAB"
            assert data["district"]["name"] == assoc.district.name
            assert len(data["images"]) == 1


class AssociationImageSerializerTests(MultiTenantSerializerTest):
    def test_create_uses_scope_from_context(self):
        
            assoc = AssociationFactory()
            serializer = AssociationImageWriteSerializer(
                data={"image":  dummy_picture},
                context=build_context(association_pk=assoc.pk),
            )
            assert serializer.is_valid(), serializer.errors

            image = serializer.save()
            image.refresh_from_db()
            assert image.association_id == assoc.pk

    def test_missing_scope_raises(self):
        
            serializer = AssociationImageWriteSerializer(
                data={"image" : dummy_picture}, context={}
            )
            assert not serializer.is_valid()
            assert "association_pk" in serializer.errors


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
class CatalogItemSerializerTests(MultiTenantSerializerTest):
    def test_create_with_translations(self):
        
            category = CategoryFactory()
            payload = {
                "category": category.pk,
                "slug": "truffle",
                "price": "29.99",
                "name":"name",
                "description": "description",
                **_tr("name"), **_tr("description"),
            }
            serializer = CatalogItemWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            item = serializer.save()
            item.refresh_from_db()
            assert item.slug == "truffle"
            assert item.category_id == category.pk

    def test_missing_default_description_raises(self):
        
            category = CategoryFactory()
            payload = {
                "category": category.pk,
                "slug": "x",
                "name": "X",
                "name_pt": "X",
                "description_en": "EN only",
            }
            serializer = CatalogItemWriteSerializer(data=payload)
            with pytest.raises(ValidationError) as exc_info:
                serializer.is_valid(raise_exception=True)
            assert "description" in serializer.errors

    def test_read_nests_category_pictures_specs(self):
        
            item = CatalogItemFactory(name_pt="Trufa")
            CatalogItemPictureFactory(catalog_item=item, is_feature=True)
            CatalogItemSpecificationFactory(item=item)

            data = CatalogItemSerializer(item).data
            assert data["name"] == "Trufa"
            assert data["category"]["slug"] == item.category.slug
            assert len(data["pictures"]) == 1
            assert data["pictures"][0]["is_feature"] is True
            assert len(data["specifications"]) == 1


class CatalogItemPictureSerializerTests(MultiTenantSerializerTest):
    def test_create_uses_scope_from_context(self):
        
            item = CatalogItemFactory()
            serializer = CatalogItemPictureWriteSerializer(
                data={"picture" : dummy_picture, "is_feature": True},
                context=build_context(item_pk=item.pk),
            )
            assert serializer.is_valid(), serializer.errors

            picture = serializer.save()
            picture.refresh_from_db()
            assert picture.catalog_item_id == item.pk
            assert picture.is_feature is True

    def test_feature_flag_unsets_previous(self):
        
            item = CatalogItemFactory()
            previous = CatalogItemPictureFactory(
                catalog_item=item, is_feature=True
            )
            serializer = CatalogItemPictureWriteSerializer(
                data={"picture" : dummy_picture, "is_feature": True},
                context=build_context(item_pk=item.pk),
            )
            assert serializer.is_valid(), serializer.errors
            serializer.save()

            previous.refresh_from_db()
            assert previous.is_feature is False


class CatalogItemSpecificationSerializerTests(MultiTenantSerializerTest):
    def test_create_uses_scope_and_translations(self):
        
            item = CatalogItemFactory()
            serializer = CatalogItemSpecificationWriteSerializer(
                data={"key":"key", **_tr("key"), **_tr("value"), "value":"value"},
                context=build_context(item_pk=item.pk),
            )
            assert serializer.is_valid(), serializer.errors

            spec = serializer.save()
            spec.refresh_from_db()
            assert spec.item_id == item.pk


# ---------------------------------------------------------------------------
# Blog / Posts
# ---------------------------------------------------------------------------
class PostSerializerTests(MultiTenantSerializerTest):
    def test_create_with_translations(self):
        
            blog_category = BlogCategoryFactory()
            payload = {
                "blog_category": blog_category.pk,
                "slug": "news",
                "picture" : dummy_picture,
                "active": True,
                **_tr("title"), **_tr("description"), **_tr("text"),
            }
            serializer = PostWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            post = serializer.save()
            post.refresh_from_db()
            for lang in LANGUAGE_CODES:
                assert getattr(post, f"title_{lang}") == f"Title {lang}"

    def test_missing_default_title_raises(self):
        
            blog_category = BlogCategoryFactory()
            payload = {
                "blog_category": blog_category.pk,
                "slug": "x",
                "picture" : dummy_picture,
                "title_en": "Only",
            }
            serializer = PostWriteSerializer(data=payload)
            assert not serializer.is_valid()
            assert "title" in serializer.errors

    def test_partial_update_title_fr(self):
        
            post = PostFactory(title_pt="T", title_en="E", title_fr="F")
            serializer = PostWriteSerializer(
                post, data={"title_fr": "Modifié"}, partial=True
            )
            assert serializer.is_valid(), serializer.errors

            serializer.save()
            post.refresh_from_db()
            assert post.title_fr == "Modifié"
            assert post.title_pt == "T"

    def test_read_nests_blog_category_and_images(self):
        
            post = PostFactory(title_pt="Notícia")
            PostImageFactory(post=post)

            data = PostSerializer(post).data
            assert data["title"] == "Notícia"
            assert data["blog_category"]["slug"] == post.blog_category.slug
            assert len(data["post_images"]) == 1


class PostImageSerializerTests(MultiTenantSerializerTest):
    def test_create_uses_scope_from_context(self):
        
            post = PostFactory()
            serializer = PostImageWriteSerializer(
                data={"picture" : dummy_picture}, context=build_context(post_pk=post.pk)
            )
            assert serializer.is_valid(), serializer.errors

            image = serializer.save()
            image.refresh_from_db()
            assert image.post_id == post.pk

    def test_missing_scope_raises(self):
        
            serializer = PostImageWriteSerializer(
                data={"picture" : dummy_picture}, context={}
            )
            assert not serializer.is_valid()
            assert "post_pk" in serializer.errors


# ---------------------------------------------------------------------------
# Documents (Budget, ExtraDoc, ExtraImage, Information)
# ---------------------------------------------------------------------------
class BudgetSerializerTests(MultiTenantSerializerTest):
    def test_create_with_translations(self):
        
            payload = {
                "slug": "2024",
                "text_file": dummy_picture,
                "year": 2024,
                "type": "B",
                **_tr("title"),
            }
            serializer = BudgetWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            budget = serializer.save()
            budget.refresh_from_db()
            assert budget.year == 2024
            assert budget.type == "B"


class ExtraDocSerializerTests(MultiTenantSerializerTest):
    def test_create_with_translations(self):
        
            payload = {
                "slug": "x",
                "picture" : dummy_picture,
                "text_file": dummy_picture,
                "active": True,
                **_tr("title"),
            }
            serializer = ExtraDocWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            doc = serializer.save()
            doc.refresh_from_db()
            assert doc.active is True


class ExtraImageSerializerTests(MultiTenantSerializerTest):
    def test_create_uses_scope_from_context(self):
        
            doc = ExtraDocFactory()
            serializer = ExtraImageWriteSerializer(
                data={"picture" : dummy_picture},
                context=build_context(extradoc_pk=doc.pk),
            )
            assert serializer.is_valid(), serializer.errors

            image = serializer.save()
            image.refresh_from_db()
            assert image.extra_doc_id == doc.pk


class InformationSerializerTests(MultiTenantSerializerTest):
    def test_create_uses_post_scope_from_context(self):
        
            post = PostFactory()
            serializer = InformationWriteSerializer(
                data={**_tr("question"), **_tr("information")},
                context=build_context(post_pk=post.pk),
            )
            assert serializer.is_valid(), serializer.errors

            info = serializer.save()
            info.refresh_from_db()
            assert info.service_id == post.pk

    def test_missing_question_default_raises(self):
        
            post = PostFactory()
            serializer = InformationWriteSerializer(
                data={"information_pt": "X"},
                context=build_context(post_pk=post.pk),
            )
            assert not serializer.is_valid()
            assert "question" in serializer.errors


# ---------------------------------------------------------------------------
# Multimedia
# ---------------------------------------------------------------------------
class VideoSerializerTests(MultiTenantSerializerTest):
    def test_create_with_translations(self):
        
            payload = {
                "link": "https://youtu.be/x",
                "is_band": True,
                "created_at": "2024-01-01",
                **_tr("title"),
            }
            serializer = VideoWriteSerializer(data=payload)
            assert serializer.is_valid(), serializer.errors

            video = serializer.save()
            video.refresh_from_db()
            assert video.is_band is True


class MessageSerializerTests(MultiTenantSerializerTest):
    def test_create_message(self):
        
            serializer = MessageWriteSerializer(
                data={
                    "name": "Ana",
                    "email": "ana@example.com",
                    "subject": "Hello",
                    "text": "World",
                }
            )
            assert serializer.is_valid(), serializer.errors

            message = serializer.save()
            message.refresh_from_db()
            assert message.sent is False


# ---------------------------------------------------------------------------
# Partners / Team
# ---------------------------------------------------------------------------
class PartnerSerializerTests(MultiTenantSerializerTest):
    def test_create(self):
        
            serializer = PartnerWriteSerializer(
                data={"title": "Fairtrade", "picture" : dummy_picture}
            )
            assert serializer.is_valid(), serializer.errors

            partner = serializer.save()
            partner.refresh_from_db()
            assert partner.title == "Fairtrade"


class RoleSerializerTests(MultiTenantSerializerTest):
    def test_create_with_translations(self):
        
            serializer = RoleWriteSerializer(data=_tr("title"))
            assert serializer.is_valid(), serializer.errors

            role = serializer.save()
            role.refresh_from_db()
            for lang in LANGUAGE_CODES:
                assert getattr(role, f"title_{lang}") == f"Title {lang}"


class TeamSerializerTests(MultiTenantSerializerTest):
    def test_create_member(self):
        
            role = RoleFactory()
            serializer = TeamWriteSerializer(
                data={"name": "João", "role": role.pk, "from_assembly": True}
            )
            assert serializer.is_valid(), serializer.errors

            member = serializer.save()
            member.refresh_from_db()
            assert member.role_id == role.pk
            assert member.from_assembly is True

    def test_unique_constraint_raises(self):
        
            role = RoleFactory()
            TeamFactory(name="João", role=role)
            serializer = TeamWriteSerializer(
                data={"name": "João", "role": role.pk}
            )
            assert not serializer.is_valid()
            assert "non_field_errors" in serializer.errors


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------
class ReviewSerializerTests(MultiTenantSerializerTest):
    def test_create_review_uses_scope_and_auth_user(self):
        
            user = UserFactory()
            item = CatalogItemFactory()

            serializer = ReviewWriteSerializer(
                data={"rating": 5, "comment": "Excellent"},
                context=build_context(
                    user_id=user.id, item_pk=item.pk
                ),
            )
            assert serializer.is_valid(), serializer.errors

            review = serializer.save()
            review.refresh_from_db()
            assert review.item_id == item.pk
            assert review.client_id == user.pk

            item.refresh_from_db()
            assert float(item.average_rating) == 5.00
            assert item.total_reviews == 1

    def test_duplicate_review_raises(self):
        
            user = UserFactory()
            item = CatalogItemFactory()
            ReviewFactory(item=item, client=user, rating=4)

            serializer = ReviewWriteSerializer(
                data={"rating": 3, "comment": "again"},
                context=build_context(
                    user_id=user.id, item_pk=item.pk
                ),
            )
            assert not serializer.is_valid()
            assert "non_field_errors" in serializer.errors

    

    def test_missing_scope_raises(self):
        
            user = UserFactory()
            serializer = ReviewWriteSerializer(
                data={"rating": 5, "comment": "x"},
                context=build_context(request=authed_request(user)),
            )
            assert not serializer.is_valid()
            assert "item_pk" in serializer.errors

    def test_update_forbidden_for_non_owner(self):
        
            owner = UserFactory()
            intruder = UserFactory()
            item = CatalogItemFactory()
            review = ReviewFactory(item=item, client=owner, rating=4)

            serializer = ReviewWriteSerializer(
                review,
                data={"rating": 1},
                partial=True,
                context=build_context(
                    user_id=intruder.id, item_pk=item.pk
                ),
            )
            assert serializer.is_valid()
            with pytest.raises(ValidationError):
                serializer.save()

    def test_read_exposes_client_username(self):
        
            user = UserFactory(username="reader")
            review = ReviewFactory(client=user, rating=5)

            data = ReviewSerializer(review).data
            assert data["client_username"] == "reader"
            assert data["rating"] == 5
            assert data["is_approved"] is True