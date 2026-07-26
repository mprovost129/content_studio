from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Enter a six-digit hex color such as #3776AB.",
)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BrandProfile(TimestampedModel):
    name = models.CharField(max_length=120, default="Code with Michael")
    social_handle = models.CharField(max_length=80, default="@code_with_michael")
    default_accent = models.CharField(
        max_length=7, default="#3776AB", validators=[hex_color_validator]
    )
    background_color = models.CharField(
        max_length=7, default="#0A0C16", validators=[hex_color_validator]
    )
    default_call_to_action = models.CharField(
        max_length=180, default="Save this post and follow for more Python lessons."
    )
    logo = models.ImageField(upload_to="branding/", blank=True)

    class Meta:
        verbose_name = "brand profile"

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        profile, _ = cls.objects.get_or_create(pk=1)
        return profile


class Category(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    accent_color = models.CharField(
        max_length=7, default="#3776AB", validators=[hex_color_validator]
    )

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(TimestampedModel):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Series(TimestampedModel):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=190, unique=True, blank=True)
    description = models.TextField(blank=True)
    total_lessons = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("title",)
        verbose_name_plural = "series"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lesson(TimestampedModel):
    class Status(models.TextChoices):
        IDEA = "idea", "Idea"
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In review"
        READY = "ready", "Ready"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        MIXED = "mixed", "Mixed"

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=230, unique=True, blank=True)
    summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True
    )
    difficulty = models.CharField(
        max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="lessons"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="lessons")
    series = models.ForeignKey(
        Series, on_delete=models.SET_NULL, null=True, blank=True, related_name="lessons"
    )
    series_position = models.PositiveSmallIntegerField(null=True, blank=True)
    accent_color = models.CharField(
        max_length=7, blank=True, validators=[hex_color_validator]
    )
    call_to_action = models.CharField(max_length=220, blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)
    enable_playground = models.BooleanField(
        default=False,
        help_text="Allow code blocks to run in the browser-based Python playground.",
    )
    internal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons_updated",
    )

    class Meta:
        ordering = ("-updated_at",)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:210] or "lesson"
            candidate = base
            suffix = 2
            while Lesson.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("studio:lesson-detail", kwargs={"slug": self.slug})

    @property
    def resolved_accent_color(self):
        if self.accent_color:
            return self.accent_color
        if self.category_id:
            return self.category.accent_color
        return BrandProfile.get_default().default_accent

    def __str__(self):
        return self.title


class LessonBlock(TimestampedModel):
    class BlockType(models.TextChoices):
        HEADING = "heading", "Heading"
        TEXT = "text", "Explanation"
        CODE = "code", "Code"
        OUTPUT = "output", "Output"
        CALLOUT = "callout", "Callout / tip"
        LIST = "list", "List"
        IMAGE = "image", "Image"
        QUIZ = "quiz", "Quiz"
        CHALLENGE = "challenge", "Challenge"
        COMPARISON = "comparison", "Comparison"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="blocks")
    position = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    block_type = models.CharField(max_length=20, choices=BlockType.choices)
    title = models.CharField(max_length=180, blank=True)
    content = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "position"), name="unique_lesson_block_position"
            )
        ]

    def __str__(self):
        return f"{self.lesson}: {self.get_block_type_display()} {self.position}"


