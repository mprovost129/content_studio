from django.contrib import admin

from .models import (
    AIGeneration,
    AIModelPricing,
    BrandProfile,
    CaptionDraft,
    Category,
    ChallengeAttempt,
    CodeChallenge,
    ChallengeTestCase,
    ContentPlan,
    LearnerBadge,
    LearnerBadgeAward,
    LessonProgress,
    GraphicAsset,
    GraphicTemplate,
    Lesson,
    LearningResource,
    ResourceLeadMagnetAccess,
    ResourceCTA,
    ResourceCTAClickEvent,
    ResourceCTARecommendationFeedback,
    ResourceLessonConversionEvent,
    RecommendationTuning,
    ResourcePerformanceEvent,
    LessonBlock,
    NewsletterSubscriber,
    NewsletterCampaign,
    NewsletterMetricImport,
    SubscriberSegment,
    PublishingRecord,
    QuizAttempt,
    QuizChoice,
    QuizQuestion,
    Series,
    Tag,
    WebsiteExport,
)


class LessonBlockInline(admin.StackedInline):
    model = LessonBlock
    extra = 0
    ordering = ("position",)


class ChallengeTestCaseInline(admin.TabularInline):
    model = ChallengeTestCase
    extra = 0
    ordering = ("position",)


class CodeChallengeInline(admin.StackedInline):
    model = CodeChallenge
    extra = 0
    ordering = ("position",)


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 1
    ordering = ("position",)


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 0
    ordering = ("position",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "website_status", "facebook_status", "instagram_status", "difficulty", "category", "series", "updated_at")
    list_filter = ("status", "website_status", "facebook_status", "instagram_status", "threads_status", "difficulty", "category", "series")
    search_fields = ("title", "summary", "learning_objective", "beginner_takeaway", "common_mistake", "practice_prompt", "internal_notes")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = (LessonBlockInline, QuizQuestionInline, CodeChallengeInline)


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


@admin.register(ContentPlan)
class ContentPlanAdmin(admin.ModelAdmin):
    list_display = ("lesson", "platform", "scheduled_at", "status", "carousel_template", "publishing_record")
    list_filter = ("platform", "status", "scheduled_at", "lesson__category", "lesson__series")
    search_fields = ("lesson__title", "carousel_template", "post_goal", "notes")
    readonly_fields = ("created_at", "updated_at")



@admin.register(PublishingRecord)
class PublishingRecordAdmin(admin.ModelAdmin):
    list_display = ("lesson", "platform", "published_at", "post_url", "impressions", "reach", "engagement_total", "new_followers")
    list_filter = ("platform", "published_at", "lesson__category", "lesson__series")
    search_fields = ("lesson__title", "post_url", "caption_text", "notes")
    readonly_fields = ("engagement_total", "engagement_rate", "created_at", "updated_at")


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "resource_type", "status", "difficulty", "category", "featured", "pdf_download_enabled", "pdf_requires_email", "updated_at")
    list_filter = ("resource_type", "status", "difficulty", "featured", "pdf_download_enabled", "pdf_requires_email", "category")
    search_fields = ("title", "summary", "content", "beginner_tip", "seo_title", "seo_description", "internal_notes")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags", "related_lessons")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ResourceCTA)
class ResourceCTAAdmin(admin.ModelAdmin):
    list_display = ("resource", "position", "title", "target_type", "target_lesson", "is_active", "updated_at")
    list_filter = ("target_type", "is_active", "resource__resource_type")
    search_fields = ("resource__title", "title", "description", "button_label", "target_lesson__title", "target_url", "internal_notes")
    readonly_fields = ("created_at", "updated_at")


