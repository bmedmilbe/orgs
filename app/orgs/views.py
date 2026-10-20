"""
View layer for the CMS + Store API.

Serializer dispatch follows one uniform pattern:

    def get_serializer_class(self):
        if self.request.method == "GET":
            return Serializer
        return WriteSerializer

Every nested child viewset delegates parent-FK binding to its
ScopedWriteSerializer by merging ``self.kwargs`` into the serializer
context via ``get_serializer_context()``. No ``perform_create`` overrides
are needed — the write serializers resolve ``<parent>_pk`` from
``self.context`` themselves.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import (
    Association,
    AssociationImage,
    BlogCategory,
    Budget,
    CatalogItem,
    CatalogItemPicture,
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
from .permissions import IsTenantStaffOrReadOnly
from .serializers.serializers import (
    AssociationImageSerializer,
    AssociationImageWriteSerializer,
    AssociationSerializer,
    AssociationWriteSerializer,
    BlogCategorySerializer,
    BlogCategoryWriteSerializer,
    BudgetSerializer,
    BudgetWriteSerializer,
    CatalogItemPictureSerializer,
    CatalogItemPictureWriteSerializer,
    CatalogItemSerializer,
    CatalogItemSpecificationSerializer,
    CatalogItemSpecificationWriteSerializer,
    CatalogItemWriteSerializer,
    CategoryDetailSerializer,
    CategoryWriteSerializer,
    CustomerSerializer,
    DistrictSerializer,
    ExtraDocSerializer,
    ExtraDocWriteSerializer,
    ExtraImageSerializer,
    ExtraImageWriteSerializer,
    InformationSerializer,
    InformationWriteSerializer,
    MessageSerializer,
    PageContentBlockSerializer,
    PageContentBlockWriteSerializer,
    PageDetailSerializer,
    PageWriteSerializer,
    PartnerSerializer,
    PartnerWriteSerializer,
    PostDetailSerializer,
    PostDocumentSerializer,
    PostDocumentWriteSerializer,
    PostFileSerializer,
    PostFileWriteSerializer,
    PostImageSerializer,
    PostImageWriteSerializer,
    PostListSerializer,
    PostVideoSerializer,
    PostVideoWriteSerializer,
    PostWriteSerializer,
    ReviewSerializer,
    ReviewWriteSerializer,
    RoleSerializer,
    RoleWriteSerializer,
    TeamSerializer,
    TeamWriteSerializer,
    VideoSerializer,
    VideoWriteSerializer,
    YearGoalSerializer,
    YearGoalWriteSerializer,
)


# ===========================================================================
# Helpers
# ===========================================================================
def _is_tenant_staff(user) -> bool:
    """Mirror of IsTenantStaffOrReadOnly for queryset branching."""
    if not user or not user.is_authenticated:
        return False
    if not getattr(user, "is_staff", False):
        return False
    return Customer.objects.filter(user=user).exists()


class NestedScopedViewMixin:
    """
    Merge URL kwargs into serializer context so ScopedWriteSerializer
    resolves ``<parent>_pk`` automatically.

    This is the *only* thing child viewsets need to do to make
    parent-scoped writes work — no ``perform_create`` override required.
    """

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(self.kwargs)
        return context


# ===========================================================================
# 1. CORE & USER MODULE
# ===========================================================================
class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """Tenant-scoped list/detail of Customer profiles (read-only)."""

    queryset = Customer.objects.optimized()
    serializer_class = CustomerSerializer
    permission_classes = [IsTenantStaffOrReadOnly]


# ===========================================================================
# 2. DYNAMIC CONTENT & PAGE BUILDER
# ===========================================================================
class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    lookup_field = "slug"
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["active"]

    def get_queryset(self):
        qs = Page.objects.all()
        if self.request.method == "GET":
            qs = qs.filter(active=True)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PageDetailSerializer
        return PageWriteSerializer


class PageContentBlockViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /pages/<page_pk>/blocks/
    Parent FK resolved by PageContentBlockWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = PageContentBlock.objects.select_related("page")
        page_pk = self.kwargs.get("page_pk")
        if page_pk is not None:
            qs = qs.filter(page_id=page_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PageContentBlockSerializer
        return PageContentBlockWriteSerializer


# ===========================================================================
# 3. METRICS & GOALS
# ===========================================================================
class YearGoalViewSet(viewsets.ModelViewSet):
    queryset = YearGoal.objects.all()
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["year", "show_in_dashboard"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return YearGoalSerializer
        return YearGoalWriteSerializer


# ===========================================================================
# 4. ASSOCIATIONS & NETWORK
# ===========================================================================
class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.all()

    serializer_class =  DistrictSerializer


class AssociationViewSet(viewsets.ModelViewSet):
    queryset = Association.objects.optimized()
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["district", "district__name"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return AssociationSerializer
        return AssociationWriteSerializer


class AssociationImageViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /associations/<association_pk>/images/
    Parent FK resolved by AssociationImageWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = AssociationImage.objects.all()
        association_pk = self.kwargs.get("association_pk")
        if association_pk is not None:
            qs = qs.filter(association_id=association_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return AssociationImageSerializer
        return AssociationImageWriteSerializer


# ===========================================================================
# 5. CATALOGUE & ECO-TOURISM
# ===========================================================================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    lookup_field = "slug"
    permission_classes = [IsTenantStaffOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CategoryDetailSerializer
        return CategoryWriteSerializer


class CatalogItemViewSet(viewsets.ModelViewSet):
    queryset = CatalogItem.objects.all()
    lookup_field = "slug"
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category", "category__slug", "is_available"]

    def get_queryset(self):
        qs = CatalogItem.objects.all()
        if self.request.method == "GET" and not _is_tenant_staff(self.request.user):
            qs = qs.filter(is_available=True)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CatalogItemSerializer
        return CatalogItemWriteSerializer


class CatalogItemPictureViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /catalog-items/<item_pk>/pictures/
    Parent FK resolved by CatalogItemPictureWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = CatalogItemPicture.objects.select_related("catalog_item")
        item_pk = self.kwargs.get("item_pk")
        if item_pk is not None:
            qs = qs.filter(catalog_item_id=item_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CatalogItemPictureSerializer
        return CatalogItemPictureWriteSerializer


class CatalogItemSpecificationViewSet(
    NestedScopedViewMixin, viewsets.ModelViewSet
):
    """
    Nested CRUD: /catalog-items/<item_pk>/specifications/
    Parent FK resolved by CatalogItemSpecificationWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = CatalogItemSpecification.objects.select_related("item")
        item_pk = self.kwargs.get("item_pk")
        if item_pk is not None:
            qs = qs.filter(item_id=item_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CatalogItemSpecificationSerializer
        return CatalogItemSpecificationWriteSerializer


# ===========================================================================
# 6. POSTS, BLOG & NEWS
# ===========================================================================
class BlogCategoryViewSet(viewsets.ModelViewSet):
    queryset = BlogCategory.objects.all()
    lookup_field = "slug"
    permission_classes = [IsTenantStaffOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BlogCategorySerializer
        return BlogCategoryWriteSerializer


class PostViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "featured",
        "is_a_service",
        "is_social_service",
        "is_to_front",
        "active",
    ]

    def get_queryset(self):
        qs = Post.objects.optimized()

        category_slug = self.kwargs.get("parent_lookup_category")
        if category_slug:
            qs = qs.filter(blog_category__slug=category_slug)

        if self.request.method == "GET" and not _is_tenant_staff(self.request.user):
            qs = qs.filter(active=True)

        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == "list":
                return PostListSerializer
            return PostDetailSerializer
        return PostWriteSerializer


class PostImageViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /posts/<post_pk>/images/
    Parent FK resolved by PostImageWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]

    def get_queryset(self):
        qs = PostImage.objects.select_related("post")
        post_pk = self.kwargs.get("post_pk")
        if post_pk is not None:
            qs = qs.filter(post_id=post_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PostImageSerializer
        return PostImageWriteSerializer


class PostDocumentViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /posts/<post_pk>/documents/
    Parent FK resolved by PostDocumentWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]

    def get_queryset(self):
        qs = PostDocument.objects.select_related("post")
        post_pk = self.kwargs.get("post_pk")
        if post_pk is not None:
            qs = qs.filter(post_id=post_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PostDocumentSerializer
        return PostDocumentWriteSerializer


class PostFileViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /posts/<post_pk>/files/
    Parent FK resolved by PostFileWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]

    def get_queryset(self):
        qs = PostFile.objects.select_related("post")
        post_pk = self.kwargs.get("post_pk")
        if post_pk is not None:
            qs = qs.filter(post_id=post_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PostFileSerializer
        return PostFileWriteSerializer


class PostVideoViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /posts/<post_pk>/videos/
    Parent FK resolved by PostVideoWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]

    def get_queryset(self):
        qs = PostVideo.objects.select_related("post", "video")
        post_pk = self.kwargs.get("post_pk")
        if post_pk is not None:
            qs = qs.filter(post_id=post_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PostVideoSerializer
        return PostVideoWriteSerializer


class InformationViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /posts/<post_pk>/informations/
    Parent FK resolved by InformationWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]

    def get_queryset(self):
        qs = Information.objects.select_related("service")
        post_pk = self.kwargs.get("post_pk")
        if post_pk is not None:
            qs = qs.filter(service_id=post_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return InformationSerializer
        return InformationWriteSerializer


# ===========================================================================
# 7. MULTIMEDIA & COMMUNICATIONS
# ===========================================================================
class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_band", "is_spot"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return VideoSerializer
        return VideoWriteSerializer


class MessageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Public contact form sinkhole: anonymous POST allowed."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            {"detail": "Message received."},
            status=status.HTTP_201_CREATED,
        )


