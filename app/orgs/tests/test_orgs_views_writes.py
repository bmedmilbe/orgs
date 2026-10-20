"""
Write-path ViewSet test suite for the orgs app.

Covers CREATE and UPDATE through the viewsets (not the serializers).
Follows the same pattern as ``test_orgs_views.py``:

* ``TenantAwareTestCase`` + ``with tenant_context(self.tenant):`` per test.
* Direct ``ViewSet.as_view({...})`` dispatch with ``APIRequestFactory``.
* No URL reversing. No fixtures. No ``setUp``.
* ``assert x == y`` assertions with ``response.status_code``.

Auth model recap
----------------
``IsTenantStaffOrReadOnly`` requires:
  1. ``request.user.is_authenticated``
  2. ``request.user.is_staff``
  3. ``Customer.objects.filter(user=request.user).exists()``

Every mutation below runs as a *tenant-staff* user produced by
``_staff_user()`` — a plain authenticated user is rejected with 403.
"""


from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django_tenants.utils import tenant_context
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from orgs.models import (
    Association,
    AssociationImage,
    Budget,
    CatalogItem,
    CatalogItemPicture,
    CatalogItemSpecification,
    Category,
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
from orgs.tests.base import TenantAwareTestCase
from orgs.tests.factories import (
    AssociationFactory,
    BlogCategoryFactory,
    BudgetFactory,
    CatalogItemFactory,
    CategoryFactory,
    CustomerFactory,
    DistrictFactory,
    ExtraDocFactory,
    PageFactory,
    PartnerFactory,
    PostFactory,
    ReviewFactory,
    RoleFactory,
    TeamFactory,
    UserFactory,
    VideoFactory,
    YearGoalFactory,
)
from orgs.views import (
    AssociationImageViewSet,
    AssociationViewSet,
    BudgetViewSet,
    CatalogItemPictureViewSet,
    CatalogItemSpecificationViewSet,
    CatalogItemViewSet,
    CategoryViewSet,
    ExtraDocViewSet,
    ExtraImageViewSet,
    InformationViewSet,
    MessageViewSet,
    PageContentBlockViewSet,
    PageViewSet,
    PartnerViewSet,
    PostImageViewSet,
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
def make_request(method, path, user=None, data=None, format="multipart"):
    """Build an authenticated or anonymous DRF request."""
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data=data, format=format)
    if user is not None:
        force_authenticate(request, user=user)
    return request


def generate_pic():
    dummy_picture = SimpleUploadedFile(
    name="test_picture.jpg",
    content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b",  # A minimal valid 1x1 pixel GIF binary string
    content_type="image/jpeg",
)
    return dummy_picture

def _staff_user(tenant):
    """
    Create a user that satisfies ``IsTenantStaffOrReadOnly``:
    authenticated + is_staff=True + has a Customer profile.
    """
    user = UserFactory(tenant=tenant, is_staff=True)
    CustomerFactory(user=user)
    return user


def _plain_user(tenant):
    """Authenticated non-staff user without a Customer profile → 403 on writes."""
    return UserFactory(tenant=tenant, is_staff=False)


def _tenant_user(tenant, **kwargs):
    """Generic tenant-bound user (used for Review, which only requires auth)."""
    return UserFactory(tenant=tenant, **kwargs)


# ==========================================
# 1. PAGE — create / update / delete
# ==========================================
class TestPageWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            payload = {
                "slug": "about",
                "title_pt": "Sobre",
                "title": "Sobre",
                "active": True,
                "order": 1,
            }
            view = PageViewSet.as_view({"post": "create"})
            response = view(make_request("post", "/api/pages/", user=user, data=payload))
            print(response.data)
            assert response.status_code == status.HTTP_201_CREATED
            page = Page.objects.get(slug="about")
            assert page.title_pt == "Sobre"

    def test_create_forbidden_for_plain_user(self):
        with tenant_context(self.tenant):
            user = _plain_user(self.tenant)
            payload = {"slug": "x", "title_pt": "X", "active": True, "order": 1}
            view = PageViewSet.as_view({"post": "create"})
            response = view(make_request("post", "/api/pages/", user=user, data=payload))

            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_forbidden_for_anonymous(self):
        with tenant_context(self.tenant):
            payload = {"slug": "x", "title_pt": "X", "active": True, "order": 1}
            view = PageViewSet.as_view({"post": "create"})
            response = view(make_request("post", "/api/pages/", data=payload))

            assert response.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            )

    def test_partial_update_preserves_other_languages(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            page = PageFactory(
                title_pt="Início",
                title_en="Home",
                title_fr="Accueil"
            )
            view = PageViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/pages/{page.slug}/",
                    user=user,
                    data={"title_en": "Main"},
                ),
                slug=page.slug,
            )

            assert response.status_code == status.HTTP_200_OK
            page.refresh_from_db()
            assert page.title_en == "Main"
            assert page.title_pt == "Início"

    def test_delete_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            page = PageFactory()

            view = PageViewSet.as_view({"delete": "destroy"})
            response = view(
                make_request("delete", f"/api/pages/{page.slug}/", user=user),
                slug=page.slug,
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert not Page.objects.filter(pk=page.pk).exists()


# ==========================================
# 2. PAGE CONTENT BLOCK — nested create / update
# ==========================================
class TestPageContentBlockWrite(TenantAwareTestCase):
    def test_create_uses_parent_from_kwargs(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            page = PageFactory()
            payload = {
                "block_type": "text",
                "title_pt": "Bloco",
                "content_pt": "Conteúdo",
                "order": 1,
            }
            view = PageContentBlockViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post", f"/api/pages/{page.pk}/blocks/", user=user, data=payload
                ),
                page_pk=page.pk,
            )

            assert response.status_code == status.HTTP_201_CREATED
            block = PageContentBlock.objects.get(page=page)
            assert block.title_pt == "Bloco"

    def test_create_missing_scope_returns_400(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            page = PageFactory()
            payload = {
                "block_type": "text",
                "content_pt": "Conteúdo",
                "order": 1,
            }
            view = PageContentBlockViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", f"/api/pages/{page.id}/blocks/", user=user, data=payload),
                page_pk=page.id,
            )
            print(response.data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            page = PageFactory()
            block = PageContentBlock.objects.create(
                page=page, block_type="text", title_pt="Old", content_pt="Old"
            )

            view = PageContentBlockViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/pages/{page.pk}/blocks/{block.pk}/",
                    user=user,
                    data={"title_pt": "New"},
                ),
                page_pk=page.pk,
                pk=block.pk,
            )

            assert response.status_code == status.HTTP_200_OK
            block.refresh_from_db()
            assert block.title_pt == "New"


