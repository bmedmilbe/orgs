
from rest_framework import serializers

from orgs.serializers import *

from ..models import Customer, Page, PageContentBlock
from .base import BaseReadSerializer, BaseWriteSerializer
from .context import ScopedWriteSerializer


class CustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "first_name", "last_name", "email"]
# --- PageContentBlock ---------------------------------------------------
class PageContentBlockSerializer(BaseReadSerializer):
    class Meta:
        model = PageContentBlock
        fields = ("id", "page", "block_type", "title", "content", "image", "order")


class PageContentBlockWriteSerializer(ScopedWriteSerializer, BaseWriteSerializer):
    scope_kwarg = "page_pk"
    scope_field = "page"
    translatable_fields = ("title", "content")

    class Meta:
        model = PageContentBlock
        fields = ("id", "block_type", "title", "content", "image", "order")
        read_only_fields = ("id",)


# --- Page ---------------------------------------------------------------
class PageSerializer(BaseReadSerializer):
    blocks = PageContentBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = ("id", "title", "slug", "active", "order", "blocks")


class PageWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("title",)

    class Meta:
        model = Page
        fields = ("id", "title", "slug", "active", "order")
        read_only_fields = ("id",)

from ..models import YearGoal
from .base import BaseReadSerializer, BaseWriteSerializer


class YearGoalSerializer(BaseReadSerializer):
    class Meta:
        model = YearGoal
        fields = ("id", "year", "label", "value", "show_in_dashboard")


class YearGoalWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("label",)

    class Meta:
        model = YearGoal
        fields = ("id", "year", "label", "value", "show_in_dashboard")
        read_only_fields = ("id",)


from rest_framework import serializers

from ..models import Association, AssociationImage, District
from .base import BaseReadSerializer, BaseWriteSerializer
from .context import ScopedWriteSerializer


class AssociationImageSerializer(BaseReadSerializer):
    class Meta:
        model = AssociationImage
        fields = ("id", "image")


class AssociationImageWriteSerializer(ScopedWriteSerializer, BaseWriteSerializer):
    scope_kwarg = "association_pk"
    scope_field = "association"

    class Meta:
        model = AssociationImage
        fields = ("id", "image")
        read_only_fields = ("id",)


class DistrictSerializer(BaseReadSerializer):
    class Meta:
        model = District
        fields = ("id", "name")


class DistrictWriteSerializer(BaseWriteSerializer):
    class Meta:
        model = District
        fields = ("id", "name")
        read_only_fields = ("id",)


class AssociationSerializer(BaseReadSerializer):
    district = DistrictSerializer(read_only=True)
    images = AssociationImageSerializer(
        source="cms_images", many=True, read_only=True
    )

    class Meta:
        model = Association
        fields = (
            "id", "name", "registered", "address", "number_of_associated",
            "picture", "district", "latitude", "longitude", "images",
        )


class AssociationWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("name", "address")

    class Meta:
        model = Association
        fields = (
            "id", "name", "registered", "address", "number_of_associated",
            "picture", "district", "latitude", "longitude",
        )
        read_only_fields = ("id",)

    def validate_latitude(self, value):
        if value is not None and not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value is not None and not (-180 <= value <= 180):
            raise serializers.ValidationError(
                "Longitude must be between -180 and 180."
            )
        return value



from ..models import (
    CatalogItem,
    CatalogItemPicture,
    CatalogItemSpecification,
    Category,
)
from .base import BaseReadSerializer, BaseWriteSerializer
from .context import ScopedWriteSerializer


