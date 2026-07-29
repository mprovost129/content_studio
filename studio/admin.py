from django.contrib import admin

from .models import (
    AIGeneration,
    AIModelPricing,
    BrandProfile,
    CaptionDraft,
    Category,
    ChallengeAttempt,
    ChallengeTestCase,
    CodeChallenge,
    ContentPlan,
    ExperimentDecisionTuning,
    ExperimentDecisionTuningChangeLog,
    ExperimentDecisionTuningExperimentSnapshot,
    ExperimentDecisionTuningSnapshotComparisonReport,
    ExperimentDecisionTuningSnapshotComparisonReportTemplate,
    ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback,
    GraphicAsset,
    GraphicTemplate,
    LearnerBadge,
    LearnerBadgeAward,
    LearningResource,
    Lesson,
    LessonBlock,
    LessonProgress,
    NewsletterCampaign,
    NewsletterMetricImport,
    NewsletterSubscriber,
    PublishingRecord,
    QuizAttempt,
    QuizChoice,
    QuizQuestion,
    RecommendationTuning,
    RecommendationTuningChangeLog,
    RecommendationTuningExperimentSnapshot,
    ReportTemplateRecommendationTuning,
    ReportTemplateRecommendationTuningChangeLog,
    ReportTemplateRecommendationTuningDecisionRules,
    ReportTemplateRecommendationTuningDecisionRulesChangeLog,
    ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot,
    ReportTemplateRecommendationTuningExperimentSnapshot,
    ResourceCTA,
    ResourceCTAClickEvent,
    ResourceCTARecommendationFeedback,
    ResourceLeadMagnetAccess,
    ResourceLessonConversionEvent,
    ResourcePerformanceEvent,
    Series,
    SubscriberSegment,
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
    list_display = (
        "title",
        "status",
        "website_status",
        "facebook_status",
        "instagram_status",
        "difficulty",
        "category",
        "series",
        "updated_at",
    )
    list_filter = (
        "status",
        "website_status",
        "facebook_status",
        "instagram_status",
        "threads_status",
        "difficulty",
        "category",
        "series",
    )
    search_fields = (
        "title",
        "summary",
        "learning_objective",
        "beginner_takeaway",
        "common_mistake",
        "practice_prompt",
        "internal_notes",
    )
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
    list_display = (
        "lesson",
        "platform",
        "scheduled_at",
        "status",
        "carousel_template",
        "publishing_record",
    )
    list_filter = (
        "platform",
        "status",
        "scheduled_at",
        "lesson__category",
        "lesson__series",
    )
    search_fields = ("lesson__title", "carousel_template", "post_goal", "notes")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PublishingRecord)
class PublishingRecordAdmin(admin.ModelAdmin):
    list_display = (
        "lesson",
        "platform",
        "published_at",
        "post_url",
        "impressions",
        "reach",
        "engagement_total",
        "new_followers",
    )
    list_filter = ("platform", "published_at", "lesson__category", "lesson__series")
    search_fields = ("lesson__title", "post_url", "caption_text", "notes")
    readonly_fields = (
        "engagement_total",
        "engagement_rate",
        "created_at",
        "updated_at",
    )


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "resource_type",
        "status",
        "difficulty",
        "category",
        "featured",
        "pdf_download_enabled",
        "pdf_requires_email",
        "updated_at",
    )
    list_filter = (
        "resource_type",
        "status",
        "difficulty",
        "featured",
        "pdf_download_enabled",
        "pdf_requires_email",
        "category",
    )
    search_fields = (
        "title",
        "summary",
        "content",
        "beginner_tip",
        "seo_title",
        "seo_description",
        "internal_notes",
    )
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags", "related_lessons")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ResourceCTA)
class ResourceCTAAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "position",
        "title",
        "target_type",
        "target_lesson",
        "is_active",
        "updated_at",
    )
    list_filter = ("target_type", "is_active", "resource__resource_type")
    search_fields = (
        "resource__title",
        "title",
        "description",
        "button_label",
        "target_lesson__title",
        "target_url",
        "internal_notes",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(RecommendationTuning)
class RecommendationTuningAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "lesson_cta_bonus",
        "quiz_cta_bonus",
        "challenge_cta_bonus",
        "pdf_lead_magnet_bonus",
        "newsletter_cta_bonus",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "notes")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Base CTA bonuses",
            {
                "fields": (
                    "name",
                    "is_active",
                    "lesson_cta_bonus",
                    "quiz_cta_bonus",
                    "challenge_cta_bonus",
                    "pdf_open_bonus",
                    "pdf_lead_magnet_bonus",
                    "newsletter_cta_bonus",
                )
            },
        ),
        (
            "Lesson match weights",
            {
                "fields": (
                    "related_lesson_weight",
                    "category_match_weight",
                    "difficulty_match_weight",
                    "topic_overlap_weight",
                    "topic_overlap_cap",
                    "active_quiz_weight",
                    "active_challenge_weight",
                    "practice_code_weight",
                    "conversion_weight",
                    "conversion_cap",
                    "cta_click_weight",
                    "cta_click_cap",
                )
            },
        ),
        (
            "Feedback weights",
            {
                "fields": (
                    "exact_accepted_boost",
                    "exact_dismissed_penalty",
                    "ignored_per_show_penalty",
                    "ignored_penalty_cap",
                    "similar_accepted_boost",
                    "similar_accepted_cap",
                    "similar_dismissed_penalty",
                    "similar_dismissed_cap",
                    "similar_ignored_penalty",
                    "similar_ignored_cap",
                    "same_lesson_accepted_boost",
                    "same_lesson_accepted_cap",
                    "same_lesson_dismissed_penalty",
                    "same_lesson_dismissed_cap",
                    "feedback_adjustment_floor",
                    "feedback_adjustment_ceiling",
                )
            },
        ),
        ("Notes", {"fields": ("notes", "created_at", "updated_at")}),
    )


