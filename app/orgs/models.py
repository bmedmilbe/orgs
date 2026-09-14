from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg

# ==========================================
# 1. CORE & USER MODULE
# ==========================================


class CustomerQuerySet(models.QuerySet):
    def optimized(self):
        return self.select_related("user")


class Customer(models.Model):
    """Manages internal client staff levels and access permissions within the tenant."""

    objects = CustomerQuerySet.as_manager()
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cms_customer"
    )
    domain = models.URLField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"


# ==========================================
# 2. DYNAMIC CONTENT & PAGE BUILDER MODULE
# ==========================================


class Page(models.Model):
    """Represents an institutional website page (e.g., 'Home', 'About Us', 'Chocolate Factory')."""

    title = models.CharField(max_length=255)  # Translatable via modeltranslate
    slug = models.SlugField(max_length=255, unique=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


class PageContentBlock(models.Model):
    """Flexible content blocks to assemble pages dynamically (Text/HTML, Banners, Processes)."""

    BLOCK_TYPES = [
        ("text", "Rich Text / HTML"),
        ("hero", "Hero Banner"),
        ("process", "Step-by-Step / Process / Timeline"),
    ]
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    block_type = models.CharField(max_length=50, choices=BLOCK_TYPES)
    title = models.CharField(max_length=255, blank=True, null=True)  # Translatable
    content = models.TextField(
        blank=True, null=True
    )  # Translatable (Supports rich text)
    image = models.FileField(
        upload_to="orgs_api/cms/pages/blocks/", blank=True, null=True
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.page.title} - {self.block_type} ({self.title or 'No Title'})"


# ==========================================
# 3. METRICS & GOALS MODULE
# ==========================================


class YearGoal(models.Model):
    """
    Tracks annual growth metrics and indicators (2024-2026).
    Accommodates cacao volume, chocolate volume, number of farmers, and associations.
    """

    year = models.IntegerField()
    label = models.CharField(
        max_length=255, default="Metric"
    )  # Translatable (e.g., "Chocolate Produced")
    value = models.DecimalField(max_digits=12, decimal_places=2)
    show_in_dashboard = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.label} ({self.year}): {self.value:.2f}"


# ==========================================
# 4. ASSOCIATIONS & NETWORK MODULE
# ==========================================


class District(models.Model):
    """Geographical regional divisions for entity filtering."""

    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.name}"


class AssociationQuerySet(models.QuerySet):
    def optimized(self):
        return self.select_related("district").prefetch_related("cms_images")


class Association(models.Model):
    """Tracks network partners or rural community associations (e.g., the 42 CECAB associations)."""

    objects = AssociationQuerySet.as_manager()
    name = models.CharField(max_length=255)
    registered = models.DateField()
    address = models.CharField(max_length=255)  # Translatable
    number_of_associated = models.IntegerField()
    picture = models.FileField(upload_to="orgs_api/cms/association_images")
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="cms_associations"
    )

    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    
    longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    

    def __str__(self) -> str:
        return f"{self.name}"


class AssociationImage(models.Model):
    association = models.ForeignKey(
        Association, on_delete=models.CASCADE, related_name="cms_images"
    )
    image = models.FileField(upload_to="orgs_api/cms/association_images/")


# ==========================================
# 5. CATALOGUE & ECO-TOURISM MODULE
# ==========================================


class Category(models.Model):
    """General item categorizations (e.g., 'Chocolates', 'Rooms/Lodging', 'Guided Tours')."""

    name = models.CharField(max_length=255)  # Translatable
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class CatalogItem(models.Model):
    """Unified catalog for factory products, visitor lodging rooms, or guided plantation tours."""

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="items"
    )
    name = models.CharField(max_length=255)  # Translatable
    slug = models.SlugField(max_length=255)
    description = models.TextField()  # Translatable
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    
    
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class CatalogItemPicture(models.Model):
    """Stores multiple images for a single CatalogItem."""

    catalog_item = models.ForeignKey(
        CatalogItem, 
        on_delete=models.CASCADE, 
        related_name="pictures"  
    )
    picture = models.FileField(upload_to="orgs_api/cms/catalog/")
    caption = models.CharField(max_length=150, blank=True)
    is_feature = models.BooleanField(
        default=False, 
        help_text="Designates if this is the main image used in catalog listings."
    )

    def __str__(self) -> str:
        return f"Picture for {self.catalog_item.name}"