class CategorySerializer(BaseReadSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class CategoryWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("name",)

    class Meta:
        model = Category
        fields = ("id", "name", "slug")
        read_only_fields = ("id",)


class CatalogItemPictureSerializer(BaseReadSerializer):
    class Meta:
        model = CatalogItemPicture
        fields = ("id", "picture", "caption", "is_feature")


class CatalogItemPictureWriteSerializer( BaseWriteSerializer):

    class Meta:
        model = CatalogItemPicture
        fields = ("id", "picture", "caption", "is_feature")
        read_only_fields = ("id",)

    def _unset_siblings(self, item_id, exclude_pk=None):
        qs = CatalogItemPicture.objects.filter(
            catalog_item_id=item_id, is_feature=True
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        qs.update(is_feature=False)

    def create(self, validated_data):
        catalogitem_pk = self.context['catalogitem_pk']
        if validated_data.get("is_feature"):
            item_id = catalogitem_pk
            self._unset_siblings(item_id)
        validated_data['catalog_item_id'] = catalogitem_pk
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_feature"):
            self._unset_siblings(instance.catalog_item_id, exclude_pk=instance.pk)
        return super().update(instance, validated_data)



class CatalogItemSpecificationSerializer(BaseReadSerializer):
    class Meta:
        model = CatalogItemSpecification
        fields = ("id", "key", "value")


class CatalogItemSpecificationWriteSerializer(
    ScopedWriteSerializer, BaseWriteSerializer
):
    scope_kwarg = "item_pk"
    scope_field = "item"
    translatable_fields = ("key", "value")

    class Meta:
        model = CatalogItemSpecification
        fields = ("id", "key", "value")
        read_only_fields = ("id",)



class CatalogItemSerializer(BaseReadSerializer):
    category = CategorySerializer(read_only=True)
    pictures = CatalogItemPictureSerializer(many=True, read_only=True)
    specifications = CatalogItemSpecificationSerializer(many=True, read_only=True)

    class Meta:
        model = CatalogItem
        fields = (
            "id", "category", "name", "slug", "description", "price",
            "is_available", "average_rating", "total_reviews",
            "pictures", "specifications",
        )

class CategoryDetailSerializer(serializers.ModelSerializer):
    """Groups catalog items cleanly under taxonomies for shop filtering views."""

    items = CatalogItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "items"]
class CatalogItemWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("name", "description")

    class Meta:
        model = CatalogItem
        fields = ("id", "category", "name", "slug", "description",
                  "price", "is_available")
        read_only_fields = ("id",)

from ..models import (
    BlogCategory,
    Post,
    PostDocument,
    PostFile,
    PostImage,
    PostVideo,
)
from .base import BaseReadSerializer, BaseWriteSerializer
from .context import ScopedWriteSerializer


class BlogCategorySerializer(BaseReadSerializer):
    class Meta:
        model = BlogCategory
        fields = ("id", "name", "slug")


class BlogCategoryWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("name",)

    class Meta:
        model = BlogCategory
        fields = ("id", "name", "slug")
        read_only_fields = ("id",)


# --- Scoped children -----------------------------------------------------
class _PostChildBase(ScopedWriteSerializer, BaseWriteSerializer):
    scope_kwarg = "post_pk"
    scope_field = "post"
    read_only_fields = ("id",)


class PostImageSerializer(BaseReadSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "picture")


class PostImageWriteSerializer(_PostChildBase):
    class Meta:
        model = PostImage
        fields = ("id", "picture")


class PostDocumentSerializer(BaseReadSerializer):
    class Meta:
        model = PostDocument
        fields = ("id", "document")


class PostDocumentWriteSerializer(_PostChildBase):
    class Meta:
        model = PostDocument
        fields = ("id", "document")


class PostFileSerializer(BaseReadSerializer):
    class Meta:
        model = PostFile
        fields = ("id", "file")


class PostFileWriteSerializer(_PostChildBase):
    class Meta:
        model = PostFile
        fields = ("id", "file")


class PostVideoSerializer(BaseReadSerializer):
    class Meta:
        model = PostVideo
        fields = ("id", "video")


class PostVideoWriteSerializer(_PostChildBase):
    class Meta:
        model = PostVideo
        fields = ("id", "video")


# --- Post ----------------------------------------------------------------
class PostSerializer(BaseReadSerializer):
    blog_category = BlogCategorySerializer(read_only=True)
    post_images = PostImageSerializer(many=True, read_only=True)
    documents = PostDocumentSerializer(many=True, read_only=True)
    cms_files = PostFileSerializer(many=True, read_only=True)
    post_videos = PostVideoSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id", "blog_category", "title", "slug", "picture",
            "description", "text", "active", "date", "featured",
            "is_a_service", "is_social_service", "is_to_front",
            "post_images", "documents", "cms_files", "post_videos",
        )


class PostWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("title", "description", "text")

    class Meta:
        model = Post
        fields = (
            "id", "blog_category", "slug", "picture",
            "text_file", "text_file_pt", "text_file_en", "text_file_fr",
            "active", "featured", "is_a_service", "is_social_service",
            "is_to_front",
            "title", "description", "text",   # base names only!
        )
        read_only_fields = (
            "id",
            "processed_text_file",
            "processed_text_file_pt",
            "processed_text_file_en",
            "processed_text_file_fr",
        )

