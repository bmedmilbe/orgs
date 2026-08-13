from django.urls import include, path
from rest_framework_nested import routers

from .views import (
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

# 1. Initialize Standard Root Router
router = routers.DefaultRouter()

# Core & Infrastructure Registration
router.register(r'customers', CustomerViewSet, basename='customers')
router.register(r'pages', PageViewSet, basename='pages')
router.register(r'metrics', YearGoalViewSet, basename='metrics')

# Regional & Association Networks
router.register(r'districts', DistrictViewSet, basename='districts')
router.register(r'associations', AssociationViewSet, basename='associations')

# Commercial Catalogue & Eco-Tourism Assets
router.register(r'catalog-categories', CategoryViewSet, basename='catalog-categories')
router.register(r'catalog-items', CatalogItemViewSet, basename='catalog-items')

# Multimedia & Public Communication Channels
router.register(r'videos', VideoViewSet, basename='videos')
router.register(r'contact-messages', MessageViewSet, basename='contact-messages')
router.register(r'partners', PartnerViewSet, basename='partners')

# Corporate Management & Governance Teams
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'team-members', TeamViewSet, basename='team-members')

# Administrative Transparency Documentation
router.register(r'financial-budgets', BudgetViewSet, basename='financial-budgets')
router.register(r'compliance-docs', ExtraDocViewSet, basename='compliance-docs')

# Parental Node Registration for Nested Blog Categories Layouts
router.register(r'categories', BlogCategoryViewSet, basename='blog-categories')
router.register(r'reviews', ReviewViewSet, basename='reviews')

# 2. Build the Hierarchical Nested Blog Router Loop
# lookup='category' creates the 'parent_lookup_category' url variable mapped inside viewset queries
nested_blog_router = routers.NestedDefaultRouter(router, r'categories', lookup='category')
nested_blog_router.register(r'posts', PostViewSet, basename='category-posts')


# 3. Assemble Consolidated URL Routing Matrix
urlpatterns = [
    # Standard Core System Endpoints
    path('', include(router.urls)),
    
    # Hierarchical Nested Architectural Loops
    path('', include(nested_blog_router.urls)),
    
    
]