# ==========================================
# 3. YEAR GOAL — create / update
# ==========================================
class TestYearGoalWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            payload = {"year": 2025, "label_pt": "Meta","label": "Meta", "value": "10.00"}
            view = YearGoalViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/metrics/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            goal = YearGoal.objects.get(year=2025)
            assert goal.label_pt == "Meta"

    def test_create_forbidden_for_plain_user(self):
        with tenant_context(self.tenant):
            user = _plain_user(self.tenant)
            payload = {"year": 2025, "label_pt": "Meta", "value": "10.00"}
            view = YearGoalViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/metrics/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            goal = YearGoalFactory(year=2025, value="10.00")

            view = YearGoalViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/metrics/{goal.pk}/",
                    user=user,
                    data={"value": "999.00"},
                ),
                pk=goal.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            goal.refresh_from_db()
            assert str(goal.value) == "999.00"


# ==========================================
# 4. ASSOCIATION — create / update
# ==========================================
class TestAssociationWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            district = DistrictFactory()
            payload = {
                "name_pt": "CECAB",
                "name": "CECAB",
                "registered": "2024-01-01",
                "address_pt": "Rua 1",
                "address": "Rua 1",
                "number_of_associated": 10,
                "picture": generate_pic(),
                "district": district.pk,
                "latitude": "0.123",
                "longitude": "10.456",
            }
            view = AssociationViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post", 
                    "/api/associations/", 
                    user=user, 
                    data=payload,
                     format="multipart"  # <-- Explicitly switch away from JSON
                )
            )
            print(response.data)
            assert response.status_code == status.HTTP_201_CREATED
            assert Association.objects.count() == 1

    def test_latitude_out_of_range_returns_400(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            district = DistrictFactory()
            payload = {
                "name_pt": "CECAB",
                "registered": "2024-01-01",
                "address_pt": "Rua 1",
                "number_of_associated": 10,
                "picture": "p.jpg",
                "district": district.pk,
                "latitude": "999.0",
            }
            view = AssociationViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/associations/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "latitude" in response.data

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            assoc = AssociationFactory(
                name_pt="Old", number_of_associated=5
            )

            view = AssociationViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/associations/{assoc.pk}/",
                    user=user,
                    data={"number_of_associated": 100},
                ),
                pk=assoc.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            assoc.refresh_from_db()
            assert assoc.number_of_associated == 100


