from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import (
    Association,
    BlogCategory,
    Budget,
    CatalogItem,
    Category,
    Customer,
    District,
    ExtraDoc,
    Message,
    Page,
    Partner,
    Post,
    Review,
    Role,
    Team,
    Video,
    YearGoal,
)
from .serializers import (
    AssociationSerializer,
    BlogCategorySerializer,
    BudgetSerializer,
    CatalogItemSerializer,
    CategoryDetailSerializer,
    CustomerSerializer,
    DistrictSerializer,
    ExtraDocSerializer,
    MessageSerializer,
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

# ==========================================
# 1. CORE & USER MODULE VIEWS
# ==========================================

class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides optimized listing of system staff members within the current schema."""
    queryset = Customer.objects.optimized()
    serializer_class = CustomerSerializer


# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER VIEWS
# ==========================================

class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Handles dynamic page retrieval.
    Allows fetching by slug using a lookup field.
    Example: /api/pages/fabrica-de-chocolate/
    """
    queryset = Page.objects.filter(active=True)
    serializer_class = PageDetailSerializer
    lookup_field = 'slug'


# ==========================================
# 3. METRICS & GOALS VIEWS
# ==========================================

class YearGoalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns annual statistical growth metrics (2024-2026).
    Supports quick filtering by active dashboard status or specific years.
    """
    queryset = YearGoal.objects.all()
    serializer_class = YearGoalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['year', 'show_in_dashboard']


# ==========================================
# 4. ASSOCIATIONS & NETWORK VIEWS
# ==========================================

class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer


class AssociationViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns geographical networks. Filters by district to help isolate the 42 associations."""
    queryset = Association.objects.optimized()
    serializer_class = AssociationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['district', 'district__name']


# ==========================================
# 5. CATALOGUE & ECO-TOURISM VIEWS
# ==========================================

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns commercial taxonomic nodes pre-grouped with their active catalog elements."""
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer
    lookup_field = 'slug'


class CatalogItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Allows individual lookups or targeted filtering for chocolates, lodging rooms, or guided tours."""
    queryset = CatalogItem.objects.filter(is_available=True)
    serializer_class = CatalogItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'category__slug']
    lookup_field = 'slug'


# ==========================================
# 6. POSTS, BLOG & NEWS VIEWS (NESTED ARCHITECTURE)
# ==========================================

class BlogCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Manages parental editorial segments (e.g., /api/categories/)."""
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    lookup_field = 'slug'


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Fully supports the hierarchical architecture powered by drf-nested-routers.
    
    Endpoints:
    - List view for a specific category: /api/categories/<category_slug>/posts/
    - Detail view for an individual article: /api/categories/<category_slug>/posts/<slug>/
    """
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['featured', 'is_a_service', 'is_social_service', 'is_to_front']

    def get_queryset(self):
        """
        Dynamically scopes the lookup queries using the parameters provided by the nested router.
        Falls back to standard optimized list parameters if no parent namespace is passed down.
        """
        queryset = Post.objects.filter(active=True).optimized()
        
        # 'parent_lookup_category' is passed down automatically by Nesting routers if looking up categories by slug
        category_slug = self.kwargs.get('parent_lookup_category')
        if category_slug:
            return queryset.filter(blog_category__slug=category_slug)
            
        return queryset

    def get_serializer_class(self):
        """Optimizes bandwidth by running a slim payload list against detailed page objects."""
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer


# ==========================================
# 7. MULTIMEDIA & COMMUNICATIONS VIEWS
# ==========================================

class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_band', 'is_spot']


class MessageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Safe inbound payload reception sinkhole handling public customer submission forms."""
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


class PartnerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer


# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM VIEWS
# ==========================================

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'from_assembly']


# ==========================================
# 9. GENERAL DOCUMENTATION VIEWS
# ==========================================

class BudgetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['year', 'type']




class ExtraDocViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExtraDoc.objects.filter(active=True)
    serializer_class = ExtraDocSerializer



class ReviewViewSet(viewsets.ModelViewSet):
    """
    Handles item reviews.
    Anyone can read reviews, but only authenticated users can post them.
    """
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['item', 'rating']