@admin.register(RecommendationTuningChangeLog)
class RecommendationTuningChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "tuning",
        "changed_by",
        "preset_name",
        "experiment_label",
        "experiment_status",
        "experiment_outcome",
        "changed_field_count",
    )
    list_filter = (
        "action",
        "experiment_status",
        "experiment_outcome",
        "preset_key",
        "created_at",
    )
    search_fields = (
        "tuning__name",
        "changed_by__email",
        "preset_name",
        "preset_key",
        "reason",
        "request_path",
        "experiment_label",
        "experiment_notes",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "changed_field_count",
        "before",
        "after",
        "diff",
        "outcome_recorded_at",
        "outcome_recorded_by",
    )
    fieldsets = (
        (
            "Change",
            {
                "fields": (
                    "tuning",
                    "action",
                    "changed_by",
                    "preset_key",
                    "preset_name",
                    "reason",
                    "request_path",
                )
            },
        ),
        (
            "Experiment",
            {
                "fields": (
                    "experiment_label",
                    "experiment_status",
                    "experiment_outcome",
                    "experiment_notes",
                    "outcome_recorded_at",
                    "outcome_recorded_by",
                )
            },
        ),
        ("Snapshots", {"fields": ("changed_field_count", "before", "after", "diff")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(RecommendationTuningExperimentSnapshot)
class RecommendationTuningExperimentSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "generated_at",
        "change_log",
        "window_days",
        "before_start",
        "after_end",
        "generated_by",
    )
    list_filter = (
        "window_days",
        "generated_at",
        "change_log__experiment_status",
        "change_log__experiment_outcome",
    )
    search_fields = (
        "change_log__experiment_label",
        "change_log__preset_name",
        "notes",
        "generated_by__email",
    )
    readonly_fields = (
        "generated_at",
        "created_at",
        "updated_at",
        "before_metrics",
        "after_metrics",
        "deltas",
        "summary",
    )
    fieldsets = (
        (
            "Experiment",
            {
                "fields": (
                    "change_log",
                    "window_days",
                    "generated_by",
                    "generated_at",
                    "notes",
                )
            },
        ),
        (
            "Windows",
            {"fields": ("before_start", "before_end", "after_start", "after_end")},
        ),
        (
            "Metrics",
            {"fields": ("summary", "before_metrics", "after_metrics", "deltas")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ExperimentDecisionTuning)
class ExperimentDecisionTuningAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "keep_score_threshold",
        "rollback_score_threshold",
        "low_confidence_abs_score",
        "max_metric_change_magnitude",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "notes")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Thresholds",
            {
                "fields": (
                    "name",
                    "is_active",
                    "keep_score_threshold",
                    "keep_primary_positive_min",
                    "keep_high_confidence_score",
                    "rollback_score_threshold",
                    "rollback_primary_negative_min",
                    "rollback_high_confidence_score",
                    "low_confidence_abs_score",
                    "max_metric_change_magnitude",
                )
            },
        ),
        (
            "Positive-signal weights",
            {
                "fields": (
                    "social_new_followers_weight",
                    "social_engagements_weight",
                    "social_reach_weight",
                    "social_clicks_weight",
                    "resources_pdf_downloads_weight",
                    "resources_pdf_unlocks_weight",
                    "resources_subscribers_weight",
                    "newsletter_clicks_weight",
                    "newsletter_open_rate_weight",
                    "ctas_cta_clicks_weight",
                    "conversions_total_conversions_weight",
                    "conversions_lesson_views_weight",
                    "conversions_quiz_attempts_weight",
                    "conversions_challenge_attempts_weight",
                    "conversions_lesson_completions_weight",
                )
            },
        ),
        (
            "Negative-signal weights",
            {
                "fields": (
                    "newsletter_unsubscribes_penalty_weight",
                    "newsletter_bounces_penalty_weight",
                )
            },
        ),
        ("Notes", {"fields": ("notes", "created_at", "updated_at")}),
    )


@admin.register(ExperimentDecisionTuningChangeLog)
class ExperimentDecisionTuningChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "preset_name",
        "experiment_label",
        "experiment_status",
        "experiment_outcome",
        "tuning",
        "changed_by",
        "changed_field_count",
    )
    list_filter = (
        "action",
        "experiment_status",
        "experiment_outcome",
        "preset_name",
        "created_at",
    )
    search_fields = (
        "tuning__name",
        "changed_by__email",
        "preset_key",
        "preset_name",
        "experiment_label",
        "reason",
        "experiment_notes",
        "request_path",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "changed_field_count",
        "before",
        "after",
        "diff",
        "outcome_recorded_at",
        "outcome_recorded_by",
    )
    fieldsets = (
        (
            "Change",
            {
                "fields": (
                    "tuning",
                    "action",
                    "changed_by",
                    "preset_key",
                    "preset_name",
                    "reason",
                    "request_path",
                )
            },
        ),
        (
            "Experiment tracking",
            {
                "fields": (
                    "experiment_label",
                    "experiment_status",
                    "experiment_outcome",
                    "experiment_notes",
                    "outcome_recorded_at",
                    "outcome_recorded_by",
                )
            },
        ),
        ("Snapshots", {"fields": ("changed_field_count", "before", "after", "diff")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ExperimentDecisionTuningExperimentSnapshot)
class ExperimentDecisionTuningExperimentSnapshotAdmin(admin.ModelAdmin):
    list_display = ("experiment_label", "window_days", "generated_at", "generated_by")
    list_filter = ("window_days", "generated_at")
    search_fields = ("change_log__experiment_label", "change_log__preset_name", "notes")
    readonly_fields = (
        "generated_at",
        "created_at",
        "updated_at",
        "before_metrics",
        "after_metrics",
        "deltas",
        "summary",
    )
    fieldsets = (
        (
            "Experiment",
            {
                "fields": (
                    "change_log",
                    "window_days",
                    "generated_by",
                    "generated_at",
                    "notes",
                )
            },
        ),
        (
            "Windows",
            {"fields": ("before_start", "before_end", "after_start", "after_end")},
        ),
        (
            "Metrics",
            {"fields": ("summary", "before_metrics", "after_metrics", "deltas")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ExperimentDecisionTuningSnapshotComparisonReport)
class ExperimentDecisionTuningSnapshotComparisonReportAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "decision_status",
        "source_template",
        "snapshot_count",
        "preset_count",
        "cloned_from",
        "updated_at",
        "created_by",
    )
    list_filter = (
        "decision_status",
        "source_template",
        "decision_recorded_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "description",
        "notes",
        "decision_summary",
        "decision_notes",
        "source_template__title",
        "cloned_from__title",
        "created_by__email",
        "updated_by__email",
        "decision_owner__email",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "snapshot_count",
        "preset_count",
        "decision_recorded_at",
        "decision_recorded_by",
    )
    filter_horizontal = ("snapshots",)
    fieldsets = (
        (
            "Report",
            {"fields": ("title", "description", "snapshots", "preset_keys", "notes")},
        ),
        (
            "Decision",
            {
                "fields": (
                    "decision_status",
                    "decision_summary",
                    "decision_notes",
                    "decision_owner",
                    "decision_recorded_by",
                    "decision_recorded_at",
                )
            },
        ),
        (
            "Ownership",
            {"fields": ("created_by", "updated_by", "source_template", "cloned_from")},
        ),
        (
            "Metadata",
            {"fields": ("snapshot_count", "preset_count", "created_at", "updated_at")},
        ),
    )


@admin.register(ExperimentDecisionTuningSnapshotComparisonReportTemplate)
class ExperimentDecisionTuningSnapshotComparisonReportTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "template_type",
        "is_active",
        "generated_report_count",
        "recommended_snapshot_count",
        "recommended_window_days",
        "preset_count",
        "focus_area_count",
        "updated_at",
    )
    list_filter = (
        "template_type",
        "is_active",
        "recommended_window_days",
        "updated_at",
    )
    search_fields = (
        "title",
        "slug",
        "description",
        "default_report_title",
        "default_notes",
    )
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = (
        "created_at",
        "updated_at",
        "preset_count",
        "focus_area_count",
        "generated_report_count",
    )
    fieldsets = (
        (
            "Template",
            {"fields": ("title", "slug", "template_type", "description", "is_active")},
        ),
        (
            "Report defaults",
            {
                "fields": (
                    "default_report_title",
                    "default_description",
                    "default_notes",
                    "default_preset_keys",
                )
            },
        ),
        (
            "Snapshot guidance",
            {
                "fields": (
                    "recommended_snapshot_count",
                    "recommended_window_days",
                    "focus_areas",
                )
            },
        ),
        ("Ownership", {"fields": ("created_by", "updated_by")}),
        (
            "Metadata",
            {
                "fields": (
                    "preset_count",
                    "focus_area_count",
                    "generated_report_count",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def generated_report_count(self, obj):
        return obj.generated_reports.count()


@admin.register(ReportTemplateRecommendationTuning)
class ReportTemplateRecommendationTuningAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "base_template_score",
        "high_priority_threshold",
        "medium_priority_threshold",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "notes")


@admin.register(ReportTemplateRecommendationTuningDecisionRules)
class ReportTemplateRecommendationTuningDecisionRulesAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "keep_score_threshold",
        "rollback_score_threshold",
        "low_confidence_abs_score",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "notes")


@admin.register(ReportTemplateRecommendationTuningChangeLog)
class ReportTemplateRecommendationTuningChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "tuning",
        "changed_by",
        "changed_field_count",
        "experiment_status",
        "experiment_outcome",
        "reason",
    )
    list_filter = (
        "action",
        "experiment_status",
        "experiment_outcome",
        "created_at",
        "tuning",
    )
    search_fields = (
        "tuning__name",
        "reason",
        "experiment_label",
        "experiment_notes",
        "changed_by__email",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "before",
        "after",
        "diff",
        "changed_field_count",
    )

    def changed_field_count(self, obj):
        return obj.changed_field_count


@admin.register(ReportTemplateRecommendationTuningExperimentSnapshot)
class ReportTemplateRecommendationTuningExperimentSnapshotAdmin(admin.ModelAdmin):
    list_display = ("experiment_label", "window_days", "generated_at", "generated_by")
    list_filter = ("window_days", "generated_at")
    search_fields = ("change_log__experiment_label", "notes", "generated_by__email")
    readonly_fields = (
        "before_metrics",
        "after_metrics",
        "deltas",
        "summary",
        "generated_at",
        "created_at",
        "updated_at",
    )

    def experiment_label(self, obj):
        return obj.experiment_label


@admin.register(
    ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback
)
class ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedbackAdmin(
    admin.ModelAdmin
):
    list_display = (
        "template",
        "status",
        "times_shown",
        "score",
        "priority",
        "last_seen_at",
        "responded_at",
        "created_by",
    )
    list_filter = (
        "status",
        "template__template_type",
        "priority",
        "last_seen_at",
        "responded_at",
    )
    search_fields = (
        "template__title",
        "recommendation_key",
        "notes",
        "created_by__email",
        "updated_by__email",
    )
    readonly_fields = (
        "first_seen_at",
        "last_seen_at",
        "responded_at",
        "created_at",
        "updated_at",
    )


@admin.register(ReportTemplateRecommendationTuningDecisionRulesChangeLog)
class ReportTemplateRecommendationTuningDecisionRulesChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "decision_rules",
        "changed_by",
        "changed_field_count",
        "experiment_label",
        "experiment_status",
        "experiment_outcome",
    )
    list_filter = ("action", "experiment_status", "experiment_outcome", "created_at")
    search_fields = (
        "decision_rules__name",
        "changed_by__email",
        "reason",
        "request_path",
        "experiment_label",
        "experiment_notes",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "before",
        "after",
        "diff",
        "outcome_recorded_at",
        "outcome_recorded_by",
    )


@admin.register(ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot)
class ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotAdmin(
    admin.ModelAdmin
):
    list_display = ("experiment_label", "window_days", "generated_at", "generated_by")
    list_filter = ("window_days", "generated_at")
    search_fields = ("change_log__experiment_label", "notes", "generated_by__email")
    readonly_fields = (
        "before_metrics",
        "after_metrics",
        "deltas",
        "summary",
        "generated_at",
        "created_at",
        "updated_at",
    )

    def experiment_label(self, obj):
        return obj.experiment_label


@admin.register(ResourceCTARecommendationFeedback)
class ResourceCTARecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "title",
        "target_type",
        "target_lesson",
        "status",
        "times_shown",
        "score",
        "last_seen_at",
    )
    list_filter = ("status", "target_type", "resource__resource_type", "last_seen_at")
    search_fields = (
        "resource__title",
        "title",
        "recommendation_key",
        "target_lesson__title",
        "notes",
    )
    readonly_fields = (
        "first_seen_at",
        "last_seen_at",
        "accepted_at",
        "dismissed_at",
        "created_at",
        "updated_at",
    )


@admin.register(ResourceCTAClickEvent)
class ResourceCTAClickEventAdmin(admin.ModelAdmin):
    list_display = ("resource", "cta", "target_lesson", "email", "user", "occurred_at")
    list_filter = ("cta__target_type", "resource", "target_lesson", "occurred_at")
    search_fields = (
        "resource__title",
        "cta__title",
        "target_lesson__title",
        "email",
        "target_url",
        "referrer",
    )
    readonly_fields = (
        "cta",
        "resource",
        "target_lesson",
        "user",
        "subscriber",
        "email",
        "source_url",
        "target_url",
        "referrer",
        "user_agent",
        "occurred_at",
        "created_at",
        "updated_at",
    )


@admin.register(ResourcePerformanceEvent)
class ResourcePerformanceEventAdmin(admin.ModelAdmin):
    list_display = ("resource", "event_type", "email", "subscriber", "occurred_at")
    list_filter = ("event_type", "resource", "occurred_at")
    search_fields = (
        "resource__title",
        "email",
        "subscriber__email",
        "source_url",
        "referrer",
    )
    readonly_fields = (
        "resource",
        "event_type",
        "subscriber",
        "user",
        "email",
        "source_url",
        "referrer",
        "user_agent",
        "occurred_at",
        "created_at",
        "updated_at",
    )


@admin.register(ResourceLessonConversionEvent)
class ResourceLessonConversionEventAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "lesson",
        "event_type",
        "cta",
        "email",
        "subscriber",
        "user",
        "occurred_at",
    )
    list_filter = (
        "event_type",
        "cta__target_type",
        "resource",
        "lesson",
        "occurred_at",
    )
    search_fields = (
        "resource__title",
        "lesson__title",
        "cta__title",
        "email",
        "subscriber__email",
        "user__email",
        "attribution_source_url",
        "referrer",
    )
    readonly_fields = (
        "resource",
        "lesson",
        "event_type",
        "source_event",
        "cta",
        "cta_click",
        "subscriber",
        "user",
        "email",
        "attribution_event_type",
        "attribution_source_url",
        "referrer",
        "metadata",
        "occurred_at",
        "created_at",
        "updated_at",
    )