# ==========================================
# 5. ASSOCIATION IMAGE — nested create / update
# ==========================================
class TestAssociationImageWrite(TenantAwareTestCase):
    def test_create_uses_parent_from_kwargs(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            assoc = AssociationFactory()
            view = AssociationImageViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/associations/{assoc.pk}/images/",
                    user=user,
                    data={"image": generate_pic()},
                ),
                association_pk=assoc.pk,
            )
            assert response.status_code == status.HTTP_201_CREATED
            image = AssociationImage.objects.get(association=assoc)
            assert "picture" in image.image.name

    def test_missing_scope_returns_400(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            view = AssociationImageViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    "/api/associations/999/images/",
                    user=user,
                    data={"image": "x.jpg"},
                ),
                association_pk=999,
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==========================================
# 6. CATEGORY — create / update
# ==========================================
class TestCategoryWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            payload = {"name_pt": "Chocolates", "name": "Chocolates", "slug": "chocolates"}
            view = CategoryViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post", "/api/catalog-categories/", user=user, data=payload
                )
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert Category.objects.get(slug="chocolates").name_pt == "Chocolates"

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            cat = CategoryFactory(name_pt="Old")

            view = CategoryViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/catalog-categories/{cat.slug}/",
                    user=user,
                    data={"name_en": "New EN"},
                ),
                slug=cat.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            cat.refresh_from_db()
            assert cat.name_en == "New EN"


# ==========================================
# 7. CATALOG ITEM — create / update
# ==========================================
class TestCatalogItemWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            category = CategoryFactory()
            payload = {
                "category": category.pk,
                "name_pt": "Trufa",
                "name": "Trufa",
                "slug": "trufa",
                "description_pt": "Doce",
                "description": "Doce",
                "price": "29.99",
                "is_available": True,
            }
            view = CatalogItemViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/catalog-items/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            item = CatalogItem.objects.get(slug="trufa")
            assert item.category_id == category.pk

    def test_create_forbidden_for_plain_user(self):
        with tenant_context(self.tenant):
            user = _plain_user(self.tenant)
            category = CategoryFactory()
            payload = {
                "category": category.pk,
                "name_pt": "X",
                "slug": "x",
                "description_pt": "Y",
            }
            view = CatalogItemViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/catalog-items/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            item = CatalogItemFactory(
                name_pt="Old", price="10.00"
            )

            view = CatalogItemViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/catalog-items/{item.slug}/",
                    user=user,
                    data={"price": "99.99"},
                ),
                slug=item.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            item.refresh_from_db()
            assert str(item.price) == "99.99"


# ==========================================
# 8. CATALOG ITEM PICTURE — nested create
# ==========================================
class TestCatalogItemPictureWrite(TenantAwareTestCase):
    def test_create_uses_parent_from_kwargs(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            item = CatalogItemFactory()
            payload = {
                "picture": generate_pic(),
                "caption": "Main",
                "is_feature": True,
            }
            view = CatalogItemPictureViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/catalog-items/{item.pk}/pictures/",
                    user=user,
                    data=payload,
                ),
                item_pk=item.pk,
            )
            print(response.data)
            assert response.status_code == status.HTTP_201_CREATED
            pic = CatalogItemPicture.objects.get(catalog_item=item)
            assert pic.is_feature is True

    def test_feature_flag_unsets_previous(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            item = CatalogItemFactory()
            previous = CatalogItemPicture.objects.create(
                catalog_item=item, picture=generate_pic(), is_feature=True
            )
            payload = {"picture": generate_pic(), "is_feature": True}

            view = CatalogItemPictureViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/catalog-items/{item.pk}/pictures/",
                    user=user,
                    data=payload,
                ),
                item_pk=item.pk,
            )
            assert response.status_code == status.HTTP_201_CREATED
            previous.refresh_from_db()
            assert previous.is_feature is False