class CatalogItemSpecification(models.Model):
    """Extra metadata properties for catalog items (e.g., 'Sustainability Stamp', 'Room Capacity')."""

    item = models.ForeignKey(
        CatalogItem, on_delete=models.CASCADE, related_name="specifications"
    )
    key = models.CharField(max_length=255)  # Translatable (e.g., "Certification")
    value = models.CharField(max_length=255)  # Translatable (e.g., "Fairtrade / FLO")


# ==========================================
# 6. POSTS, BLOG & NEWS MODULE (NESTED ARCHITECTURE)
# ==========================================


class BlogCategory(models.Model):
    """Dedicated categorization node for articles (e.g., 'News', 'Social Programs', 'Projects')."""

    name = models.CharField(max_length=255)  # Translatable
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Blog Categories"

    def __str__(self) -> str:
        return self.name


class PostQuerySet(models.QuerySet):
    def optimized(self):
        return self.select_related("blog_category").prefetch_related(
            "post_images", "post_videos", "cms_files", "documents", "informations"
        )


class Post(models.Model):
    """Editorial system managing dynamic entries, news blogs, and community programs."""

    objects = PostQuerySet.as_manager()
    blog_category = models.ForeignKey(
        BlogCategory,
        on_delete=models.PROTECT,
        related_name="posts",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)  # Translatable
    slug = models.SlugField(max_length=255, db_index=True)
    picture = models.FileField(upload_to="orgs_api/cms/posts/images/")
    text_file = models.FileField(
        upload_to="orgs_api/cms/posts/documents/", null=True, max_length=500, blank=True
    )
    processed_text_file = models.FileField(
        upload_to="orgs_api/cms/posts/processed/",
        null=True,
        max_length=500,
        blank=True,
        help_text="Auto-generated JSON file with processed HTML content",
    )
    active = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False)
    is_a_service = models.BooleanField(default=False)
    is_social_service = models.BooleanField(default=False)
    is_to_front = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)  # Translatable
    text = models.TextField(null=True, blank=True)  # Translatable

    text_file_pt = models.FileField(
        upload_to="orgs_api/cms/posts/documents/pt/",
        null=True,
        max_length=500,
        blank=True,
        verbose_name="Portuguese Document (DOCX)",
    )
    text_file_en = models.FileField(
        upload_to="orgs_api/cms/posts/documents/en/",
        null=True,
        max_length=500,
        blank=True,
        verbose_name="English Document (DOCX)",
    )
    text_file_fr = models.FileField(
        upload_to="orgs_api/cms/posts/documents/fr/",
        null=True,
        max_length=500,
        blank=True,
        verbose_name="French Document (DOCX)",
    )

    processed_text_file_pt = models.FileField(
        upload_to="orgs_api/cms/posts/processed/pt/",
        null=True,
        max_length=500,
        blank=True,
        verbose_name="Processed Portuguese JSON",
    )
    processed_text_file_en = models.FileField(
        upload_to="orgs_api/cms/posts/processed/en/",
        null=True,
        max_length=500,
        blank=True,
        verbose_name="Processed English JSON",
    )
    processed_text_file_fr = models.FileField(
        upload_to="orgs_api/cms/posts/processed/fr/",
        null=True,
        max_length=500,
        blank=True,
        verbose_name="Processed French JSON",
    )

    def __str__(self):
        return self.title


class PostDocument(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="documents")
    document = models.FileField(upload_to="orgs_api/cms/post/documents/")


class PostFile(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="cms_files")
    file = models.FileField(upload_to="orgs_api/cms/posts/file/")


class PostImage(models.Model):
    picture = models.FileField(upload_to="orgs_api/cms/posts/images/")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_images")


# ==========================================
# 7. MULTIMEDIA & COMMUNICATIONS MODULE
# ==========================================


class Video(models.Model):
    """Handles external video integrations (e.g., CECAB Band performance showcases)."""

    title = models.CharField(max_length=255)  # Translatable
    link = models.URLField()
    picture = models.FileField(
        upload_to="orgs_api/cms/video_images/", null=True, blank=True
    )
    is_band = models.BooleanField(default=False)
    is_spot = models.BooleanField(default=False)
    created_at = models.DateField()

    def __str__(self) -> str:
        return self.title