@admin.register(ResourceLeadMagnetAccess)
class ResourceLeadMagnetAccessAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "email",
        "subscriber",
        "download_count",
        "access_granted_at",
        "last_downloaded_at",
    )
    list_filter = ("resource", "access_granted_at", "last_downloaded_at")
    search_fields = ("resource__title", "email", "first_name", "subscriber__email")
    readonly_fields = (
        "access_granted_at",
        "last_downloaded_at",
        "download_count",
        "created_at",
        "updated_at",
    )


@admin.register(WebsiteExport)
class WebsiteExportAdmin(admin.ModelAdmin):
    list_display = (
        "lesson",
        "revision",
        "schema_version",
        "content_hash",
        "created_at",
    )
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
    list_display = (
        "lesson",
        "position",
        "title",
        "validation_mode",
        "test_case_count",
        "is_active",
        "updated_at",
    )
    list_filter = ("validation_mode", "is_active", "lesson__category")
    search_fields = (
        "lesson__title",
        "title",
        "prompt",
        "starter_code",
        "solution_code",
    )
    inlines = (ChallengeTestCaseInline,)

    def test_case_count(self, obj):
        return obj.test_cases.count()


@admin.register(ChallengeTestCase)
class ChallengeTestCaseAdmin(admin.ModelAdmin):
    list_display = ("challenge", "position", "name", "is_active", "updated_at")
    list_filter = ("is_active", "challenge__lesson__category")
    search_fields = (
        "challenge__title",
        "challenge__lesson__title",
        "name",
        "description",
        "test_code",
        "expected_output",
    )