@admin.register(RecommendationTuning)
class RecommendationTuningAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "lesson_cta_bonus", "quiz_cta_bonus", "challenge_cta_bonus", "pdf_lead_magnet_bonus", "newsletter_cta_bonus", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "notes")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Base CTA bonuses", {"fields": ("name", "is_active", "lesson_cta_bonus", "quiz_cta_bonus", "challenge_cta_bonus", "pdf_open_bonus", "pdf_lead_magnet_bonus", "newsletter_cta_bonus")}),
        ("Lesson match weights", {"fields": ("related_lesson_weight", "category_match_weight", "difficulty_match_weight", "topic_overlap_weight", "topic_overlap_cap", "active_quiz_weight", "active_challenge_weight", "practice_code_weight", "conversion_weight", "conversion_cap", "cta_click_weight", "cta_click_cap")}),
        ("Feedback weights", {"fields": ("exact_accepted_boost", "exact_dismissed_penalty", "ignored_per_show_penalty", "ignored_penalty_cap", "similar_accepted_boost", "similar_accepted_cap", "similar_dismissed_penalty", "similar_dismissed_cap", "similar_ignored_penalty", "similar_ignored_cap", "same_lesson_accepted_boost", "same_lesson_accepted_cap", "same_lesson_dismissed_penalty", "same_lesson_dismissed_cap", "feedback_adjustment_floor", "feedback_adjustment_ceiling")}),
        ("Notes", {"fields": ("notes", "created_at", "updated_at")}),
    )


@admin.register(ResourceCTARecommendationFeedback)
class ResourceCTARecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ("resource", "title", "target_type", "target_lesson", "status", "times_shown", "score", "last_seen_at")
    list_filter = ("status", "target_type", "resource__resource_type", "last_seen_at")
    search_fields = ("resource__title", "title", "recommendation_key", "target_lesson__title", "notes")
    readonly_fields = ("first_seen_at", "last_seen_at", "accepted_at", "dismissed_at", "created_at", "updated_at")


@admin.register(ResourceCTAClickEvent)
class ResourceCTAClickEventAdmin(admin.ModelAdmin):
    list_display = ("resource", "cta", "target_lesson", "email", "user", "occurred_at")
    list_filter = ("cta__target_type", "resource", "target_lesson", "occurred_at")
    search_fields = ("resource__title", "cta__title", "target_lesson__title", "email", "target_url", "referrer")
    readonly_fields = ("cta", "resource", "target_lesson", "user", "subscriber", "email", "source_url", "target_url", "referrer", "user_agent", "occurred_at", "created_at", "updated_at")


@admin.register(ResourcePerformanceEvent)
class ResourcePerformanceEventAdmin(admin.ModelAdmin):
    list_display = ("resource", "event_type", "email", "subscriber", "occurred_at")
    list_filter = ("event_type", "resource", "occurred_at")
    search_fields = ("resource__title", "email", "subscriber__email", "source_url", "referrer")
    readonly_fields = ("resource", "event_type", "subscriber", "user", "email", "source_url", "referrer", "user_agent", "occurred_at", "created_at", "updated_at")


@admin.register(ResourceLessonConversionEvent)
class ResourceLessonConversionEventAdmin(admin.ModelAdmin):
    list_display = ("resource", "lesson", "event_type", "cta", "email", "subscriber", "user", "occurred_at")
    list_filter = ("event_type", "cta__target_type", "resource", "lesson", "occurred_at")
    search_fields = ("resource__title", "lesson__title", "cta__title", "email", "subscriber__email", "user__email", "attribution_source_url", "referrer")
    readonly_fields = ("resource", "lesson", "event_type", "source_event", "cta", "cta_click", "subscriber", "user", "email", "attribution_event_type", "attribution_source_url", "referrer", "metadata", "occurred_at", "created_at", "updated_at")


@admin.register(ResourceLeadMagnetAccess)
class ResourceLeadMagnetAccessAdmin(admin.ModelAdmin):
    list_display = ("resource", "email", "subscriber", "download_count", "access_granted_at", "last_downloaded_at")
    list_filter = ("resource", "access_granted_at", "last_downloaded_at")
    search_fields = ("resource__title", "email", "first_name", "subscriber__email")
    readonly_fields = ("access_granted_at", "last_downloaded_at", "download_count", "created_at", "updated_at")


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


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("lesson", "position", "question_type", "is_active", "updated_at")
    list_filter = ("question_type", "is_active", "lesson__category")
    search_fields = ("lesson__title", "prompt", "explanation")
    inlines = (QuizChoiceInline,)