# ==========================================
# 9. CATALOG ITEM SPECIFICATION — nested create
# ==========================================
class TestCatalogItemSpecificationWrite(TenantAwareTestCase):
    def test_create_uses_parent_from_kwargs(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            item = CatalogItemFactory()
            payload = {"key_pt": "Certificação", "value_pt": "Fairtrade",
                       "key": "Certificação", "value": "Fairtrade"}
            view = CatalogItemSpecificationViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/catalog-items/{item.pk}/specifications/",
                    user=user,
                    data=payload,
                ),
                item_pk=item.pk,
            )
            assert response.status_code == status.HTTP_201_CREATED
            spec = CatalogItemSpecification.objects.get(item=item)
            assert spec.key_pt == "Certificação"


# ==========================================
# 10. POST — create / update
# ==========================================
class TestPostWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            category = BlogCategoryFactory()
            payload = {
                "blog_category": category.pk,
                "title_pt": "Notícia",
                "title": "Notícia",
                "slug": "noticia",
                "picture": generate_pic(),
                "active": True,
                "description_pt": "Descrição",
                "description": "Descrição",
                "text_pt": "Texto",
                "text": "Texto",
            }
            view = PostViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/categories/{category.slug}/posts/",
                    user=user,
                    data=payload,
                ),
                parent_lookup_category=category.slug,
            )
            assert response.status_code == status.HTTP_201_CREATED
            post = Post.objects.get(slug="noticia")
            assert post.blog_category_id == category.pk

    def test_create_forbidden_for_plain_user(self):
        with tenant_context(self.tenant):
            user = _plain_user(self.tenant)
            category = BlogCategoryFactory()
            payload = {
                "blog_category": category.pk,
                "title_pt": "X",
                "slug": "x",
                "picture": generate_pic(),
            }
            view = PostViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/categories/{category.slug}/posts/",
                    user=user,
                    data=payload,
                ),
                parent_lookup_category=category.slug,
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            post = PostFactory(
                title_pt="Old", title_en="Old EN"
            )

            view = PostViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/posts/{post.slug}/",
                    user=user,
                    data={"title_en": "New EN"},
                ),
                slug=post.slug,
            )
            assert response.status_code == status.HTTP_200_OK
            post.refresh_from_db()
            assert post.title_en == "New EN"
            assert post.title_pt == "Old"


# ==========================================
# 11. POST IMAGE — nested create
# ==========================================
class TestPostImageWrite(TenantAwareTestCase):
    def test_create_uses_parent_from_kwargs(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            post = PostFactory()
            view = PostImageViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/posts/{post.pk}/images/",
                    user=user,
                    data={"picture": generate_pic()},
                ),
                post_pk=post.pk,
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert PostImage.objects.filter(post=post).count() == 1

    def test_missing_scope_returns_400(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            view = PostImageViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    "/api/posts/999/images/",
                    user=user,
                    data={"picture": "i.jpg"},
                ),
                post_pk=999,
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==========================================
# 12. INFORMATION — nested create
# ==========================================
class TestInformationWrite(TenantAwareTestCase):
    def test_create_uses_parent_from_kwargs(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            post = PostFactory()
            payload = {
                "question_pt": "Pergunta?",
                "information_pt": "Resposta.",
                "question": "Pergunta?",
                "information": "Resposta.",
            }
            view = InformationViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/posts/{post.pk}/informations/",
                    user=user,
                    data=payload,
                ),
                post_pk=post.pk,
            )
            assert response.status_code == status.HTTP_201_CREATED
            info = Information.objects.get(service=post)
            assert info.question_pt == "Pergunta?"


# ==========================================
# 13. VIDEO — create / update
# ==========================================
class TestVideoWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            payload = {
                "title_pt": "Vídeo",
                "title": "Vídeo",
                "link": "https://youtu.be/x",
                "created_at": "2024-01-01",
                "is_band": True,
            }
            view = VideoViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/videos/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert Video.objects.get(link="https://youtu.be/x").is_band is True

    def test_create_forbidden_for_plain_user(self):
        with tenant_context(self.tenant):
            user = _plain_user(self.tenant)
            payload = {
                "title_pt": "V",
                "link": "https://x",
                "created_at": "2024-01-01",
            }
            view = VideoViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/videos/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            video = VideoFactory(is_band=False)

            view = VideoViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/videos/{video.pk}/",
                    user=user,
                    data={"is_band": True},
                ),
                pk=video.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            video.refresh_from_db()
            assert video.is_band is True