@admin.register(ChallengeAttempt)
class ChallengeAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "challenge",
        "user",
        "passed",
        "tests_passed",
        "tests_total",
        "created_at",
    )
    list_filter = ("passed", "created_at")
    search_fields = (
        "challenge__title",
        "challenge__lesson__title",
        "submitted_code",
        "observed_output",
        "feedback",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lesson",
        "status",
        "percent_complete",
        "quiz_correct",
        "quiz_total",
        "challenges_passed",
        "last_activity_at",
    )
    list_filter = ("status", "last_activity_at", "lesson__category")
    search_fields = ("user__email", "lesson__title")
    readonly_fields = (
        "started_at",
        "completed_at",
        "last_activity_at",
        "created_at",
        "updated_at",
    )


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
    list_display = (
        "name",
        "is_active",
        "status_filter",
        "source_filter",
        "skill_level_filter",
        "external_provider",
        "provider_sync_status",
        "subscriber_count",
    )
    list_filter = (
        "is_active",
        "status_filter",
        "source_filter",
        "skill_level_filter",
        "external_provider",
        "provider_sync_status",
        "source_lesson",
    )
    search_fields = (
        "name",
        "description",
        "search_text",
        "notes",
        "provider_notes",
        "external_segment_id",
        "external_audience_id",
        "source_lesson__title",
    )
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("subscriber_count", "created_at", "updated_at")


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "status",
        "target_segment",
        "saved_segment",
        "external_provider",
        "provider_sync_status",
        "scheduled_at",
        "sent_at",
        "actual_recipients",
        "open_rate",
        "click_rate",
    )
    list_filter = (
        "status",
        "target_segment",
        "saved_segment",
        "external_provider",
        "provider_sync_status",
        "scheduled_at",
        "sent_at",
    )
    search_fields = (
        "title",
        "subject",
        "preview_text",
        "body",
        "lesson__title",
        "notes",
        "provider_notes",
        "external_campaign_id",
        "external_audience_id",
    )
    readonly_fields = (
        "open_rate",
        "click_rate",
        "click_to_open_rate",
        "created_at",
        "updated_at",
    )


@admin.register(NewsletterMetricImport)
class NewsletterMetricImportAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "provider",
        "applied_at",
        "actual_recipients",
        "opens",
        "clicks",
        "imported_by",
    )
    list_filter = ("provider", "applied_at")
    search_fields = ("campaign__title", "campaign__subject", "source_filename", "notes")
    readonly_fields = (
        "normalized_data",
        "raw_payload",
        "warnings",
        "applied_at",
        "created_at",
        "updated_at",
    )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "status",
        "source",
        "source_lesson",
        "source_resource",
        "external_provider",
        "provider_sync_status",
        "subscribed_at",
    )
    list_filter = (
        "status",
        "source",
        "external_provider",
        "provider_sync_status",
        "source_resource",
        "subscribed_at",
    )
    search_fields = (
        "email",
        "first_name",
        "source_lesson__title",
        "source_resource__title",
        "notes",
        "provider_notes",
        "external_contact_id",
        "external_list_id",
    )
    readonly_fields = ("subscribed_at", "created_at", "updated_at")