# multimedia.py
from ..models import Message, Video
from .base import BaseReadSerializer, BaseWriteSerializer


class VideoSerializer(BaseReadSerializer):
    class Meta:
        model = Video
        fields = ("id", "title", "link", "picture",
                  "is_band", "is_spot", "created_at")


class VideoWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("title",)

    class Meta:
        model = Video
        fields = ("id", "title", "link", "picture",
                  "is_band", "is_spot", "created_at")
        read_only_fields = ("id",)


class MessageSerializer(BaseReadSerializer):
    class Meta:
        model = Message
        fields = ("id", "name", "email", "subject", "text", "sent", "date")


class MessageWriteSerializer(BaseWriteSerializer):
    class Meta:
        model = Message
        fields = ("id", "name", "email", "subject", "text")
        read_only_fields = ("id",)

# partners_team.py
from ..models import Partner, Role, Team
from .base import BaseReadSerializer, BaseWriteSerializer


class PartnerSerializer(BaseReadSerializer):
    class Meta:
        model = Partner
        fields = ("id", "title", "picture")


class PartnerWriteSerializer(BaseWriteSerializer):
    class Meta:
        model = Partner
        fields = ("id", "title", "picture")
        read_only_fields = ("id",)


class RoleSerializer(BaseReadSerializer):
    class Meta:
        model = Role
        fields = ("id", "title")


class RoleWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("title",)

    class Meta:
        model = Role
        fields = ("id", "title")
        read_only_fields = ("id",)


class TeamSerializer(BaseReadSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = Team
        fields = ("id", "name", "image", "role", "from_assembly")


class TeamWriteSerializer(BaseWriteSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "image", "role", "from_assembly")
        read_only_fields = ("id",)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        name = attrs.get("name", getattr(self.instance, "name", None))
        role = attrs.get("role", getattr(self.instance, "role", None))
        if name and role:
            qs = Team.objects.filter(name=name, role=role)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "A team member with this name and role already exists."
                )
        return attrs

# docs.py
from ..models import Budget, ExtraDoc, ExtraImage, Information
from .base import BaseReadSerializer, BaseWriteSerializer
from .context import ScopedWriteSerializer


class BudgetSerializer(BaseReadSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Budget
        fields = ("id", "title", "slug", "text_file",
                  "date", "year", "type", "type_display")


class BudgetWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("title",)

    class Meta:
        model = Budget
        fields = ("id", "title", "slug", "text_file", "year", "type")
        read_only_fields = ("id",)


class ExtraImageSerializer(BaseReadSerializer):
    class Meta:
        model = ExtraImage
        fields = ("id", "picture")


class ExtraImageWriteSerializer(ScopedWriteSerializer, BaseWriteSerializer):
    scope_kwarg = "extradoc_pk"
    scope_field = "extra_doc"

    class Meta:
        model = ExtraImage
        fields = ("id", "picture")
        read_only_fields = ("id",)


class ExtraDocSerializer(BaseReadSerializer):
    images = ExtraImageSerializer(
        source="cms_extra_images", many=True, read_only=True
    )

    class Meta:
        model = ExtraDoc
        fields = ("id", "title", "slug", "picture", "text_file",
                  "active", "date", "images")


class ExtraDocWriteSerializer(BaseWriteSerializer):
    translatable_fields = ("title",)

    class Meta:
        model = ExtraDoc
        fields = ("id", "title", "slug", "picture", "text_file", "active")
        read_only_fields = ("id",)


class InformationSerializer(BaseReadSerializer):
    class Meta:
        model = Information
        fields = ("id", "question", "information")


class InformationWriteSerializer(ScopedWriteSerializer, BaseWriteSerializer):
    scope_kwarg = "post_pk"
    scope_field = "service"
    translatable_fields = ("question", "information")

    class Meta:
        model = Information
        fields = ("id", "question", "information")
        read_only_fields = ("id",)

# reviews.py
from rest_framework import serializers

from ..models import Review
from .base import BaseReadSerializer, BaseWriteSerializer
from .context import ParentScopeMixin


class ReviewSerializer(BaseReadSerializer):
    client_username = serializers.CharField(source="client.username", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "item", "client", "client_username",
                  "rating", "comment", "is_approved", "created_at")


class ReviewWriteSerializer(ParentScopeMixin, BaseWriteSerializer):
    class Meta:
        model = Review
        fields = ("id", "rating", "comment")
        read_only_fields = ("id",)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        item_id = self.get_parent_id("item_pk")

        user_id = self.context.get("user_id")

        if not user_id:
            raise serializers.ValidationError({"user": "User id must be provided."})
        

        if self.instance is None and Review.objects.filter(
            item_id=item_id, client_id=user_id
        ).exists():
            raise serializers.ValidationError("You have already reviewed this item.")
        return attrs

    def create(self, validated_data):
        item_id = self.get_parent_id("item_pk")
        user_id = self.context["user_id"]
        return Review.objects.create(item_id=item_id, client_id=user_id, **validated_data)

    def update(self, instance, validated_data):
        user_id = self.context.get("user_id")
        if user_id and instance.client_id != user_id:
            raise serializers.ValidationError("You cannot edit another user's review.")
        return super().update(instance, validated_data)



# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER SERIALIZERS
# ==========================================


class PageContentBlockSerializer(serializers.ModelSerializer):
    """Renders modular blocks. Localized values are resolved automatically via modeltranslate."""

    class Meta:
        model = PageContentBlock
        fields = ["id", "block_type", "title", "content", "image", "order"]


class PageDetailSerializer(serializers.ModelSerializer):
    """Returns a holistic page container holding sorted component content arrays."""

    blocks = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "title", "slug", "active", "order", "blocks"]

    def get_blocks(self, instance):
        ordered_blocks = instance.blocks.filter(page__active=True).order_by("order")
        return PageContentBlockSerializer(
            ordered_blocks, many=True, context=self.context
        ).data