class GraphicTemplate(TimestampedModel):
    class TemplateType(models.TextChoices):
        LESSON = "lesson", "Lesson explainer"
        PROJECT = "project", "Project series"
        CHALLENGE = "challenge", "Challenge / quiz"
        ANSWER = "answer", "Answer"
        SPOT_BUG = "spot_bug", "Spot the bug"
        MINI_PROGRAM = "mini_program", "Mini program"
        COMPARISON = "comparison", "Comparison / cheat sheet"
        ERROR = "error", "Errors / common mistakes"
        COMMUNITY = "community", "Community / celebration"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=130, unique=True)
    template_type = models.CharField(max_length=30, choices=TemplateType.choices)
    description = models.TextField(blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class GraphicAsset(TimestampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    class Format(models.TextChoices):
        INSTAGRAM_SQUARE = "instagram_square", "Instagram / Facebook square"
        INSTAGRAM_PORTRAIT = "instagram_portrait", "Instagram / Threads portrait"
        STORY = "story", "Instagram / Facebook story"
        FACEBOOK_LANDSCAPE = "facebook_landscape", "Facebook landscape"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="assets")
    template = models.ForeignKey(
        GraphicTemplate, on_delete=models.PROTECT, related_name="assets"
    )
    output_format = models.CharField(max_length=30, choices=Format.choices)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    slide_number = models.PositiveSmallIntegerField(default=1)
    file = models.ImageField(upload_to="generated/%Y/%m/", blank=True)
    alt_text = models.CharField(max_length=300, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("output_format", "slide_number", "created_at")

    def __str__(self):
        return f"{self.lesson} - {self.get_output_format_display()} #{self.slide_number}"


class AIModelPricing(TimestampedModel):
    model = models.CharField(max_length=80)
    effective_from = models.DateField(default=timezone.localdate)
    input_per_million = models.DecimalField(max_digits=10, decimal_places=4)
    cached_input_per_million = models.DecimalField(max_digits=10, decimal_places=4)
    output_per_million = models.DecimalField(max_digits=10, decimal_places=4)
    cache_write_multiplier = models.DecimalField(
        max_digits=5, decimal_places=3, default=Decimal("1.250")
    )
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-effective_from", "model")
        constraints = [
            models.UniqueConstraint(
                fields=("model", "effective_from"), name="unique_model_price_date"
            )
        ]

    def __str__(self):
        return f"{self.model} pricing from {self.effective_from}"


class AIGeneration(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    class Purpose(models.TextChoices):
        CAPTION = "caption", "Caption"
        LESSON_DRAFT = "lesson_draft", "Lesson draft"
        IMPROVEMENT = "improvement", "Lesson improvement"
        QUIZ = "quiz", "Quiz"
        CHALLENGE = "challenge", "Challenge"

    lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_generations"
    )
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    model = models.CharField(max_length=80)
    reasoning_effort = models.CharField(max_length=20, blank=True)
    response_id = models.CharField(max_length=120, blank=True, db_index=True)
    instructions = models.TextField(blank=True)
    prompt = models.TextField()
    response_text = models.TextField(blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    cached_input_tokens = models.PositiveIntegerField(default=0)
    cache_write_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    reasoning_tokens = models.PositiveIntegerField(default=0)
    input_price_per_million = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    cached_input_price_per_million = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    output_price_per_million = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    cache_write_multiplier = models.DecimalField(
        max_digits=5, decimal_places=3, default=Decimal("1.250")
    )
    estimated_cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def calculate_estimated_cost(self):
        million = Decimal("1000000")
        uncached = max(self.input_tokens - self.cached_input_tokens - self.cache_write_tokens, 0)
        regular_cost = Decimal(uncached) * self.input_price_per_million / million
        cached_cost = (
            Decimal(self.cached_input_tokens) * self.cached_input_price_per_million / million
        )
        cache_write_cost = (
            Decimal(self.cache_write_tokens)
            * self.input_price_per_million
            * self.cache_write_multiplier
            / million
        )
        output_cost = Decimal(self.output_tokens) * self.output_price_per_million / million
        return (regular_cost + cached_cost + cache_write_cost + output_cost).quantize(
            Decimal("0.000001")
        )

    def __str__(self):
        return f"{self.get_purpose_display()} via {self.model} ({self.status})"


class CaptionDraft(TimestampedModel):
    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"
        THREADS = "threads", "Threads"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        ARCHIVED = "archived", "Archived"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="captions")
    platform = models.CharField(max_length=20, choices=Platform.choices)
    content = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    generation = models.ForeignKey(
        AIGeneration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caption_drafts",
    )

    class Meta:
        ordering = ("platform", "-created_at")

    def __str__(self):
        return f"{self.lesson} - {self.get_platform_display()} caption"


class WebsiteExport(TimestampedModel):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="website_exports"
    )
    revision = models.PositiveIntegerField()
    schema_version = models.CharField(max_length=20, default="1.0")
    content_hash = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField()
    rendered_html = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="website_exports_created",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "revision"), name="unique_lesson_website_revision"
            )
        ]

    def __str__(self):
        return f"{self.lesson} website export r{self.revision}"
