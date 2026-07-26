from django.contrib import admin

from .models import (
    AIGeneration,
    AIModelPricing,
    BrandProfile,
    CaptionDraft,
    Category,
    GraphicAsset,
    GraphicTemplate,
    Lesson,
    LessonBlock,
    Series,
    Tag,
    WebsiteExport,
)


class LessonBlockInline(admin.StackedInline):
    model = LessonBlock
    extra = 0
    ordering = ("position",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "difficulty", "category", "series", "updated_at")
    list_filter = ("status", "difficulty", "category", "series")
    search_fields = ("title", "summary", "internal_notes")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = (LessonBlockInline,)


@admin.register(AIGeneration)
class AIGenerationAdmin(admin.ModelAdmin):
    list_display = (
        "purpose",
        "lesson",
        "model",
        "status",
        "input_tokens",
        "output_tokens",
        "estimated_cost_usd",
        "created_at",
    )
    list_filter = ("purpose", "status", "model")
    search_fields = ("lesson__title", "response_id", "prompt", "response_text")
    readonly_fields = (
        "response_id",
        "response_payload",
        "input_tokens",
        "cached_input_tokens",
        "cache_write_tokens",
        "output_tokens",
        "reasoning_tokens",
        "estimated_cost_usd",
        "duration_ms",
        "created_at",
        "updated_at",
    )


@admin.register(GraphicAsset)
class GraphicAssetAdmin(admin.ModelAdmin):
    list_display = ("lesson", "output_format", "slide_number", "status", "created_at")
    list_filter = ("output_format", "status", "template")


admin.site.register(BrandProfile)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Series)
admin.site.register(GraphicTemplate)
admin.site.register(AIModelPricing)
admin.site.register(CaptionDraft)


@admin.register(WebsiteExport)
class WebsiteExportAdmin(admin.ModelAdmin):
    list_display = ("lesson", "revision", "schema_version", "content_hash", "created_at")
    search_fields = ("lesson__title", "content_hash")
    readonly_fields = (
        "lesson",
        "revision",
        "schema_version",
        "content_hash",
        "payload",
        "rendered_html",
        "created_by",
        "created_at",
        "updated_at",
    )
