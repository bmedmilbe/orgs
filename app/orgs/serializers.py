import json

from rest_framework import serializers

from .models import (
    Association,
    BlogCategory,
    Budget,
    CatalogItem,
    CatalogItemSpecification,
    Category,
    Customer,
    District,
    ExtraDoc,
    Information,
    Message,
    Page,
    PageContentBlock,
    Partner,
    Post,
    Review,
    Role,
    Team,
    Video,
    YearGoal,
)

# ==========================================
# 1. CORE & USER MODULE SERIALIZERS
# ==========================================


class CustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "first_name", "last_name", "email"]


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
# 3. METRICS & GOALS SERIALIZERS
# ==========================================


class YearGoalSerializer(serializers.ModelSerializer):
    """Delivers sequential statistical charts or metric value fields (2024-2026)."""

    class Meta:
        model = YearGoal
        fields = ["id", "year", "label", "value", "show_in_dashboard"]


# ==========================================
# 4. ASSOCIATIONS & NETWORK SERIALIZERS
# ==========================================


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]


class AssociationSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source="district.name", read_only=True)
    gallery_images = serializers.SerializerMethodField()

    class Meta:
        model = Association
        fields = [
            "id",
            "name",
            "registered",
            "address",
            "number_of_associated",
            "picture",
            "district",
            "district_name",
            "gallery_images",
        ]

    def get_gallery_images(self, instance):
        return [img.image.url for img in instance.cms_images.all() if img.image]


# ==========================================
# 5. CATALOGUE & ECO-TOURISM SERIALIZERS
# ==========================================


class CatalogItemSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItemSpecification
        fields = ["id", "key", "value"]


class CatalogItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    specifications = CatalogItemSpecificationSerializer(many=True, read_only=True)

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
            "picture",
            "specifications",
        ]


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Groups catalog items cleanly under taxonomies for shop filtering views."""

    items = CatalogItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "items"]


# ==========================================
# 6. POSTS, BLOG & NEWS SERIALIZERS (NESTED)
# ==========================================


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ["id", "name", "slug"]


class InformationSerializer(serializers.ModelSerializer):
    """Renders Q&A accordions directly alongside corresponding blog/service pages."""

    class Meta:
        model = Information
        fields = ["id", "question", "information"]


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
# 7. MULTIMEDIA & COMMUNICATIONS SERIALIZERS
# ==========================================


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "title", "link", "picture", "is_band", "is_spot", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "name", "email", "subject", "text", "sent", "date"]
        read_only_fields = ["sent", "date"]


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ["id", "title", "picture"]


# ==========================================
# 8. CORPORATE GOVERNANCE & TEAM SERIALIZERS
# ==========================================


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "title"]


class TeamSerializer(serializers.ModelSerializer):
    role_title = serializers.CharField(source="role.title", read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "image", "role", "role_title", "from_assembly"]


# ==========================================
# 9. GENERAL DOCUMENTATION SERIALIZERS
# ==========================================


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "title", "slug", "text_file", "date", "year", "type"]


class ExtraDocSerializer(serializers.ModelSerializer):
    gallery_images = serializers.SerializerMethodField()

    class Meta:
        model = ExtraDoc
        fields = [
            "id",
            "title",
            "slug",
            "picture",
            "text_file",
            "active",
            "date",
            "gallery_images",
        ]

    def get_gallery_images(self, instance):
        return [
            img.picture.url for img in instance.cms_extra_images.all() if img.picture
        ]


class ReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.first_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "item", "client_name", "rating", "comment", "created_at"]
        read_only_fields = ["client"]

    def create(self, validated_data):
        client = self.context["request"].user

        instance, created = Review.objects.update_or_create(
            client=client, defaults=validated_data
        )

        return instance