@admin.register(QuizChoice)
class QuizChoiceAdmin(admin.ModelAdmin):
    list_display = ("question", "position", "text", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("question__lesson__title", "question__prompt", "text")


@admin.register(CodeChallenge)
class CodeChallengeAdmin(admin.ModelAdmin):
    list_display = ("lesson", "position", "title", "validation_mode", "test_case_count", "is_active", "updated_at")
    list_filter = ("validation_mode", "is_active", "lesson__category")
    search_fields = ("lesson__title", "title", "prompt", "starter_code", "solution_code")
    inlines = (ChallengeTestCaseInline,)

    def test_case_count(self, obj):
        return obj.test_cases.count()


@admin.register(ChallengeTestCase)
class ChallengeTestCaseAdmin(admin.ModelAdmin):
    list_display = ("challenge", "position", "name", "is_active", "updated_at")
    list_filter = ("is_active", "challenge__lesson__category")
    search_fields = ("challenge__title", "challenge__lesson__title", "name", "description", "test_code", "expected_output")


@admin.register(ChallengeAttempt)
class ChallengeAttemptAdmin(admin.ModelAdmin):
    list_display = ("challenge", "user", "passed", "tests_passed", "tests_total", "created_at")
    list_filter = ("passed", "created_at")
    search_fields = ("challenge__title", "challenge__lesson__title", "submitted_code", "observed_output", "feedback")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "status", "percent_complete", "quiz_correct", "quiz_total", "challenges_passed", "last_activity_at")
    list_filter = ("status", "last_activity_at", "lesson__category")
    search_fields = ("user__email", "lesson__title")
    readonly_fields = ("started_at", "completed_at", "last_activity_at", "created_at", "updated_at")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "selected_choice", "is_correct", "created_at")
    list_filter = ("is_correct", "created_at")
    search_fields = ("user__email", "question__prompt", "question__lesson__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LearnerBadge)
class LearnerBadgeAdmin(admin.ModelAdmin):
    list_display = ("title", "criteria_type", "threshold", "is_active")
    list_filter = ("criteria_type", "is_active")
    search_fields = ("key", "title", "description")


@admin.register(LearnerBadgeAward)
class LearnerBadgeAwardAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    list_filter = ("badge", "awarded_at")
    search_fields = ("user__email", "badge__title")
    readonly_fields = ("awarded_at", "created_at", "updated_at")


@admin.register(SubscriberSegment)
class SubscriberSegmentAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "status_filter", "source_filter", "skill_level_filter", "external_provider", "provider_sync_status", "subscriber_count")
    list_filter = ("is_active", "status_filter", "source_filter", "skill_level_filter", "external_provider", "provider_sync_status", "source_lesson")
    search_fields = ("name", "description", "search_text", "notes", "provider_notes", "external_segment_id", "external_audience_id", "source_lesson__title")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("subscriber_count", "created_at", "updated_at")


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "status", "target_segment", "saved_segment", "external_provider", "provider_sync_status", "scheduled_at", "sent_at", "actual_recipients", "open_rate", "click_rate")
    list_filter = ("status", "target_segment", "saved_segment", "external_provider", "provider_sync_status", "scheduled_at", "sent_at")
    search_fields = ("title", "subject", "preview_text", "body", "lesson__title", "notes", "provider_notes", "external_campaign_id", "external_audience_id")
    readonly_fields = ("open_rate", "click_rate", "click_to_open_rate", "created_at", "updated_at")


@admin.register(NewsletterMetricImport)
class NewsletterMetricImportAdmin(admin.ModelAdmin):
    list_display = ("campaign", "provider", "applied_at", "actual_recipients", "opens", "clicks", "imported_by")
    list_filter = ("provider", "applied_at")
    search_fields = ("campaign__title", "campaign__subject", "source_filename", "notes")
    readonly_fields = ("normalized_data", "raw_payload", "warnings", "applied_at", "created_at", "updated_at")


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "status", "source", "source_lesson", "source_resource", "external_provider", "provider_sync_status", "subscribed_at")
    list_filter = ("status", "source", "external_provider", "provider_sync_status", "source_resource", "subscribed_at")
    search_fields = ("email", "first_name", "source_lesson__title", "source_resource__title", "notes", "provider_notes", "external_contact_id", "external_list_id")
    readonly_fields = ("subscribed_at", "created_at", "updated_at")
