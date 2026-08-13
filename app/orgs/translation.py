from modeltranslation.translator import TranslationOptions, register

from .models import (
    Association,
    BlogCategory,
    Budget,
    CatalogItem,
    CatalogItemSpecification,
    Category,
    ExtraDoc,
    Information,
    Page,
    PageContentBlock,
    Post,
    Role,
    Video,
    YearGoal,
)


@register(PageContentBlock)
class PageContentBlockTranslationOptions(TranslationOptions):
    fields = ('title', 'content',)

@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(YearGoal)
class YearGoalTranslationOptions(TranslationOptions):
    fields = ('label',)

@register(Association)
class AssociationTranslationOptions(TranslationOptions):
    fields = ('name', 'address',)

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(CatalogItem)
class CatalogItemTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

@register(CatalogItemSpecification)
class CatalogItemSpecificationTranslationOptions(TranslationOptions):
    fields = ('key', 'value',)

@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'text',)

@register(Video)
class VideoTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(Role)
class RoleTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(Budget)
class BudgetTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(ExtraDoc)
class ExtraDocTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(Information)
class InformationTranslationOptions(TranslationOptions):
    fields = ('question', 'information',)

@register(BlogCategory)
class BlogCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