class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    permission_classes = [IsTenantStaffOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PartnerSerializer
        return PartnerWriteSerializer


# ===========================================================================
# 8. CORPORATE GOVERNANCE & TEAM
# ===========================================================================
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    permission_classes = [IsTenantStaffOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RoleSerializer
        return RoleWriteSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related("role")
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["role", "from_assembly"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TeamSerializer
        return TeamWriteSerializer


# ===========================================================================
# 9. GENERAL DOCUMENTATION
# ===========================================================================
class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    permission_classes = [IsTenantStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["year", "type"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BudgetSerializer
        return BudgetWriteSerializer


class ExtraDocViewSet(viewsets.ModelViewSet):
    queryset = ExtraDoc.objects.all()
    permission_classes = [IsTenantStaffOrReadOnly]

    def get_queryset(self):
        qs = ExtraDoc.objects.all()
        if self.request.method == "GET" and not _is_tenant_staff(self.request.user):
            qs = qs.filter(active=True)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ExtraDocSerializer
        return ExtraDocWriteSerializer


class ExtraImageViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /compliance-docs/<extradoc_pk>/images/
    Parent FK resolved by ExtraImageWriteSerializer from context.
    """

    permission_classes = [IsTenantStaffOrReadOnly]

    def get_queryset(self):
        qs = ExtraImage.objects.select_related("extra_doc")
        doc_pk = self.kwargs.get("extradoc_pk")
        if doc_pk is not None:
            qs = qs.filter(extra_doc_id=doc_pk)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ExtraImageSerializer
        return ExtraImageWriteSerializer


# ===========================================================================
# 10. REVIEWS
# ===========================================================================
class ReviewViewSet(NestedScopedViewMixin, viewsets.ModelViewSet):
    """
    Nested CRUD: /catalog-items/<catalog_item_pk>/reviews/

    Parent FK is resolved by ReviewWriteSerializer from context.
    ``client`` is bound in ``perform_create`` because it comes from the
    request, not the URL.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["rating", "is_approved"]

    def get_queryset(self):
        qs = Review.objects.select_related("item", "client")

        item_pk = self.kwargs.get("catalog_item_pk") or self.kwargs.get("item_pk")
        print(self.kwargs)
        if item_pk is not None:
            qs = qs.filter(item_id=item_pk)

        if self.request.method != "GET":
            user = self.request.user
            if user and user.is_authenticated and not _is_tenant_staff(user):
                qs = qs.filter(client=user)
        else:
            if not _is_tenant_staff(self.request.user):
                qs = qs.filter(is_approved=True)

        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReviewSerializer
        return ReviewWriteSerializer

    def perform_create(self, serializer):
        # Item FK comes from context (via NestedScopedViewMixin),
        # but client must be bound from the request.
        serializer.save(client=self.request.user)

    def perform_update(self, serializer):
        if not _is_tenant_staff(self.request.user):
            serializer.save(client=self.request.user)
        else:
            serializer.save()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request and self.request.user:
            context["user_id"] = self.request.user.id
        return context