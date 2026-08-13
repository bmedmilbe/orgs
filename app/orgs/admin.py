# file: orgs/admin.py

from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline

# ==============================================================================
# IMPORTANTE: Carregar translation.py ANTES de qualquer import do TranslationAdmin
# ==============================================================================
import orgs.translation  # noqa - Esta linha DEVE vir primeiro!

from .models import (
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
    Review,
    Role,
    Team,
    Video,
    YearGoal,
)


# ==============================================================================
# 0. GLOBAL CORE MEDIA SETTINGS FOR TRANS-TAB INTERFACES
# ==============================================================================
class BaseTranslationAdminMedia:
    """Injects steady runtime jQuery dependency streams to support translation sub-tabs."""
    class Media:
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }


# ... resto do código permanece igual

# ==============================================================================
# 1. CORE & USER MODULE MANAGEMENT
# ==============================================================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'get_first_name', 'get_last_name', 'domain')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)

    def get_email(self, obj):
        return obj.user.email if obj.user else '-'
    get_email.short_description = 'Email Address'

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else '-'
    get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else '-'
    get_last_name.short_description = 'Last Name'


# ==============================================================================
# 2. DYNAMIC CONTENT & PAGE BUILDER MODULE (MODULAR CMS)
# ==============================================================================
class PageContentBlockInline(TranslationStackedInline):
    model = PageContentBlock
    extra = 1
    fieldsets = (
        (None, {'fields': ('block_type', 'order')}),
        ('Localized Block Content', {'fields': ('title', 'content', 'image')}),
    )


@admin.register(Page)
class PageAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('title', 'slug', 'active', 'order')
    list_editable = ('active', 'order')
    prepopulated_fields = {'slug': ('title_pt',)}
    inlines = [PageContentBlockInline]
    search_fields = ('title', 'slug')
    


# ==============================================================================
# 3. METRICS & GOALS MODULE
# ==============================================================================
@admin.register(YearGoal)
class YearGoalAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('label', 'year', 'value', 'show_in_dashboard')
    list_filter = ('year', 'show_in_dashboard')
    list_editable = ('value', 'show_in_dashboard')
    search_fields = ('label',)


# ==============================================================================
# 4. ASSOCIATIONS & NETWORK MODULE
# ==============================================================================
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class AssociationImageInline(admin.TabularInline):
    model = AssociationImage
    extra = 3


@admin.register(Association)
class AssociationAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('name', 'district', 'registered', 'number_of_associated')
    list_filter = ('district', 'registered')
    search_fields = ('name', 'address')
    inlines = [AssociationImageInline]


# ==============================================================================
# 5. CATALOGUE & ECO-TOURISM MODULE
# ==============================================================================
class CatalogItemSpecificationInline(TranslationStackedInline):
    model = CatalogItemSpecification
    extra = 1


@admin.register(Category)
class CategoryAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name_pt',)}
    search_fields = ('name',)


@admin.register(CatalogItem)
class CatalogItemAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('name', 'category', 'price', 'average_rating', 'total_reviews', 'is_available')
    list_filter = ('category', 'is_available')
    list_editable = ('price', 'is_available')
    readonly_fields = ('average_rating', 'total_reviews')
    prepopulated_fields = {'slug': ('name_pt',)}
    search_fields = ('name', 'description')
    inlines = [CatalogItemSpecificationInline]


# ==============================================================================
# 6. POSTS, BLOG & NEWS MODULE (NESTED DOCX PARSER PIPELINE)
# ==============================================================================
@admin.register(BlogCategory)
class BlogCategoryAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name_pt',)}
    search_fields = ('name',)


class PostDocumentInline(admin.TabularInline):
    model = PostDocument
    extra = 1


class PostFileInline(admin.TabularInline):
    model = PostFile
    extra = 1


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 3


class InformationInline(TranslationStackedInline):
    """Embeds Q&A Accordion blocks right inside specific Article layouts."""
    model = Information
    extra = 1