# ==========================================
# 4. ASSOCIATIONS & NETWORK SERIALIZERS
# ==========================================


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]



class CatalogItemSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItemSpecification
        fields = ["id", "key", "value"]
class CatalogItemPictureSerializer(serializers.ModelSerializer):
    """Serializer for handling nested or standalone CatalogItem pictures."""
    
    class Meta:
        model = CatalogItemPicture
        fields = ['id', 'caption', 'is_feature']

class CatalogItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  
    
    category_name = serializers.CharField(source="category.name", read_only=True)
    specifications = CatalogItemSpecificationSerializer(many=True, read_only=True)
    
    reviews = ReviewSerializer(many=True, read_only=True)
    pictures = CatalogItemPictureSerializer(many=True, read_only=True)

    class Meta:
        model = CatalogItem
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "price",
            "is_available",
            "specifications",
            "reviews",
            "pictures"
        ]





# ==========================================
# 6. POSTS, BLOG & NEWS SERIALIZERS (NESTED)
# ==========================================


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ["id", "name", "slug"]




class PostListSerializer(serializers.ModelSerializer):
    """Lightweight post serializer to render fast list views or cards."""

    category_slug = serializers.CharField(source="blog_category.slug", read_only=True)

    class Meta:
        model = Post
        fields = [
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


class PostDetailSerializer(serializers.ModelSerializer):
    """Comprehensive blog rendering object supporting dynamic parser JSON injections."""

    category = BlogCategorySerializer(source="blog_category", read_only=True)
    gallery_images = serializers.SerializerMethodField()
    gallery_videos = serializers.SerializerMethodField()
    downloadable_documents = serializers.SerializerMethodField()
    faq_entries = InformationSerializer(
        source="informations", many=True, read_only=True
    )
    parsed_json_data = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
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

    def get_gallery_images(self, instance):
        return [img.picture.url for img in instance.post_images.all() if img.picture]

    def get_gallery_videos(self, instance):
        return [
            {"title": v.video.title, "url": v.video.link}
            for v in instance.post_videos.all()
            if v.video
        ]

    def get_downloadable_documents(self, instance):
        docs = [d.document.url for d in instance.documents.all() if d.document]
        files = [f.file.url for f in instance.cms_files.all() if f.file]
        return {"documents": docs, "files": files}

    def get_parsed_json_data(self, instance):
        """
        Safely attempts to pass down raw JSON metadata from the Word parser pipeline
        straight to Next.js components, stripping file loading chores from the client frontend.
        """
        if instance.processed_text_file:
            try:
                with instance.processed_text_file.open("r") as f:
                    return json.load(f)
            except Exception:
                return None
        return None




# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM SERIALIZERS
# ==========================================


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "title"]