class PostVideo(models.Model):
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="post_videos", null=True
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="post_videos", null=True
    )


class Message(models.Model):
    """Inbound customer contact forms."""

    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    subject = models.CharField(max_length=255)
    text = models.TextField()
    sent = models.BooleanField(default=False, blank=True)
    date = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self) -> str:
        return f"{self.name}"


# ==============================================================================
# PARTNER MODULE
# ==============================================================================
class Partner(models.Model):
    """External sustainability certificates, FLO/Fairtrade, or commercial allies."""

    title = models.CharField(max_length=255)
    picture = models.FileField(upload_to="orgs_api/cms/partner_images/")

    def __str__(self) -> str:
        return f"{self.title}"


# ==============================================================================
# 8. CORPORATE GOVERNANCE & TEAM MODULE
# ==============================================================================
class Role(models.Model):
    """Corporate structure organizational positions."""

    title = models.CharField(max_length=255)  # Translatable

    def __str__(self) -> str:
        return f"{self.title}"


class Team(models.Model):
    """Board directors, community leadership, and active members management."""

    name = models.CharField(max_length=255)
    image = models.FileField(upload_to="orgs_api/cms/team/images/", null=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="teams")
    from_assembly = models.BooleanField(default=False)

    class Meta:
        unique_together = ["name", "role"]

    def __str__(self) -> str:
        return f"{self.name} - {self.role}"


# ==============================================================================
# 9. GENERAL DOCUMENTATION MODULE
# ==============================================================================
class Budget(models.Model):
    """Official financial transparency documents and corporate laws."""

    TYPE_BUDGET = "B"
    TYPE_REPORT = "R"
    TYPE_LAW = "L"
    STATUS_CHOICES = [
        (TYPE_BUDGET, "Budget"),
        (TYPE_REPORT, "Report"),
        (TYPE_LAW, "Law"),
    ]

    title = models.CharField(max_length=255)  # Translatable
    slug = models.SlugField(max_length=255, null=True)
    text_file = models.FileField(upload_to="orgs_api/cms/docs/documents/")
    date = models.DateTimeField(auto_now_add=True)
    year = models.IntegerField(null=True, blank=True)
    type = models.CharField(max_length=1, choices=STATUS_CHOICES)

    def __str__(self) -> str:
        return f"{self.title}"


class ExtraDoc(models.Model):
    """Auxiliary downloadable legal or quality documentation sheets."""

    title = models.CharField(max_length=255)  # Translatable
    slug = models.SlugField(max_length=255, null=True)
    picture = models.FileField(upload_to="orgs_api/cms/posts/images/", null=True)
    text_file = models.FileField(upload_to="orgs_api/cms/posts/documents/")
    active = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title}"


class ExtraImage(models.Model):
    picture = models.FileField(upload_to="orgs_api/cms/extras/images/")
    extra_doc = models.ForeignKey(
        ExtraDoc, on_delete=models.CASCADE, related_name="cms_extra_images"
    )


class Information(models.Model):
    """Service-specific detailed Q&A documentation arrays."""

    service = models.ForeignKey(
        "Post", on_delete=models.PROTECT, related_name="informations"
    )
    question = models.CharField(max_length=255)  # Translatable
    information = models.TextField()  # Translatable

    def __str__(self) -> str:
        return f"{self.question}"


class Review(models.Model):
    """Allows authenticated clients to leave ratings and feedback on catalog entries."""

    item = models.ForeignKey(
        CatalogItem, on_delete=models.CASCADE, related_name="reviews"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()  # Translatable if needed, otherwise kept as raw text
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        # Ensures a unique customer can only review a specific product/tour once
        unique_together = ("item", "client")

    def __str__(self) -> str:
        return f"Review by {self.client.username} on {self.item.name} ({self.rating}/5)"

    def update_item_rating(self):
        """Safely aggregates and caches calculations isolated purely to the target item context."""
        # Query strictly isolated to this item's approved reviews
        item_reviews = Review.objects.filter(item=self.item, is_approved=True)
        stats = item_reviews.aggregate(avg_rating=Avg("rating"))

        # Save metrics directly back to the parent item cache
        self.item.average_rating = stats["avg_rating"] or 0.00
        self.item.total_reviews = item_reviews.count()
        self.item.save(update_fields=["average_rating", "total_reviews"])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_item_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.update_item_rating()