@admin.register(Post)
class PostAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('title', 'blog_category', 'date', 'active', 'featured', 'is_to_front', 'processed_text_file_pt')
    list_filter = ('blog_category', 'active', 'featured', 'is_to_front', 'date')
    list_editable = ('active', 'featured', 'is_to_front')
    search_fields = ('title', 'description', 'text')
    prepopulated_fields = {'slug': ('title_pt',)}
    readonly_fields = ('processed_text_file',)
    inlines = [PostDocumentInline, PostFileInline, PostImageInline, InformationInline]
    
    fieldsets = (
            ('Categorization Hierarchy', {
                'fields': ('blog_category', 'title', 'slug')
            }),
            ('Document Upload by Language', {
                'fields': (
                    ('text_file_pt', 'processed_text_file_pt'),
                    ('text_file_en', 'processed_text_file_en'),
                    ('text_file_fr', 'processed_text_file_fr'),
                ),
                'description': 'Upload a .docx file for each language. The system will automatically process and generate JSON.'
            }),
            ('Legacy Document Upload (Single File)', {
                'fields': ('text_file', 'processed_text_file'),
                'classes': ('collapse',),
                'description': 'Legacy field for backward compatibility.'
            }),
            ('Display Visibility Configurations', {
                'fields': ('active', 'featured', 'is_a_service', 'is_social_service', 'is_to_front')
            }),
            ('Core Multi-Language Metadata Override Fallbacks', {
                'fields': ('picture', 'description', 'text'),
                'description': 'These fields represent automated outputs filled by the processing signal layer but can be modified manually.'
            }),
        )

    def processed_text_file_pt(self, obj):
        """Displays a visual indicator icon validating whether the document parser built a clean JSON payload."""
        if obj.processed_text_file:
            return format_html('<span style="color: green; font-weight: bold;">✔ Ready</span>')
        return format_html('<span style="color: gray;">No File Uploaded</span>')
    processed_text_file_pt.short_description = 'Word Parsing Status'


# ==============================================================================
# 7. MULTIMEDIA & COMMUNICATIONS MODULE
# ==============================================================================
@admin.register(Video)
class VideoAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('title', 'created_at', 'is_band', 'is_spot')
    list_filter = ('is_band', 'is_spot', 'created_at')
    search_fields = ('title', 'link')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'date', 'sent')
    list_filter = ('sent', 'date')
    search_fields = ('name', 'email', 'subject', 'text')
    readonly_fields = ('name', 'email', 'subject', 'text', 'date', 'sent')


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


# ==============================================================================
# 8. CORPORATE GOVERNANCE & TEAM MODULE
# ==============================================================================
@admin.register(Role)
class RoleAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'from_assembly')
    list_filter = ('role', 'from_assembly')
    search_fields = ('name', 'role__title')


# ==============================================================================
# 9. GENERAL DOCUMENTATION MODULE
# ==============================================================================
@admin.register(Budget)
class BudgetAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('title', 'type', 'year', 'date')
    list_filter = ('type', 'year', 'date')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title_pt',)}


class ExtraImageInline(admin.TabularInline):
    model = ExtraImage
    extra = 3


@admin.register(ExtraDoc)
class ExtraDocAdmin(BaseTranslationAdminMedia, TranslationAdmin):
    list_display = ('title', 'active', 'date')
    list_filter = ('active', 'date')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title_pt',)}
    inlines = [ExtraImageInline]


# ==============================================================================
# 10. CLIENT MODERATION REVIEW MODULE (OPTIMIZED FOR BATCH WORKFLOWS)
# ==============================================================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('item', 'client', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at', 'item__category')
    search_fields = (
        'client__username',
        'client__first_name',
        'client__last_name',
        'item__name',
        'comment',
    )
    list_editable = ('is_approved',)
    readonly_fields = ('created_at',)
    actions = ['approve_reviews', 'reject_reviews']

    @admin.action(description='Approve selected reviews (Publish to frontend)')
    def approve_reviews(self, request, queryset):
        """Approve selected reviews and update ratings."""
        to_update = queryset.filter(is_approved=False)
        updated_count = to_update.count()

        if updated_count > 0:
            to_update.update(is_approved=True)
            # Update item ratings for affected items
            for review in to_update:
                review.update_item_rating()

        self.message_user(
            request,
            f'Successfully approved {updated_count} reviews. Frontend rating metrics updated.',
        )

    @admin.action(description='Reject / Hide selected reviews from frontend')
    def reject_reviews(self, request, queryset):
        """Reject selected reviews and update ratings."""
        to_update = queryset.filter(is_approved=True)
        updated_count = to_update.count()

        if updated_count > 0:
            to_update.update(is_approved=False)
            # Update item ratings for affected items
            for review in to_update:
                review.update_item_rating()

        self.message_user(
            request,
            f'Successfully unapproved {updated_count} reviews. Frontend rating metrics updated.',
        )