# ==========================================
# 14. MESSAGE — public create
# ==========================================
class TestMessageWrite(TenantAwareTestCase):
    def test_create_allowed_for_anonymous(self):
        with tenant_context(self.tenant):
            payload = {
                "name": "Ana",
                "email": "ana@example.com",
                "subject": "Hi",
                "text": "Hello",
            }
            view = MessageViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/contact-messages/", data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert Message.objects.count() == 1

    def test_create_invalid_email_returns_400(self):
        with tenant_context(self.tenant):
            payload = {
                "name": "Ana",
                "email": "not-valid",
                "subject": "Hi",
                "text": "Hello",
            }
            view = MessageViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/contact-messages/", data=payload)
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "email" in response.data


# ==========================================
# 15. PARTNER — create / update
# ==========================================
class TestPartnerWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            payload = {"title": "Fairtrade", "picture": generate_pic()}
            view = PartnerViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/partners/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            partner = Partner.objects.get(title="Fairtrade")
            assert "test_picture_" in partner.picture.name.lower()

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            partner = PartnerFactory(title="Old")

            view = PartnerViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/partners/{partner.pk}/",
                    user=user,
                    data={"title": "New"},
                ),
                pk=partner.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            partner.refresh_from_db()
            assert partner.title == "New"


# ==========================================
# 16. ROLE — create / update
# ==========================================
class TestRoleWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            view = RoleViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post", "/api/roles/", user=user, data={"title_pt": "Diretor", "title": "Diretor"}
                )
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert Role.objects.get(title_pt="Diretor").title_pt == "Diretor"

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            role = RoleFactory(title_pt="Old")

            view = RoleViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/roles/{role.pk}/",
                    user=user,
                    data={"title_en": "Director"},
                ),
                pk=role.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            role.refresh_from_db()
            assert role.title_en == "Director"


# ==========================================
# 17. TEAM — create / update / unique constraint
# ==========================================
class TestTeamWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            role = RoleFactory()
            payload = {
                "name": "João",
                "role": role.pk,
                "from_assembly": True,
                "image": generate_pic(),
            }
            view = TeamViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/team-members/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            member = Team.objects.get(name="João")
            assert member.role_id == role.pk

    def test_unique_name_role_constraint_returns_400(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            role = RoleFactory()
            TeamFactory(name="João", role=role)

            payload = {"name": "João", "role": role.pk, "image": generate_pic()}
            view = TeamViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/team-members/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "non_field_errors" in response.data

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            member = TeamFactory(from_assembly=False)

            view = TeamViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/team-members/{member.pk}/",
                    user=user,
                    data={"from_assembly": True},
                ),
                pk=member.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            member.refresh_from_db()
            assert member.from_assembly is True


# ==========================================
# 18. BUDGET — create / update
# ==========================================
class TestBudgetWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            payload = {
                "title_pt": "Orçamento",
                "title": "Orçamento",
                "slug": "2024",
                "text_file": generate_pic(),
                "year": 2024,
                "type": "B",
            }
            view = BudgetViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post", "/api/financial-budgets/", user=user, data=payload
                )
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert Budget.objects.get(slug="2024").year == 2024

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            budget = BudgetFactory(year=2023)

            view = BudgetViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/financial-budgets/{budget.pk}/",
                    user=user,
                    data={"year": 2025},
                ),
                pk=budget.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            budget.refresh_from_db()
            assert budget.year == 2025


# ==========================================
# 19. EXTRA DOC — create / update
# ==========================================
class TestExtraDocWrite(TenantAwareTestCase):
    def test_create_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            payload = {
                "title_pt": "Extra",
                "title": "Extra",
                "slug": "extra",
                "picture": generate_pic(),
                "text_file": generate_pic(),
                "active": True,
            }
            view = ExtraDocViewSet.as_view({"post": "create"})
            response = view(
                make_request("post", "/api/compliance-docs/", user=user, data=payload)
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert ExtraDoc.objects.get(slug="extra").active is True

    def test_partial_update_as_staff(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            doc = ExtraDocFactory(active=False)

            view = ExtraDocViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/compliance-docs/{doc.pk}/",
                    user=user,
                    data={"active": True},
                ),
                pk=doc.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            doc.refresh_from_db()
            assert doc.active is True


# ==========================================
# 20. EXTRA IMAGE — nested create
# ==========================================
class TestExtraImageWrite(TenantAwareTestCase):
    def test_create_uses_parent_from_kwargs(self):
        with tenant_context(self.tenant):
            user = _staff_user(self.tenant)
            doc = ExtraDocFactory()
            view = ExtraImageViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/compliance-docs/{doc.pk}/images/",
                    user=user,
                    data={"picture": generate_pic()},
                ),
                extradoc_pk=doc.pk,
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert ExtraImage.objects.filter(extra_doc=doc).count() == 1


# ==========================================
# 21. REVIEW — create with authenticated user (item scoped)
# ==========================================
class TestReviewWrite(TenantAwareTestCase):
    def test_create_authenticated_uses_item_and_user(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant, username="reviewer")
            item = CatalogItemFactory()
            payload = {"rating": 5, "comment": "Great"}

            view = ReviewViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/catalog-items/{item.pk}/reviews/",
                    user=user,
                    data=payload,
                ),
                item_pk=item.pk,
            )
            assert response.status_code == status.HTTP_201_CREATED
            review = Review.objects.get()
            assert review.client_id == user.pk
            assert review.item_id == item.pk
            assert review.rating == 5

    def test_create_unauthenticated_returns_401(self):
        with tenant_context(self.tenant):
            item = CatalogItemFactory()
            payload = {"rating": 5, "comment": "Great"}

            view = ReviewViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/catalog-items/{item.pk}/reviews/",
                    data=payload,
                ),
                item_pk=item.pk,
            )
            assert response.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            )

    def test_create_duplicate_review_returns_400(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant, username="dup-reviewer")
            item = CatalogItemFactory()
            ReviewFactory(
                item=item, client=user, rating=4
            )

            payload = {"rating": 5, "comment": "Again"}
            view = ReviewViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/catalog-items/{item.pk}/reviews/",
                    user=user,
                    data=payload,
                ),
                item_pk=item.pk,
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "non_field_errors" in response.data

    def test_create_invalid_rating_returns_400(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant, username="bad-rating")
            item = CatalogItemFactory()
            payload = {"rating": 6, "comment": "Too high"}

            view = ReviewViewSet.as_view({"post": "create"})
            response = view(
                make_request(
                    "post",
                    f"/api/catalog-items/{item.pk}/reviews/",
                    user=user,
                    data=payload,
                ),
                item_pk=item.pk,
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "rating" in response.data

    def test_partial_update_own_review(self):
        with tenant_context(self.tenant):
            user = _tenant_user(self.tenant, username="owner")
            item = CatalogItemFactory()
            review = ReviewFactory(
                item=item, client=user, rating=4
            )

            view = ReviewViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/catalog-items/{item.pk}/reviews/{review.pk}/",
                    user=user,
                    data={"rating": 5},
                ),
                item_pk=item.pk,
                pk=review.pk,
            )
            assert response.status_code == status.HTTP_200_OK
            review.refresh_from_db()
            assert review.rating == 5

    def test_partial_update_forbidden_for_other_user(self):
        with tenant_context(self.tenant):
            owner = _tenant_user(self.tenant, username="owner")
            intruder = _tenant_user(self.tenant, username="intruder")
            item = CatalogItemFactory()
            review = ReviewFactory(
                item=item, client=owner, rating=4
            )

            view = ReviewViewSet.as_view({"patch": "partial_update"})
            response = view(
                make_request(
                    "patch",
                    f"/api/catalog-items/{item.pk}/reviews/{review.pk}/",
                    user=intruder,
                    data={"rating": 1},
                ),
                item_pk=item.pk,
                pk=review.pk,
            )
            # Non-staff cannot see the review → 404 (isolation at queryset)
            assert response.status_code in (
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            )
            review.refresh_from_db()
            assert review.rating == 4  # unchanged