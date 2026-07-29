import csv
import json
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Max, Prefetch, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import (
    BlockTemplateApplyForm,
    BrandProfileForm,
    CaptionDraftForm,
    CaptionGenerationForm,
    ChallengeTestCaseForm,
    CodeChallengeForm,
    ContentPlanForm,
    ExperimentDecisionTuningExperimentOutcomeForm,
    ExperimentDecisionTuningExperimentSnapshotComparisonForm,
    ExperimentDecisionTuningExperimentSnapshotForm,
    ExperimentDecisionTuningForm,
    ExperimentDecisionTuningSimulationForm,
    ExperimentDecisionTuningSnapshotComparisonReportCloneForm,
    ExperimentDecisionTuningSnapshotComparisonReportForm,
    ExperimentDecisionTuningSnapshotComparisonReportFromTemplateForm,
    ExperimentDecisionTuningSnapshotComparisonReportTemplateForm,
    GraphicGenerationForm,
    LearningResourceForm,
    LessonBlockForm,
    LessonForm,
    LessonIdeaForm,
    NewsletterCampaignForm,
    NewsletterMetricImportForm,
    NewsletterSignupForm,
    NewsletterSubscriberForm,
    PublishingRecordForm,
    QuizChoiceForm,
    QuizQuestionForm,
    RecommendationTuningExperimentOutcomeForm,
    RecommendationTuningExperimentSnapshotForm,
    RecommendationTuningForm,
    RecommendationTuningSimulationForm,
    ReportTemplateRecommendationTuningDecisionRulesExperimentOutcomeForm,
    ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotForm,
    ReportTemplateRecommendationTuningDecisionRulesForm,
    ReportTemplateRecommendationTuningExperimentOutcomeForm,
    ReportTemplateRecommendationTuningExperimentSnapshotForm,
    ReportTemplateRecommendationTuningForm,
    ResourceCTAForm,
    ResourceIdeaForm,
    SocialCarouselTemplateApplyForm,
    SubscriberSegmentForm,
)
from .models import (
    AIGeneration,
    BrandProfile,
    CaptionDraft,
    ChallengeAttempt,
    ChallengeTestCase,
    CodeChallenge,
    ContentPlan,
    EmailProvider,
    ExperimentDecisionTuning,
    ExperimentDecisionTuningChangeLog,
    ExperimentDecisionTuningExperimentSnapshot,
    ExperimentDecisionTuningSnapshotComparisonReport,
    ExperimentDecisionTuningSnapshotComparisonReportTemplate,
    ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback,
    LearnerBadge,
    LearnerBadgeAward,
    LearningResource,
    Lesson,
    LessonBlock,
    LessonProgress,
    NewsletterCampaign,
    NewsletterMetricImport,
    NewsletterSubscriber,
    ProviderSyncStatus,
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
    WebsiteExport,
)
from .services.block_templates import (
    BLOCK_TEMPLATES,
    apply_block_template_to_lesson,
    get_block_template,
)
from .services.experiment_decision_tuning_history import (
    create_decision_tuning_change_log,
    decision_tuning_snapshot,
    restore_decision_tuning_snapshot,
)
from .services.experiment_decision_tuning_presets import (
    DECISION_PRESETS,
    apply_decision_preset_to_active_tuning,
    build_decision_tuning_from_preset_key,
    decision_preset_rows,
    get_decision_preset,
)
from .services.experiment_decisions import (
    apply_decision_to_change_log,
    apply_decision_to_decision_rule_change_log,
    recommend_experiment_decision,
)
from .services.experiment_snapshots import (
    create_decision_rule_experiment_snapshot,
    create_experiment_snapshot,
    create_report_template_recommendation_decision_rule_experiment_snapshot,
    create_report_template_recommendation_tuning_experiment_snapshot,
    report_template_decision_rule_snapshot_section_rows,
    report_template_snapshot_section_rows,
    snapshot_section_rows,
)
from .services.graphics import GraphicGenerationError, generate_graphics
from .services.lesson_ideas import LessonIdeaDraft, create_lesson_from_idea
from .services.newsletter_imports import parse_newsletter_metrics
from .services.openai import OpenAIServiceError, generate_caption
from .services.project_health import (
    build_project_health_checks,
    grouped_project_health,
    project_health_summary,
)
from .services.provider_readiness import (
    ISSUE_LABELS,
    RECORD_TYPE_LABELS,
    provider_readiness_rows,
    provider_readiness_summary,
)
from .services.recommendation_tuning_presets import (
    PRESETS,
    apply_preset_to_active_tuning,
    build_tuning_from_preset_key,
    create_tuning_change_log,
    get_preset,
    preset_rows,
    restore_tuning_snapshot,
    tuning_snapshot,
)
from .services.report_template_recommendation_decision_rule_snapshot_decisions import (
    apply_report_template_decision_rule_snapshot_decision_to_change_log,
    recommend_report_template_decision_rule_snapshot_decision,
)
from .services.report_template_recommendation_tuning_decision_rule_history import (
    create_report_template_decision_rule_change_log,
    report_template_decision_rule_snapshot,
    restore_report_template_decision_rule_snapshot,
)
from .services.report_template_recommendation_tuning_decisions import (
    apply_report_template_tuning_decision_to_change_log,
    recommend_report_template_tuning_decision,
)
from .services.report_template_recommendation_tuning_history import (
    create_report_template_tuning_change_log,
    report_template_tuning_snapshot,
    restore_report_template_tuning_snapshot,
)
from .services.report_template_recommendations import (
    build_report_template_recommendations,
    record_template_recommendation_response,
    record_template_recommendation_shown,
)
from .services.resource_ideas import ResourceIdeaDraft, create_resource_from_idea
from .services.resource_pdfs import render_learning_resource_pdf, resource_pdf_filename
from .services.resource_recommendations import (
    attach_recommendation_feedback,
    build_resource_cta_recommendations,
    create_cta_from_recommendation,
    mark_recommendation_dismissed,
)
from .services.seo import (
    absolute_url,
    lesson_canonical_url,
    lesson_schema,
    resource_canonical_url,
    resource_schema,
    series_canonical_url,
    series_schema,
    website_schema,
)
from .services.social_carousels import (
    SOCIAL_CAROUSEL_TEMPLATES,
    apply_social_carousel_template_to_lesson,
    get_social_carousel_template,
)
from .services.website import (
    create_website_export,
    render_website_page,
    seo_diagnostics,
)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


staff_required = user_passes_test(lambda user: user.is_staff, login_url="login")


def _public_lessons_queryset():
    return Lesson.objects.filter(
        website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED]
    ).exclude(status=Lesson.Status.ARCHIVED)


def _public_resources_queryset():
    return LearningResource.objects.filter(
        status__in=[LearningResource.Status.READY, LearningResource.Status.PUBLISHED]
    )


RESOURCE_ATTRIBUTION_SESSION_KEY = "resource_conversion_attribution"
RESOURCE_CONVERSION_KEYS_SESSION_KEY = "resource_conversion_keys"
RESOURCE_CTA_ATTRIBUTION_SESSION_KEY = "resource_cta_attribution"
RESOURCE_ATTRIBUTION_DAYS = 30


def _track_resource_event(request, resource, event_type, subscriber=None, email=""):
    """Record lightweight public resource analytics for Studio reporting and store last-touch attribution."""
    user = (
        request.user
        if getattr(request, "user", None) and request.user.is_authenticated
        else None
    )
    event = ResourcePerformanceEvent.objects.create(
        resource=resource,
        event_type=event_type,
        subscriber=subscriber,
        user=user,
        email=(email or (subscriber.email if subscriber else ""))[:254],
        source_url=request.build_absolute_uri(request.path)[:300],
        referrer=request.META.get("HTTP_REFERER", "")[:300],
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )
    request.session[RESOURCE_ATTRIBUTION_SESSION_KEY] = {
        "resource_id": resource.pk,
        "event_id": event.pk,
        "event_type": event.event_type,
        "occurred_at": event.occurred_at.isoformat(),
    }
    return event


def _get_resource_attribution(request):
    data = request.session.get(RESOURCE_ATTRIBUTION_SESSION_KEY) or {}
    resource_id = data.get("resource_id")
    if not resource_id:
        return None, None, data
    source_event = None
    event_id = data.get("event_id")
    if event_id:
        source_event = (
            ResourcePerformanceEvent.objects.filter(
                pk=event_id, resource_id=resource_id
            )
            .select_related("resource", "subscriber")
            .first()
        )
    resource = (
        source_event.resource
        if source_event
        else LearningResource.objects.filter(pk=resource_id).first()
    )
    if not resource:
        return None, None, data
    occurred_at = source_event.occurred_at if source_event else None
    if not occurred_at and data.get("occurred_at"):
        try:
            occurred_at = datetime.fromisoformat(data["occurred_at"])
        except (TypeError, ValueError):
            occurred_at = None
    if occurred_at and timezone.is_naive(occurred_at):
        occurred_at = timezone.make_aware(occurred_at)
    if occurred_at and occurred_at < timezone.now() - timedelta(
        days=RESOURCE_ATTRIBUTION_DAYS
    ):
        return None, None, data
    return resource, source_event, data


def _track_resource_conversion(
    request,
    event_type,
    lesson=None,
    subscriber=None,
    email="",
    metadata=None,
    dedupe=True,
):
    resource, source_event, attribution = _get_resource_attribution(request)
    if not resource:
        return None
    cta = None
    cta_click = None
    cta_data = request.session.get(RESOURCE_CTA_ATTRIBUTION_SESSION_KEY) or {}
    if str(cta_data.get("resource_id")) == str(resource.pk):
        cta_id = cta_data.get("cta_id")
        click_id = cta_data.get("click_id")
        if click_id:
            cta_click = (
                ResourceCTAClickEvent.objects.filter(pk=click_id, resource=resource)
                .select_related("cta")
                .first()
            )
            cta = cta_click.cta if cta_click else None
        if not cta and cta_id:
            cta = ResourceCTA.objects.filter(pk=cta_id, resource=resource).first()
    user = (
        request.user
        if getattr(request, "user", None) and request.user.is_authenticated
        else None
    )
    key = f"{resource.pk}:{lesson.pk if lesson else 'none'}:{event_type}:{user.pk if user else email or 'anon'}:{cta.pk if cta else 'nocta'}"
    seen = request.session.get(RESOURCE_CONVERSION_KEYS_SESSION_KEY, [])
    if dedupe and key in seen:
        return None
    conversion = ResourceLessonConversionEvent.objects.create(
        resource=resource,
        lesson=lesson,
        event_type=event_type,
        source_event=source_event,
        subscriber=subscriber or (source_event.subscriber if source_event else None),
        user=user,
        cta=cta,
        cta_click=cta_click,
        email=(
            email
            or (subscriber.email if subscriber else "")
            or (source_event.email if source_event else "")
        )[:254],
        attribution_event_type=(
            source_event.event_type
            if source_event
            else attribution.get("event_type", "")
        )[:20],
        attribution_source_url=(source_event.source_url if source_event else "")[:300],
        referrer=request.META.get("HTTP_REFERER", "")[:300],
        metadata=metadata or {},
    )
    if dedupe:
        seen = (seen + [key])[-100:]
        request.session[RESOURCE_CONVERSION_KEYS_SESSION_KEY] = seen
    return conversion


def _resource_pdf_unlock_session_key(resource):
    return f"resource_pdf_unlocked_{resource.pk}"


def _resource_pdf_access_session_key(resource):
    return f"resource_pdf_access_{resource.pk}"


def _resource_cta_target_url(cta, request=None):
    if (
        cta.target_type
        in {
            ResourceCTA.TargetType.LESSON,
            ResourceCTA.TargetType.QUIZ,
            ResourceCTA.TargetType.CHALLENGE,
        }
        and cta.target_lesson_id
    ):
        url = reverse("learn:lesson-detail", kwargs={"slug": cta.target_lesson.slug})
        if cta.target_type in {
            ResourceCTA.TargetType.QUIZ,
            ResourceCTA.TargetType.CHALLENGE,
        }:
            url += "#practice"
        return url
    if cta.target_type == ResourceCTA.TargetType.PDF:
        if cta.resource.pdf_requires_email:
            return reverse(
                "learn:resource-pdf-gate", kwargs={"slug": cta.resource.slug}
            )
        return reverse("learn:resource-pdf", kwargs={"slug": cta.resource.slug})
    if cta.target_type == ResourceCTA.TargetType.NEWSLETTER:
        return cta.resource.public_url + "#newsletter"
    return cta.target_url or cta.resource.public_url


def _touch_lesson_progress(user, lesson):
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    progress.status = (
        progress.Status.IN_PROGRESS
        if progress.status != progress.Status.COMPLETED
        else progress.status
    )
    progress.last_activity_at = timezone.now()
    progress.save(update_fields=["status", "last_activity_at", "updated_at"])
    return progress


def _refresh_lesson_progress(user, lesson):
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    progress.quiz_total = (
        QuizAttempt.objects.filter(user=user, question__lesson=lesson)
        .values("question_id")
        .distinct()
        .count()
    )
    progress.quiz_correct = (
        QuizAttempt.objects.filter(user=user, question__lesson=lesson, is_correct=True)
        .values("question_id")
        .distinct()
        .count()
    )
    progress.challenges_passed = (
        ChallengeAttempt.objects.filter(
            user=user, challenge__lesson=lesson, passed=True
        )
        .values("challenge_id")
        .distinct()
        .count()
    )
    progress.last_activity_at = timezone.now()
    progress.save(
        update_fields=[
            "quiz_total",
            "quiz_correct",
            "challenges_passed",
            "last_activity_at",
            "updated_at",
        ]
    )
    _award_earned_badges(user)
    return progress


def _award_earned_badges(user):
    if not user.is_authenticated:
        return []
    stats = {
        LearnerBadge.CriteriaType.LESSONS_COMPLETED: LessonProgress.objects.filter(
            user=user, status=LessonProgress.Status.COMPLETED
        ).count(),
        LearnerBadge.CriteriaType.QUIZZES_CORRECT: QuizAttempt.objects.filter(
            user=user, is_correct=True
        ).count(),
        LearnerBadge.CriteriaType.CHALLENGES_PASSED: ChallengeAttempt.objects.filter(
            user=user, passed=True
        ).count(),
    }
    awards = []
    for badge in LearnerBadge.objects.filter(is_active=True):
        if stats.get(badge.criteria_type, 0) >= badge.threshold:
            award, created = LearnerBadgeAward.objects.get_or_create(
                user=user, badge=badge
            )
            if created:
                awards.append(award)
    return awards


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "studio/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson_counts"] = Lesson.objects.values("status").annotate(
            total=Count("id")
        )
        context["recent_lessons"] = Lesson.objects.select_related("category", "series")[
            :8
        ]
        context["total_ai_cost"] = (
            AIGeneration.objects.filter(status=AIGeneration.Status.SUCCEEDED).aggregate(
                total=Sum("estimated_cost_usd")
            )["total"]
            or 0
        )
        context["recent_generations"] = AIGeneration.objects.select_related("lesson")[
            :6
        ]
        context["recent_publishing_records"] = PublishingRecord.objects.select_related(
            "lesson"
        )[:6]
        context["upcoming_content_plans"] = (
            ContentPlan.objects.select_related("lesson", "caption", "graphic")
            .filter(scheduled_at__gte=timezone.now())
            .order_by("scheduled_at")[:6]
        )
        context["publishing_totals"] = PublishingRecord.objects.aggregate(
            impressions=Sum("impressions"),
            reach=Sum("reach"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            saves=Sum("saves"),
            shares=Sum("shares"),
            clicks=Sum("clicks"),
            new_followers=Sum("new_followers"),
        )
        context["subscriber_totals"] = {
            "active": NewsletterSubscriber.objects.filter(
                status=NewsletterSubscriber.Status.ACTIVE
            ).count(),
            "total": NewsletterSubscriber.objects.count(),
            "recent": NewsletterSubscriber.objects.filter(
                subscribed_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            "segments": SubscriberSegment.objects.filter(is_active=True).count(),
        }
        context["recent_subscribers"] = NewsletterSubscriber.objects.select_related(
            "source_lesson"
        )[:6]
        context["subscriber_segments"] = SubscriberSegment.objects.filter(
            is_active=True
        )[:6]
        context["upcoming_newsletter_campaigns"] = (
            NewsletterCampaign.objects.select_related("lesson")
            .filter(
                status__in=[
                    NewsletterCampaign.Status.READY,
                    NewsletterCampaign.Status.SCHEDULED,
                ],
                scheduled_at__gte=timezone.now(),
            )
            .order_by("scheduled_at")[:6]
        )
        context["newsletter_campaign_totals"] = {
            "draft": NewsletterCampaign.objects.filter(
                status=NewsletterCampaign.Status.DRAFT
            ).count(),
            "scheduled": NewsletterCampaign.objects.filter(
                status=NewsletterCampaign.Status.SCHEDULED
            ).count(),
            "sent": NewsletterCampaign.objects.filter(
                status=NewsletterCampaign.Status.SENT
            ).count(),
        }
        context["provider_readiness_summary"] = provider_readiness_summary()
        last_30_days = timezone.now() - timedelta(days=30)
        context["resource_performance_totals"] = {
            "views": ResourcePerformanceEvent.objects.filter(
                event_type=ResourcePerformanceEvent.EventType.VIEW,
                occurred_at__gte=last_30_days,
            ).count(),
            "unlocks": ResourcePerformanceEvent.objects.filter(
                event_type=ResourcePerformanceEvent.EventType.PDF_UNLOCK,
                occurred_at__gte=last_30_days,
            ).count(),
            "downloads": ResourcePerformanceEvent.objects.filter(
                event_type=ResourcePerformanceEvent.EventType.PDF_DOWNLOAD,
                occurred_at__gte=last_30_days,
            ).count(),
        }
        context["resource_conversion_totals"] = {
            "lesson_views": ResourceLessonConversionEvent.objects.filter(
                event_type=ResourceLessonConversionEvent.EventType.LESSON_VIEW,
                occurred_at__gte=last_30_days,
            ).count(),
            "signups": ResourceLessonConversionEvent.objects.filter(
                event_type=ResourceLessonConversionEvent.EventType.ACCOUNT_SIGNUP,
                occurred_at__gte=last_30_days,
            ).count(),
            "completions": ResourceLessonConversionEvent.objects.filter(
                event_type=ResourceLessonConversionEvent.EventType.LESSON_COMPLETE,
                occurred_at__gte=last_30_days,
            ).count(),
        }
        context["recommendation_tuning"] = RecommendationTuning.get_active()
        context["report_template_totals"] = {
            "templates": ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.count(),
            "generated_reports": ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
                source_template__isnull=False
            ).count(),
            "keep": ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
                source_template__isnull=False,
                decision_status=ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.KEEP,
            ).count(),
            "roll_back": ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
                source_template__isnull=False,
                decision_status=ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.ROLL_BACK,
            ).count(),
        }
        first_lesson = Lesson.objects.order_by("created_at").first()
        lesson_url = (
            first_lesson.get_absolute_url()
            if first_lesson
            else reverse("studio:lesson-create")
        )
        steps = [
            {
                "label": "Sign in to your private studio",
                "description": "Your email-only account protects every studio screen.",
                "complete": True,
                "url": reverse("studio:dashboard"),
            },
            {
                "label": "Create your first lesson",
                "description": "Start with a title, summary, difficulty, and Draft status.",
                "complete": first_lesson is not None,
                "url": reverse("studio:lesson-create"),
            },
            {
                "label": "Add lesson content blocks",
                "description": "Build the explanation, code, output, quiz, or challenge.",
                "complete": LessonBlock.objects.exists(),
                "url": lesson_url,
            },
            {
                "label": "Generate a social graphic",
                "description": "Choose a template and one or more platform sizes.",
                "complete": Lesson.objects.filter(assets__status="ready").exists(),
                "url": lesson_url,
            },
            {
                "label": "Generate and review a caption",
                "description": "Create platform drafts, then edit or approve the copy.",
                "complete": CaptionDraft.objects.exists(),
                "url": lesson_url,
            },
            {
                "label": "Plan the week",
                "description": "Schedule lessons, captions, and graphics by platform before you post.",
                "complete": ContentPlan.objects.exists(),
                "url": reverse("studio:content-planner"),
            },
            {
                "label": "Record a published post",
                "description": "Save the URL, caption, graphic, and engagement metrics after posting.",
                "complete": PublishingRecord.objects.exists(),
                "url": reverse("studio:content-calendar"),
            },
            {
                "label": "Review performance",
                "description": "Compare formats, platforms, and top posts so you know what to repeat.",
                "complete": PublishingRecord.objects.count() >= 2,
                "url": reverse("studio:performance-report"),
            },
            {
                "label": "Capture learner emails",
                "description": "Use the public newsletter form to collect beginners who want lessons and practice prompts.",
                "complete": NewsletterSubscriber.objects.filter(
                    status=NewsletterSubscriber.Status.ACTIVE
                ).exists(),
                "url": reverse("studio:newsletter-subscriber-list"),
            },
            {
                "label": "Create saved audience segments",
                "description": "Group subscribers by source, skill level, recency, or lesson signup so campaigns can target repeatable audiences.",
                "complete": SubscriberSegment.objects.filter(is_active=True).exists(),
                "url": reverse("studio:subscriber-segment-list"),
            },
            {
                "label": "Plan a newsletter campaign",
                "description": "Draft or schedule a weekly email from a lesson and track its send status.",
                "complete": NewsletterCampaign.objects.exists(),
                "url": reverse("studio:newsletter-campaign-list"),
            },
            {
                "label": "Preview the website lesson",
                "description": "Resolve SEO warnings and inspect the standalone page.",
                "complete": WebsiteExport.objects.exists(),
                "url": lesson_url,
            },
        ]
        completed = sum(step["complete"] for step in steps)
        context["onboarding_steps"] = steps
        context["onboarding_completed"] = completed
        context["onboarding_total"] = len(steps)
        context["onboarding_percent"] = round(completed / len(steps) * 100)
        return context


class RecommendationTuningUpdateView(StaffRequiredMixin, UpdateView):
    model = RecommendationTuning
    form_class = RecommendationTuningForm
    template_name = "studio/recommendation_tuning_form.html"

    def get_object(self, queryset=None):
        return RecommendationTuning.get_active()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["preset_rows"] = preset_rows(self.get_object())
        return context

    def form_valid(self, form):
        before = tuning_snapshot(self.get_object())
        response = super().form_valid(form)
        create_tuning_change_log(
            self.object,
            before=before,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.request.user,
            reason=form.cleaned_data.get("change_reason", ""),
            request_path=self.request.path,
            experiment_label=form.cleaned_data.get("experiment_label", ""),
            experiment_status=form.cleaned_data.get("experiment_status")
            or RecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
            experiment_notes=form.cleaned_data.get("experiment_notes", ""),
        )
        messages.success(self.request, "Recommendation tuning controls saved.")
        return response

    def get_success_url(self):
        return reverse("studio:recommendation-tuning")


class ExperimentDecisionTuningUpdateView(StaffRequiredMixin, UpdateView):
    model = ExperimentDecisionTuning
    form_class = ExperimentDecisionTuningForm
    template_name = "studio/experiment_decision_tuning_form.html"
    context_object_name = "decision_tuning"

    def get_object(self, queryset=None):
        return ExperimentDecisionTuning.get_active()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["preset_rows"] = decision_preset_rows(self.get_object())
        context["decision_presets"] = DECISION_PRESETS
        return context

    def form_valid(self, form):
        before = decision_tuning_snapshot(self.get_object())
        response = super().form_valid(form)
        create_decision_tuning_change_log(
            self.object,
            before=before,
            action=ExperimentDecisionTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.request.user,
            reason=form.cleaned_data.get("change_reason", ""),
            request_path=self.request.path,
            experiment_label=form.cleaned_data.get("experiment_label", ""),
            experiment_status=form.cleaned_data.get("experiment_status")
            or ExperimentDecisionTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
            experiment_notes=form.cleaned_data.get("experiment_notes", ""),
        )
        messages.success(
            self.request, "Experiment decision thresholds and weights saved."
        )
        return response

    def get_success_url(self):
        return reverse("studio:experiment-decision-tuning")


@staff_required
@require_POST
def apply_experiment_decision_tuning_preset(request):
    preset = get_decision_preset(request.POST.get("preset_key", ""))
    if not preset:
        messages.error(request, "Choose a valid decision-rule preset.")
        return redirect("studio:experiment-decision-tuning")
    apply_decision_preset_to_active_tuning(
        preset,
        changed_by=request.user,
        reason=request.POST.get("change_reason", "")
        or "Applied experiment decision-rule preset.",
        request_path=request.path,
        experiment_label=request.POST.get("experiment_label", ""),
        experiment_status=request.POST.get("experiment_status", "")
        or ExperimentDecisionTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        experiment_notes=request.POST.get("experiment_notes", ""),
    )
    messages.success(request, f"Applied the {preset.name} decision-rule preset.")
    next_url = request.POST.get("next") or reverse("studio:experiment-decision-tuning")
    return redirect(next_url)


class ExperimentDecisionTuningSimulationView(StaffRequiredMixin, FormView):
    template_name = "studio/experiment_decision_tuning_simulation.html"
    form_class = ExperimentDecisionTuningSimulationForm

    def get_initial(self):
        initial = super().get_initial()
        first_snapshot = ExperimentDecisionTuningExperimentSnapshot.objects.order_by(
            "-generated_at", "-pk"
        ).first()
        if first_snapshot:
            initial["snapshot"] = first_snapshot.pk
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        if form and form.is_bound and form.is_valid():
            snapshot = form.cleaned_data.get("snapshot")
            selected_keys = form.cleaned_data.get("preset_keys") or [
                preset.key for preset in DECISION_PRESETS
            ]
        else:
            raw_snapshot = form.initial.get("snapshot") if form else None
            snapshot = (
                ExperimentDecisionTuningExperimentSnapshot.objects.filter(
                    pk=raw_snapshot
                ).first()
                if raw_snapshot
                else None
            )
            selected_keys = [preset.key for preset in DECISION_PRESETS]

        simulations = []
        if snapshot:
            active_tuning = ExperimentDecisionTuning.get_active()
            simulations.append(
                {
                    "name": f"Active: {active_tuning.name}",
                    "description": active_tuning.notes
                    or "Current saved decision-rule profile.",
                    "preset_key": "active",
                    "is_active": True,
                    "recommendation": recommend_experiment_decision(
                        snapshot, tuning=active_tuning
                    ),
                }
            )
            for key in selected_keys:
                preset = get_decision_preset(key)
                if not preset:
                    continue
                simulated_tuning = build_decision_tuning_from_preset_key(key)
                simulations.append(
                    {
                        "name": preset.name,
                        "description": preset.description,
                        "preset_key": preset.key,
                        "is_active": False,
                        "recommendation": recommend_experiment_decision(
                            snapshot, tuning=simulated_tuning
                        ),
                    }
                )

        context["snapshot"] = snapshot
        context["simulations"] = simulations
        context["decision_presets"] = DECISION_PRESETS
        context["preset_rows"] = decision_preset_rows()
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ExperimentDecisionTuningRollbackView(StaffRequiredMixin, DetailView):
    model = ExperimentDecisionTuningChangeLog
    template_name = "studio/experiment_decision_tuning_rollback.html"
    context_object_name = "change_log"

    def post(self, request, *args, **kwargs):
        change_log = self.get_object()
        snapshot = request.POST.get("snapshot", "before")
        if snapshot not in {"before", "after"}:
            messages.error(request, "Choose a valid decision-rule snapshot to restore.")
            return redirect(
                "studio:experiment-decision-tuning-rollback", pk=change_log.pk
            )
        restore_decision_tuning_snapshot(
            change_log,
            snapshot=snapshot,
            changed_by=request.user,
            reason=request.POST.get("rollback_reason", ""),
            request_path=request.path,
        )
        label = "before-change" if snapshot == "before" else "after-change"
        messages.success(
            request,
            f"Restored the {label} decision-rule snapshot and logged the rollback.",
        )
        return redirect("studio:experiment-decision-tuning-history")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active = ExperimentDecisionTuning.get_active()
        active_snapshot = decision_tuning_snapshot(active)
        context["active_tuning"] = active
        context["active_snapshot"] = active_snapshot
        context["tracked_fields"] = [
            {
                "name": field,
                "active": active_snapshot.get(field),
                "before": self.object.before.get(field),
                "after": self.object.after.get(field),
            }
            for field in active_snapshot.keys()
        ]
        return context


class ExperimentDecisionTuningHistoryView(StaffRequiredMixin, ListView):
    model = ExperimentDecisionTuningChangeLog
    template_name = "studio/experiment_decision_tuning_history.html"
    context_object_name = "change_logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = ExperimentDecisionTuningChangeLog.objects.select_related(
            "tuning", "changed_by", "outcome_recorded_by"
        )
        action = self.request.GET.get("action", "")
        status = self.request.GET.get("experiment_status", "")
        outcome = self.request.GET.get("experiment_outcome", "")
        label = self.request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        return queryset.order_by("-created_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = ExperimentDecisionTuningChangeLog.Action.choices
        context["experiment_statuses"] = (
            ExperimentDecisionTuningChangeLog.ExperimentStatus.choices
        )
        context["experiment_outcomes"] = (
            ExperimentDecisionTuningChangeLog.ExperimentOutcome.choices
        )
        context["selected_action"] = self.request.GET.get("action", "")
        context["selected_experiment_status"] = self.request.GET.get(
            "experiment_status", ""
        )
        context["selected_experiment_outcome"] = self.request.GET.get(
            "experiment_outcome", ""
        )
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        ).strip()
        context["latest_change"] = ExperimentDecisionTuningChangeLog.objects.order_by(
            "-created_at", "-pk"
        ).first()
        context["active_experiment_count"] = (
            ExperimentDecisionTuningChangeLog.objects.exclude(
                experiment_status=ExperimentDecisionTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT
            )
            .filter(
                experiment_outcome=ExperimentDecisionTuningChangeLog.ExperimentOutcome.NOT_RECORDED
            )
            .count()
        )
        context["completed_outcome_count"] = (
            ExperimentDecisionTuningChangeLog.objects.exclude(
                experiment_outcome=ExperimentDecisionTuningChangeLog.ExperimentOutcome.NOT_RECORDED
            ).count()
        )
        context["total_changes"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("change_logs", []))
        )
        return context


class ExperimentDecisionTuningHistoryExportView(StaffRequiredMixin, ListView):
    model = ExperimentDecisionTuningChangeLog

    def get(self, request, *args, **kwargs):
        queryset = ExperimentDecisionTuningChangeLog.objects.select_related(
            "tuning", "changed_by", "outcome_recorded_by"
        ).order_by("-created_at", "-pk")
        action = request.GET.get("action", "")
        status = request.GET.get("experiment_status", "")
        outcome = request.GET.get("experiment_outcome", "")
        label = request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="experiment_decision_rule_change_history.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "created_at",
                "action",
                "decision_rules_profile",
                "changed_by",
                "preset_key",
                "preset_name",
                "changed_fields",
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "experiment_notes",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "diff_json",
                "reason",
                "request_path",
            ]
        )
        for log in queryset:
            writer.writerow(
                [
                    log.created_at.isoformat(),
                    log.get_action_display(),
                    log.tuning.name if log.tuning_id else "",
                    getattr(log.changed_by, "email", "") or "",
                    log.preset_key,
                    log.preset_name,
                    log.changed_field_count,
                    log.experiment_label,
                    log.get_experiment_status_display(),
                    log.get_experiment_outcome_display(),
                    log.experiment_notes,
                    log.outcome_recorded_at.isoformat()
                    if log.outcome_recorded_at
                    else "",
                    getattr(log.outcome_recorded_by, "email", "") or "",
                    json.dumps(log.diff, sort_keys=True),
                    log.reason,
                    log.request_path,
                ]
            )
        return response


class ExperimentDecisionTuningExperimentOutcomeView(StaffRequiredMixin, UpdateView):
    model = ExperimentDecisionTuningChangeLog
    form_class = ExperimentDecisionTuningExperimentOutcomeForm
    template_name = "studio/experiment_decision_tuning_experiment_form.html"
    context_object_name = "change_log"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.outcome_recorded_at = timezone.now()
        self.object.outcome_recorded_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        self.object.save(
            update_fields=[
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "experiment_notes",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "updated_at",
            ]
        )
        messages.success(self.request, "Decision-rule experiment outcome saved.")
        return redirect("studio:experiment-decision-tuning-history")

    def get_success_url(self):
        return reverse("studio:experiment-decision-tuning-history")


class ExperimentDecisionTuningExperimentSnapshotListView(StaffRequiredMixin, ListView):
    model = ExperimentDecisionTuningExperimentSnapshot
    template_name = "studio/experiment_decision_tuning_experiment_snapshots.html"
    context_object_name = "snapshots"
    paginate_by = 30

    def get_queryset(self):
        queryset = ExperimentDecisionTuningExperimentSnapshot.objects.select_related(
            "change_log", "change_log__tuning", "generated_by"
        )
        label = self.request.GET.get("experiment_label", "").strip()
        window_days = self.request.GET.get("window_days", "").strip()
        if label:
            queryset = queryset.filter(change_log__experiment_label__icontains=label)
        if window_days.isdigit():
            queryset = queryset.filter(window_days=int(window_days))
        return queryset.order_by("-generated_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        ).strip()
        context["selected_window_days"] = self.request.GET.get(
            "window_days", ""
        ).strip()
        context["window_choices"] = [7, 14, 30, 60]
        context["snapshot_count"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("snapshots", []))
        )
        context["latest_snapshot"] = (
            ExperimentDecisionTuningExperimentSnapshot.objects.order_by(
                "-generated_at"
            ).first()
        )
        return context


class ExperimentDecisionTuningExperimentSnapshotCreateView(
    StaffRequiredMixin, DetailView
):
    model = ExperimentDecisionTuningChangeLog
    template_name = "studio/experiment_decision_tuning_experiment_snapshot_form.html"
    context_object_name = "change_log"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = (
            kwargs.get("form") or ExperimentDecisionTuningExperimentSnapshotForm()
        )
        context["existing_snapshots"] = (
            self.object.performance_snapshots.select_related("generated_by")[:10]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ExperimentDecisionTuningExperimentSnapshotForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        snapshot = create_decision_rule_experiment_snapshot(
            change_log=self.object,
            window_days=form.cleaned_data["window_days"],
            generated_by=request.user if request.user.is_authenticated else None,
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(
            request, "Decision-rule experiment performance snapshot created."
        )
        return redirect(
            "studio:experiment-decision-tuning-experiment-snapshot-detail",
            pk=snapshot.pk,
        )


class ExperimentDecisionTuningExperimentSnapshotDetailView(
    StaffRequiredMixin, DetailView
):
    model = ExperimentDecisionTuningExperimentSnapshot
    template_name = "studio/experiment_decision_tuning_experiment_snapshot_detail.html"
    context_object_name = "snapshot"

    def get_queryset(self):
        return ExperimentDecisionTuningExperimentSnapshot.objects.select_related(
            "change_log", "change_log__tuning", "generated_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metric_rows"] = snapshot_section_rows(self.object)
        context["sections"] = _group_snapshot_rows_by_section(context["metric_rows"])
        context["decision_recommendation"] = recommend_experiment_decision(self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        if action != "apply_decision_recommendation":
            messages.error(request, "Unknown snapshot action.")
            return redirect(
                "studio:experiment-decision-tuning-experiment-snapshot-detail",
                pk=self.object.pk,
            )
        apply_decision_to_decision_rule_change_log(
            snapshot=self.object,
            user=request.user if request.user.is_authenticated else None,
            note=request.POST.get("decision_note", "").strip(),
        )
        messages.success(
            request, "Decision recommendation recorded on the decision-rule experiment."
        )
        return redirect(
            "studio:experiment-decision-tuning-experiment-snapshot-detail",
            pk=self.object.pk,
        )


class ExperimentDecisionTuningExperimentSnapshotExportView(
    StaffRequiredMixin, DetailView
):
    model = ExperimentDecisionTuningExperimentSnapshot

    def get(self, request, *args, **kwargs):
        snapshot = self.get_object()
        filename = (
            f"code-with-michael-decision-rule-experiment-snapshot-{snapshot.pk}.csv"
        )
        response = _csv_response(filename)
        recommendation = recommend_experiment_decision(snapshot)
        writer = csv.writer(response)
        writer.writerow(["decision_recommendation", recommendation.label])
        writer.writerow(["decision_confidence", recommendation.confidence])
        writer.writerow(["decision_score", recommendation.score])
        writer.writerow(["decision_summary", recommendation.summary])
        writer.writerow([])
        writer.writerow(["Weighted signals"])
        writer.writerow(
            ["section", "metric", "change", "weight", "contribution", "direction"]
        )
        for signal in recommendation.weighted_signals:
            writer.writerow(
                [
                    signal.get("section"),
                    signal.get("metric"),
                    signal.get("change"),
                    signal.get("weight"),
                    signal.get("contribution"),
                    signal.get("direction"),
                ]
            )
        writer.writerow([])
        writer.writerow(["Snapshot metrics"])
        writer.writerow(
            [
                "experiment_label",
                "generated_at",
                "window_days",
                "before_start",
                "before_end",
                "after_start",
                "after_end",
                "section",
                "metric",
                "before",
                "after",
                "change",
                "percent_change",
            ]
        )
        for row in snapshot_section_rows(snapshot):
            writer.writerow(
                [
                    snapshot.experiment_label,
                    snapshot.generated_at.isoformat(),
                    snapshot.window_days,
                    snapshot.before_start.isoformat(),
                    snapshot.before_end.isoformat(),
                    snapshot.after_start.isoformat(),
                    snapshot.after_end.isoformat(),
                    row["section_label"],
                    row["metric_label"],
                    row["before"],
                    row["after"],
                    row["change"],
                    row["pct"] if row["pct"] is not None else "",
                ]
            )
        return response


class ExperimentDecisionTuningExperimentSnapshotCompareView(
    StaffRequiredMixin, FormView
):
    template_name = "studio/experiment_decision_tuning_experiment_snapshot_compare.html"
    form_class = ExperimentDecisionTuningExperimentSnapshotComparisonForm

    def get_initial(self):
        initial = super().get_initial()
        latest = ExperimentDecisionTuningExperimentSnapshot.objects.order_by(
            "-generated_at", "-pk"
        )[:3]
        initial["snapshots"] = [snapshot.pk for snapshot in latest]
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET" and self.request.GET:
            kwargs["data"] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        if self.request.GET and not form.is_valid():
            snapshots = []
            preset_keys = []
        else:
            snapshots = _selected_decision_rule_snapshots(form)
            preset_keys = (
                form.cleaned_data.get("preset_keys", []) if form.is_valid() else []
            )
        comparison = _decision_rule_snapshot_comparison(
            snapshots, preset_keys=preset_keys
        )
        context.update(
            {
                "comparison": comparison,
                "comparison_charts": _decision_rule_snapshot_comparison_charts(
                    comparison
                ),
                "snapshots": snapshots,
                "selected_count": len(snapshots),
                "export_query": self.request.GET.urlencode(),
            }
        )
        return context


class ExperimentDecisionTuningExperimentSnapshotCompareExportView(
    StaffRequiredMixin, FormView
):
    form_class = ExperimentDecisionTuningExperimentSnapshotComparisonForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["data"] = self.request.GET or None
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if request.GET and not form.is_valid():
            snapshots = []
            preset_keys = []
        else:
            snapshots = _selected_decision_rule_snapshots(form)
            preset_keys = (
                form.cleaned_data.get("preset_keys", []) if form.is_valid() else []
            )
        comparison = _decision_rule_snapshot_comparison(
            snapshots, preset_keys=preset_keys
        )
        response = _csv_response(
            "code-with-michael-decision-rule-snapshot-comparison.csv"
        )
        writer = csv.writer(response)

        writer.writerow(["Summary comparison"])
        writer.writerow(
            ["metric"]
            + [
                f"{card['snapshot'].experiment_label} ({card['snapshot'].window_days}d)"
                for card in comparison["snapshot_cards"]
            ]
        )
        for row in comparison["summary_rows"]:
            writer.writerow([row["label"]] + [cell["change"] for cell in row["cells"]])

        writer.writerow([])
        writer.writerow(["Decision recommendations"])
        writer.writerow(
            [
                "snapshot",
                "window_days",
                "rules_profile",
                "recommendation",
                "confidence",
                "score",
                "summary",
            ]
        )
        for card in comparison["snapshot_cards"]:
            for rec_row in card["recommendations"]:
                rec = rec_row["recommendation"]
                writer.writerow(
                    [
                        card["snapshot"].experiment_label,
                        card["snapshot"].window_days,
                        rec_row["profile"]["label"],
                        rec.label,
                        rec.confidence,
                        rec.score,
                        rec.summary,
                    ]
                )

        writer.writerow([])
        writer.writerow(["Metric comparison"])
        writer.writerow(
            ["section", "metric"]
            + [
                f"{card['snapshot'].experiment_label} change"
                for card in comparison["snapshot_cards"]
            ]
        )
        for row in comparison["metric_rows"]:
            writer.writerow(
                [row["section_label"], row["metric_label"]]
                + [cell["change"] for cell in row["cells"]]
            )

        charts = _decision_rule_snapshot_comparison_charts(comparison)
        writer.writerow([])
        writer.writerow(["Chart data - decision counts"])
        writer.writerow(["recommendation", "count"])
        for row in charts["decision_count_chart"]:
            writer.writerow([row["label"], row["count"]])

        writer.writerow([])
        writer.writerow(["Chart data - top metric deltas"])
        writer.writerow(
            ["section", "metric"]
            + [
                f"{card['snapshot'].experiment_label} change"
                for card in comparison["snapshot_cards"]
            ]
        )
        for row in charts["metric_delta_chart"]:
            writer.writerow(
                [row["section_label"], row["metric_label"]]
                + [cell["display"] for cell in row["bars"]]
            )
        return response


REPORT_TEMPLATE_DEFINITIONS = [
    {
        "title": "Monthly Growth Review",
        "slug": "monthly-growth-review",
        "template_type": ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.MONTHLY_GROWTH,
        "description": "Recurring monthly review for overall Code with Michael growth across social, resource, newsletter, CTA, and learner-conversion metrics.",
        "default_report_title": "Monthly Growth Review",
        "default_description": "Monthly decision-rule snapshot comparison for overall growth and learning impact.",
        "default_notes": "Review follower growth, reach, engagement, resource downloads, newsletter clicks, CTA clicks, and learner conversions. Decide whether current decision rules should be kept, watched, or rolled back.",
        "default_preset_keys": ["balanced_learning", "aggressive_growth"],
        "recommended_snapshot_count": 3,
        "recommended_window_days": 30,
        "focus_areas": [
            "Follower growth",
            "Engagement",
            "Newsletter clicks",
            "Learner conversions",
        ],
    },
    {
        "title": "Lead Magnet Review",
        "slug": "lead-magnet-review",
        "template_type": ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.LEAD_MAGNET,
        "description": "Review whether PDF resources and gated downloads are creating subscribers and downstream lesson activity.",
        "default_report_title": "Lead Magnet Review",
        "default_description": "Decision-rule comparison focused on resource unlocks, PDF downloads, email capture, and resource-to-lesson conversion.",
        "default_notes": "Check PDF unlocks, downloads, new subscribers, CTA clicks, and resource-attributed learner conversions. Watch for vanity download volume without lesson activity.",
        "default_preset_keys": ["lead_magnet_focus", "balanced_learning"],
        "recommended_snapshot_count": 3,
        "recommended_window_days": 14,
        "focus_areas": [
            "PDF unlocks",
            "PDF downloads",
            "Subscribers",
            "Resource-to-lesson conversions",
        ],
    },
    {
        "title": "Instagram Experiment Review",
        "slug": "instagram-experiment-review",
        "template_type": ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.INSTAGRAM_EXPERIMENT,
        "description": "Review Instagram-focused growth experiments, especially carousel formats, CTA behavior, and follower movement.",
        "default_report_title": "Instagram Experiment Review",
        "default_description": "Decision-rule comparison focused on Instagram growth, post engagement, clicks, and follow-through into beginner learning actions.",
        "default_notes": "Compare follower growth, reach, engagement, clicks, CTA clicks, and conversions from Instagram-heavy posting periods. Note whether results justify continuing the rule profile.",
        "default_preset_keys": ["aggressive_growth", "balanced_learning"],
        "recommended_snapshot_count": 2,
        "recommended_window_days": 14,
        "focus_areas": [
            "Instagram reach",
            "Follower growth",
            "Carousel engagement",
            "CTA clicks",
        ],
    },
    {
        "title": "Learning Conversion Review",
        "slug": "learning-conversion-review",
        "template_type": ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.LEARNING_CONVERSION,
        "description": "Review whether recommendation and decision rules are pushing learners toward lessons, quizzes, challenges, and completions.",
        "default_report_title": "Learning Conversion Review",
        "default_description": "Decision-rule comparison focused on lesson views, quiz attempts, challenge attempts, and completed lessons.",
        "default_notes": "Prioritize meaningful beginner learning behavior over raw traffic. Compare lesson views, quiz attempts, challenge attempts, and lesson completions before deciding to keep or roll back.",
        "default_preset_keys": ["balanced_learning", "conservative_quality"],
        "recommended_snapshot_count": 3,
        "recommended_window_days": 30,
        "focus_areas": [
            "Lesson views",
            "Quiz attempts",
            "Challenge attempts",
            "Lesson completions",
        ],
    },
]


def ensure_default_report_templates(user=None):
    """Create built-in report templates when the template library is first opened."""
    for definition in REPORT_TEMPLATE_DEFINITIONS:
        defaults = dict(definition)
        slug = defaults.pop("slug")
        defaults.setdefault(
            "created_by", user if getattr(user, "is_authenticated", False) else None
        )
        defaults.setdefault(
            "updated_by", user if getattr(user, "is_authenticated", False) else None
        )
        ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.get_or_create(
            slug=slug, defaults=defaults
        )


def _recent_snapshot_ids_for_template(template):
    count = max(1, min(int(template.recommended_snapshot_count or 3), 6))
    qs = ExperimentDecisionTuningExperimentSnapshot.objects.select_related(
        "change_log"
    ).order_by("-generated_at", "-pk")
    if template.recommended_window_days:
        filtered = qs.filter(window_days=template.recommended_window_days)
        if filtered.exists():
            qs = filtered
    return [str(pk) for pk in qs.values_list("pk", flat=True)[:count]]


class ExperimentDecisionTuningSnapshotComparisonReportTemplateListView(
    StaffRequiredMixin, ListView
):
    model = ExperimentDecisionTuningSnapshotComparisonReportTemplate
    template_name = (
        "studio/experiment_decision_tuning_snapshot_comparison_report_templates.html"
    )
    context_object_name = "templates"

    def dispatch(self, request, *args, **kwargs):
        ensure_default_report_templates(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.select_related(
            "created_by", "updated_by"
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(default_notes__icontains=q)
            )
        template_type = self.request.GET.get("template_type", "").strip()
        if template_type:
            qs = qs.filter(template_type=template_type)
        active = self.request.GET.get("active", "").strip()
        if active == "yes":
            qs = qs.filter(is_active=True)
        elif active == "no":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["template_type"] = self.request.GET.get("template_type", "").strip()
        context["active"] = self.request.GET.get("active", "").strip()
        context["template_type_choices"] = (
            ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.choices
        )
        context["template_count"] = (
            context["templates"].count()
            if hasattr(context["templates"], "count")
            else len(context["templates"])
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportTemplateCreateView(
    StaffRequiredMixin, CreateView
):
    model = ExperimentDecisionTuningSnapshotComparisonReportTemplate
    form_class = ExperimentDecisionTuningSnapshotComparisonReportTemplateForm
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_template_form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["recommended_snapshot_count"] = 3
        initial["recommended_window_days"] = 14
        initial["is_active"] = True
        return initial

    def form_valid(self, form):
        form.instance.created_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        form.instance.updated_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        if not form.instance.slug:
            form.instance.slug = slugify(form.instance.title)
        messages.success(self.request, "Created report template.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "studio:experiment-decision-tuning-snapshot-comparison-report-template-detail",
            kwargs={"slug": self.object.slug},
        )


class ExperimentDecisionTuningSnapshotComparisonReportTemplateUpdateView(
    StaffRequiredMixin, UpdateView
):
    model = ExperimentDecisionTuningSnapshotComparisonReportTemplate
    form_class = ExperimentDecisionTuningSnapshotComparisonReportTemplateForm
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_template_form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def form_valid(self, form):
        form.instance.updated_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        messages.success(self.request, "Updated report template.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "studio:experiment-decision-tuning-snapshot-comparison-report-template-detail",
            kwargs={"slug": self.object.slug},
        )


class ExperimentDecisionTuningSnapshotComparisonReportTemplateDetailView(
    StaffRequiredMixin, DetailView
):
    model = ExperimentDecisionTuningSnapshotComparisonReportTemplate
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_template_detail.html"
    context_object_name = "report_template"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suggested_snapshots"] = (
            ExperimentDecisionTuningExperimentSnapshot.objects.select_related(
                "change_log"
            )
            .filter(pk__in=_recent_snapshot_ids_for_template(self.object))
            .order_by("-generated_at", "-pk")
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportTemplateDeleteView(
    StaffRequiredMixin, DeleteView
):
    model = ExperimentDecisionTuningSnapshotComparisonReportTemplate
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_template_confirm_delete.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy(
        "studio:experiment-decision-tuning-snapshot-comparison-report-templates"
    )

    def form_valid(self, form):
        messages.success(self.request, "Deleted report template.")
        return super().form_valid(form)


class ExperimentDecisionTuningSnapshotComparisonReportFromTemplateView(
    StaffRequiredMixin, CreateView
):
    model = ExperimentDecisionTuningSnapshotComparisonReport
    form_class = ExperimentDecisionTuningSnapshotComparisonReportFromTemplateForm
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_from_template_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.report_template = get_object_or_404(
            ExperimentDecisionTuningSnapshotComparisonReportTemplate,
            slug=kwargs["slug"],
            is_active=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["template"] = self.report_template
        return kwargs

    def get_initial(self):
        initial = self.report_template.build_report_initial()
        initial["title"] = f"{initial['title']} · {timezone.now():%B %Y}"
        initial["snapshots"] = _recent_snapshot_ids_for_template(self.report_template)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_template"] = self.report_template
        return context

    def form_valid(self, form):
        form.instance.created_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        form.instance.updated_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        form.instance.source_template = self.report_template
        messages.success(
            self.request,
            f"Created saved report from the {self.report_template.title} template.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "studio:experiment-decision-tuning-snapshot-comparison-report-detail",
            kwargs={"pk": self.object.pk},
        )


def _template_usage_rows(template_queryset=None, report_queryset=None):
    """Build template usage rows without relying on complex database-specific annotations."""
    templates = list(
        (
            template_queryset
            if template_queryset is not None
            else ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.all()
        )
        .prefetch_related("generated_reports__snapshots")
        .select_related("created_by", "updated_by")
        .order_by("template_type", "title")
    )
    reports = list(
        (
            report_queryset
            if report_queryset is not None
            else ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
                source_template__isnull=False
            )
        )
        .select_related("source_template", "created_by", "updated_by", "decision_owner")
        .prefetch_related("snapshots")
        .order_by("-updated_at", "-pk")
    )
    reports_by_template = {}
    for report in reports:
        if report.source_template_id:
            reports_by_template.setdefault(report.source_template_id, []).append(report)

    rows = []
    decision_values = [
        choice[0]
        for choice in ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.choices
    ]
    for template in templates:
        template_reports = reports_by_template.get(template.pk, [])
        decision_counts = {key: 0 for key in decision_values}
        snapshot_total = 0
        preset_total = 0
        last_report = None
        for report in template_reports:
            decision_counts[report.decision_status] = (
                decision_counts.get(report.decision_status, 0) + 1
            )
            snapshot_total += report.snapshot_count
            preset_total += report.preset_count
            if last_report is None or report.updated_at > last_report.updated_at:
                last_report = report
        total_reports = len(template_reports)
        rows.append(
            {
                "template": template,
                "total_reports": total_reports,
                "decision_counts": decision_counts,
                "keep_count": decision_counts.get(
                    ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.KEEP,
                    0,
                ),
                "roll_back_count": decision_counts.get(
                    ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.ROLL_BACK,
                    0,
                ),
                "watch_count": decision_counts.get(
                    ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.WATCH,
                    0,
                ),
                "archived_count": decision_counts.get(
                    ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.ARCHIVED,
                    0,
                ),
                "undecided_count": decision_counts.get(
                    ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.UNDECIDED,
                    0,
                ),
                "avg_snapshots": round(snapshot_total / total_reports, 1)
                if total_reports
                else 0,
                "avg_presets": round(preset_total / total_reports, 1)
                if total_reports
                else 0,
                "last_report": last_report,
            }
        )
    return rows, reports


def _template_type_usage_rows(rows):
    grouped = {}
    for row in rows:
        template_type = row["template"].template_type
        label = row["template"].get_template_type_display()
        bucket = grouped.setdefault(
            template_type,
            {
                "template_type": template_type,
                "label": label,
                "template_count": 0,
                "total_reports": 0,
                "keep_count": 0,
                "roll_back_count": 0,
                "watch_count": 0,
                "archived_count": 0,
                "undecided_count": 0,
            },
        )
        bucket["template_count"] += 1
        for key in (
            "total_reports",
            "keep_count",
            "roll_back_count",
            "watch_count",
            "archived_count",
            "undecided_count",
        ):
            bucket[key] += row[key]
    return sorted(
        grouped.values(), key=lambda item: (-item["total_reports"], item["label"])
    )


class ReportTemplateRecommendationTuningUpdateView(StaffRequiredMixin, UpdateView):
    model = ReportTemplateRecommendationTuning
    form_class = ReportTemplateRecommendationTuningForm
    template_name = "studio/report_template_recommendation_tuning_form.html"
    context_object_name = "report_template_tuning"

    def get_object(self, queryset=None):
        return ReportTemplateRecommendationTuning.get_active()

    def form_valid(self, form):
        before = report_template_tuning_snapshot(self.get_object())
        response = super().form_valid(form)
        create_report_template_tuning_change_log(
            self.object,
            before=before,
            action=ReportTemplateRecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.request.user,
            reason=form.cleaned_data.get("reason_note", ""),
            request_path=self.request.path,
            experiment_label=form.cleaned_data.get("experiment_label", ""),
            experiment_status=form.cleaned_data.get("experiment_status")
            or ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
            experiment_notes=form.cleaned_data.get("experiment_notes", ""),
        )
        messages.success(
            self.request, "Report-template recommendation tuning saved and logged."
        )
        return response

    def get_success_url(self):
        return reverse("studio:report-template-recommendation-tuning")


class ReportTemplateRecommendationTuningHistoryView(StaffRequiredMixin, ListView):
    model = ReportTemplateRecommendationTuningChangeLog
    template_name = "studio/report_template_recommendation_tuning_history.html"
    context_object_name = "change_logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = ReportTemplateRecommendationTuningChangeLog.objects.select_related(
            "tuning", "changed_by"
        )
        action = self.request.GET.get("action", "")
        status = self.request.GET.get("experiment_status", "")
        outcome = self.request.GET.get("experiment_outcome", "")
        label = self.request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        return queryset.order_by("-created_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = ReportTemplateRecommendationTuningChangeLog.Action.choices
        context["experiment_statuses"] = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.choices
        )
        context["experiment_outcomes"] = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentOutcome.choices
        )
        context["selected_action"] = self.request.GET.get("action", "")
        context["selected_experiment_status"] = self.request.GET.get(
            "experiment_status", ""
        )
        context["selected_experiment_outcome"] = self.request.GET.get(
            "experiment_outcome", ""
        )
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        ).strip()
        context["latest_change"] = (
            ReportTemplateRecommendationTuningChangeLog.objects.order_by(
                "-created_at", "-pk"
            ).first()
        )
        context["total_changes"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("change_logs", []))
        )
        context["active_experiment_count"] = (
            ReportTemplateRecommendationTuningChangeLog.objects.exclude(
                experiment_status=ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT
            )
            .exclude(
                experiment_status=ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.COMPLETE
            )
            .count()
        )
        return context


class ReportTemplateRecommendationTuningHistoryExportView(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        queryset = ReportTemplateRecommendationTuningChangeLog.objects.select_related(
            "tuning", "changed_by"
        ).order_by("-created_at", "-pk")
        action = request.GET.get("action", "")
        status = request.GET.get("experiment_status", "")
        outcome = request.GET.get("experiment_outcome", "")
        label = request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="report_template_recommendation_tuning_history.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "created_at",
                "action",
                "profile",
                "changed_by",
                "changed_fields",
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "experiment_notes",
                "diff_json",
                "reason",
                "request_path",
            ]
        )
        for log in queryset:
            writer.writerow(
                [
                    log.created_at.isoformat(),
                    log.get_action_display(),
                    log.tuning.name if log.tuning_id else "",
                    getattr(log.changed_by, "email", "") or "",
                    log.changed_field_count,
                    log.experiment_label,
                    log.get_experiment_status_display(),
                    log.get_experiment_outcome_display(),
                    log.outcome_recorded_at.isoformat()
                    if log.outcome_recorded_at
                    else "",
                    getattr(log.outcome_recorded_by, "email", "") or "",
                    log.experiment_notes,
                    json.dumps(log.diff, sort_keys=True),
                    log.reason,
                    log.request_path,
                ]
            )
        return response


class ReportTemplateRecommendationTuningRollbackView(StaffRequiredMixin, DetailView):
    model = ReportTemplateRecommendationTuningChangeLog
    template_name = "studio/report_template_recommendation_tuning_rollback.html"
    context_object_name = "change_log"

    def post(self, request, *args, **kwargs):
        change_log = self.get_object()
        snapshot = request.POST.get("snapshot", "before")
        if snapshot not in {"before", "after"}:
            messages.error(
                request,
                "Choose a valid report-template recommendation tuning snapshot to restore.",
            )
            return redirect(
                "studio:report-template-recommendation-tuning-rollback",
                pk=change_log.pk,
            )
        restore_report_template_tuning_snapshot(
            change_log,
            snapshot=snapshot,
            changed_by=request.user,
            reason=request.POST.get("rollback_reason", ""),
            request_path=request.path,
        )
        label = "before-change" if snapshot == "before" else "after-change"
        messages.success(
            request,
            f"Restored the {label} report-template recommendation tuning snapshot and logged the rollback.",
        )
        return redirect("studio:report-template-recommendation-tuning-history")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active = ReportTemplateRecommendationTuning.get_active()
        active_snapshot = report_template_tuning_snapshot(active)
        context["active_tuning"] = active
        context["active_snapshot"] = active_snapshot
        context["tracked_fields"] = [
            {
                "name": field,
                "active": active_snapshot.get(field),
                "before": self.object.before.get(field),
                "after": self.object.after.get(field),
            }
            for field in active_snapshot.keys()
        ]
        return context


class ReportTemplateRecommendationTuningExperimentOutcomeView(
    StaffRequiredMixin, UpdateView
):
    model = ReportTemplateRecommendationTuningChangeLog
    form_class = ReportTemplateRecommendationTuningExperimentOutcomeForm
    template_name = "studio/report_template_recommendation_tuning_experiment_form.html"
    context_object_name = "change_log"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.outcome_recorded_at = timezone.now()
        self.object.outcome_recorded_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        self.object.save(
            update_fields=[
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "experiment_notes",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "updated_at",
            ]
        )
        messages.success(
            self.request, "Template-recommendation tuning experiment outcome saved."
        )
        return redirect("studio:report-template-recommendation-tuning-history")

    def get_success_url(self):
        return reverse("studio:report-template-recommendation-tuning-history")


class ReportTemplateRecommendationTuningDecisionRulesUpdateView(
    StaffRequiredMixin, UpdateView
):
    model = ReportTemplateRecommendationTuningDecisionRules
    form_class = ReportTemplateRecommendationTuningDecisionRulesForm
    template_name = (
        "studio/report_template_recommendation_tuning_decision_rules_form.html"
    )
    context_object_name = "decision_rules"

    def get_object(self, queryset=None):
        return ReportTemplateRecommendationTuningDecisionRules.get_active()

    def form_valid(self, form):
        before = report_template_decision_rule_snapshot(self.get_object())
        response = super().form_valid(form)
        create_report_template_decision_rule_change_log(
            self.object,
            before=before,
            action=ReportTemplateRecommendationTuningDecisionRulesChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.request.user,
            reason=form.cleaned_data.get("change_reason", ""),
            request_path=self.request.path,
            experiment_label=form.cleaned_data.get("experiment_label", ""),
            experiment_status=form.cleaned_data.get("experiment_status", "")
            or ReportTemplateRecommendationTuningDecisionRulesChangeLog.ExperimentStatus.NOT_EXPERIMENT,
            experiment_notes=form.cleaned_data.get("experiment_notes", ""),
        )
        messages.success(
            self.request,
            "Template-recommendation snapshot decision rules saved and logged. Future snapshot decisions will use the active rule profile.",
        )
        return response

    def get_success_url(self):
        return reverse("studio:report-template-recommendation-tuning-decision-rules")


class ReportTemplateRecommendationTuningDecisionRulesHistoryView(
    StaffRequiredMixin, ListView
):
    model = ReportTemplateRecommendationTuningDecisionRulesChangeLog
    template_name = (
        "studio/report_template_recommendation_tuning_decision_rules_history.html"
    )
    context_object_name = "change_logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = ReportTemplateRecommendationTuningDecisionRulesChangeLog.objects.select_related(
            "decision_rules", "changed_by"
        )
        action = self.request.GET.get("action", "")
        status = self.request.GET.get("experiment_status", "")
        outcome = self.request.GET.get("experiment_outcome", "")
        label = self.request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        return queryset.order_by("-created_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = (
            ReportTemplateRecommendationTuningDecisionRulesChangeLog.Action.choices
        )
        context["experiment_statuses"] = (
            ReportTemplateRecommendationTuningDecisionRulesChangeLog.ExperimentStatus.choices
        )
        context["experiment_outcomes"] = (
            ReportTemplateRecommendationTuningDecisionRulesChangeLog.ExperimentOutcome.choices
        )
        context["selected_action"] = self.request.GET.get("action", "")
        context["selected_experiment_status"] = self.request.GET.get(
            "experiment_status", ""
        )
        context["selected_experiment_outcome"] = self.request.GET.get(
            "experiment_outcome", ""
        )
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        ).strip()
        context["latest_change"] = (
            ReportTemplateRecommendationTuningDecisionRulesChangeLog.objects.order_by(
                "-created_at", "-pk"
            ).first()
        )
        context["total_changes"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("change_logs", []))
        )
        context["active_experiment_count"] = (
            ReportTemplateRecommendationTuningDecisionRulesChangeLog.objects.exclude(
                experiment_status=ReportTemplateRecommendationTuningDecisionRulesChangeLog.ExperimentStatus.NOT_EXPERIMENT
            )
            .exclude(
                experiment_status=ReportTemplateRecommendationTuningDecisionRulesChangeLog.ExperimentStatus.COMPLETE
            )
            .count()
        )
        return context


class ReportTemplateRecommendationTuningDecisionRulesHistoryExportView(
    StaffRequiredMixin, View
):
    def get(self, request, *args, **kwargs):
        queryset = ReportTemplateRecommendationTuningDecisionRulesChangeLog.objects.select_related(
            "decision_rules", "changed_by"
        ).order_by("-created_at", "-pk")
        action = request.GET.get("action", "")
        status = request.GET.get("experiment_status", "")
        outcome = request.GET.get("experiment_outcome", "")
        label = request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="report_template_recommendation_decision_rule_history.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "created_at",
                "action",
                "decision_rule_profile",
                "changed_by",
                "changed_fields",
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "experiment_notes",
                "diff_json",
                "reason",
                "request_path",
            ]
        )
        for log in queryset:
            writer.writerow(
                [
                    log.created_at.isoformat(),
                    log.get_action_display(),
                    log.decision_rules.name if log.decision_rules_id else "",
                    getattr(log.changed_by, "email", "") or "",
                    log.changed_field_count,
                    log.experiment_label,
                    log.get_experiment_status_display(),
                    log.get_experiment_outcome_display(),
                    log.outcome_recorded_at.isoformat()
                    if log.outcome_recorded_at
                    else "",
                    getattr(log.outcome_recorded_by, "email", "") or "",
                    log.experiment_notes,
                    json.dumps(log.diff, sort_keys=True),
                    log.reason,
                    log.request_path,
                ]
            )
        return response


class ReportTemplateRecommendationTuningDecisionRulesRollbackView(
    StaffRequiredMixin, DetailView
):
    model = ReportTemplateRecommendationTuningDecisionRulesChangeLog
    template_name = (
        "studio/report_template_recommendation_tuning_decision_rules_rollback.html"
    )
    context_object_name = "change_log"

    def post(self, request, *args, **kwargs):
        change_log = self.get_object()
        snapshot = request.POST.get("snapshot", "before")
        if snapshot not in {"before", "after"}:
            messages.error(
                request,
                "Choose a valid template-recommendation decision-rule snapshot to restore.",
            )
            return redirect(
                "studio:report-template-recommendation-tuning-decision-rules-rollback",
                pk=change_log.pk,
            )
        restore_report_template_decision_rule_snapshot(
            change_log,
            snapshot=snapshot,
            changed_by=request.user,
            reason=request.POST.get("rollback_reason", ""),
            request_path=request.path,
        )
        label = "before-change" if snapshot == "before" else "after-change"
        messages.success(
            request,
            f"Restored the {label} template-recommendation decision-rule snapshot and logged the rollback.",
        )
        return redirect(
            "studio:report-template-recommendation-tuning-decision-rules-history"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active = ReportTemplateRecommendationTuningDecisionRules.get_active()
        active_snapshot = report_template_decision_rule_snapshot(active)
        context["active_decision_rules"] = active
        context["active_snapshot"] = active_snapshot
        context["tracked_fields"] = [
            {
                "name": field,
                "active": active_snapshot.get(field),
                "before": self.object.before.get(field),
                "after": self.object.after.get(field),
            }
            for field in active_snapshot.keys()
        ]
        return context


class ReportTemplateRecommendationTuningDecisionRulesExperimentOutcomeView(
    StaffRequiredMixin, UpdateView
):
    model = ReportTemplateRecommendationTuningDecisionRulesChangeLog
    form_class = ReportTemplateRecommendationTuningDecisionRulesExperimentOutcomeForm
    template_name = "studio/report_template_recommendation_tuning_decision_rules_experiment_form.html"
    context_object_name = "change_log"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.outcome_recorded_at = timezone.now()
        self.object.outcome_recorded_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        self.object.save(
            update_fields=[
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "experiment_notes",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "updated_at",
            ]
        )
        messages.success(
            self.request,
            "Template-recommendation decision-rule experiment outcome saved.",
        )
        return redirect(
            "studio:report-template-recommendation-tuning-decision-rules-history"
        )

    def get_success_url(self):
        return reverse(
            "studio:report-template-recommendation-tuning-decision-rules-history"
        )


class ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotListView(
    StaffRequiredMixin, ListView
):
    model = ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot
    template_name = "studio/report_template_recommendation_tuning_decision_rules_experiment_snapshots.html"
    context_object_name = "snapshots"
    paginate_by = 30

    def get_queryset(self):
        queryset = ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot.objects.select_related(
            "change_log", "change_log__decision_rules", "generated_by"
        )
        label = self.request.GET.get("experiment_label", "").strip()
        window_days = self.request.GET.get("window_days", "").strip()
        if label:
            queryset = queryset.filter(change_log__experiment_label__icontains=label)
        if window_days.isdigit():
            queryset = queryset.filter(window_days=int(window_days))
        return queryset.order_by("-generated_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        ).strip()
        context["selected_window_days"] = self.request.GET.get(
            "window_days", ""
        ).strip()
        context["window_choices"] = [7, 14, 30, 60]
        context["snapshot_count"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("snapshots", []))
        )
        context["latest_snapshot"] = (
            ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot.objects.order_by(
                "-generated_at"
            ).first()
        )
        return context


class ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotCreateView(
    StaffRequiredMixin, DetailView
):
    model = ReportTemplateRecommendationTuningDecisionRulesChangeLog
    template_name = "studio/report_template_recommendation_tuning_decision_rules_experiment_snapshot_form.html"
    context_object_name = "change_log"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = (
            kwargs.get("form")
            or ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotForm()
        )
        context["existing_snapshots"] = (
            self.object.performance_snapshots.select_related("generated_by")[:10]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotForm(
            request.POST
        )
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        snapshot = (
            create_report_template_recommendation_decision_rule_experiment_snapshot(
                change_log=self.object,
                window_days=form.cleaned_data["window_days"],
                generated_by=request.user if request.user.is_authenticated else None,
                notes=form.cleaned_data.get("notes", ""),
            )
        )
        messages.success(
            request,
            "Template-recommendation decision-rule experiment snapshot created.",
        )
        return redirect(
            "studio:report-template-recommendation-tuning-decision-rules-experiment-snapshot-detail",
            pk=snapshot.pk,
        )


class ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotDetailView(
    StaffRequiredMixin, DetailView
):
    model = ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot
    template_name = "studio/report_template_recommendation_tuning_decision_rules_experiment_snapshot_detail.html"
    context_object_name = "snapshot"

    def get_queryset(self):
        return ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot.objects.select_related(
            "change_log", "change_log__decision_rules", "generated_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metric_rows"] = report_template_decision_rule_snapshot_section_rows(
            self.object
        )
        context["sections"] = _group_snapshot_rows_by_section(context["metric_rows"])
        context["active_decision_rules"] = (
            ReportTemplateRecommendationTuningDecisionRules.get_active()
        )
        context["decision_recommendation"] = (
            recommend_report_template_decision_rule_snapshot_decision(
                self.object, context["active_decision_rules"]
            )
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        if action != "apply_template_decision_rule_snapshot_decision":
            messages.error(
                request,
                "Choose a valid template-recommendation decision-rule snapshot action.",
            )
            return redirect(
                "studio:report-template-recommendation-tuning-decision-rules-experiment-snapshot-detail",
                pk=self.object.pk,
            )
        apply_report_template_decision_rule_snapshot_decision_to_change_log(
            snapshot=self.object,
            user=request.user,
            note=request.POST.get("decision_note", "").strip(),
        )
        messages.success(
            request,
            "Decision recommendation recorded on the template-recommendation decision-rule experiment.",
        )
        return redirect(
            "studio:report-template-recommendation-tuning-decision-rules-experiment-snapshot-detail",
            pk=self.object.pk,
        )


class ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshotExportView(
    StaffRequiredMixin, DetailView
):
    model = ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot

    def get(self, request, *args, **kwargs):
        snapshot = self.get_object()
        filename = (
            f"code-with-michael-template-decision-rule-snapshot-{snapshot.pk}.csv"
        )
        response = _csv_response(filename)
        writer = csv.writer(response)
        writer.writerow(["experiment_label", snapshot.experiment_label])
        writer.writerow(["generated_at", snapshot.generated_at.isoformat()])
        writer.writerow(
            ["decision_rules_profile", snapshot.change_log.decision_rules.name]
        )
        writer.writerow(["window_days", snapshot.window_days])
        recommendation = recommend_report_template_decision_rule_snapshot_decision(
            snapshot
        )
        writer.writerow(["decision_recommendation", recommendation.label])
        writer.writerow(["decision_confidence", recommendation.confidence])
        writer.writerow(["decision_score", recommendation.score])
        writer.writerow(["decision_summary", recommendation.summary])
        writer.writerow(["decision_rules_profile", recommendation.decision_rules_name])
        writer.writerow([])
        writer.writerow(["weighted_signals"])
        writer.writerow(
            ["section", "metric", "change", "weight", "score_impact", "direction"]
        )
        for signal in recommendation.weighted_signals:
            writer.writerow(
                [
                    signal["section"],
                    signal["metric"],
                    signal["change"],
                    signal["weight"],
                    signal["contribution"],
                    signal["direction"],
                ]
            )
        writer.writerow([])
        writer.writerow(
            ["section", "metric", "before", "after", "change", "percent_change"]
        )
        for row in report_template_decision_rule_snapshot_section_rows(snapshot):
            writer.writerow(
                [
                    row["section_label"],
                    row["metric_label"],
                    row["before"],
                    row["after"],
                    row["change"],
                    row["pct"] if row["pct"] is not None else "",
                ]
            )
        return response


class ReportTemplateRecommendationTuningExperimentSnapshotListView(
    StaffRequiredMixin, ListView
):
    model = ReportTemplateRecommendationTuningExperimentSnapshot
    template_name = (
        "studio/report_template_recommendation_tuning_experiment_snapshots.html"
    )
    context_object_name = "snapshots"
    paginate_by = 30

    def get_queryset(self):
        queryset = (
            ReportTemplateRecommendationTuningExperimentSnapshot.objects.select_related(
                "change_log", "change_log__tuning", "generated_by"
            )
        )
        label = self.request.GET.get("experiment_label", "").strip()
        window_days = self.request.GET.get("window_days", "").strip()
        if label:
            queryset = queryset.filter(change_log__experiment_label__icontains=label)
        if window_days.isdigit():
            queryset = queryset.filter(window_days=int(window_days))
        return queryset.order_by("-generated_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        ).strip()
        context["selected_window_days"] = self.request.GET.get(
            "window_days", ""
        ).strip()
        context["window_choices"] = [7, 14, 30, 60]
        context["snapshot_count"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("snapshots", []))
        )
        context["latest_snapshot"] = (
            ReportTemplateRecommendationTuningExperimentSnapshot.objects.order_by(
                "-generated_at"
            ).first()
        )
        return context


class ReportTemplateRecommendationTuningExperimentSnapshotCreateView(
    StaffRequiredMixin, DetailView
):
    model = ReportTemplateRecommendationTuningChangeLog
    template_name = (
        "studio/report_template_recommendation_tuning_experiment_snapshot_form.html"
    )
    context_object_name = "change_log"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = (
            kwargs.get("form")
            or ReportTemplateRecommendationTuningExperimentSnapshotForm()
        )
        context["existing_snapshots"] = (
            self.object.performance_snapshots.select_related("generated_by")[:10]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ReportTemplateRecommendationTuningExperimentSnapshotForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        snapshot = create_report_template_recommendation_tuning_experiment_snapshot(
            change_log=self.object,
            window_days=form.cleaned_data["window_days"],
            generated_by=request.user if request.user.is_authenticated else None,
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(
            request,
            "Report-template recommendation tuning experiment snapshot created.",
        )
        return redirect(
            "studio:report-template-recommendation-tuning-experiment-snapshot-detail",
            pk=snapshot.pk,
        )


class ReportTemplateRecommendationTuningExperimentSnapshotDetailView(
    StaffRequiredMixin, DetailView
):
    model = ReportTemplateRecommendationTuningExperimentSnapshot
    template_name = (
        "studio/report_template_recommendation_tuning_experiment_snapshot_detail.html"
    )
    context_object_name = "snapshot"

    def get_queryset(self):
        return (
            ReportTemplateRecommendationTuningExperimentSnapshot.objects.select_related(
                "change_log", "change_log__tuning", "generated_by"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metric_rows"] = report_template_snapshot_section_rows(self.object)
        context["sections"] = _group_snapshot_rows_by_section(context["metric_rows"])
        context["active_decision_rules"] = (
            ReportTemplateRecommendationTuningDecisionRules.get_active()
        )
        context["decision_recommendation"] = recommend_report_template_tuning_decision(
            self.object, context["active_decision_rules"]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        if action != "apply_template_recommendation_decision":
            messages.error(
                request,
                "Choose a valid template-recommendation tuning decision action.",
            )
            return redirect(
                "studio:report-template-recommendation-tuning-experiment-snapshot-detail",
                pk=self.object.pk,
            )
        apply_report_template_tuning_decision_to_change_log(
            snapshot=self.object,
            user=request.user,
            note=request.POST.get("decision_note", "").strip(),
        )
        messages.success(
            request,
            "Decision recommendation recorded on the report-template recommendation tuning experiment.",
        )
        return redirect(
            "studio:report-template-recommendation-tuning-experiment-snapshot-detail",
            pk=self.object.pk,
        )


class ReportTemplateRecommendationTuningExperimentSnapshotExportView(
    StaffRequiredMixin, DetailView
):
    model = ReportTemplateRecommendationTuningExperimentSnapshot

    def get(self, request, *args, **kwargs):
        snapshot = self.get_object()
        filename = f"code-with-michael-report-template-recommendation-tuning-snapshot-{snapshot.pk}.csv"
        response = _csv_response(filename)
        recommendation = recommend_report_template_tuning_decision(snapshot)
        writer = csv.writer(response)
        writer.writerow(["decision_recommendation", recommendation.label])
        writer.writerow(["decision_confidence", recommendation.confidence])
        writer.writerow(["decision_score", recommendation.score])
        writer.writerow(["decision_rules_profile", recommendation.decision_rules_name])
        writer.writerow(
            [
                "decision_rule_thresholds_json",
                json.dumps(recommendation.rule_thresholds),
            ]
        )
        writer.writerow(["decision_summary", recommendation.summary])
        writer.writerow([])
        writer.writerow(["Weighted signals"])
        writer.writerow(
            ["section", "metric", "change", "weight", "contribution", "direction"]
        )
        for signal in recommendation.weighted_signals:
            writer.writerow(
                [
                    signal.get("section"),
                    signal.get("metric"),
                    signal.get("change"),
                    signal.get("weight"),
                    signal.get("contribution"),
                    signal.get("direction"),
                ]
            )
        writer.writerow([])
        writer.writerow(["Snapshot metrics"])
        writer.writerow(
            [
                "experiment_label",
                "generated_at",
                "window_days",
                "before_start",
                "before_end",
                "after_start",
                "after_end",
                "section",
                "metric",
                "before",
                "after",
                "change",
                "percent_change",
            ]
        )
        for row in report_template_snapshot_section_rows(snapshot):
            writer.writerow(
                [
                    snapshot.experiment_label,
                    snapshot.generated_at.isoformat(),
                    snapshot.window_days,
                    snapshot.before_start.isoformat(),
                    snapshot.before_end.isoformat(),
                    snapshot.after_start.isoformat(),
                    snapshot.after_end.isoformat(),
                    row["section_label"],
                    row["metric_label"],
                    row["before"],
                    row["after"],
                    row["change"],
                    row["pct"] if row["pct"] is not None else "",
                ]
            )
        return response


class ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationsView(
    StaffRequiredMixin, TemplateView
):
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_template_recommendations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ensure_default_report_templates(self.request.user)
        active_tuning = ReportTemplateRecommendationTuning.get_active()
        recommendations = build_report_template_recommendations(
            self.request.user, limit=12, tuning=active_tuning
        )
        for recommendation in recommendations:
            record_template_recommendation_shown(recommendation, self.request.user)
        context.update(
            {
                "recommendations": recommendations,
                "active_tuning": active_tuning,
                "total_recommendations": len(recommendations),
                "high_priority_count": sum(
                    1 for item in recommendations if item.priority == "High"
                ),
                "medium_priority_count": sum(
                    1 for item in recommendations if item.priority == "Medium"
                ),
                "low_priority_count": sum(
                    1 for item in recommendations if item.priority == "Low"
                ),
            }
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationsExportView(
    StaffRequiredMixin, TemplateView
):
    def get(self, request, *args, **kwargs):
        ensure_default_report_templates(request.user)
        active_tuning = ReportTemplateRecommendationTuning.get_active()
        recommendations = build_report_template_recommendations(
            request.user, limit=50, tuning=active_tuning
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="decision_rule_report_template_recommendations.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "rank",
                "active_tuning",
                "template_title",
                "template_type",
                "priority",
                "score",
                "base_score",
                "snapshot_focus_score",
                "usage_history_score",
                "focus_area_score",
                "preset_default_score",
                "feedback_adjustment",
                "recommended_window_days",
                "recommended_snapshot_count",
                "suggested_snapshot_ids",
                "suggested_snapshot_labels",
                "reasons",
                "feedback_notes",
            ]
        )
        for index, recommendation in enumerate(recommendations, start=1):
            writer.writerow(
                [
                    index,
                    active_tuning.name,
                    recommendation.template.title,
                    recommendation.template.get_template_type_display(),
                    recommendation.priority,
                    recommendation.score,
                    recommendation.score_parts.get("base", 0),
                    recommendation.score_parts.get("snapshot_focus", 0),
                    recommendation.score_parts.get("usage_history", 0),
                    recommendation.score_parts.get("focus_areas", 0),
                    recommendation.score_parts.get("preset_defaults", 0),
                    recommendation.score_parts.get("feedback", 0),
                    recommendation.template.recommended_window_days,
                    recommendation.template.recommended_snapshot_count,
                    ",".join(
                        str(snapshot.pk)
                        for snapshot in recommendation.suggested_snapshots
                    ),
                    " | ".join(
                        snapshot.experiment_label
                        for snapshot in recommendation.suggested_snapshots
                    ),
                    " | ".join(recommendation.reasons),
                    " | ".join(recommendation.feedback_notes),
                ]
            )
        return response


@method_decorator(require_POST, name="dispatch")
class ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedbackActionView(
    StaffRequiredMixin, View
):
    def post(self, request, *args, **kwargs):
        template = get_object_or_404(
            ExperimentDecisionTuningSnapshotComparisonReportTemplate,
            pk=request.POST.get("template_id"),
        )
        recommendation_key = request.POST.get("recommendation_key", "").strip()
        status = request.POST.get("status", "").strip()
        if not recommendation_key:
            messages.error(request, "Missing recommendation key.")
            return redirect(
                "studio:experiment-decision-tuning-snapshot-comparison-report-template-recommendations"
            )
        try:
            score = int(request.POST.get("score", "0") or 0)
        except ValueError:
            score = 0
        reasons = [item for item in request.POST.get("reasons", "").split("||") if item]
        snapshot_ids = []
        for value in request.POST.get("suggested_snapshot_ids", "").split(","):
            if value.strip().isdigit():
                snapshot_ids.append(int(value.strip()))
        try:
            feedback = record_template_recommendation_response(
                template=template,
                recommendation_key=recommendation_key,
                status=status,
                user=request.user,
                score=score,
                priority=request.POST.get("priority", ""),
                reasons=reasons,
                suggested_snapshot_ids=snapshot_ids,
                notes=request.POST.get("notes", "").strip(),
            )
        except ValueError:
            messages.error(request, "Invalid feedback action.")
        else:
            messages.success(
                request,
                f"Marked {template.title} recommendation as {feedback.get_status_display()}.",
            )
        return redirect(
            "studio:experiment-decision-tuning-snapshot-comparison-report-template-recommendations"
        )


class ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedbackView(
    StaffRequiredMixin, TemplateView
):
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_template_feedback.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.objects.select_related(
            "template", "created_by", "updated_by"
        ).order_by("-last_seen_at", "template__title")
        status = self.request.GET.get("status", "").strip()
        template_type = self.request.GET.get("template_type", "").strip()
        q = self.request.GET.get("q", "").strip()
        if status:
            qs = qs.filter(status=status)
        if template_type:
            qs = qs.filter(template__template_type=template_type)
        if q:
            qs = qs.filter(
                Q(template__title__icontains=q)
                | Q(recommendation_key__icontains=q)
                | Q(notes__icontains=q)
            )
        feedback = list(qs[:200])
        context.update(
            {
                "feedback": feedback,
                "status": status,
                "template_type": template_type,
                "q": q,
                "status_choices": ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.choices,
                "template_type_choices": ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.choices,
                "total_feedback": len(feedback),
                "useful_count": sum(
                    1 for item in feedback if item.status == item.Status.USEFUL
                ),
                "dismissed_count": sum(
                    1 for item in feedback if item.status == item.Status.DISMISSED
                ),
                "revisit_count": sum(
                    1 for item in feedback if item.status == item.Status.REVISIT
                ),
                "ignored_count": sum(1 for item in feedback if item.is_ignored_signal),
            }
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedbackExportView(
    StaffRequiredMixin, TemplateView
):
    def get(self, request, *args, **kwargs):
        qs = ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.objects.select_related(
            "template", "created_by", "updated_by"
        ).order_by("-last_seen_at")
        status = request.GET.get("status", "").strip()
        template_type = request.GET.get("template_type", "").strip()
        q = request.GET.get("q", "").strip()
        if status:
            qs = qs.filter(status=status)
        if template_type:
            qs = qs.filter(template__template_type=template_type)
        if q:
            qs = qs.filter(
                Q(template__title__icontains=q)
                | Q(recommendation_key__icontains=q)
                | Q(notes__icontains=q)
            )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="decision_rule_report_template_recommendation_feedback.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "template_title",
                "template_type",
                "recommendation_key",
                "status",
                "times_shown",
                "score",
                "priority",
                "suggested_snapshot_ids",
                "notes",
                "first_seen_at",
                "last_seen_at",
                "responded_at",
                "created_by",
                "updated_by",
                "reasons",
            ]
        )
        for item in qs:
            writer.writerow(
                [
                    item.template.title,
                    item.template.get_template_type_display(),
                    item.recommendation_key,
                    item.get_status_display(),
                    item.times_shown,
                    item.score,
                    item.priority,
                    ",".join(
                        str(value) for value in (item.suggested_snapshot_ids or [])
                    ),
                    item.notes,
                    item.first_seen_at.isoformat() if item.first_seen_at else "",
                    item.last_seen_at.isoformat() if item.last_seen_at else "",
                    item.responded_at.isoformat() if item.responded_at else "",
                    getattr(item.created_by, "email", ""),
                    getattr(item.updated_by, "email", ""),
                    " | ".join(item.reasons or []),
                ]
            )
        return response


class ExperimentDecisionTuningSnapshotComparisonReportTemplateUsageView(
    StaffRequiredMixin, TemplateView
):
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_template_usage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ensure_default_report_templates(self.request.user)
        template_qs = (
            ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.all()
        )
        report_qs = ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
            source_template__isnull=False
        )

        template_type = self.request.GET.get("template_type", "").strip()
        if template_type:
            template_qs = template_qs.filter(template_type=template_type)
            report_qs = report_qs.filter(source_template__template_type=template_type)
        active = self.request.GET.get("active", "").strip()
        if active == "yes":
            template_qs = template_qs.filter(is_active=True)
            report_qs = report_qs.filter(source_template__is_active=True)
        elif active == "no":
            template_qs = template_qs.filter(is_active=False)
            report_qs = report_qs.filter(source_template__is_active=False)
        decision_status = self.request.GET.get("decision_status", "").strip()
        if decision_status:
            report_qs = report_qs.filter(decision_status=decision_status)

        rows, reports = _template_usage_rows(template_qs, report_qs)
        context.update(
            {
                "rows": rows,
                "type_rows": _template_type_usage_rows(rows),
                "recent_reports": reports[:12],
                "template_type": template_type,
                "active": active,
                "decision_status": decision_status,
                "template_type_choices": ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.choices,
                "decision_status_choices": ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.choices,
                "total_templates": len(rows),
                "active_templates": sum(1 for row in rows if row["template"].is_active),
                "total_reports": sum(row["total_reports"] for row in rows),
                "total_keep": sum(row["keep_count"] for row in rows),
                "total_roll_back": sum(row["roll_back_count"] for row in rows),
                "total_watch": sum(row["watch_count"] for row in rows),
            }
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportTemplateUsageExportView(
    StaffRequiredMixin, TemplateView
):
    def get(self, request, *args, **kwargs):
        ensure_default_report_templates(request.user)
        template_qs = (
            ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.all()
        )
        report_qs = ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
            source_template__isnull=False
        )
        template_type = request.GET.get("template_type", "").strip()
        if template_type:
            template_qs = template_qs.filter(template_type=template_type)
            report_qs = report_qs.filter(source_template__template_type=template_type)
        active = request.GET.get("active", "").strip()
        if active == "yes":
            template_qs = template_qs.filter(is_active=True)
            report_qs = report_qs.filter(source_template__is_active=True)
        elif active == "no":
            template_qs = template_qs.filter(is_active=False)
            report_qs = report_qs.filter(source_template__is_active=False)
        decision_status = request.GET.get("decision_status", "").strip()
        if decision_status:
            report_qs = report_qs.filter(decision_status=decision_status)
        rows, _reports = _template_usage_rows(template_qs, report_qs)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="decision_rule_report_template_usage.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "template_title",
                "template_type",
                "active",
                "reports_created",
                "keep",
                "roll_back",
                "watch",
                "archived",
                "undecided",
                "avg_snapshots",
                "avg_presets",
                "last_report_title",
                "last_report_updated",
            ]
        )
        for row in rows:
            last = row["last_report"]
            writer.writerow(
                [
                    row["template"].title,
                    row["template"].get_template_type_display(),
                    "yes" if row["template"].is_active else "no",
                    row["total_reports"],
                    row["keep_count"],
                    row["roll_back_count"],
                    row["watch_count"],
                    row["archived_count"],
                    row["undecided_count"],
                    row["avg_snapshots"],
                    row["avg_presets"],
                    last.title if last else "",
                    timezone.localtime(last.updated_at).strftime("%Y-%m-%d %H:%M")
                    if last
                    else "",
                ]
            )
        return response


class ExperimentDecisionTuningSnapshotComparisonReportListView(
    StaffRequiredMixin, ListView
):
    model = ExperimentDecisionTuningSnapshotComparisonReport
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_reports.html"
    context_object_name = "reports"

    def get_queryset(self):
        qs = ExperimentDecisionTuningSnapshotComparisonReport.objects.prefetch_related(
            "snapshots"
        ).select_related(
            "created_by",
            "updated_by",
            "decision_owner",
            "decision_recorded_by",
            "cloned_from",
            "source_template",
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(notes__icontains=q)
                | Q(decision_summary__icontains=q)
                | Q(decision_notes__icontains=q)
            )
        decision_status = self.request.GET.get("decision_status", "").strip()
        if decision_status:
            qs = qs.filter(decision_status=decision_status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["decision_status"] = self.request.GET.get("decision_status", "").strip()
        context["decision_status_choices"] = (
            ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.choices
        )
        context["report_count"] = (
            context["reports"].count()
            if hasattr(context["reports"], "count")
            else len(context["reports"])
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportCreateView(
    StaffRequiredMixin, CreateView
):
    model = ExperimentDecisionTuningSnapshotComparisonReport
    form_class = ExperimentDecisionTuningSnapshotComparisonReportForm
    template_name = (
        "studio/experiment_decision_tuning_snapshot_comparison_report_form.html"
    )

    def get_initial(self):
        initial = super().get_initial()
        snapshot_ids = self.request.GET.getlist("snapshots")
        if not snapshot_ids:
            snapshot_ids = [
                str(pk)
                for pk in ExperimentDecisionTuningExperimentSnapshot.objects.order_by(
                    "-generated_at", "-pk"
                ).values_list("pk", flat=True)[:3]
            ]
        initial["snapshots"] = snapshot_ids
        initial["preset_keys"] = self.request.GET.getlist("preset_keys")
        initial["title"] = self.request.GET.get(
            "title", "Decision-rule snapshot comparison"
        )
        return initial

    def form_valid(self, form):
        form.instance.created_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        form.instance.updated_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        if form.instance.has_recorded_decision:
            form.instance.decision_recorded_by = (
                self.request.user if self.request.user.is_authenticated else None
            )
            form.instance.decision_recorded_at = timezone.now()
        messages.success(self.request, "Saved snapshot comparison report.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "studio:experiment-decision-tuning-snapshot-comparison-report-detail",
            kwargs={"pk": self.object.pk},
        )


class ExperimentDecisionTuningSnapshotComparisonReportUpdateView(
    StaffRequiredMixin, UpdateView
):
    model = ExperimentDecisionTuningSnapshotComparisonReport
    form_class = ExperimentDecisionTuningSnapshotComparisonReportForm
    template_name = (
        "studio/experiment_decision_tuning_snapshot_comparison_report_form.html"
    )

    def form_valid(self, form):
        previous = self.get_object()
        form.instance.updated_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        decision_fields = (
            "decision_status",
            "decision_summary",
            "decision_notes",
            "decision_owner",
        )
        decision_changed = any(
            getattr(previous, field) != getattr(form.instance, field)
            for field in decision_fields
        )
        if decision_changed and form.instance.has_recorded_decision:
            form.instance.decision_recorded_by = (
                self.request.user if self.request.user.is_authenticated else None
            )
            form.instance.decision_recorded_at = timezone.now()
        elif (
            form.instance.decision_status
            == ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.UNDECIDED
        ):
            form.instance.decision_recorded_by = None
            form.instance.decision_recorded_at = None
        messages.success(self.request, "Updated snapshot comparison report.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "studio:experiment-decision-tuning-snapshot-comparison-report-detail",
            kwargs={"pk": self.object.pk},
        )


class ExperimentDecisionTuningSnapshotComparisonReportCloneView(
    StaffRequiredMixin, FormView
):
    template_name = (
        "studio/experiment_decision_tuning_snapshot_comparison_report_clone.html"
    )
    form_class = ExperimentDecisionTuningSnapshotComparisonReportCloneForm

    def dispatch(self, request, *args, **kwargs):
        self.source_report = get_object_or_404(
            ExperimentDecisionTuningSnapshotComparisonReport.objects.prefetch_related(
                "snapshots"
            ),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            "title": f"Copy of {self.source_report.title}",
            "description": self.source_report.description,
            "notes": self.source_report.notes,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["source_report"] = self.source_report
        context["source_snapshots"] = list(
            self.source_report.snapshots.select_related("change_log").order_by(
                "-generated_at", "-pk"
            )
        )
        context["source_preset_count"] = len(self.source_report.preset_keys or [])
        return context

    @transaction.atomic
    def form_valid(self, form):
        cloned_report = ExperimentDecisionTuningSnapshotComparisonReport.objects.create(
            title=form.cleaned_data["title"],
            description=form.cleaned_data.get("description", ""),
            notes=form.cleaned_data.get("notes", ""),
            preset_keys=list(self.source_report.preset_keys or []),
            cloned_from=self.source_report,
            source_template=self.source_report.source_template,
            created_by=self.request.user
            if self.request.user.is_authenticated
            else None,
            updated_by=self.request.user
            if self.request.user.is_authenticated
            else None,
            decision_status=ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.UNDECIDED,
        )
        cloned_report.snapshots.set(self.source_report.snapshots.all())
        messages.success(
            self.request,
            "Cloned saved snapshot comparison report. Decision fields were reset for the new report.",
        )
        self.object = cloned_report
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "studio:experiment-decision-tuning-snapshot-comparison-report-detail",
            kwargs={"pk": self.object.pk},
        )


class ExperimentDecisionTuningSnapshotComparisonReportDetailView(
    StaffRequiredMixin, DetailView
):
    model = ExperimentDecisionTuningSnapshotComparisonReport
    template_name = (
        "studio/experiment_decision_tuning_snapshot_comparison_report_detail.html"
    )
    context_object_name = "report"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("snapshots__change_log")
            .select_related(
                "created_by",
                "updated_by",
                "decision_owner",
                "decision_recorded_by",
                "cloned_from",
                "source_template",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        snapshots = list(
            self.object.snapshots.select_related("change_log", "generated_by").order_by(
                "-generated_at", "-pk"
            )
        )
        comparison = _decision_rule_snapshot_comparison(
            snapshots, preset_keys=self.object.preset_keys or []
        )
        context["snapshots"] = snapshots
        context["comparison"] = comparison
        context["comparison_charts"] = _decision_rule_snapshot_comparison_charts(
            comparison
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportPrintView(
    ExperimentDecisionTuningSnapshotComparisonReportDetailView
):
    """Clean, standalone report view intended for browser printing or saving to PDF."""

    template_name = (
        "studio/experiment_decision_tuning_snapshot_comparison_report_print.html"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["generated_at"] = timezone.now()
        context["print_summary_cards"] = _printable_decision_rule_report_summary(
            context["comparison"], context["comparison_charts"]
        )
        return context


class ExperimentDecisionTuningSnapshotComparisonReportDeleteView(
    StaffRequiredMixin, DeleteView
):
    model = ExperimentDecisionTuningSnapshotComparisonReport
    template_name = "studio/experiment_decision_tuning_snapshot_comparison_report_confirm_delete.html"
    success_url = reverse_lazy(
        "studio:experiment-decision-tuning-snapshot-comparison-reports"
    )

    def form_valid(self, form):
        messages.success(self.request, "Deleted saved snapshot comparison report.")
        return super().form_valid(form)


class ExperimentDecisionTuningSnapshotComparisonReportExportView(
    StaffRequiredMixin, DetailView
):
    model = ExperimentDecisionTuningSnapshotComparisonReport

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("snapshots__change_log")
            .select_related("decision_owner", "decision_recorded_by")
        )

    def get(self, request, *args, **kwargs):
        report = self.get_object()
        snapshots = list(
            report.snapshots.select_related("change_log", "generated_by").order_by(
                "-generated_at", "-pk"
            )
        )
        comparison = _decision_rule_snapshot_comparison(
            snapshots, preset_keys=report.preset_keys or []
        )
        safe_id = f"{report.pk}"
        response = _csv_response(
            f"code-with-michael-saved-decision-rule-comparison-{safe_id}.csv"
        )
        writer = csv.writer(response)

        writer.writerow(["Saved comparison report"])
        writer.writerow(["title", report.title])
        writer.writerow(["description", report.description])
        writer.writerow(["created_at", report.created_at.isoformat()])
        writer.writerow(["updated_at", report.updated_at.isoformat()])
        writer.writerow(["notes", report.notes])
        writer.writerow(["decision_status", report.get_decision_status_display()])
        writer.writerow(["decision_summary", report.decision_summary])
        writer.writerow(["decision_notes", report.decision_notes])
        writer.writerow(
            [
                "decision_owner",
                report.decision_owner.get_full_name() or report.decision_owner.email
                if report.decision_owner
                else "",
            ]
        )
        writer.writerow(
            [
                "decision_recorded_by",
                report.decision_recorded_by.get_full_name()
                or report.decision_recorded_by.email
                if report.decision_recorded_by
                else "",
            ]
        )
        writer.writerow(
            [
                "decision_recorded_at",
                report.decision_recorded_at.isoformat()
                if report.decision_recorded_at
                else "",
            ]
        )

        writer.writerow([])
        writer.writerow(["Summary comparison"])
        writer.writerow(
            ["metric"]
            + [
                f"{card['snapshot'].experiment_label} ({card['snapshot'].window_days}d)"
                for card in comparison["snapshot_cards"]
            ]
        )
        for row in comparison["summary_rows"]:
            writer.writerow([row["label"]] + [cell["change"] for cell in row["cells"]])

        writer.writerow([])
        writer.writerow(["Decision recommendations"])
        writer.writerow(
            [
                "snapshot",
                "window_days",
                "rules_profile",
                "recommendation",
                "confidence",
                "score",
                "summary",
            ]
        )
        for card in comparison["snapshot_cards"]:
            for rec_row in card["recommendations"]:
                rec = rec_row["recommendation"]
                writer.writerow(
                    [
                        card["snapshot"].experiment_label,
                        card["snapshot"].window_days,
                        rec_row["profile"]["label"],
                        rec.label,
                        rec.confidence,
                        rec.score,
                        rec.summary,
                    ]
                )

        writer.writerow([])
        writer.writerow(["Metric comparison"])
        writer.writerow(
            ["section", "metric"]
            + [
                f"{card['snapshot'].experiment_label} change"
                for card in comparison["snapshot_cards"]
            ]
        )
        for row in comparison["metric_rows"]:
            writer.writerow(
                [row["section_label"], row["metric_label"]]
                + [cell["change"] for cell in row["cells"]]
            )

        charts = _decision_rule_snapshot_comparison_charts(comparison)
        writer.writerow([])
        writer.writerow(["Chart data - decision counts"])
        writer.writerow(["recommendation", "count"])
        for row in charts["decision_count_chart"]:
            writer.writerow([row["label"], row["count"]])

        writer.writerow([])
        writer.writerow(["Chart data - top metric deltas"])
        writer.writerow(
            ["section", "metric"]
            + [
                f"{card['snapshot'].experiment_label} change"
                for card in comparison["snapshot_cards"]
            ]
        )
        for row in charts["metric_delta_chart"]:
            writer.writerow(
                [row["section_label"], row["metric_label"]]
                + [cell["display"] for cell in row["bars"]]
            )
        return response


class RecommendationTuningSimulationView(StaffRequiredMixin, FormView):
    template_name = "studio/recommendation_tuning_simulation.html"
    form_class = RecommendationTuningSimulationForm

    def get_initial(self):
        initial = super().get_initial()
        first_resource = LearningResource.objects.order_by("title").first()
        if first_resource:
            initial["resource"] = first_resource.pk
        initial["limit"] = 8
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        if form and form.is_bound and form.is_valid():
            resource = form.cleaned_data.get("resource")
            selected_keys = form.cleaned_data.get("preset_keys") or [
                preset.key for preset in PRESETS
            ]
            limit = form.cleaned_data.get("limit") or 8
        else:
            resource = form.initial.get("resource") if form else None
            if isinstance(resource, int):
                resource = LearningResource.objects.filter(pk=resource).first()
            selected_keys = [preset.key for preset in PRESETS]
            limit = 8

        simulations = []
        if resource:
            active_tuning = RecommendationTuning.get_active()
            simulations.append(
                {
                    "name": f"Active: {active_tuning.name}",
                    "description": active_tuning.notes
                    or "Current saved recommendation tuning profile.",
                    "preset_key": "active",
                    "is_active": True,
                    "recommendations": build_resource_cta_recommendations(
                        resource, limit=limit, tuning=active_tuning
                    ),
                }
            )
            for key in selected_keys:
                preset = get_preset(key)
                if not preset:
                    continue
                simulated_tuning = build_tuning_from_preset_key(key)
                simulations.append(
                    {
                        "name": preset.name,
                        "description": preset.description,
                        "preset_key": preset.key,
                        "is_active": False,
                        "recommendations": build_resource_cta_recommendations(
                            resource, limit=limit, tuning=simulated_tuning
                        ),
                    }
                )

        context["resource"] = resource
        context["simulations"] = simulations
        context["presets"] = PRESETS
        context["preset_rows"] = preset_rows()
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


@staff_required
@require_POST
def apply_recommendation_tuning_preset(request):
    preset = get_preset(request.POST.get("preset_key", ""))
    if not preset:
        messages.error(request, "Choose a valid tuning preset.")
        return redirect("studio:recommendation-tuning")
    apply_preset_to_active_tuning(
        preset,
        changed_by=request.user,
        reason=request.POST.get("change_reason", "")
        or "Applied recommendation tuning preset.",
        request_path=request.path,
        experiment_label=request.POST.get("experiment_label", ""),
        experiment_status=request.POST.get("experiment_status", "")
        or RecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        experiment_notes=request.POST.get("experiment_notes", ""),
    )
    messages.success(
        request, f"Applied the {preset.name} recommendation tuning preset."
    )
    next_url = request.POST.get("next") or reverse("studio:recommendation-tuning")
    return redirect(next_url)


class RecommendationTuningRollbackView(StaffRequiredMixin, DetailView):
    model = RecommendationTuningChangeLog
    template_name = "studio/recommendation_tuning_rollback.html"
    context_object_name = "change_log"

    def post(self, request, *args, **kwargs):
        change_log = self.get_object()
        snapshot = request.POST.get("snapshot", "before")
        if snapshot not in {"before", "after"}:
            messages.error(request, "Choose a valid tuning snapshot to restore.")
            return redirect("studio:recommendation-tuning-rollback", pk=change_log.pk)
        restore_tuning_snapshot(
            change_log,
            snapshot=snapshot,
            changed_by=request.user,
            reason=request.POST.get("rollback_reason", ""),
            request_path=request.path,
        )
        label = "before-change" if snapshot == "before" else "after-change"
        messages.success(
            request,
            f"Restored the {label} recommendation tuning snapshot and logged the rollback.",
        )
        return redirect("studio:recommendation-tuning-history")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active = RecommendationTuning.get_active()
        context["active_tuning"] = active
        context["active_snapshot"] = tuning_snapshot(active)
        context["tracked_fields"] = [
            {
                "name": field,
                "active": context["active_snapshot"].get(field),
                "before": self.object.before.get(field),
                "after": self.object.after.get(field),
            }
            for field in context["active_snapshot"].keys()
        ]
        return context


class RecommendationTuningHistoryView(StaffRequiredMixin, ListView):
    model = RecommendationTuningChangeLog
    template_name = "studio/recommendation_tuning_history.html"
    context_object_name = "change_logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = RecommendationTuningChangeLog.objects.select_related(
            "tuning", "changed_by"
        )
        action = self.request.GET.get("action", "")
        status = self.request.GET.get("experiment_status", "")
        outcome = self.request.GET.get("experiment_outcome", "")
        label = self.request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        return queryset.order_by("-created_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = RecommendationTuningChangeLog.Action.choices
        context["experiment_statuses"] = (
            RecommendationTuningChangeLog.ExperimentStatus.choices
        )
        context["experiment_outcomes"] = (
            RecommendationTuningChangeLog.ExperimentOutcome.choices
        )
        context["selected_action"] = self.request.GET.get("action", "")
        context["selected_experiment_status"] = self.request.GET.get(
            "experiment_status", ""
        )
        context["selected_experiment_outcome"] = self.request.GET.get(
            "experiment_outcome", ""
        )
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        )
        context["latest_change"] = RecommendationTuningChangeLog.objects.order_by(
            "-created_at", "-pk"
        ).first()
        context["active_experiments"] = RecommendationTuningChangeLog.objects.filter(
            experiment_status__in=[
                RecommendationTuningChangeLog.ExperimentStatus.PLANNED,
                RecommendationTuningChangeLog.ExperimentStatus.RUNNING,
            ]
        ).count()
        context["completed_experiments"] = (
            RecommendationTuningChangeLog.objects.exclude(
                experiment_status=RecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT
            )
            .exclude(
                experiment_outcome=RecommendationTuningChangeLog.ExperimentOutcome.NOT_RECORDED
            )
            .count()
        )
        context["total_changes"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("change_logs", []))
        )
        return context


class RecommendationTuningHistoryExportView(StaffRequiredMixin, ListView):
    model = RecommendationTuningChangeLog

    def get(self, request, *args, **kwargs):
        queryset = RecommendationTuningChangeLog.objects.select_related(
            "tuning", "changed_by"
        ).order_by("-created_at", "-pk")
        action = request.GET.get("action", "")
        status = request.GET.get("experiment_status", "")
        outcome = request.GET.get("experiment_outcome", "")
        label = request.GET.get("experiment_label", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if status:
            queryset = queryset.filter(experiment_status=status)
        if outcome:
            queryset = queryset.filter(experiment_outcome=outcome)
        if label:
            queryset = queryset.filter(experiment_label__icontains=label)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="recommendation_tuning_change_history.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "created_at",
                "action",
                "tuning_profile",
                "changed_by",
                "preset_key",
                "preset_name",
                "changed_fields",
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "experiment_notes",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "diff_json",
                "reason",
                "request_path",
            ]
        )
        for log in queryset:
            writer.writerow(
                [
                    log.created_at.isoformat(),
                    log.get_action_display(),
                    log.tuning.name if log.tuning_id else "",
                    getattr(log.changed_by, "email", "") or "",
                    log.preset_key,
                    log.preset_name,
                    log.changed_field_count,
                    log.experiment_label,
                    log.get_experiment_status_display(),
                    log.get_experiment_outcome_display(),
                    log.experiment_notes,
                    log.outcome_recorded_at.isoformat()
                    if log.outcome_recorded_at
                    else "",
                    getattr(log.outcome_recorded_by, "email", "") or "",
                    json.dumps(log.diff, sort_keys=True),
                    log.reason,
                    log.request_path,
                ]
            )
        return response


class RecommendationTuningExperimentOutcomeView(StaffRequiredMixin, UpdateView):
    model = RecommendationTuningChangeLog
    form_class = RecommendationTuningExperimentOutcomeForm
    template_name = "studio/recommendation_tuning_experiment_form.html"
    context_object_name = "change_log"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.outcome_recorded_at = timezone.now()
        self.object.outcome_recorded_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        self.object.save(
            update_fields=[
                "experiment_label",
                "experiment_status",
                "experiment_outcome",
                "experiment_notes",
                "outcome_recorded_at",
                "outcome_recorded_by",
                "updated_at",
            ]
        )
        messages.success(self.request, "Tuning experiment outcome saved.")
        return redirect("studio:recommendation-tuning-history")

    def get_success_url(self):
        return reverse("studio:recommendation-tuning-history")


class RecommendationTuningExperimentSnapshotListView(StaffRequiredMixin, ListView):
    model = RecommendationTuningExperimentSnapshot
    template_name = "studio/recommendation_tuning_experiment_snapshots.html"
    context_object_name = "snapshots"
    paginate_by = 30

    def get_queryset(self):
        queryset = RecommendationTuningExperimentSnapshot.objects.select_related(
            "change_log", "change_log__tuning", "generated_by"
        )
        label = self.request.GET.get("experiment_label", "").strip()
        window_days = self.request.GET.get("window_days", "").strip()
        if label:
            queryset = queryset.filter(change_log__experiment_label__icontains=label)
        if window_days.isdigit():
            queryset = queryset.filter(window_days=int(window_days))
        return queryset.order_by("-generated_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_experiment_label"] = self.request.GET.get(
            "experiment_label", ""
        ).strip()
        context["selected_window_days"] = self.request.GET.get(
            "window_days", ""
        ).strip()
        context["window_choices"] = [7, 14, 30, 60]
        context["snapshot_count"] = (
            context.get("paginator").count
            if context.get("paginator")
            else len(context.get("snapshots", []))
        )
        context["latest_snapshot"] = (
            RecommendationTuningExperimentSnapshot.objects.order_by(
                "-generated_at"
            ).first()
        )
        return context


class RecommendationTuningExperimentSnapshotCreateView(StaffRequiredMixin, DetailView):
    model = RecommendationTuningChangeLog
    template_name = "studio/recommendation_tuning_experiment_snapshot_form.html"
    context_object_name = "change_log"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = (
            kwargs.get("form") or RecommendationTuningExperimentSnapshotForm()
        )
        context["existing_snapshots"] = (
            self.object.performance_snapshots.select_related("generated_by")[:10]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = RecommendationTuningExperimentSnapshotForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        snapshot = create_experiment_snapshot(
            change_log=self.object,
            window_days=form.cleaned_data["window_days"],
            generated_by=request.user if request.user.is_authenticated else None,
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(request, "Experiment performance snapshot created.")
        return redirect(
            "studio:recommendation-tuning-experiment-snapshot-detail", pk=snapshot.pk
        )


class RecommendationTuningExperimentSnapshotDetailView(StaffRequiredMixin, DetailView):
    model = RecommendationTuningExperimentSnapshot
    template_name = "studio/recommendation_tuning_experiment_snapshot_detail.html"
    context_object_name = "snapshot"

    def get_queryset(self):
        return RecommendationTuningExperimentSnapshot.objects.select_related(
            "change_log", "change_log__tuning", "generated_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metric_rows"] = snapshot_section_rows(self.object)
        context["sections"] = _group_snapshot_rows_by_section(context["metric_rows"])
        context["decision_recommendation"] = recommend_experiment_decision(self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        if action != "apply_decision_recommendation":
            messages.error(request, "Unknown snapshot action.")
            return redirect(
                "studio:recommendation-tuning-experiment-snapshot-detail",
                pk=self.object.pk,
            )
        apply_decision_to_change_log(
            snapshot=self.object,
            user=request.user if request.user.is_authenticated else None,
            note=request.POST.get("decision_note", "").strip(),
        )
        messages.success(
            request, "Decision recommendation recorded on the tuning experiment."
        )
        return redirect(
            "studio:recommendation-tuning-experiment-snapshot-detail", pk=self.object.pk
        )


class RecommendationTuningExperimentSnapshotExportView(StaffRequiredMixin, DetailView):
    model = RecommendationTuningExperimentSnapshot

    def get(self, request, *args, **kwargs):
        snapshot = self.get_object()
        filename = f"code-with-michael-tuning-experiment-snapshot-{snapshot.pk}.csv"
        response = _csv_response(filename)
        recommendation = recommend_report_template_tuning_decision(snapshot)
        writer = csv.writer(response)
        writer.writerow(["decision_recommendation", recommendation.label])
        writer.writerow(["decision_confidence", recommendation.confidence])
        writer.writerow(["decision_score", recommendation.score])
        writer.writerow(["decision_summary", recommendation.summary])
        writer.writerow([])
        writer.writerow(["Weighted signals"])
        writer.writerow(
            ["section", "metric", "change", "weight", "contribution", "direction"]
        )
        for signal in recommendation.weighted_signals:
            writer.writerow(
                [
                    signal.get("section"),
                    signal.get("metric"),
                    signal.get("change"),
                    signal.get("weight"),
                    signal.get("contribution"),
                    signal.get("direction"),
                ]
            )
        writer.writerow([])
        writer.writerow(["Snapshot metrics"])
        writer.writerow(
            [
                "experiment_label",
                "generated_at",
                "window_days",
                "before_start",
                "before_end",
                "after_start",
                "after_end",
                "section",
                "metric",
                "before",
                "after",
                "change",
                "percent_change",
            ]
        )
        for row in snapshot_section_rows(snapshot):
            writer.writerow(
                [
                    snapshot.experiment_label,
                    snapshot.generated_at.isoformat(),
                    snapshot.window_days,
                    snapshot.before_start.isoformat(),
                    snapshot.before_end.isoformat(),
                    snapshot.after_start.isoformat(),
                    snapshot.after_end.isoformat(),
                    row["section_label"],
                    row["metric_label"],
                    row["before"],
                    row["after"],
                    row["change"],
                    row["pct"] if row["pct"] is not None else "",
                ]
            )
        return response


def _group_snapshot_rows_by_section(rows):
    sections = []
    by_key = {}
    for row in rows:
        section = by_key.setdefault(
            row["section_key"],
            {"key": row["section_key"], "label": row["section_label"], "rows": []},
        )
        section["rows"].append(row)
    for key in ["social", "resources", "newsletter", "ctas", "conversions"]:
        if key in by_key:
            sections.append(by_key[key])
    for key, section in by_key.items():
        if key not in {"social", "resources", "newsletter", "ctas", "conversions"}:
            sections.append(section)
    return sections


def _selected_decision_rule_snapshots(form):
    if form.is_valid() and form.cleaned_data.get("snapshots"):
        return list(form.cleaned_data["snapshots"])
    return list(
        ExperimentDecisionTuningExperimentSnapshot.objects.select_related(
            "change_log", "generated_by"
        ).order_by("-generated_at", "-pk")[:3]
    )


def _decision_rule_snapshot_comparison(snapshots, preset_keys=None):
    active_tuning = ExperimentDecisionTuning.get_active()
    profiles = [
        {
            "key": "active",
            "label": f"Active: {active_tuning.name}",
            "tuning": active_tuning,
        }
    ]
    for key in preset_keys or []:
        try:
            preset = get_decision_preset(key)
            profiles.append(
                {
                    "key": key,
                    "label": preset.name,
                    "tuning": build_decision_tuning_from_preset_key(key),
                }
            )
        except KeyError:
            continue

    metric_index = {}
    snapshot_cards = []
    for snapshot in snapshots:
        rows = snapshot_section_rows(snapshot)
        row_lookup = {}
        for row in rows:
            metric_key = f"{row['section_key']}::{row['metric_key']}"
            metric_index.setdefault(
                metric_key,
                {
                    "section_key": row["section_key"],
                    "section_label": row["section_label"],
                    "metric_key": row["metric_key"],
                    "metric_label": row["metric_label"],
                    "is_percent_metric": row["is_percent_metric"],
                },
            )
            row_lookup[metric_key] = row
        recommendations = []
        for profile in profiles:
            recommendations.append(
                {
                    "profile": profile,
                    "recommendation": recommend_experiment_decision(
                        snapshot, tuning=profile["tuning"]
                    ),
                }
            )
        snapshot_cards.append(
            {
                "snapshot": snapshot,
                "rows": row_lookup,
                "recommendations": recommendations,
                "active_tuning": active_tuning,
            }
        )

    metric_rows = []
    preferred = ["social", "resources", "newsletter", "ctas", "conversions"]

    def sort_key(item):
        key, meta = item
        try:
            section_order = preferred.index(meta["section_key"])
        except ValueError:
            section_order = len(preferred)
        return (section_order, meta["metric_label"])

    for metric_key, meta in sorted(metric_index.items(), key=sort_key):
        cells = []
        for card in snapshot_cards:
            row = card["rows"].get(metric_key, {})
            cells.append(
                {
                    "snapshot": card["snapshot"],
                    "before": row.get("before"),
                    "after": row.get("after"),
                    "change": row.get("change"),
                    "pct": row.get("pct"),
                }
            )
        metric_rows.append({**meta, "cells": cells})

    summary_keys = [
        ("primary_social_delta", "Follower growth"),
        ("primary_resource_delta", "Resource downloads"),
        ("primary_newsletter_delta", "Newsletter clicks"),
        ("primary_cta_delta", "CTA clicks"),
        ("primary_conversion_delta", "Learner conversions"),
    ]
    summary_rows = []
    for key, label in summary_keys:
        summary_rows.append(
            {
                "key": key,
                "label": label,
                "cells": [
                    {
                        "snapshot": card["snapshot"],
                        "change": (card["snapshot"].summary or {})
                        .get(key, {})
                        .get("change", 0),
                        "pct": (card["snapshot"].summary or {}).get(key, {}).get("pct"),
                    }
                    for card in snapshot_cards
                ],
            }
        )

    return {
        "profiles": profiles,
        "snapshot_cards": snapshot_cards,
        "metric_rows": metric_rows,
        "summary_rows": summary_rows,
    }


def _coerce_chart_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _chart_tone(value):
    value = _coerce_chart_number(value)
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def _chart_width(value, maximum):
    value = abs(_coerce_chart_number(value))
    maximum = abs(_coerce_chart_number(maximum))
    if maximum <= 0:
        return 2
    return max(4, min(100, round((value / maximum) * 100)))


def _decision_rule_snapshot_comparison_charts(comparison):
    """Build lightweight chart data for visual saved-report and comparison views."""
    snapshot_cards = comparison.get("snapshot_cards", [])
    summary_rows = comparison.get("summary_rows", [])
    metric_rows = comparison.get("metric_rows", [])

    max_summary = max(
        [
            abs(_coerce_chart_number(cell.get("change")))
            for row in summary_rows
            for cell in row.get("cells", [])
        ]
        or [0]
    )
    summary_chart = []
    for row in summary_rows:
        summary_chart.append(
            {
                "label": row.get("label", ""),
                "bars": [
                    {
                        "snapshot": cell.get("snapshot"),
                        "label": getattr(
                            cell.get("snapshot"), "experiment_label", "Snapshot"
                        ),
                        "value": _coerce_chart_number(cell.get("change")),
                        "display": cell.get("change", 0),
                        "pct": cell.get("pct"),
                        "width": _chart_width(cell.get("change"), max_summary),
                        "tone": _chart_tone(cell.get("change")),
                    }
                    for cell in row.get("cells", [])
                ],
            }
        )

    score_values = [
        abs(_coerce_chart_number(item["recommendation"].score))
        for card in snapshot_cards
        for item in card.get("recommendations", [])
    ]
    max_score = max(score_values or [0])
    decision_score_chart = []
    for card in snapshot_cards:
        decision_score_chart.append(
            {
                "snapshot": card.get("snapshot"),
                "label": getattr(card.get("snapshot"), "experiment_label", "Snapshot"),
                "scores": [
                    {
                        "profile": item["profile"],
                        "recommendation": item["recommendation"],
                        "score": _coerce_chart_number(item["recommendation"].score),
                        "width": _chart_width(item["recommendation"].score, max_score),
                        "tone": item["recommendation"].css_class,
                    }
                    for item in card.get("recommendations", [])
                ],
            }
        )

    ranked_metric_rows = sorted(
        metric_rows,
        key=lambda row: sum(
            abs(_coerce_chart_number(cell.get("change")))
            for cell in row.get("cells", [])
        ),
        reverse=True,
    )[:10]
    max_metric = max(
        [
            abs(_coerce_chart_number(cell.get("change")))
            for row in ranked_metric_rows
            for cell in row.get("cells", [])
        ]
        or [0]
    )
    metric_delta_chart = []
    for row in ranked_metric_rows:
        metric_delta_chart.append(
            {
                "section_label": row.get("section_label", ""),
                "metric_label": row.get("metric_label", ""),
                "is_percent_metric": row.get("is_percent_metric", False),
                "bars": [
                    {
                        "snapshot": cell.get("snapshot"),
                        "label": getattr(
                            cell.get("snapshot"), "experiment_label", "Snapshot"
                        ),
                        "value": _coerce_chart_number(cell.get("change")),
                        "display": cell.get("change", 0),
                        "pct": cell.get("pct"),
                        "width": _chart_width(cell.get("change"), max_metric),
                        "tone": _chart_tone(cell.get("change")),
                    }
                    for cell in row.get("cells", [])
                ],
            }
        )

    decision_counts = {}
    for card in snapshot_cards:
        for item in card.get("recommendations", []):
            label = item["recommendation"].label
            css_class = item["recommendation"].css_class
            if label not in decision_counts:
                decision_counts[label] = {
                    "label": label,
                    "css_class": css_class,
                    "count": 0,
                }
            decision_counts[label]["count"] += 1
    max_decision_count = max([row["count"] for row in decision_counts.values()] or [0])
    decision_count_chart = [
        {**row, "width": _chart_width(row["count"], max_decision_count)}
        for row in sorted(
            decision_counts.values(), key=lambda row: (-row["count"], row["label"])
        )
    ]

    return {
        "summary_chart": summary_chart,
        "decision_score_chart": decision_score_chart,
        "metric_delta_chart": metric_delta_chart,
        "decision_count_chart": decision_count_chart,
    }


def _printable_decision_rule_report_summary(comparison, charts):
    """Build short report highlights for the printable saved-comparison view."""
    snapshot_count = len(comparison.get("snapshot_cards", []))
    profile_count = len(comparison.get("profiles", []))
    top_metric = (charts.get("metric_delta_chart") or [None])[0]
    top_metric_label = "No major metric movement"
    if top_metric:
        top_metric_label = f"{top_metric.get('section_label', '')}: {top_metric.get('metric_label', '')}".strip(
            ": "
        )
    top_decision = (charts.get("decision_count_chart") or [None])[0]
    top_decision_label = (
        top_decision.get("label") if top_decision else "No decision available"
    )
    return [
        {"label": "Snapshots compared", "value": snapshot_count},
        {"label": "Decision profiles", "value": profile_count},
        {"label": "Most common recommendation", "value": top_decision_label},
        {"label": "Largest movement", "value": top_metric_label},
    ]


class ContentCalendarView(StaffRequiredMixin, TemplateView):
    template_name = "studio/content_calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lessons = Lesson.objects.select_related("category", "series").prefetch_related(
            "assets", "captions"
        )
        status_order = [choice[0] for choice in Lesson.Status.choices]
        status_labels = dict(Lesson.Status.choices)
        columns = []
        for status in status_order:
            items = [lesson for lesson in lessons if lesson.status == status]
            columns.append(
                {"status": status, "label": status_labels[status], "lessons": items}
            )
        platform_backlog = []
        for lesson in lessons:
            missing = []
            if lesson.facebook_status not in {
                Lesson.Status.READY,
                Lesson.Status.PUBLISHED,
            }:
                missing.append("Facebook")
            if lesson.instagram_status not in {
                Lesson.Status.READY,
                Lesson.Status.PUBLISHED,
            }:
                missing.append("Instagram")
            if lesson.threads_status not in {
                Lesson.Status.READY,
                Lesson.Status.PUBLISHED,
            }:
                missing.append("Threads")
            if lesson.website_status not in {
                Lesson.Status.READY,
                Lesson.Status.PUBLISHED,
            }:
                missing.append("Website")
            if missing:
                platform_backlog.append({"lesson": lesson, "missing": missing})
        context["columns"] = columns
        context["platform_backlog"] = platform_backlog[:20]
        context["recent_publishing_records"] = PublishingRecord.objects.select_related(
            "lesson"
        ).order_by("-published_at")[:20]
        context["upcoming_content_plans"] = (
            ContentPlan.objects.select_related("lesson", "caption", "graphic")
            .filter(scheduled_at__gte=timezone.now())
            .order_by("scheduled_at")[:20]
        )
        context["platform_metrics"] = (
            PublishingRecord.objects.values("platform")
            .annotate(
                posts=Count("id"),
                impressions=Sum("impressions"),
                reach=Sum("reach"),
                likes=Sum("likes"),
                comments=Sum("comments"),
                saves=Sum("saves"),
                shares=Sum("shares"),
                clicks=Sum("clicks"),
                new_followers=Sum("new_followers"),
            )
            .order_by("platform")
        )
        return context


def _planner_week_bounds(request):
    raw_week = request.GET.get("week", "").strip()
    today = timezone.localdate()
    try:
        selected = datetime.strptime(raw_week, "%Y-%m-%d").date() if raw_week else today
    except ValueError:
        selected = today
    week_start = selected - timedelta(days=selected.weekday())
    week_end = week_start + timedelta(days=6)
    start_dt = timezone.make_aware(datetime.combine(week_start, time.min))
    end_dt = timezone.make_aware(
        datetime.combine(week_end + timedelta(days=1), time.min)
    )
    return week_start, week_end, start_dt, end_dt


class ContentPlannerView(StaffRequiredMixin, TemplateView):
    template_name = "studio/content_planner.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        week_start, week_end, start_dt, end_dt = _planner_week_bounds(self.request)
        plans = (
            ContentPlan.objects.filter(
                scheduled_at__gte=start_dt, scheduled_at__lt=end_dt
            )
            .select_related(
                "lesson",
                "lesson__category",
                "lesson__series",
                "caption",
                "graphic",
                "publishing_record",
            )
            .order_by("scheduled_at", "platform")
        )
        days = []
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            day_plans = [
                plan
                for plan in plans
                if timezone.localtime(plan.scheduled_at).date() == day
            ]
            days.append({"date": day, "plans": day_plans})

        unscheduled_ready_lessons = (
            Lesson.objects.filter(
                status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED]
            )
            .exclude(
                content_plans__scheduled_at__gte=start_dt,
                content_plans__scheduled_at__lt=end_dt,
            )
            .select_related("category", "series")[:12]
        )
        platform_counts = (
            plans.values("platform").annotate(total=Count("id")).order_by("platform")
        )
        status_counts = (
            plans.values("status").annotate(total=Count("id")).order_by("status")
        )
        newsletter_campaigns = (
            NewsletterCampaign.objects.filter(
                scheduled_at__gte=start_dt, scheduled_at__lt=end_dt
            )
            .select_related("lesson", "content_plan", "publishing_record")
            .order_by("scheduled_at", "title")
        )

        context.update(
            {
                "week_start": week_start,
                "week_end": week_end,
                "previous_week": week_start - timedelta(days=7),
                "next_week": week_start + timedelta(days=7),
                "days": days,
                "plans": plans,
                "platform_counts": platform_counts,
                "status_counts": status_counts,
                "unscheduled_ready_lessons": unscheduled_ready_lessons,
                "newsletter_campaigns": newsletter_campaigns,
            }
        )
        return context


REPORT_WINDOW_DAYS = 90


def _report_date_from_query(raw_value):
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _content_plan_for_record(record):
    try:
        return record.content_plan
    except ContentPlan.DoesNotExist:
        return None


def _record_content_format(record):
    plan = _content_plan_for_record(record)
    if plan and plan.carousel_template:
        template = get_social_carousel_template(plan.carousel_template)
        return {
            "key": plan.carousel_template,
            "label": template.name
            if template
            else plan.carousel_template.replace("_", " ").title(),
            "source": "Planned carousel",
        }
    if record.graphic_id and record.graphic and record.graphic.template_id:
        return {
            "key": record.graphic.template.slug,
            "label": record.graphic.template.name,
            "source": "Graphic template",
        }
    if record.caption_id:
        return {"key": "caption_only", "label": "Caption only", "source": "Caption"}
    return {"key": "unspecified", "label": "Unspecified", "source": "Manual entry"}


def _new_report_bucket(label):
    return {
        "label": label,
        "posts": 0,
        "impressions": 0,
        "reach": 0,
        "likes": 0,
        "comments": 0,
        "saves": 0,
        "shares": 0,
        "clicks": 0,
        "new_followers": 0,
        "engagements": 0,
        "engagement_rate": None,
        "followers_per_post": 0,
        "clicks_per_post": 0,
    }


def _add_record_to_bucket(bucket, record):
    bucket["posts"] += 1
    bucket["impressions"] += record.impressions or 0
    bucket["reach"] += record.reach or 0
    bucket["likes"] += record.likes or 0
    bucket["comments"] += record.comments or 0
    bucket["saves"] += record.saves or 0
    bucket["shares"] += record.shares or 0
    bucket["clicks"] += record.clicks or 0
    bucket["new_followers"] += record.new_followers or 0
    bucket["engagements"] += record.engagement_total


def _finalize_report_bucket(bucket):
    denominator = bucket["reach"] or bucket["impressions"]
    if denominator:
        bucket["engagement_rate"] = round(bucket["engagements"] / denominator * 100, 2)
    if bucket["posts"]:
        bucket["followers_per_post"] = round(
            bucket["new_followers"] / bucket["posts"], 2
        )
        bucket["clicks_per_post"] = round(bucket["clicks"] / bucket["posts"], 2)
    return bucket


def _performance_report_window(request):
    today = timezone.localdate()
    default_start = today - timedelta(days=REPORT_WINDOW_DAYS)
    start_date = _report_date_from_query(request.GET.get("start")) or default_start
    end_date = _report_date_from_query(request.GET.get("end")) or today
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


def _performance_report_records(request):
    start_date, end_date = _performance_report_window(request)
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    end_dt = timezone.make_aware(
        datetime.combine(end_date + timedelta(days=1), time.min)
    )
    platform_filter = request.GET.get("platform", "").strip()
    valid_platforms = {choice[0] for choice in PublishingRecord.Platform.choices}

    records = (
        PublishingRecord.objects.filter(
            published_at__gte=start_dt, published_at__lt=end_dt
        )
        .select_related("lesson", "caption", "graphic", "graphic__template")
        .order_by("-published_at")
    )
    if platform_filter in valid_platforms:
        records = records.filter(platform=platform_filter)
    return (
        list(records),
        start_date,
        end_date,
        platform_filter if platform_filter in valid_platforms else "",
    )


def _performance_report_tables(records):
    format_buckets = {}
    platform_buckets = {}
    matrix = {}
    for record in records:
        format_info = _record_content_format(record)
        format_key = format_info["key"]
        format_bucket = format_buckets.setdefault(
            format_key, _new_report_bucket(format_info["label"])
        )
        format_bucket["key"] = format_key
        format_bucket["source"] = format_info["source"]
        _add_record_to_bucket(format_bucket, record)

        platform_label = record.get_platform_display()
        platform_bucket = platform_buckets.setdefault(
            record.platform, _new_report_bucket(platform_label)
        )
        platform_bucket["key"] = record.platform
        _add_record_to_bucket(platform_bucket, record)

        matrix_key = (format_key, record.platform)
        matrix_bucket = matrix.setdefault(
            matrix_key, _new_report_bucket(f"{format_info['label']} · {platform_label}")
        )
        matrix_bucket["format_label"] = format_info["label"]
        matrix_bucket["platform_label"] = platform_label
        _add_record_to_bucket(matrix_bucket, record)

    format_rows = sorted(
        (_finalize_report_bucket(row) for row in format_buckets.values()),
        key=lambda row: (row["new_followers"], row["engagements"], row["posts"]),
        reverse=True,
    )
    platform_rows = sorted(
        (_finalize_report_bucket(row) for row in platform_buckets.values()),
        key=lambda row: row["posts"],
        reverse=True,
    )
    matrix_rows = sorted(
        (_finalize_report_bucket(row) for row in matrix.values()),
        key=lambda row: (row["format_label"], row["platform_label"]),
    )

    totals = _new_report_bucket("Total")
    for record in records:
        _add_record_to_bucket(totals, record)
    _finalize_report_bucket(totals)

    top_records = sorted(
        records,
        key=lambda record: (
            record.new_followers,
            record.engagement_total,
            record.reach or record.impressions,
        ),
        reverse=True,
    )[:10]
    return {
        "totals": totals,
        "format_rows": format_rows,
        "platform_rows": platform_rows,
        "matrix_rows": matrix_rows,
        "top_records": top_records,
    }


def _csv_response(filename):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    return response


class PerformanceReportView(StaffRequiredMixin, TemplateView):
    template_name = "studio/performance_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records, start_date, end_date, platform_filter = _performance_report_records(
            self.request
        )
        tables = _performance_report_tables(records)
        export_query = self.request.GET.urlencode()

        context.update(
            {
                "start_date": start_date,
                "end_date": end_date,
                "platform_filter": platform_filter,
                "platform_choices": PublishingRecord.Platform.choices,
                "records": records,
                "export_query": export_query,
                "report_window_days": REPORT_WINDOW_DAYS,
                **tables,
            }
        )
        return context


class PerformanceReportExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        records, start_date, end_date, platform_filter = _performance_report_records(
            request
        )
        tables = _performance_report_tables(records)
        section = request.GET.get("section", "posts")
        platform_label = platform_filter or "all-platforms"
        filename = f"code-with-michael-performance-{section}-{start_date}-to-{end_date}-{platform_label}.csv"
        response = _csv_response(filename)
        writer = csv.writer(response)

        if section == "formats":
            writer.writerow(
                [
                    "Format",
                    "Source",
                    "Posts",
                    "Impressions",
                    "Reach",
                    "Engagements",
                    "Engagement Rate",
                    "Clicks",
                    "New Followers",
                    "Clicks Per Post",
                    "Followers Per Post",
                ]
            )
            for row in tables["format_rows"]:
                writer.writerow(
                    [
                        row["label"],
                        row.get("source", ""),
                        row["posts"],
                        row["impressions"],
                        row["reach"],
                        row["engagements"],
                        row["engagement_rate"]
                        if row["engagement_rate"] is not None
                        else "",
                        row["clicks"],
                        row["new_followers"],
                        row["clicks_per_post"],
                        row["followers_per_post"],
                    ]
                )
        elif section == "platforms":
            writer.writerow(
                [
                    "Platform",
                    "Posts",
                    "Impressions",
                    "Reach",
                    "Engagements",
                    "Engagement Rate",
                    "Clicks",
                    "New Followers",
                    "Clicks Per Post",
                    "Followers Per Post",
                ]
            )
            for row in tables["platform_rows"]:
                writer.writerow(
                    [
                        row["label"],
                        row["posts"],
                        row["impressions"],
                        row["reach"],
                        row["engagements"],
                        row["engagement_rate"]
                        if row["engagement_rate"] is not None
                        else "",
                        row["clicks"],
                        row["new_followers"],
                        row["clicks_per_post"],
                        row["followers_per_post"],
                    ]
                )
        elif section == "matrix":
            writer.writerow(
                [
                    "Format",
                    "Platform",
                    "Posts",
                    "Impressions",
                    "Reach",
                    "Engagements",
                    "Engagement Rate",
                    "Clicks",
                    "New Followers",
                    "Clicks Per Post",
                    "Followers Per Post",
                ]
            )
            for row in tables["matrix_rows"]:
                writer.writerow(
                    [
                        row["format_label"],
                        row["platform_label"],
                        row["posts"],
                        row["impressions"],
                        row["reach"],
                        row["engagements"],
                        row["engagement_rate"]
                        if row["engagement_rate"] is not None
                        else "",
                        row["clicks"],
                        row["new_followers"],
                        row["clicks_per_post"],
                        row["followers_per_post"],
                    ]
                )
        else:
            writer.writerow(
                [
                    "Published At",
                    "Lesson",
                    "Platform",
                    "Content Format",
                    "Format Source",
                    "Post URL",
                    "Impressions",
                    "Reach",
                    "Likes",
                    "Comments",
                    "Saves",
                    "Shares",
                    "Clicks",
                    "Engagements",
                    "Engagement Rate",
                    "New Followers",
                    "Follower Count After",
                    "Caption",
                    "Notes",
                ]
            )
            for record in records:
                format_info = _record_content_format(record)
                writer.writerow(
                    [
                        timezone.localtime(record.published_at).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        record.lesson.title,
                        record.get_platform_display(),
                        format_info["label"],
                        format_info["source"],
                        record.post_url,
                        record.impressions,
                        record.reach,
                        record.likes,
                        record.comments,
                        record.saves,
                        record.shares,
                        record.clicks,
                        record.engagement_total,
                        record.engagement_rate
                        if record.engagement_rate is not None
                        else "",
                        record.new_followers,
                        record.follower_count_after,
                        record.caption_text,
                        record.notes,
                    ]
                )
        return response


def _resource_report_events(request):
    today = timezone.localdate()
    raw_start = request.GET.get("start") or (today - timedelta(days=30)).isoformat()
    raw_end = request.GET.get("end") or today.isoformat()
    event_type = request.GET.get("event_type", "").strip()
    resource_type = request.GET.get("resource_type", "").strip()

    try:
        start_date = datetime.strptime(raw_start, "%Y-%m-%d").date()
    except ValueError:
        start_date = today - timedelta(days=30)
    try:
        end_date = datetime.strptime(raw_end, "%Y-%m-%d").date()
    except ValueError:
        end_date = today
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    end_dt = timezone.make_aware(
        datetime.combine(end_date + timedelta(days=1), time.min)
    )
    events = ResourcePerformanceEvent.objects.select_related(
        "resource", "subscriber", "user"
    ).filter(
        occurred_at__gte=start_dt,
        occurred_at__lt=end_dt,
    )
    if event_type:
        events = events.filter(event_type=event_type)
    if resource_type:
        events = events.filter(resource__resource_type=resource_type)
    return events, start_date, end_date, event_type, resource_type


def _resource_report_rows(events, start_date, end_date, resource_type=""):
    resources = (
        LearningResource.objects.select_related("category")
        .filter(performance_events__in=events)
        .distinct()
    )
    if resource_type:
        resources = resources.filter(resource_type=resource_type)

    rows = []
    for resource in resources.order_by("resource_type", "title"):
        resource_events = events.filter(resource=resource)
        views = resource_events.filter(
            event_type=ResourcePerformanceEvent.EventType.VIEW
        ).count()
        unlocks = resource_events.filter(
            event_type=ResourcePerformanceEvent.EventType.PDF_UNLOCK
        ).count()
        downloads = resource_events.filter(
            event_type=ResourcePerformanceEvent.EventType.PDF_DOWNLOAD
        ).count()
        active_subscribers = NewsletterSubscriber.objects.filter(
            source_resource=resource,
            status=NewsletterSubscriber.Status.ACTIVE,
            subscribed_at__date__gte=start_date,
            subscribed_at__date__lte=end_date,
        ).count()
        rows.append(
            {
                "resource": resource,
                "views": views,
                "unlocks": unlocks,
                "downloads": downloads,
                "subscribers": active_subscribers,
                "unlock_rate": round(unlocks / views * 100, 2) if views else None,
                "download_rate": round(downloads / views * 100, 2) if views else None,
                "subscriber_rate": round(active_subscribers / views * 100, 2)
                if views
                else None,
            }
        )
    rows.sort(
        key=lambda row: (
            row["subscribers"],
            row["downloads"],
            row["unlocks"],
            row["views"],
        ),
        reverse=True,
    )
    return rows


def _resource_type_summary(resource_rows):
    labels = dict(LearningResource.ResourceType.choices)
    summary = {}
    for row in resource_rows:
        key = row["resource"].resource_type
        bucket = summary.setdefault(
            key,
            {
                "key": key,
                "label": labels.get(key, key),
                "resources": 0,
                "views": 0,
                "unlocks": 0,
                "downloads": 0,
                "subscribers": 0,
            },
        )
        bucket["resources"] += 1
        bucket["views"] += row["views"]
        bucket["unlocks"] += row["unlocks"]
        bucket["downloads"] += row["downloads"]
        bucket["subscribers"] += row["subscribers"]
    rows = []
    for bucket in summary.values():
        views = bucket["views"]
        bucket["unlock_rate"] = (
            round(bucket["unlocks"] / views * 100, 2) if views else None
        )
        bucket["download_rate"] = (
            round(bucket["downloads"] / views * 100, 2) if views else None
        )
        bucket["subscriber_rate"] = (
            round(bucket["subscribers"] / views * 100, 2) if views else None
        )
        rows.append(bucket)
    return sorted(
        rows,
        key=lambda row: (row["subscribers"], row["downloads"], row["views"]),
        reverse=True,
    )


class ResourcePerformanceReportView(StaffRequiredMixin, TemplateView):
    template_name = "studio/resource_performance_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events, start_date, end_date, event_type, resource_type = (
            _resource_report_events(self.request)
        )
        rows = _resource_report_rows(
            events, start_date, end_date, resource_type=resource_type
        )
        totals = {
            "views": sum(row["views"] for row in rows),
            "unlocks": sum(row["unlocks"] for row in rows),
            "downloads": sum(row["downloads"] for row in rows),
            "subscribers": sum(row["subscribers"] for row in rows),
        }
        totals["unlock_rate"] = (
            round(totals["unlocks"] / totals["views"] * 100, 2)
            if totals["views"]
            else None
        )
        totals["download_rate"] = (
            round(totals["downloads"] / totals["views"] * 100, 2)
            if totals["views"]
            else None
        )
        totals["subscriber_rate"] = (
            round(totals["subscribers"] / totals["views"] * 100, 2)
            if totals["views"]
            else None
        )
        context.update(
            {
                "start_date": start_date,
                "end_date": end_date,
                "event_type": event_type,
                "resource_type": resource_type,
                "event_type_choices": ResourcePerformanceEvent.EventType.choices,
                "resource_type_choices": LearningResource.ResourceType.choices,
                "resource_rows": rows,
                "resource_type_rows": _resource_type_summary(rows),
                "totals": totals,
                "recent_events": events.order_by("-occurred_at")[:40],
                "export_query": self.request.GET.urlencode(),
            }
        )
        return context


class ResourcePerformanceReportExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        events, start_date, end_date, event_type, resource_type = (
            _resource_report_events(request)
        )
        rows = _resource_report_rows(
            events, start_date, end_date, resource_type=resource_type
        )
        section = request.GET.get("section", "resources")
        filename = f"code-with-michael-resource-performance-{section}-{start_date}-to-{end_date}.csv"
        response = _csv_response(filename)
        writer = csv.writer(response)
        if section == "types":
            writer.writerow(
                [
                    "Resource Type",
                    "Resources",
                    "Views",
                    "PDF Unlocks",
                    "PDF Downloads",
                    "Subscribers",
                    "Unlock Rate",
                    "Download Rate",
                    "Subscriber Conversion Rate",
                ]
            )
            for row in _resource_type_summary(rows):
                writer.writerow(
                    [
                        row["label"],
                        row["resources"],
                        row["views"],
                        row["unlocks"],
                        row["downloads"],
                        row["subscribers"],
                        row["unlock_rate"] if row["unlock_rate"] is not None else "",
                        row["download_rate"]
                        if row["download_rate"] is not None
                        else "",
                        row["subscriber_rate"]
                        if row["subscriber_rate"] is not None
                        else "",
                    ]
                )
        elif section == "events":
            writer.writerow(
                [
                    "Occurred At",
                    "Event",
                    "Resource",
                    "Resource Type",
                    "Email",
                    "Subscriber",
                    "Source URL",
                    "Referrer",
                ]
            )
            for event in events.order_by("-occurred_at"):
                writer.writerow(
                    [
                        timezone.localtime(event.occurred_at).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        event.get_event_type_display(),
                        event.resource.title,
                        event.resource.get_resource_type_display(),
                        event.email,
                        event.subscriber.email if event.subscriber else "",
                        event.source_url,
                        event.referrer,
                    ]
                )
        else:
            writer.writerow(
                [
                    "Resource",
                    "Resource Type",
                    "Status",
                    "Views",
                    "PDF Unlocks",
                    "PDF Downloads",
                    "Subscribers",
                    "Unlock Rate",
                    "Download Rate",
                    "Subscriber Conversion Rate",
                    "Public URL",
                ]
            )
            for row in rows:
                resource = row["resource"]
                writer.writerow(
                    [
                        resource.title,
                        resource.get_resource_type_display(),
                        resource.get_status_display(),
                        row["views"],
                        row["unlocks"],
                        row["downloads"],
                        row["subscribers"],
                        row["unlock_rate"] if row["unlock_rate"] is not None else "",
                        row["download_rate"]
                        if row["download_rate"] is not None
                        else "",
                        row["subscriber_rate"]
                        if row["subscriber_rate"] is not None
                        else "",
                        resource.public_url,
                    ]
                )
        return response


def _resource_conversion_report_events(request):
    today = timezone.localdate()
    raw_start = request.GET.get("start") or (today - timedelta(days=30)).isoformat()
    raw_end = request.GET.get("end") or today.isoformat()
    event_type = request.GET.get("event_type", "").strip()
    resource_type = request.GET.get("resource_type", "").strip()
    try:
        start_date = datetime.strptime(raw_start, "%Y-%m-%d").date()
    except ValueError:
        start_date = today - timedelta(days=30)
    try:
        end_date = datetime.strptime(raw_end, "%Y-%m-%d").date()
    except ValueError:
        end_date = today
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    end_dt = timezone.make_aware(
        datetime.combine(end_date + timedelta(days=1), time.min)
    )
    events = ResourceLessonConversionEvent.objects.select_related(
        "resource", "lesson", "subscriber", "user", "source_event"
    ).filter(
        occurred_at__gte=start_dt,
        occurred_at__lt=end_dt,
    )
    if event_type:
        events = events.filter(event_type=event_type)
    if resource_type:
        events = events.filter(resource__resource_type=resource_type)
    return events, start_date, end_date, event_type, resource_type


def _resource_conversion_rows(events, start_date, end_date, resource_type=""):
    resources = (
        LearningResource.objects.select_related("category")
        .filter(lesson_conversion_events__in=events)
        .distinct()
    )
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    rows = []
    for resource in resources.order_by("resource_type", "title"):
        resource_events = events.filter(resource=resource)
        views = ResourcePerformanceEvent.objects.filter(
            resource=resource,
            event_type=ResourcePerformanceEvent.EventType.VIEW,
            occurred_at__date__gte=start_date,
            occurred_at__date__lte=end_date,
        ).count()
        signups = resource_events.filter(
            event_type=ResourceLessonConversionEvent.EventType.ACCOUNT_SIGNUP
        ).count()
        lesson_views = resource_events.filter(
            event_type=ResourceLessonConversionEvent.EventType.LESSON_VIEW
        ).count()
        quiz_attempts = resource_events.filter(
            event_type=ResourceLessonConversionEvent.EventType.QUIZ_ATTEMPT
        ).count()
        challenge_attempts = resource_events.filter(
            event_type=ResourceLessonConversionEvent.EventType.CHALLENGE_ATTEMPT
        ).count()
        completions = resource_events.filter(
            event_type=ResourceLessonConversionEvent.EventType.LESSON_COMPLETE
        ).count()
        rows.append(
            {
                "resource": resource,
                "resource_views": views,
                "lesson_views": lesson_views,
                "account_signups": signups,
                "quiz_attempts": quiz_attempts,
                "challenge_attempts": challenge_attempts,
                "lesson_completions": completions,
                "total_conversions": resource_events.count(),
                "signup_rate": round(signups / views * 100, 2) if views else None,
                "lesson_view_rate": round(lesson_views / views * 100, 2)
                if views
                else None,
                "completion_rate": round(completions / views * 100, 2)
                if views
                else None,
            }
        )
    rows.sort(
        key=lambda row: (
            row["lesson_completions"],
            row["account_signups"],
            row["lesson_views"],
            row["total_conversions"],
        ),
        reverse=True,
    )
    return rows


def _resource_conversion_action_summary(events):
    labels = dict(ResourceLessonConversionEvent.EventType.choices)
    rows = []
    for key, label in labels.items():
        count = events.filter(event_type=key).count()
        if count:
            rows.append({"key": key, "label": label, "count": count})
    return sorted(rows, key=lambda row: row["count"], reverse=True)


class ResourceConversionReportView(StaffRequiredMixin, TemplateView):
    template_name = "studio/resource_conversion_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events, start_date, end_date, event_type, resource_type = (
            _resource_conversion_report_events(self.request)
        )
        rows = _resource_conversion_rows(
            events, start_date, end_date, resource_type=resource_type
        )
        totals = {
            "resource_views": sum(row["resource_views"] for row in rows),
            "lesson_views": sum(row["lesson_views"] for row in rows),
            "account_signups": sum(row["account_signups"] for row in rows),
            "quiz_attempts": sum(row["quiz_attempts"] for row in rows),
            "challenge_attempts": sum(row["challenge_attempts"] for row in rows),
            "lesson_completions": sum(row["lesson_completions"] for row in rows),
            "total_conversions": sum(row["total_conversions"] for row in rows),
        }
        totals["signup_rate"] = (
            round(totals["account_signups"] / totals["resource_views"] * 100, 2)
            if totals["resource_views"]
            else None
        )
        totals["lesson_view_rate"] = (
            round(totals["lesson_views"] / totals["resource_views"] * 100, 2)
            if totals["resource_views"]
            else None
        )
        totals["completion_rate"] = (
            round(totals["lesson_completions"] / totals["resource_views"] * 100, 2)
            if totals["resource_views"]
            else None
        )
        top_lessons = (
            events.exclude(lesson__isnull=True)
            .values("lesson__title", "lesson__slug")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        context.update(
            {
                "start_date": start_date,
                "end_date": end_date,
                "event_type": event_type,
                "resource_type": resource_type,
                "event_type_choices": ResourceLessonConversionEvent.EventType.choices,
                "resource_type_choices": LearningResource.ResourceType.choices,
                "resource_rows": rows,
                "action_rows": _resource_conversion_action_summary(events),
                "top_lessons": top_lessons,
                "totals": totals,
                "recent_events": events.order_by("-occurred_at")[:50],
                "export_query": self.request.GET.urlencode(),
            }
        )
        return context


class ResourceConversionReportExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        events, start_date, end_date, event_type, resource_type = (
            _resource_conversion_report_events(request)
        )
        rows = _resource_conversion_rows(
            events, start_date, end_date, resource_type=resource_type
        )
        section = request.GET.get("section", "resources")
        filename = f"code-with-michael-resource-conversions-{section}-{start_date}-to-{end_date}.csv"
        response = _csv_response(filename)
        writer = csv.writer(response)
        if section == "events":
            writer.writerow(
                [
                    "Occurred At",
                    "Conversion",
                    "Resource",
                    "Resource Type",
                    "Lesson",
                    "User",
                    "Email",
                    "Attribution Event",
                    "Attribution URL",
                    "Referrer",
                ]
            )
            for event in events.order_by("-occurred_at"):
                writer.writerow(
                    [
                        timezone.localtime(event.occurred_at).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        event.get_event_type_display(),
                        event.resource.title,
                        event.resource.get_resource_type_display(),
                        event.lesson.title if event.lesson else "",
                        event.user.email if event.user else "",
                        event.email,
                        event.get_attribution_event_type_display()
                        if event.attribution_event_type
                        else "",
                        event.attribution_source_url,
                        event.referrer,
                    ]
                )
        elif section == "actions":
            writer.writerow(["Conversion Type", "Count"])
            for row in _resource_conversion_action_summary(events):
                writer.writerow([row["label"], row["count"]])
        else:
            writer.writerow(
                [
                    "Resource",
                    "Resource Type",
                    "Resource Views",
                    "Lesson Views",
                    "Account Signups",
                    "Quiz Attempts",
                    "Challenge Attempts",
                    "Lesson Completions",
                    "Total Conversions",
                    "Lesson View Rate",
                    "Signup Rate",
                    "Completion Rate",
                    "Public URL",
                ]
            )
            for row in rows:
                resource = row["resource"]
                writer.writerow(
                    [
                        resource.title,
                        resource.get_resource_type_display(),
                        row["resource_views"],
                        row["lesson_views"],
                        row["account_signups"],
                        row["quiz_attempts"],
                        row["challenge_attempts"],
                        row["lesson_completions"],
                        row["total_conversions"],
                        row["lesson_view_rate"]
                        if row["lesson_view_rate"] is not None
                        else "",
                        row["signup_rate"] if row["signup_rate"] is not None else "",
                        row["completion_rate"]
                        if row["completion_rate"] is not None
                        else "",
                        resource.public_url,
                    ]
                )
        return response


class PublicResourceCTAClickView(DetailView):
    model = ResourceCTA

    def get_queryset(self):
        return ResourceCTA.objects.filter(
            is_active=True,
            resource__slug=self.kwargs.get("resource_slug"),
            resource__status__in=[
                LearningResource.Status.READY,
                LearningResource.Status.PUBLISHED,
            ],
        ).select_related("resource", "target_lesson")

    def get(self, request, *args, **kwargs):
        cta = self.get_object()
        target_url = _resource_cta_target_url(cta, request=request)
        user = request.user if request.user.is_authenticated else None
        click = ResourceCTAClickEvent.objects.create(
            cta=cta,
            resource=cta.resource,
            target_lesson=cta.target_lesson,
            user=user,
            source_url=request.build_absolute_uri(request.path)[:300],
            target_url=target_url[:300],
            referrer=request.META.get("HTTP_REFERER", "")[:300],
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
        request.session[RESOURCE_ATTRIBUTION_SESSION_KEY] = {
            "resource_id": cta.resource_id,
            "event_type": "cta_click",
            "occurred_at": click.occurred_at.isoformat(),
        }
        request.session[RESOURCE_CTA_ATTRIBUTION_SESSION_KEY] = {
            "resource_id": cta.resource_id,
            "cta_id": cta.pk,
            "click_id": click.pk,
            "target_lesson_id": cta.target_lesson_id,
            "occurred_at": click.occurred_at.isoformat(),
        }
        return redirect(target_url)


def _resource_cta_report_data(request):
    today = timezone.localdate()
    raw_start = request.GET.get("start") or (today - timedelta(days=30)).isoformat()
    raw_end = request.GET.get("end") or today.isoformat()
    target_type = request.GET.get("target_type", "").strip()
    resource_type = request.GET.get("resource_type", "").strip()
    try:
        start_date = datetime.strptime(raw_start, "%Y-%m-%d").date()
    except ValueError:
        start_date = today - timedelta(days=30)
    try:
        end_date = datetime.strptime(raw_end, "%Y-%m-%d").date()
    except ValueError:
        end_date = today
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    end_dt = timezone.make_aware(
        datetime.combine(end_date + timedelta(days=1), time.min)
    )
    ctas = ResourceCTA.objects.select_related("resource", "target_lesson").filter(
        resource__status__in=[
            LearningResource.Status.READY,
            LearningResource.Status.PUBLISHED,
        ]
    )
    clicks = ResourceCTAClickEvent.objects.select_related(
        "cta", "resource", "target_lesson", "user"
    ).filter(occurred_at__gte=start_dt, occurred_at__lt=end_dt)
    conversions = ResourceLessonConversionEvent.objects.select_related(
        "cta", "resource", "lesson", "user", "subscriber"
    ).filter(occurred_at__gte=start_dt, occurred_at__lt=end_dt, cta__isnull=False)
    if target_type:
        ctas = ctas.filter(target_type=target_type)
        clicks = clicks.filter(cta__target_type=target_type)
        conversions = conversions.filter(cta__target_type=target_type)
    if resource_type:
        ctas = ctas.filter(resource__resource_type=resource_type)
        clicks = clicks.filter(resource__resource_type=resource_type)
        conversions = conversions.filter(resource__resource_type=resource_type)
    rows = []
    for cta in ctas.order_by("resource__title", "position"):
        cta_clicks = clicks.filter(cta=cta).count()
        cta_conversions = conversions.filter(cta=cta).count()
        lesson_views = conversions.filter(
            cta=cta, event_type=ResourceLessonConversionEvent.EventType.LESSON_VIEW
        ).count()
        quiz_attempts = conversions.filter(
            cta=cta, event_type=ResourceLessonConversionEvent.EventType.QUIZ_ATTEMPT
        ).count()
        challenge_attempts = conversions.filter(
            cta=cta,
            event_type=ResourceLessonConversionEvent.EventType.CHALLENGE_ATTEMPT,
        ).count()
        completions = conversions.filter(
            cta=cta, event_type=ResourceLessonConversionEvent.EventType.LESSON_COMPLETE
        ).count()
        rows.append(
            {
                "cta": cta,
                "clicks": cta_clicks,
                "lesson_views": lesson_views,
                "quiz_attempts": quiz_attempts,
                "challenge_attempts": challenge_attempts,
                "lesson_completions": completions,
                "total_conversions": cta_conversions,
                "conversion_rate": round(cta_conversions / cta_clicks * 100, 2)
                if cta_clicks
                else None,
                "completion_rate": round(completions / cta_clicks * 100, 2)
                if cta_clicks
                else None,
            }
        )
    rows.sort(
        key=lambda row: (
            row["lesson_completions"],
            row["total_conversions"],
            row["clicks"],
        ),
        reverse=True,
    )
    return rows, clicks, conversions, start_date, end_date, target_type, resource_type


class ResourceCTAReportView(StaffRequiredMixin, TemplateView):
    template_name = "studio/resource_cta_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows, clicks, conversions, start_date, end_date, target_type, resource_type = (
            _resource_cta_report_data(self.request)
        )
        totals = {
            "clicks": sum(row["clicks"] for row in rows),
            "lesson_views": sum(row["lesson_views"] for row in rows),
            "quiz_attempts": sum(row["quiz_attempts"] for row in rows),
            "challenge_attempts": sum(row["challenge_attempts"] for row in rows),
            "lesson_completions": sum(row["lesson_completions"] for row in rows),
            "total_conversions": sum(row["total_conversions"] for row in rows),
        }
        totals["conversion_rate"] = (
            round(totals["total_conversions"] / totals["clicks"] * 100, 2)
            if totals["clicks"]
            else None
        )
        context.update(
            {
                "rows": rows,
                "recent_clicks": clicks.order_by("-occurred_at")[:50],
                "recent_conversions": conversions.order_by("-occurred_at")[:50],
                "totals": totals,
                "start_date": start_date,
                "end_date": end_date,
                "target_type": target_type,
                "resource_type": resource_type,
                "target_type_choices": ResourceCTA.TargetType.choices,
                "resource_type_choices": LearningResource.ResourceType.choices,
                "export_query": self.request.GET.urlencode(),
            }
        )
        return context


class ResourceCTAReportExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        rows, clicks, conversions, start_date, end_date, target_type, resource_type = (
            _resource_cta_report_data(request)
        )
        section = request.GET.get("section", "ctas")
        response = _csv_response(
            f"code-with-michael-resource-ctas-{section}-{start_date}-to-{end_date}.csv"
        )
        writer = csv.writer(response)
        if section == "clicks":
            writer.writerow(
                [
                    "Occurred At",
                    "Resource",
                    "Resource Type",
                    "CTA",
                    "CTA Type",
                    "Target Lesson",
                    "Target URL",
                    "User",
                    "Referrer",
                ]
            )
            for click in clicks.order_by("-occurred_at"):
                writer.writerow(
                    [
                        timezone.localtime(click.occurred_at).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        click.resource.title,
                        click.resource.get_resource_type_display(),
                        click.cta.title,
                        click.cta.get_target_type_display(),
                        click.target_lesson.title if click.target_lesson else "",
                        click.target_url,
                        click.user.email if click.user else "",
                        click.referrer,
                    ]
                )
        elif section == "conversions":
            writer.writerow(
                [
                    "Occurred At",
                    "Conversion",
                    "Resource",
                    "CTA",
                    "CTA Type",
                    "Lesson",
                    "User",
                    "Email",
                ]
            )
            for event in conversions.order_by("-occurred_at"):
                writer.writerow(
                    [
                        timezone.localtime(event.occurred_at).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        event.get_event_type_display(),
                        event.resource.title,
                        event.cta.title if event.cta else "",
                        event.cta.get_target_type_display() if event.cta else "",
                        event.lesson.title if event.lesson else "",
                        event.user.email if event.user else "",
                        event.email,
                    ]
                )
        else:
            writer.writerow(
                [
                    "Resource",
                    "Resource Type",
                    "CTA",
                    "CTA Type",
                    "Button",
                    "Target Lesson",
                    "Clicks",
                    "Lesson Views",
                    "Quiz Attempts",
                    "Challenge Attempts",
                    "Lesson Completions",
                    "Total Conversions",
                    "Conversion Rate",
                    "Completion Rate",
                ]
            )
            for row in rows:
                cta = row["cta"]
                writer.writerow(
                    [
                        cta.resource.title,
                        cta.resource.get_resource_type_display(),
                        cta.title,
                        cta.get_target_type_display(),
                        cta.button_label,
                        cta.target_lesson.title if cta.target_lesson else "",
                        row["clicks"],
                        row["lesson_views"],
                        row["quiz_attempts"],
                        row["challenge_attempts"],
                        row["lesson_completions"],
                        row["total_conversions"],
                        row["conversion_rate"]
                        if row["conversion_rate"] is not None
                        else "",
                        row["completion_rate"]
                        if row["completion_rate"] is not None
                        else "",
                    ]
                )
        return response


class ContentPlanCreateView(StaffRequiredMixin, CreateView):
    model = ContentPlan
    form_class = ContentPlanForm
    template_name = "studio/content_plan_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = get_object_or_404(Lesson, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lesson"] = self.lesson
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        platform = self.request.GET.get("platform")
        valid_platforms = {choice[0] for choice in ContentPlan.Platform.choices}
        if platform in valid_platforms:
            initial["platform"] = platform
        scheduled_at = self.request.GET.get("scheduled_at")
        if scheduled_at:
            initial["scheduled_at"] = scheduled_at
        carousel_template = self.request.GET.get("carousel_template")
        if carousel_template:
            initial["carousel_template"] = carousel_template
        return initial

    def form_valid(self, form):
        form.instance.lesson = self.lesson
        form.instance.created_by = self.request.user
        messages.success(self.request, "Content plan saved.")
        return super().form_valid(form)

    def get_success_url(self):
        week = (
            self.object.week_start.isoformat()
            if self.object.scheduled_at
            else timezone.localdate().isoformat()
        )
        return reverse("studio:content-planner") + f"?week={week}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.lesson
        context["form_title"] = "Plan a post"
        return context


class ContentPlanUpdateView(StaffRequiredMixin, UpdateView):
    model = ContentPlan
    form_class = ContentPlanForm
    template_name = "studio/content_plan_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lesson"] = self.object.lesson
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Content plan updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return (
            reverse("studio:content-planner")
            + f"?week={self.object.week_start.isoformat()}"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.lesson
        context["form_title"] = "Edit planned post"
        return context


class ContentPlanDeleteView(StaffRequiredMixin, DeleteView):
    model = ContentPlan
    template_name = "studio/content_plan_confirm_delete.html"

    def get_success_url(self):
        return (
            reverse("studio:content-planner")
            + f"?week={self.object.week_start.isoformat()}"
        )


@require_POST
def newsletter_signup(request):
    form = NewsletterSignupForm(request.POST)
    next_url = request.POST.get("next") or reverse("learn:home")
    source = request.POST.get("source") or NewsletterSubscriber.Source.LEARN_HOME
    lesson = None
    resource = None
    lesson_slug = request.POST.get("lesson_slug")
    resource_slug = request.POST.get("resource_slug")
    if lesson_slug:
        lesson = Lesson.objects.filter(slug=lesson_slug).first()
    if resource_slug:
        resource = LearningResource.objects.filter(slug=resource_slug).first()

    if form.is_valid():
        email = form.cleaned_data["email"]
        defaults = {
            "first_name": form.cleaned_data.get("first_name", ""),
            "source": source
            if source in dict(NewsletterSubscriber.Source.choices)
            else NewsletterSubscriber.Source.OTHER,
            "source_url": request.build_absolute_uri(next_url)[:300],
            "source_lesson": lesson,
            "source_resource": resource,
            "user": request.user if request.user.is_authenticated else None,
            "status": NewsletterSubscriber.Status.ACTIVE,
            "unsubscribed_at": None,
        }
        subscriber, created = NewsletterSubscriber.objects.update_or_create(
            email=email, defaults=defaults
        )
        if not created and subscriber.status != NewsletterSubscriber.Status.ACTIVE:
            subscriber.mark_active()
            subscriber.save(
                update_fields=[
                    "status",
                    "unsubscribed_at",
                    "subscribed_at",
                    "updated_at",
                ]
            )
        messages.success(request, "You're on the Code with Michael email list.")
    else:
        messages.error(request, "Please enter a valid email address to join the list.")
    return redirect(next_url)


def _newsletter_campaign_draft_for_lesson(lesson):
    objective = lesson.learning_objective or f"practice {lesson.title.lower()}"
    takeaway = (
        lesson.beginner_takeaway
        or lesson.summary
        or "one small Python idea you can use right away"
    )
    prompt = lesson.practice_prompt or "Try changing the example code and run it again."
    cta = f"Open the lesson: {lesson.title}"
    body = f"""Hi there,

This week's beginner Python lesson is: {lesson.title}.

What you'll practice:
{objective}

The main idea:
{takeaway}

Try this:
{prompt}

A common mistake to watch for:
{lesson.common_mistake or "Do not rush past the output. Read what Python prints and compare it with what you expected."}

Keep going — small, consistent practice is how Python starts to feel natural.

Michael
"""
    return {
        "title": f"Weekly Python: {lesson.title}",
        "subject": f"Practice Python: {lesson.title}",
        "preview_text": takeaway[:220],
        "body": body,
        "call_to_action": cta,
        "target_segment": NewsletterCampaign.Segment.ALL_ACTIVE,
        "estimated_recipients": NewsletterSubscriber.objects.filter(
            status=NewsletterSubscriber.Status.ACTIVE
        ).count(),
    }


class NewsletterCampaignListView(StaffRequiredMixin, ListView):
    model = NewsletterCampaign
    template_name = "studio/newsletter_campaigns.html"
    context_object_name = "campaigns"
    paginate_by = 40

    def get_queryset(self):
        queryset = NewsletterCampaign.objects.select_related(
            "lesson", "content_plan", "publishing_record", "created_by", "saved_segment"
        )
        status = self.request.GET.get("status", "")
        segment = self.request.GET.get("segment", "")
        saved_segment = self.request.GET.get("saved_segment", "")
        provider = self.request.GET.get("provider", "")
        sync_status = self.request.GET.get("sync_status", "")
        query = self.request.GET.get("q", "").strip()
        if status:
            queryset = queryset.filter(status=status)
        if segment:
            queryset = queryset.filter(target_segment=segment)
        if saved_segment:
            queryset = queryset.filter(saved_segment_id=saved_segment)
        if provider:
            queryset = queryset.filter(external_provider=provider)
        if sync_status:
            queryset = queryset.filter(provider_sync_status=sync_status)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(subject__icontains=query)
                | Q(preview_text__icontains=query)
                | Q(body__icontains=query)
                | Q(lesson__title__icontains=query)
                | Q(external_campaign_id__icontains=query)
                | Q(external_audience_id__icontains=query)
                | Q(provider_notes__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["status_filter"] = self.request.GET.get("status", "")
        context["segment_filter"] = self.request.GET.get("segment", "")
        context["saved_segment_filter"] = self.request.GET.get("saved_segment", "")
        context["provider_filter"] = self.request.GET.get("provider", "")
        context["sync_status_filter"] = self.request.GET.get("sync_status", "")
        context["provider_choices"] = [
            (value, label)
            for value, label in EmailProvider.choices
            if value != EmailProvider.NONE
        ]
        context["sync_status_choices"] = ProviderSyncStatus.choices
        context["status_choices"] = NewsletterCampaign.Status.choices
        context["segment_choices"] = NewsletterCampaign.Segment.choices
        context["saved_segments"] = SubscriberSegment.objects.filter(
            is_active=True
        ).order_by("name")
        context["draft_count"] = NewsletterCampaign.objects.filter(
            status=NewsletterCampaign.Status.DRAFT
        ).count()
        context["scheduled_count"] = NewsletterCampaign.objects.filter(
            status=NewsletterCampaign.Status.SCHEDULED
        ).count()
        context["sent_count"] = NewsletterCampaign.objects.filter(
            status=NewsletterCampaign.Status.SENT
        ).count()
        context["active_subscribers"] = NewsletterSubscriber.objects.filter(
            status=NewsletterSubscriber.Status.ACTIVE
        ).count()
        return context


class NewsletterCampaignCreateView(StaffRequiredMixin, CreateView):
    model = NewsletterCampaign
    form_class = NewsletterCampaignForm
    template_name = "studio/newsletter_campaign_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = None
        slug = kwargs.get("slug") or request.GET.get("lesson")
        if slug:
            self.lesson = get_object_or_404(Lesson, slug=slug)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.lesson:
            initial.update(_newsletter_campaign_draft_for_lesson(self.lesson))
            initial["lesson"] = self.lesson
        scheduled_at = self.request.GET.get("scheduled_at")
        if scheduled_at:
            initial["scheduled_at"] = scheduled_at
            initial["status"] = NewsletterCampaign.Status.SCHEDULED
        plan_id = self.request.GET.get("plan")
        if plan_id:
            plan = ContentPlan.objects.filter(
                pk=plan_id, platform=ContentPlan.Platform.EMAIL
            ).first()
            if plan:
                initial["content_plan"] = plan
                initial.setdefault("lesson", plan.lesson)
                initial.setdefault("scheduled_at", plan.scheduled_at)
                initial.setdefault("status", NewsletterCampaign.Status.SCHEDULED)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lesson"] = self.lesson
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if form.instance.content_plan and not form.instance.lesson_id:
            form.instance.lesson = form.instance.content_plan.lesson
        if form.instance.saved_segment_id and not form.instance.estimated_recipients:
            form.instance.estimated_recipients = (
                form.instance.saved_segment.subscriber_count
            )
        elif not form.instance.estimated_recipients:
            form.instance.estimated_recipients = form.instance.estimated_segment_count
        messages.success(self.request, "Newsletter campaign saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("studio:newsletter-campaign-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.lesson
        context["form_title"] = "Plan newsletter campaign"
        return context


class NewsletterCampaignUpdateView(StaffRequiredMixin, UpdateView):
    model = NewsletterCampaign
    form_class = NewsletterCampaignForm
    template_name = "studio/newsletter_campaign_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lesson"] = self.object.lesson
        return kwargs

    def form_valid(self, form):
        if form.instance.saved_segment_id and not form.instance.estimated_recipients:
            form.instance.estimated_recipients = (
                form.instance.saved_segment.subscriber_count
            )
        messages.success(self.request, "Newsletter campaign updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("studio:newsletter-campaign-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.lesson
        context["form_title"] = "Edit newsletter campaign"
        return context


class NewsletterCampaignDeleteView(StaffRequiredMixin, DeleteView):
    model = NewsletterCampaign
    template_name = "studio/newsletter_campaign_confirm_delete.html"
    success_url = reverse_lazy("studio:newsletter-campaign-list")


@staff_required
@require_POST
def mark_newsletter_campaign_sent(request, pk):
    campaign = get_object_or_404(NewsletterCampaign, pk=pk)
    campaign.mark_sent()
    campaign.actual_recipients = (
        campaign.actual_recipients or campaign.estimated_recipients
    )
    campaign.save(
        update_fields=["status", "sent_at", "actual_recipients", "updated_at"]
    )
    if (
        campaign.content_plan
        and campaign.content_plan.status != ContentPlan.Status.POSTED
    ):
        campaign.content_plan.status = ContentPlan.Status.POSTED
        campaign.content_plan.save(update_fields=["status", "updated_at"])
    messages.success(
        request,
        "Newsletter campaign marked as sent. Add performance metrics when they are available.",
    )
    return redirect("studio:newsletter-campaign-list")


class NewsletterMetricImportView(StaffRequiredMixin, FormView):
    template_name = "studio/newsletter_metric_import.html"
    form_class = NewsletterMetricImportForm

    def dispatch(self, request, *args, **kwargs):
        self.campaign = None
        campaign_id = kwargs.get("pk") or request.GET.get("campaign")
        if campaign_id:
            self.campaign = get_object_or_404(NewsletterCampaign, pk=campaign_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["campaign"] = self.campaign
        return kwargs

    def form_valid(self, form):
        source_text = form.source_text()
        result = parse_newsletter_metrics(source_text)
        if not result.has_metrics:
            for warning in result.warnings:
                messages.error(self.request, warning)
            return self.form_invalid(form)

        campaign = form.cleaned_data["campaign"]
        upload = form.cleaned_data.get("metrics_file")
        normalized = {
            field: result.metrics.get(field) or 0
            for field in (
                "actual_recipients",
                "opens",
                "clicks",
                "unsubscribes",
                "bounces",
            )
        }
        normalized["matched_labels"] = result.matched_labels
        normalized["rows_seen"] = result.rows_seen
        metric_import = NewsletterMetricImport.objects.create(
            campaign=campaign,
            provider=form.cleaned_data["provider"],
            source_filename=getattr(upload, "name", "") if upload else "",
            raw_payload=source_text[:20000],
            normalized_data=normalized,
            actual_recipients=normalized["actual_recipients"],
            opens=normalized["opens"],
            clicks=normalized["clicks"],
            unsubscribes=normalized["unsubscribes"],
            bounces=normalized["bounces"],
            warnings=result.warnings,
            imported_by=self.request.user,
            notes=form.cleaned_data.get("notes", ""),
        )
        metric_import.apply_to_campaign(mark_sent=form.cleaned_data.get("mark_sent"))
        if (
            campaign.content_plan
            and campaign.content_plan.status != ContentPlan.Status.POSTED
            and form.cleaned_data.get("mark_sent")
        ):
            campaign.content_plan.status = ContentPlan.Status.POSTED
            campaign.content_plan.save(update_fields=["status", "updated_at"])
        messages.success(
            self.request,
            f"Imported newsletter metrics for {campaign.title}: {metric_import.actual_recipients} recipients, {metric_import.opens} opens, {metric_import.clicks} clicks.",
        )
        for warning in result.warnings:
            messages.warning(self.request, warning)
        return redirect("studio:newsletter-campaign-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.campaign
        context["recent_imports"] = NewsletterMetricImport.objects.select_related(
            "campaign", "imported_by"
        ).order_by("-applied_at")[:12]
        return context


class NewsletterSubscriberListView(StaffRequiredMixin, ListView):
    model = NewsletterSubscriber
    template_name = "studio/newsletter_subscribers.html"
    context_object_name = "subscribers"
    paginate_by = 50

    def get_queryset(self):
        queryset = NewsletterSubscriber.objects.select_related(
            "source_lesson", "source_resource", "user"
        )
        status = self.request.GET.get("status", "")
        source = self.request.GET.get("source", "")
        provider = self.request.GET.get("provider", "")
        sync_status = self.request.GET.get("sync_status", "")
        query = self.request.GET.get("q", "").strip()
        if status:
            queryset = queryset.filter(status=status)
        if source:
            queryset = queryset.filter(source=source)
        if provider:
            queryset = queryset.filter(external_provider=provider)
        if sync_status:
            queryset = queryset.filter(provider_sync_status=sync_status)
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(source_lesson__title__icontains=query)
                | Q(source_resource__title__icontains=query)
                | Q(notes__icontains=query)
                | Q(provider_notes__icontains=query)
                | Q(external_contact_id__icontains=query)
                | Q(external_list_id__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = NewsletterSubscriber.Status.choices
        context["source_choices"] = NewsletterSubscriber.Source.choices
        context["status_filter"] = self.request.GET.get("status", "")
        context["source_filter"] = self.request.GET.get("source", "")
        context["provider_filter"] = self.request.GET.get("provider", "")
        context["sync_status_filter"] = self.request.GET.get("sync_status", "")
        context["provider_choices"] = [
            (value, label)
            for value, label in EmailProvider.choices
            if value != EmailProvider.NONE
        ]
        context["sync_status_choices"] = ProviderSyncStatus.choices
        context["query"] = self.request.GET.get("q", "")
        context["active_count"] = NewsletterSubscriber.objects.filter(
            status=NewsletterSubscriber.Status.ACTIVE
        ).count()
        context["total_count"] = NewsletterSubscriber.objects.count()
        context["recent_count"] = NewsletterSubscriber.objects.filter(
            subscribed_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        context["export_query"] = self.request.GET.urlencode()
        return context


class NewsletterSubscriberUpdateView(StaffRequiredMixin, UpdateView):
    model = NewsletterSubscriber
    form_class = NewsletterSubscriberForm
    template_name = "studio/newsletter_subscriber_form.html"

    def get_success_url(self):
        return reverse("studio:newsletter-subscriber-list")

    def form_valid(self, form):
        messages.success(self.request, "Subscriber updated.")
        return super().form_valid(form)


class NewsletterSubscriberExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        list_view = NewsletterSubscriberListView()
        list_view.request = request
        subscribers = list_view.get_queryset()
        status_label = request.GET.get("status") or "all"
        response = _csv_response(
            f"code-with-michael-newsletter-subscribers-{status_label}.csv"
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "Email",
                "First Name",
                "Status",
                "Source",
                "Source Lesson",
                "Source Resource",
                "Subscribed At",
                "Unsubscribed At",
                "Source URL",
                "Provider",
                "Provider Contact ID",
                "Provider List ID",
                "Provider Sync Status",
                "Provider Last Synced At",
                "Provider Notes",
                "Notes",
            ]
        )
        for subscriber in subscribers:
            writer.writerow(
                [
                    subscriber.email,
                    subscriber.first_name,
                    subscriber.get_status_display(),
                    subscriber.get_source_display(),
                    subscriber.source_lesson.title if subscriber.source_lesson else "",
                    subscriber.source_resource.title
                    if subscriber.source_resource
                    else "",
                    timezone.localtime(subscriber.subscribed_at).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if subscriber.subscribed_at
                    else "",
                    timezone.localtime(subscriber.unsubscribed_at).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if subscriber.unsubscribed_at
                    else "",
                    subscriber.source_url,
                    subscriber.get_external_provider_display(),
                    subscriber.external_contact_id,
                    subscriber.external_list_id,
                    subscriber.get_provider_sync_status_display(),
                    timezone.localtime(subscriber.provider_last_synced_at).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if subscriber.provider_last_synced_at
                    else "",
                    subscriber.provider_notes,
                    subscriber.notes,
                ]
            )
        return response


class SubscriberSegmentListView(StaffRequiredMixin, ListView):
    model = SubscriberSegment
    template_name = "studio/subscriber_segments.html"
    context_object_name = "segments"
    paginate_by = 40

    def get_queryset(self):
        queryset = SubscriberSegment.objects.select_related(
            "source_lesson", "created_by"
        )
        query = self.request.GET.get("q", "").strip()
        active = self.request.GET.get("active", "")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(search_text__icontains=query)
                | Q(source_lesson__title__icontains=query)
                | Q(source_resource__title__icontains=query)
                | Q(notes__icontains=query)
                | Q(provider_notes__icontains=query)
                | Q(external_segment_id__icontains=query)
                | Q(external_audience_id__icontains=query)
            )
        if active == "yes":
            queryset = queryset.filter(is_active=True)
        elif active == "no":
            queryset = queryset.filter(is_active=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        segments = list(context["segments"])
        context["segment_rows"] = [
            {"segment": segment, "subscriber_count": segment.subscriber_count}
            for segment in segments
        ]
        context["query"] = self.request.GET.get("q", "")
        context["active_filter"] = self.request.GET.get("active", "")
        context["active_segment_count"] = SubscriberSegment.objects.filter(
            is_active=True
        ).count()
        context["total_segment_count"] = SubscriberSegment.objects.count()
        context["active_subscriber_count"] = NewsletterSubscriber.objects.filter(
            status=NewsletterSubscriber.Status.ACTIVE
        ).count()
        return context


class SubscriberSegmentCreateView(StaffRequiredMixin, CreateView):
    model = SubscriberSegment
    form_class = SubscriberSegmentForm
    template_name = "studio/subscriber_segment_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Subscriber segment saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("studio:subscriber-segment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Create subscriber segment"
        return context


class SubscriberSegmentUpdateView(StaffRequiredMixin, UpdateView):
    model = SubscriberSegment
    form_class = SubscriberSegmentForm
    template_name = "studio/subscriber_segment_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Subscriber segment updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("studio:subscriber-segment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit subscriber segment"
        context["subscriber_count"] = self.object.subscriber_count
        return context


class SubscriberSegmentDeleteView(StaffRequiredMixin, DeleteView):
    model = SubscriberSegment
    template_name = "studio/subscriber_segment_confirm_delete.html"
    success_url = reverse_lazy("studio:subscriber-segment-list")


class SubscriberSegmentExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, pk, *args, **kwargs):
        segment = get_object_or_404(SubscriberSegment, pk=pk)
        response = _csv_response(
            f"code-with-michael-segment-{segment.slug}-subscribers.csv"
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "Email",
                "First Name",
                "Status",
                "Source",
                "Skill Level",
                "Source Lesson",
                "Subscribed At",
                "Source URL",
                "Provider",
                "Provider Contact ID",
                "Provider List ID",
                "Provider Sync Status",
                "Provider Last Synced At",
                "Provider Notes",
                "Notes",
            ]
        )
        for subscriber in segment.matching_subscribers():
            writer.writerow(
                [
                    subscriber.email,
                    subscriber.first_name,
                    subscriber.get_status_display(),
                    subscriber.get_source_display(),
                    subscriber.user.get_skill_level_display()
                    if subscriber.user_id
                    else "",
                    subscriber.source_lesson.title if subscriber.source_lesson else "",
                    subscriber.source_resource.title
                    if subscriber.source_resource
                    else "",
                    timezone.localtime(subscriber.subscribed_at).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if subscriber.subscribed_at
                    else "",
                    subscriber.source_url,
                    subscriber.get_external_provider_display(),
                    subscriber.external_contact_id,
                    subscriber.external_list_id,
                    subscriber.get_provider_sync_status_display(),
                    timezone.localtime(subscriber.provider_last_synced_at).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if subscriber.provider_last_synced_at
                    else "",
                    subscriber.provider_notes,
                    subscriber.notes,
                ]
            )
        return response


def _newsletter_segment_performance_rows():
    campaigns = NewsletterCampaign.objects.select_related("saved_segment").filter(
        status=NewsletterCampaign.Status.SENT
    )
    buckets = {}
    for campaign in campaigns:
        if campaign.saved_segment_id:
            key = f"saved:{campaign.saved_segment_id}"
            label = campaign.saved_segment.name
            source = "Saved segment"
        else:
            key = f"legacy:{campaign.target_segment}"
            label = campaign.get_target_segment_display()
            source = "Legacy quick segment"
        bucket = buckets.setdefault(
            key,
            {
                "label": label,
                "source": source,
                "campaigns": 0,
                "recipients": 0,
                "opens": 0,
                "clicks": 0,
                "unsubscribes": 0,
                "bounces": 0,
                "open_rate": None,
                "click_rate": None,
                "click_to_open_rate": None,
            },
        )
        bucket["campaigns"] += 1
        bucket["recipients"] += (
            campaign.actual_recipients or campaign.estimated_recipients or 0
        )
        bucket["opens"] += campaign.opens or 0
        bucket["clicks"] += campaign.clicks or 0
        bucket["unsubscribes"] += campaign.unsubscribes or 0
        bucket["bounces"] += campaign.bounces or 0
    for bucket in buckets.values():
        if bucket["recipients"]:
            bucket["open_rate"] = round(bucket["opens"] / bucket["recipients"] * 100, 2)
            bucket["click_rate"] = round(
                bucket["clicks"] / bucket["recipients"] * 100, 2
            )
        if bucket["opens"]:
            bucket["click_to_open_rate"] = round(
                bucket["clicks"] / bucket["opens"] * 100, 2
            )
    return sorted(
        buckets.values(),
        key=lambda row: (row["clicks"], row["open_rate"] or 0, row["campaigns"]),
        reverse=True,
    )


class NewsletterSegmentPerformanceView(StaffRequiredMixin, TemplateView):
    template_name = "studio/newsletter_segment_performance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rows"] = _newsletter_segment_performance_rows()
        context["sent_campaigns"] = NewsletterCampaign.objects.filter(
            status=NewsletterCampaign.Status.SENT
        ).count()
        context["active_segments"] = SubscriberSegment.objects.filter(
            is_active=True
        ).count()
        return context


class NewsletterSegmentPerformanceExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        response = _csv_response("code-with-michael-newsletter-segment-performance.csv")
        writer = csv.writer(response)
        writer.writerow(
            [
                "Segment",
                "Source",
                "Campaigns",
                "Recipients",
                "Opens",
                "Open Rate",
                "Clicks",
                "Click Rate",
                "Click-to-open Rate",
                "Unsubscribes",
                "Bounces",
            ]
        )
        for row in _newsletter_segment_performance_rows():
            writer.writerow(
                [
                    row["label"],
                    row["source"],
                    row["campaigns"],
                    row["recipients"],
                    row["opens"],
                    row["open_rate"] if row["open_rate"] is not None else "",
                    row["clicks"],
                    row["click_rate"] if row["click_rate"] is not None else "",
                    row["click_to_open_rate"]
                    if row["click_to_open_rate"] is not None
                    else "",
                    row["unsubscribes"],
                    row["bounces"],
                ]
            )
        return response


class ProviderSyncReadinessView(StaffRequiredMixin, TemplateView):
    template_name = "studio/provider_sync_readiness.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record_type = self.request.GET.get("record_type", "")
        provider = self.request.GET.get("provider", "")
        sync_status = self.request.GET.get("sync_status", "")
        issue = self.request.GET.get("issue", "")
        rows = provider_readiness_rows(
            record_type=record_type,
            provider=provider,
            sync_status=sync_status,
            issue=issue,
        )
        context.update(
            {
                "rows": rows,
                "summary": provider_readiness_summary(rows),
                "record_type_filter": record_type,
                "provider_filter": provider,
                "sync_status_filter": sync_status,
                "issue_filter": issue,
                "record_type_choices": RECORD_TYPE_LABELS.items(),
                "provider_choices": EmailProvider.choices,
                "sync_status_choices": ProviderSyncStatus.choices,
                "issue_choices": ISSUE_LABELS.items(),
                "export_query": self.request.GET.urlencode(),
            }
        )
        return context


class ProviderSyncReadinessExportView(StaffRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        rows = provider_readiness_rows(
            record_type=request.GET.get("record_type", ""),
            provider=request.GET.get("provider", ""),
            sync_status=request.GET.get("sync_status", ""),
            issue=request.GET.get("issue", ""),
        )
        response = _csv_response("code-with-michael-provider-sync-readiness.csv")
        writer = csv.writer(response)
        writer.writerow(
            [
                "Record Type",
                "Name / Email",
                "Provider",
                "Sync Status",
                "Readiness Issue",
                "Missing Fields",
                "External ID",
                "External Audience/List ID",
                "Provider URL",
                "Last Synced At",
                "Provider Notes",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    RECORD_TYPE_LABELS.get(row.record_type, row.record_type),
                    row.label,
                    row.provider_label,
                    row.sync_status_label,
                    row.issue_label,
                    "; ".join(row.missing_fields),
                    row.external_id,
                    row.external_audience_id,
                    row.provider_url,
                    row.last_synced_display,
                    row.notes,
                ]
            )
        return response


class PublicLearnHomeView(ListView):
    model = Lesson
    template_name = "learn/home.html"
    context_object_name = "lessons"

    def get_queryset(self):
        return (
            _public_lessons_queryset()
            .select_related("category", "series")
            .order_by("series__title", "series_position", "title")[:12]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["series_list"] = (
            Series.objects.filter(
                is_active=True,
                lessons__website_status__in=[
                    Lesson.Status.READY,
                    Lesson.Status.PUBLISHED,
                ],
            )
            .annotate(
                published_lessons=Count(
                    "lessons",
                    filter=Q(
                        lessons__website_status__in=[
                            Lesson.Status.READY,
                            Lesson.Status.PUBLISHED,
                        ]
                    ),
                )
            )
            .order_by("title")
            .distinct()
        )
        context["playground_lessons"] = Lesson.objects.filter(
            enable_playground=True,
            website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED],
        ).select_related("category", "series")[:6]
        context["canonical_url"] = absolute_url(
            reverse("learn:home"), request=self.request
        )
        context["structured_data"] = website_schema(request=self.request)
        context["newsletter_form"] = NewsletterSignupForm()
        context["newsletter_source"] = NewsletterSubscriber.Source.LEARN_HOME
        context["featured_resources"] = (
            _public_resources_queryset()
            .filter(featured=True)
            .select_related("category")[:6]
        )
        return context


class PublicLessonListView(ListView):
    model = Lesson
    template_name = "learn/lesson_list.html"
    context_object_name = "lessons"
    paginate_by = 24

    def get_queryset(self):
        queryset = (
            _public_lessons_queryset()
            .select_related("category", "series")
            .prefetch_related("tags")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(learning_objective__icontains=query)
                | Q(beginner_takeaway__icontains=query)
                | Q(category__name__icontains=query)
                | Q(tags__name__icontains=query)
            )
        return queryset.distinct().order_by("series__title", "series_position", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["canonical_url"] = absolute_url(
            reverse("learn:lesson-list"), request=self.request
        )
        return context


class PublicSeriesDetailView(DetailView):
    model = Series
    template_name = "learn/series_detail.html"
    context_object_name = "series"

    def get_queryset(self):
        return Series.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                "lessons",
                queryset=Lesson.objects.filter(
                    website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED]
                )
                .exclude(status=Lesson.Status.ARCHIVED)
                .select_related("category", "series")
                .order_by("series_position", "title"),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lessons = list(self.object.lessons.all())
        context["canonical_url"] = series_canonical_url(
            self.object, request=self.request
        )
        context["structured_data"] = series_schema(
            self.object, lessons, request=self.request
        )
        return context


class PublicLessonDetailView(DetailView):
    model = Lesson
    template_name = "learn/lesson_detail.html"
    context_object_name = "lesson"

    def get_queryset(self):
        return (
            _public_lessons_queryset()
            .select_related("category", "series", "next_lesson")
            .prefetch_related(
                "blocks",
                "tags",
                "code_challenges__test_cases",
                "quiz_questions__choices",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _track_resource_conversion(
            self.request,
            ResourceLessonConversionEvent.EventType.LESSON_VIEW,
            lesson=self.object,
            metadata={"source": "public_lesson_detail"},
        )
        payload = render_website_page(
            self.object, request=self.request, is_preview=False
        )[1]
        context["page"] = payload["lesson"]
        context["brand"] = payload["brand"]
        context["canonical_url"] = lesson_canonical_url(
            self.object, request=self.request
        )
        context["structured_data"] = lesson_schema(self.object, request=self.request)
        if self.request.user.is_authenticated:
            context["progress"] = LessonProgress.objects.filter(
                user=self.request.user, lesson=self.object
            ).first()
            context["quiz_attempts"] = {
                attempt.question_id: attempt
                for attempt in QuizAttempt.objects.filter(
                    user=self.request.user, question__lesson=self.object
                ).order_by("question_id", "-created_at")
            }
            context["lesson_challenge_attempts"] = (
                ChallengeAttempt.objects.filter(
                    user=self.request.user, challenge__lesson=self.object
                )
                .select_related("challenge")
                .order_by("-created_at")[:10]
            )
        context["newsletter_form"] = NewsletterSignupForm()
        context["newsletter_source"] = NewsletterSubscriber.Source.LESSON
        if self.object.series_id:
            context["series_lessons"] = (
                Lesson.objects.filter(
                    series=self.object.series,
                    website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED],
                )
                .exclude(status=Lesson.Status.ARCHIVED)
                .order_by("series_position", "title")
            )
        return context


class PublicResourceListView(ListView):
    model = LearningResource
    template_name = "learn/resource_list.html"
    context_object_name = "resources"
    paginate_by = 24

    def get_queryset(self):
        queryset = (
            _public_resources_queryset()
            .select_related("category")
            .prefetch_related("tags", "related_lessons")
        )
        resource_type = self.request.GET.get("type", "").strip()
        query = self.request.GET.get("q", "").strip()
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
                | Q(beginner_tip__icontains=query)
                | Q(category__name__icontains=query)
                | Q(tags__name__icontains=query)
            )
        return queryset.distinct().order_by("resource_type", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_types"] = LearningResource.ResourceType.choices
        context["selected_type"] = self.request.GET.get("type", "")
        context["canonical_url"] = absolute_url(
            reverse("learn:resource-list"), request=self.request
        )
        return context


class PublicResourceDetailView(DetailView):
    model = LearningResource
    template_name = "learn/resource_detail.html"
    context_object_name = "resource"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        _track_resource_event(
            request, self.object, ResourcePerformanceEvent.EventType.VIEW
        )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        return (
            _public_resources_queryset()
            .select_related("category")
            .prefetch_related("tags", "related_lessons")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["canonical_url"] = resource_canonical_url(
            self.object, request=self.request
        )
        context["structured_data"] = resource_schema(self.object, request=self.request)
        context["pdf_is_gated"] = (
            self.object.pdf_download_enabled and self.object.pdf_requires_email
        )
        context["cta_blocks"] = self.object.cta_blocks.filter(
            is_active=True
        ).select_related("target_lesson")
        context["newsletter_form"] = NewsletterSignupForm()
        context["newsletter_source"] = NewsletterSubscriber.Source.RESOURCE
        return context


class PublicResourcePDFGateView(DetailView):
    model = LearningResource
    template_name = "learn/resource_pdf_gate.html"
    context_object_name = "resource"

    def get_queryset(self):
        return (
            _public_resources_queryset()
            .select_related("category")
            .prefetch_related("related_lessons")
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.pdf_download_enabled:
            return redirect(self.object.public_url)
        if not self.object.pdf_requires_email:
            return redirect("learn:resource-pdf", slug=self.object.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or NewsletterSignupForm()
        context["canonical_url"] = absolute_url(
            reverse("learn:resource-pdf-gate", kwargs={"slug": self.object.slug}),
            request=self.request,
        )
        return context

    def post(self, request, *args, **kwargs):
        resource = self.object
        form = NewsletterSignupForm(request.POST)
        if not form.is_valid():
            messages.error(
                request, "Please enter a valid email address to unlock the PDF."
            )
            return self.render_to_response(self.get_context_data(form=form))

        email = form.cleaned_data["email"]
        first_name = form.cleaned_data.get("first_name", "")
        source_url = request.build_absolute_uri(resource.public_url)[:300]
        defaults = {
            "first_name": first_name,
            "source": NewsletterSubscriber.Source.RESOURCE,
            "source_url": source_url,
            "source_resource": resource,
            "user": request.user if request.user.is_authenticated else None,
            "status": NewsletterSubscriber.Status.ACTIVE,
            "unsubscribed_at": None,
            "consent_text": "Send me beginner Python lessons, practice prompts, Code with Michael updates, and this resource download.",
        }
        subscriber, created = NewsletterSubscriber.objects.update_or_create(
            email=email, defaults=defaults
        )
        if not created and subscriber.status != NewsletterSubscriber.Status.ACTIVE:
            subscriber.mark_active()
            subscriber.source = NewsletterSubscriber.Source.RESOURCE
            subscriber.source_resource = resource
            subscriber.source_url = source_url
            subscriber.user = (
                request.user if request.user.is_authenticated else subscriber.user
            )
            subscriber.save(
                update_fields=[
                    "status",
                    "unsubscribed_at",
                    "subscribed_at",
                    "source",
                    "source_resource",
                    "source_url",
                    "user",
                    "updated_at",
                ]
            )

        access, _ = ResourceLeadMagnetAccess.objects.update_or_create(
            resource=resource,
            email=email,
            defaults={
                "subscriber": subscriber,
                "user": request.user if request.user.is_authenticated else None,
                "first_name": first_name,
                "source_url": source_url,
                "access_granted_at": timezone.now(),
            },
        )
        _track_resource_event(
            request,
            resource,
            ResourcePerformanceEvent.EventType.PDF_UNLOCK,
            subscriber=subscriber,
            email=email,
        )
        request.session[_resource_pdf_unlock_session_key(resource)] = True
        request.session[_resource_pdf_access_session_key(resource)] = access.pk
        messages.success(request, "Your PDF is unlocked. The download is ready.")
        return redirect("learn:resource-pdf", slug=resource.slug)


class PublicResourcePDFDownloadView(DetailView):
    model = LearningResource

    def get_queryset(self):
        return (
            _public_resources_queryset()
            .select_related("category")
            .prefetch_related("related_lessons")
        )

    def get(self, request, *args, **kwargs):
        resource = self.get_object()
        if not resource.pdf_download_enabled:
            return redirect(resource.public_url)
        if resource.pdf_requires_email and not request.session.get(
            _resource_pdf_unlock_session_key(resource)
        ):
            return redirect("learn:resource-pdf-gate", slug=resource.slug)
        access_id = request.session.get(_resource_pdf_access_session_key(resource))
        subscriber = None
        email = ""
        if access_id:
            access = (
                ResourceLeadMagnetAccess.objects.filter(pk=access_id, resource=resource)
                .select_related("subscriber")
                .first()
            )
            if access:
                access.register_download()
                subscriber = access.subscriber
                email = access.email
        _track_resource_event(
            request,
            resource,
            ResourcePerformanceEvent.EventType.PDF_DOWNLOAD,
            subscriber=subscriber,
            email=email,
        )
        pdf_bytes = render_learning_resource_pdf(
            resource,
            site_url=absolute_url(reverse("learn:home"), request=request),
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{resource_pdf_filename(resource)}"'
        )
        return response


class LearnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "learn/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        progress = LessonProgress.objects.filter(user=user).select_related(
            "lesson", "lesson__series", "lesson__category"
        )
        completed_count = progress.filter(
            status=LessonProgress.Status.COMPLETED
        ).count()
        in_progress_count = progress.filter(
            status=LessonProgress.Status.IN_PROGRESS
        ).count()
        week_start = timezone.now() - timedelta(days=7)
        weekly_minutes = (
            progress.filter(last_activity_at__gte=week_start).count() * 15
            + QuizAttempt.objects.filter(user=user, created_at__gte=week_start).count()
            * 3
            + ChallengeAttempt.objects.filter(
                user=user, created_at__gte=week_start
            ).count()
            * 10
        )
        weekly_goal = max(1, getattr(user, "weekly_goal_minutes", 30) or 30)
        context["learner_name"] = getattr(user, "learner_name", user.get_short_name())
        context["progress_records"] = progress[:20]
        context["completed_count"] = completed_count
        context["in_progress_count"] = in_progress_count
        context["quiz_correct_count"] = QuizAttempt.objects.filter(
            user=user, is_correct=True
        ).count()
        context["challenge_passed_count"] = ChallengeAttempt.objects.filter(
            user=user, passed=True
        ).count()
        context["badges"] = LearnerBadgeAward.objects.filter(user=user).select_related(
            "badge"
        )
        context["recommended_lessons"] = (
            _public_lessons_queryset()
            .exclude(progress_records__user=user)
            .select_related("category", "series")[:6]
        )
        context["estimated_learning_minutes"] = weekly_minutes
        context["weekly_goal_minutes"] = weekly_goal
        context["weekly_goal_percent"] = min(
            100, round(weekly_minutes / weekly_goal * 100)
        )
        context["recent_quiz_attempts"] = QuizAttempt.objects.filter(
            user=user
        ).select_related("question", "question__lesson", "selected_choice")[:5]
        context["recent_challenge_attempts"] = ChallengeAttempt.objects.filter(
            user=user
        ).select_related("challenge", "challenge__lesson")[:5]
        return context


class LearnerActivityView(LoginRequiredMixin, TemplateView):
    template_name = "learn/activity.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["progress_records"] = LessonProgress.objects.filter(
            user=user
        ).select_related("lesson", "lesson__series", "lesson__category")[:50]
        context["quiz_attempts"] = QuizAttempt.objects.filter(user=user).select_related(
            "question", "question__lesson", "selected_choice"
        )[:50]
        context["challenge_attempts"] = ChallengeAttempt.objects.filter(
            user=user
        ).select_related("challenge", "challenge__lesson")[:50]
        context["badge_awards"] = LearnerBadgeAward.objects.filter(
            user=user
        ).select_related("badge")[:50]
        return context


@login_required
def mark_lesson_complete(request, slug):
    lesson = get_object_or_404(_public_lessons_queryset(), slug=slug)
    if request.method != "POST":
        return redirect("learn:lesson-detail", slug=lesson.slug)
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    progress.mark_completed()
    progress.save()
    _track_resource_conversion(
        request,
        ResourceLessonConversionEvent.EventType.LESSON_COMPLETE,
        lesson=lesson,
        metadata={"status": progress.status},
    )
    awards = _award_earned_badges(request.user)
    if awards:
        messages.success(request, "Lesson completed. You also earned a new badge.")
    else:
        messages.success(request, "Lesson marked complete.")
    return redirect("learn:lesson-detail", slug=lesson.slug)


@login_required
def submit_quiz_answer(request, question_pk):
    question = get_object_or_404(
        QuizQuestion.objects.select_related("lesson").prefetch_related("choices"),
        pk=question_pk,
        is_active=True,
        lesson__website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED],
    )
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    choice_id = request.POST.get("choice_id")
    selected_choice = None
    if choice_id:
        selected_choice = get_object_or_404(question.choices, pk=choice_id)
    is_correct = bool(selected_choice and selected_choice.is_correct)
    feedback = (
        "Correct. Nice work."
        if is_correct
        else "Not quite. Review the choices and try again."
    )
    attempt = QuizAttempt.objects.create(
        question=question,
        user=request.user,
        selected_choice=selected_choice,
        response_text=request.POST.get("response_text", ""),
        is_correct=is_correct,
        feedback=feedback,
    )
    _track_resource_conversion(
        request,
        ResourceLessonConversionEvent.EventType.QUIZ_ATTEMPT,
        lesson=question.lesson,
        metadata={
            "question_id": question.pk,
            "attempt_id": attempt.pk,
            "is_correct": is_correct,
        },
        dedupe=False,
    )
    _refresh_lesson_progress(request.user, question.lesson)
    return JsonResponse({"correct": is_correct, "feedback": feedback})


@login_required
def submit_challenge_attempt(request, challenge_pk):
    challenge = get_object_or_404(
        CodeChallenge.objects.select_related("lesson").prefetch_related("test_cases"),
        pk=challenge_pk,
        is_active=True,
        lesson__website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED],
    )
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    submitted_code = request.POST.get("submitted_code", "")
    observed_output = request.POST.get("observed_output", "")
    raw_results = request.POST.get("test_results", "")
    test_results = {}
    if raw_results:
        try:
            test_results = json.loads(raw_results)
        except json.JSONDecodeError:
            test_results = {"error": "Submitted test results were not valid JSON."}

    active_test_count = challenge.test_cases.filter(is_active=True).count()
    tests_total = int(request.POST.get("tests_total") or active_test_count or 0)
    tests_passed = int(request.POST.get("tests_passed") or 0)
    client_passed = request.POST.get("passed") == "true"
    passed = (
        tests_total > 0 and tests_passed == tests_total
        if active_test_count
        else client_passed
    )
    feedback = (
        f"Saved as passed. {tests_passed}/{tests_total} tests passed."
        if passed and tests_total
        else f"Saved. {tests_passed}/{tests_total} tests passed."
        if tests_total
        else ("Saved as passed." if passed else "Saved for review.")
    )
    attempt = ChallengeAttempt.objects.create(
        challenge=challenge,
        user=request.user,
        submitted_code=submitted_code,
        observed_output=observed_output,
        test_results=test_results,
        tests_passed=tests_passed,
        tests_total=tests_total,
        passed=passed,
        feedback=feedback,
    )
    _track_resource_conversion(
        request,
        ResourceLessonConversionEvent.EventType.CHALLENGE_ATTEMPT,
        lesson=challenge.lesson,
        metadata={
            "challenge_id": challenge.pk,
            "attempt_id": attempt.pk,
            "passed": passed,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
        },
        dedupe=False,
    )
    _refresh_lesson_progress(request.user, challenge.lesson)
    return JsonResponse(
        {
            "passed": passed,
            "feedback": feedback,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "attempt_url": reverse(
                "learn:challenge-attempt-detail", kwargs={"pk": attempt.pk}
            ),
        }
    )


class ChallengeAttemptDetailView(LoginRequiredMixin, DetailView):
    model = ChallengeAttempt
    template_name = "learn/challenge_attempt_detail.html"
    context_object_name = "attempt"

    def get_queryset(self):
        return (
            ChallengeAttempt.objects.filter(user=self.request.user)
            .select_related(
                "challenge", "challenge__lesson", "challenge__lesson__series"
            )
            .prefetch_related("challenge__test_cases")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        raw_results = attempt.test_results or []
        if isinstance(raw_results, dict):
            if isinstance(raw_results.get("results"), list):
                results = raw_results["results"]
            elif isinstance(raw_results.get("error"), str):
                results = [
                    {
                        "name": "Saved test results",
                        "passed": False,
                        "observed": raw_results["error"],
                    }
                ]
            else:
                results = [
                    {"name": str(key), "observed": value, "passed": False}
                    for key, value in raw_results.items()
                ]
        elif isinstance(raw_results, list):
            results = raw_results
        else:
            results = []
        context["test_results_list"] = results
        context["previous_attempts"] = (
            ChallengeAttempt.objects.filter(
                user=self.request.user, challenge=attempt.challenge
            )
            .exclude(pk=attempt.pk)
            .order_by("-created_at")[:10]
        )
        return context


class PublicPlaygroundView(TemplateView):
    template_name = "learn/playground.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["canonical_url"] = absolute_url(
            reverse("learn:playground"), request=self.request
        )
        return context


class HelpView(StaffRequiredMixin, TemplateView):
    template_name = "studio/help.html"


class ProjectHealthView(StaffRequiredMixin, TemplateView):
    template_name = "studio/project_health.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checks = build_project_health_checks()
        context["checks"] = checks
        context["grouped_checks"] = grouped_project_health(checks)
        context["summary"] = project_health_summary(checks)
        context["generated_at"] = timezone.now()
        return context


class ProjectHealthExportView(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        checks = build_project_health_checks()
        response = _csv_response("code-with-michael-project-health.csv")
        writer = csv.writer(response)
        writer.writerow(["generated_at", timezone.now().isoformat()])
        writer.writerow([])
        writer.writerow(
            [
                "section",
                "status",
                "title",
                "detail",
                "count",
                "action_label",
                "action_url",
            ]
        )
        for check in checks:
            writer.writerow(
                [
                    check.section,
                    check.status,
                    check.title,
                    check.detail,
                    check.count if check.count is not None else "",
                    check.action_label,
                    request.build_absolute_uri(check.action_url)
                    if check.action_url
                    else "",
                ]
            )
        return response


class LearningResourceListView(StaffRequiredMixin, ListView):
    model = LearningResource
    template_name = "studio/resource_list.html"
    context_object_name = "resources"
    paginate_by = 30

    def get_queryset(self):
        queryset = LearningResource.objects.select_related("category").prefetch_related(
            "tags", "related_lessons"
        )
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        resource_type = self.request.GET.get("type", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
                | Q(internal_notes__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        return queryset.distinct().order_by("resource_type", "title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_types"] = LearningResource.ResourceType.choices
        context["statuses"] = LearningResource.Status.choices
        return context


class LearningResourceDetailView(StaffRequiredMixin, DetailView):
    model = LearningResource
    template_name = "studio/resource_detail.html"
    context_object_name = "resource"

    def get_queryset(self):
        return LearningResource.objects.select_related("category").prefetch_related(
            "tags", "related_lessons"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events = self.object.performance_events.all()
        views = events.filter(
            event_type=ResourcePerformanceEvent.EventType.VIEW
        ).count()
        unlocks = events.filter(
            event_type=ResourcePerformanceEvent.EventType.PDF_UNLOCK
        ).count()
        downloads = events.filter(
            event_type=ResourcePerformanceEvent.EventType.PDF_DOWNLOAD
        ).count()
        subscribers = NewsletterSubscriber.objects.filter(
            source_resource=self.object, status=NewsletterSubscriber.Status.ACTIVE
        ).count()
        context["resource_stats"] = {
            "views": views,
            "unlocks": unlocks,
            "downloads": downloads,
            "subscribers": subscribers,
            "unlock_rate": round(unlocks / views * 100, 2) if views else None,
            "download_rate": round(downloads / views * 100, 2) if views else None,
            "subscriber_rate": round(subscribers / views * 100, 2) if views else None,
        }
        context["cta_blocks"] = self.object.cta_blocks.select_related(
            "target_lesson"
        ).annotate(click_count=Count("click_events"))
        context["recent_cta_clicks"] = self.object.cta_click_events.select_related(
            "cta", "target_lesson", "user"
        )[:12]
        context["recent_resource_events"] = (
            self.object.performance_events.select_related("subscriber", "user")[:12]
        )
        recommendations = build_resource_cta_recommendations(self.object, limit=8)
        context["cta_recommendations"] = attach_recommendation_feedback(
            self.object, recommendations, user=self.request.user
        )
        context["cta_recommendation_feedback"] = (
            self.object.cta_recommendation_feedback.select_related(
                "target_lesson", "applied_cta"
            )[:10]
        )
        return context


@require_POST
@staff_required
def apply_resource_cta_recommendation(request, slug):
    resource = get_object_or_404(LearningResource, slug=slug)
    recommendation_key = request.POST.get("recommendation_key", "").strip()
    try:
        cta = create_cta_from_recommendation(
            resource, recommendation_key, user=request.user
        )
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"CTA recommendation applied: {cta.title}")
    return redirect(resource)


@require_POST
@staff_required
def dismiss_resource_cta_recommendation(request, slug):
    resource = get_object_or_404(LearningResource, slug=slug)
    recommendation_key = request.POST.get("recommendation_key", "").strip()
    try:
        feedback = mark_recommendation_dismissed(
            resource, recommendation_key, user=request.user
        )
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"CTA recommendation dismissed: {feedback.title}")
    return redirect(resource)


class ResourceCTARecommendationFeedbackReportView(StaffRequiredMixin, TemplateView):
    template_name = "studio/resource_cta_recommendation_feedback.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get("status", "").strip()
        target_type = self.request.GET.get("target_type", "").strip()
        queryset = ResourceCTARecommendationFeedback.objects.select_related(
            "resource", "target_lesson", "applied_cta", "updated_by"
        )
        if status:
            queryset = queryset.filter(status=status)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        context["feedback_rows"] = queryset[:200]
        context["statuses"] = ResourceCTARecommendationFeedback.Status.choices
        context["target_types"] = ResourceCTA.TargetType.choices
        context["selected_status"] = status
        context["selected_target_type"] = target_type
        context["recommendation_tuning"] = RecommendationTuning.get_active()
        context["report_template_totals"] = {
            "templates": ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.count(),
            "generated_reports": ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
                source_template__isnull=False
            ).count(),
            "keep": ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
                source_template__isnull=False,
                decision_status=ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.KEEP,
            ).count(),
            "roll_back": ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
                source_template__isnull=False,
                decision_status=ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.ROLL_BACK,
            ).count(),
        }
        context["summary"] = {
            "shown": ResourceCTARecommendationFeedback.objects.filter(
                status=ResourceCTARecommendationFeedback.Status.SHOWN
            ).count(),
            "accepted": ResourceCTARecommendationFeedback.objects.filter(
                status=ResourceCTARecommendationFeedback.Status.ACCEPTED
            ).count(),
            "dismissed": ResourceCTARecommendationFeedback.objects.filter(
                status=ResourceCTARecommendationFeedback.Status.DISMISSED
            ).count(),
            "ignored": ResourceCTARecommendationFeedback.objects.filter(
                status=ResourceCTARecommendationFeedback.Status.SHOWN, times_shown__gt=1
            ).count(),
            "accepted_patterns": ResourceCTARecommendationFeedback.objects.filter(
                status=ResourceCTARecommendationFeedback.Status.ACCEPTED
            )
            .values("target_type")
            .distinct()
            .count(),
            "dismissed_patterns": ResourceCTARecommendationFeedback.objects.filter(
                status=ResourceCTARecommendationFeedback.Status.DISMISSED
            )
            .values("target_type")
            .distinct()
            .count(),
        }
        return context


class LearningResourcePDFPreviewView(StaffRequiredMixin, DetailView):
    model = LearningResource

    def get_queryset(self):
        return LearningResource.objects.select_related("category").prefetch_related(
            "related_lessons"
        )

    def get(self, request, *args, **kwargs):
        resource = self.get_object()
        pdf_bytes = render_learning_resource_pdf(
            resource,
            site_url=absolute_url(reverse("learn:home"), request=request),
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{resource_pdf_filename(resource)}"'
        )
        return response


class ResourceIdeaGenerateView(StaffRequiredMixin, FormView):
    template_name = "studio/resource_idea_form.html"
    form_class = ResourceIdeaForm

    def form_valid(self, form):
        resource = create_resource_from_idea(
            ResourceIdeaDraft(
                topic=form.cleaned_data["topic"],
                resource_type=form.cleaned_data["resource_type"],
                audience=form.cleaned_data.get("audience") or "absolute beginners",
                category=form.cleaned_data.get("category"),
                related_lessons=list(form.cleaned_data.get("related_lessons") or []),
                featured=form.cleaned_data.get("featured", False),
                created_by=self.request.user,
            )
        )
        messages.success(
            self.request,
            "Draft resource generated. Review the content, examples, SEO fields, links, downloads, and status before publishing.",
        )
        return redirect(resource)


class LearningResourceCreateView(StaffRequiredMixin, CreateView):
    model = LearningResource
    form_class = LearningResourceForm
    template_name = "studio/resource_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Resource created.")
        return super().form_valid(form)


class LearningResourceUpdateView(StaffRequiredMixin, UpdateView):
    model = LearningResource
    form_class = LearningResourceForm
    template_name = "studio/resource_form.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Resource updated.")
        return super().form_valid(form)


class LearningResourceDeleteView(StaffRequiredMixin, DeleteView):
    model = LearningResource
    template_name = "studio/resource_confirm_delete.html"
    success_url = reverse_lazy("studio:resource-list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Resource deleted.")
        return super().delete(request, *args, **kwargs)


class ResourceCTACreateView(StaffRequiredMixin, CreateView):
    model = ResourceCTA
    form_class = ResourceCTAForm
    template_name = "studio/resource_cta_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.resource = get_object_or_404(LearningResource, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        next_position = (
            self.resource.cta_blocks.aggregate(Max("position"))["position__max"] or 0
        ) + 1
        initial.setdefault("position", next_position)
        target_type = self.request.GET.get("target_type")
        valid_types = {choice[0] for choice in ResourceCTA.TargetType.choices}
        if target_type in valid_types:
            initial["target_type"] = target_type
        return initial

    def form_valid(self, form):
        form.instance.resource = self.resource
        messages.success(self.request, "Resource CTA block saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.resource.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource"] = self.resource
        return context


class ResourceCTAUpdateView(StaffRequiredMixin, UpdateView):
    model = ResourceCTA
    form_class = ResourceCTAForm
    template_name = "studio/resource_cta_form.html"

    def get_queryset(self):
        return ResourceCTA.objects.select_related("resource", "target_lesson")

    def form_valid(self, form):
        messages.success(self.request, "Resource CTA block updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.resource.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource"] = self.object.resource
        return context


class ResourceCTADeleteView(StaffRequiredMixin, DeleteView):
    model = ResourceCTA
    template_name = "studio/resource_cta_confirm_delete.html"

    def get_queryset(self):
        return ResourceCTA.objects.select_related("resource")

    def get_success_url(self):
        return self.object.resource.get_absolute_url()

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Resource CTA block deleted.")
        return super().delete(request, *args, **kwargs)


class LessonListView(StaffRequiredMixin, ListView):
    model = Lesson
    template_name = "studio/lesson_list.html"
    context_object_name = "lessons"
    paginate_by = 30

    def get_queryset(self):
        queryset = Lesson.objects.select_related("category", "series")
        status = self.request.GET.get("status")
        if status in Lesson.Status.values:
            queryset = queryset.filter(status=status)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(seo_title__icontains=query)
                | Q(seo_description__icontains=query)
                | Q(internal_notes__icontains=query)
                | Q(blocks__title__icontains=query)
                | Q(blocks__content__icontains=query)
                | Q(category__name__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(series__title__icontains=query)
            )
        return queryset.distinct()


class LessonIdeaGenerateView(StaffRequiredMixin, FormView):
    template_name = "studio/lesson_idea_form.html"
    form_class = LessonIdeaForm

    def form_valid(self, form):
        lesson = create_lesson_from_idea(
            LessonIdeaDraft(
                topic=form.cleaned_data["topic"],
                audience=form.cleaned_data.get("audience") or "absolute beginners",
                objective=form.cleaned_data.get("objective") or "",
                category=form.cleaned_data.get("category"),
                series=form.cleaned_data.get("series"),
                include_quiz=form.cleaned_data.get("include_quiz", True),
                include_challenge=form.cleaned_data.get("include_challenge", True),
                created_by=self.request.user,
            )
        )
        messages.success(
            self.request,
            "Draft lesson generated. Review the details, code, output, quiz, challenge, and test case before publishing.",
        )
        return redirect(lesson)


class LessonCreateView(StaffRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = "studio/lesson_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Lesson created. Add its content blocks next.")
        return super().form_valid(form)


class LessonUpdateView(StaffRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = "studio/lesson_form.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Lesson saved.")
        return super().form_valid(form)


@staff_required
def duplicate_lesson(request, slug):
    source = get_object_or_404(
        Lesson.objects.prefetch_related(
            "tags", "blocks", "quiz_questions__choices", "code_challenges__test_cases"
        ),
        slug=slug,
    )
    if request.method != "POST":
        return redirect(source)

    copy = Lesson.objects.create(
        title=f"Copy of {source.title}",
        summary=source.summary,
        status=Lesson.Status.DRAFT,
        difficulty=source.difficulty,
        category=source.category,
        series=source.series,
        series_position=None,
        accent_color=source.accent_color,
        call_to_action=source.call_to_action,
        seo_title="",
        seo_description="",
        learning_objective=source.learning_objective,
        beginner_takeaway=source.beginner_takeaway,
        common_mistake=source.common_mistake,
        practice_prompt=source.practice_prompt,
        starter_code=source.starter_code,
        solution_code=source.solution_code,
        expected_output=source.expected_output,
        hint_1=source.hint_1,
        hint_2=source.hint_2,
        next_lesson=source.next_lesson,
        enable_playground=source.enable_playground,
        internal_notes=f"Duplicated from {source.title}.\n\n{source.internal_notes}".strip(),
        created_by=request.user,
        updated_by=request.user,
    )
    copy.tags.set(source.tags.all())
    for block in source.blocks.all():
        LessonBlock.objects.create(
            lesson=copy,
            position=block.position,
            block_type=block.block_type,
            title=block.title,
            content=block.content,
            data=block.data,
        )
    for question in source.quiz_questions.all():
        copied_question = QuizQuestion.objects.create(
            lesson=copy,
            position=question.position,
            question_type=question.question_type,
            prompt=question.prompt,
            explanation=question.explanation,
            is_active=question.is_active,
        )
        for choice in question.choices.all():
            QuizChoice.objects.create(
                question=copied_question,
                position=choice.position,
                text=choice.text,
                is_correct=choice.is_correct,
            )
    for challenge in source.code_challenges.all():
        copied_challenge = CodeChallenge.objects.create(
            lesson=copy,
            position=challenge.position,
            title=challenge.title,
            prompt=challenge.prompt,
            starter_code=challenge.starter_code,
            solution_code=challenge.solution_code,
            expected_output=challenge.expected_output,
            hint_1=challenge.hint_1,
            hint_2=challenge.hint_2,
            validation_mode=challenge.validation_mode,
            is_active=challenge.is_active,
        )
        for test_case in challenge.test_cases.all():
            ChallengeTestCase.objects.create(
                challenge=copied_challenge,
                position=test_case.position,
                name=test_case.name,
                description=test_case.description,
                test_code=test_case.test_code,
                expected_output=test_case.expected_output,
                is_active=test_case.is_active,
            )
    messages.success(
        request,
        "Lesson duplicated as a new draft, including blocks, quizzes, and challenges.",
    )
    return redirect(copy)


class LessonDetailView(StaffRequiredMixin, DetailView):
    model = Lesson
    template_name = "studio/lesson_detail.html"

    def get_queryset(self):
        return Lesson.objects.select_related("category", "series").prefetch_related(
            "blocks",
            "captions__generation",
            "assets__template",
            "ai_generations",
            "website_exports",
            "publishing_records__caption",
            "publishing_records__graphic",
            "content_plans__caption",
            "content_plans__graphic",
            "content_plans__publishing_record",
            "quiz_questions__choices",
            "code_challenges__test_cases",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["caption_form"] = CaptionGenerationForm()
        context["graphic_form"] = GraphicGenerationForm()
        context["block_template_form"] = BlockTemplateApplyForm()
        context["block_templates"] = BLOCK_TEMPLATES
        context["social_carousel_form"] = SocialCarouselTemplateApplyForm()
        context["social_carousel_templates"] = SOCIAL_CAROUSEL_TEMPLATES
        context["seo_diagnostics"] = seo_diagnostics(self.object)
        context["quality_diagnostics"] = self.object.quality_diagnostics
        context["platform_statuses"] = [
            (
                "Facebook",
                self.object.facebook_status,
                self.object.get_facebook_status_display(),
            ),
            (
                "Instagram",
                self.object.instagram_status,
                self.object.get_instagram_status_display(),
            ),
            (
                "Threads",
                self.object.threads_status,
                self.object.get_threads_status_display(),
            ),
            (
                "Website",
                self.object.website_status,
                self.object.get_website_status_display(),
            ),
        ]
        context["lesson_workflow"] = [
            {
                "label": "Details",
                "complete": bool(self.object.summary),
                "url": reverse("studio:lesson-update", args=[self.object.slug]),
            },
            {
                "label": "Content",
                "complete": self.object.blocks.exists(),
                "url": reverse("studio:block-create", args=[self.object.slug]),
            },
            {
                "label": "Social",
                "complete": self.object.blocks.filter(
                    title__icontains="Slide 1"
                ).exists()
                or self.object.assets.filter(status="ready").exists(),
                "url": "#social-carousels",
            },
            {
                "label": "Captions",
                "complete": self.object.captions.exists(),
                "url": "#captions",
            },
            {
                "label": "Planner",
                "complete": self.object.content_plans.exists(),
                "url": "#planner",
            },
            {
                "label": "Publishing",
                "complete": self.object.publishing_records.exists(),
                "url": "#publishing",
            },
            {
                "label": "Quiz/challenge",
                "complete": self.object.quiz_questions.exists()
                or self.object.code_challenges.exists(),
                "url": "#assessments",
            },
            {
                "label": "Website",
                "complete": self.object.website_exports.exists(),
                "url": "#website",
            },
        ]
        return context


@staff_required
def apply_block_template(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method != "POST":
        return redirect(lesson)
    form = BlockTemplateApplyForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Choose a valid block template.")
        return redirect(lesson)
    template = get_block_template(form.cleaned_data["template_key"])
    if not template:
        messages.error(request, "That block template is no longer available.")
        return redirect(lesson)
    created = apply_block_template_to_lesson(lesson, template)
    summary = ", ".join(
        f"{count} {label}"
        for label, count in [
            ("block(s)", created["blocks"]),
            ("quiz question(s)", created["quizzes"]),
            ("challenge(s)", created["challenges"]),
            ("test case(s)", created["tests"]),
        ]
        if count
    )
    messages.success(
        request, f"Applied {template.name}. Added {summary or 'template content'}."
    )
    return redirect(lesson.get_absolute_url() + "#block-templates")


@staff_required
def apply_social_carousel_template(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method != "POST":
        return redirect(lesson)
    form = SocialCarouselTemplateApplyForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Choose a valid social carousel template.")
        return redirect(lesson.get_absolute_url() + "#social-carousels")
    template = get_social_carousel_template(form.cleaned_data["template_key"])
    if not template:
        messages.error(request, "That social carousel template is no longer available.")
        return redirect(lesson.get_absolute_url() + "#social-carousels")
    try:
        created = apply_social_carousel_template_to_lesson(
            lesson,
            template,
            output_formats=form.cleaned_data.get("output_formats") or (),
            generate_now=form.cleaned_data.get("generate_now", False),
        )
    except GraphicGenerationError as exc:
        messages.error(
            request, f"Applied carousel blocks, but graphic generation failed: {exc}"
        )
        return redirect(lesson.get_absolute_url() + "#social-carousels")
    message = (
        f"Applied {template.name}. Added {created['blocks']} carousel-ready block(s)."
    )
    if created.get("assets"):
        message += f" Generated {created['assets']} graphic asset(s)."
    messages.success(request, message)
    return redirect(lesson.get_absolute_url() + "#social-carousels")


class BlockCreateView(StaffRequiredMixin, CreateView):
    model = LessonBlock
    form_class = LessonBlockForm
    template_name = "studio/block_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = get_object_or_404(Lesson, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.lesson = self.lesson
        form.instance.position = (
            self.lesson.blocks.aggregate(maximum=Max("position"))["maximum"] or 0
        ) + 1
        messages.success(self.request, "Content block added.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.lesson.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.lesson
        return context


class BlockUpdateView(StaffRequiredMixin, UpdateView):
    model = LessonBlock
    form_class = LessonBlockForm
    template_name = "studio/block_form.html"

    def get_success_url(self):
        messages.success(self.request, "Content block updated.")
        return self.object.lesson.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.lesson
        return context


@staff_required
def duplicate_block(request, pk):
    source = get_object_or_404(LessonBlock, pk=pk)
    if request.method != "POST":
        return redirect(source.lesson)

    new_position = (
        source.lesson.blocks.aggregate(maximum=Max("position"))["maximum"] or 0
    ) + 1
    LessonBlock.objects.create(
        lesson=source.lesson,
        position=new_position,
        block_type=source.block_type,
        title=source.title,
        content=source.content,
        data=source.data,
    )
    messages.success(request, "Content block duplicated at the end of the lesson.")
    return redirect(source.lesson)


class BlockDeleteView(StaffRequiredMixin, DeleteView):
    model = LessonBlock
    template_name = "studio/block_confirm_delete.html"

    def get_success_url(self):
        return self.object.lesson.get_absolute_url()


class QuizQuestionCreateView(StaffRequiredMixin, CreateView):
    model = QuizQuestion
    form_class = QuizQuestionForm
    template_name = "studio/assessment_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = get_object_or_404(Lesson, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["position"] = (
            self.lesson.quiz_questions.aggregate(maximum=Max("position"))["maximum"]
            or 0
        ) + 1
        return initial

    def form_valid(self, form):
        form.instance.lesson = self.lesson
        if not form.instance.position:
            form.instance.position = (
                self.lesson.quiz_questions.aggregate(maximum=Max("position"))["maximum"]
                or 0
            ) + 1
        messages.success(self.request, "Quiz question saved. Add answer choices next.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.lesson
        context["form_title"] = "Add quiz question"
        return context


class QuizQuestionUpdateView(StaffRequiredMixin, UpdateView):
    model = QuizQuestion
    form_class = QuizQuestionForm
    template_name = "studio/assessment_form.html"

    def get_success_url(self):
        messages.success(self.request, "Quiz question updated.")
        return self.object.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.lesson
        context["form_title"] = "Edit quiz question"
        return context


class QuizQuestionDeleteView(StaffRequiredMixin, DeleteView):
    model = QuizQuestion
    template_name = "studio/assessment_confirm_delete.html"

    def get_success_url(self):
        return self.object.lesson.get_absolute_url() + "#assessments"


class QuizChoiceCreateView(StaffRequiredMixin, CreateView):
    model = QuizChoice
    form_class = QuizChoiceForm
    template_name = "studio/assessment_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            QuizQuestion.objects.select_related("lesson"), pk=kwargs["question_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["position"] = (
            self.question.choices.aggregate(maximum=Max("position"))["maximum"] or 0
        ) + 1
        return initial

    def form_valid(self, form):
        form.instance.question = self.question
        if not form.instance.position:
            form.instance.position = (
                self.question.choices.aggregate(maximum=Max("position"))["maximum"] or 0
            ) + 1
        messages.success(self.request, "Answer choice saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.question.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.question.lesson
        context["form_title"] = "Add quiz answer choice"
        return context


class QuizChoiceUpdateView(StaffRequiredMixin, UpdateView):
    model = QuizChoice
    form_class = QuizChoiceForm
    template_name = "studio/assessment_form.html"

    def get_success_url(self):
        messages.success(self.request, "Answer choice updated.")
        return self.object.question.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.question.lesson
        context["form_title"] = "Edit quiz answer choice"
        return context


class QuizChoiceDeleteView(StaffRequiredMixin, DeleteView):
    model = QuizChoice
    template_name = "studio/assessment_confirm_delete.html"

    def get_success_url(self):
        return self.object.question.lesson.get_absolute_url() + "#assessments"


class CodeChallengeCreateView(StaffRequiredMixin, CreateView):
    model = CodeChallenge
    form_class = CodeChallengeForm
    template_name = "studio/assessment_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = get_object_or_404(Lesson, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["position"] = (
            self.lesson.code_challenges.aggregate(maximum=Max("position"))["maximum"]
            or 0
        ) + 1
        return initial

    def form_valid(self, form):
        form.instance.lesson = self.lesson
        if not form.instance.position:
            form.instance.position = (
                self.lesson.code_challenges.aggregate(maximum=Max("position"))[
                    "maximum"
                ]
                or 0
            ) + 1
        messages.success(self.request, "Code challenge saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.lesson
        context["form_title"] = "Add code challenge"
        return context


class CodeChallengeUpdateView(StaffRequiredMixin, UpdateView):
    model = CodeChallenge
    form_class = CodeChallengeForm
    template_name = "studio/assessment_form.html"

    def get_success_url(self):
        messages.success(self.request, "Code challenge updated.")
        return self.object.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.lesson
        context["form_title"] = "Edit code challenge"
        return context


class CodeChallengeDeleteView(StaffRequiredMixin, DeleteView):
    model = CodeChallenge
    template_name = "studio/assessment_confirm_delete.html"

    def get_success_url(self):
        return self.object.lesson.get_absolute_url() + "#assessments"


class ChallengeTestCaseCreateView(StaffRequiredMixin, CreateView):
    model = ChallengeTestCase
    form_class = ChallengeTestCaseForm
    template_name = "studio/assessment_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.challenge = get_object_or_404(
            CodeChallenge.objects.select_related("lesson"), pk=kwargs["challenge_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["position"] = (
            self.challenge.test_cases.aggregate(maximum=Max("position"))["maximum"] or 0
        ) + 1
        return initial

    def form_valid(self, form):
        form.instance.challenge = self.challenge
        if not form.instance.position:
            form.instance.position = (
                self.challenge.test_cases.aggregate(maximum=Max("position"))["maximum"]
                or 0
            ) + 1
        messages.success(self.request, "Challenge test case saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.challenge.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.challenge.lesson
        context["form_title"] = "Add challenge test case"
        return context


class ChallengeTestCaseUpdateView(StaffRequiredMixin, UpdateView):
    model = ChallengeTestCase
    form_class = ChallengeTestCaseForm
    template_name = "studio/assessment_form.html"

    def get_success_url(self):
        messages.success(self.request, "Challenge test case updated.")
        return self.object.challenge.lesson.get_absolute_url() + "#assessments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.challenge.lesson
        context["form_title"] = "Edit challenge test case"
        return context


class ChallengeTestCaseDeleteView(StaffRequiredMixin, DeleteView):
    model = ChallengeTestCase
    template_name = "studio/assessment_confirm_delete.html"

    def get_success_url(self):
        return self.object.challenge.lesson.get_absolute_url() + "#assessments"


class PublishingRecordCreateView(StaffRequiredMixin, CreateView):
    model = PublishingRecord
    form_class = PublishingRecordForm
    template_name = "studio/publishing_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = get_object_or_404(Lesson, slug=kwargs["slug"])
        self.content_plan = None
        plan_id = request.GET.get("plan") or request.POST.get("plan")
        if plan_id:
            self.content_plan = get_object_or_404(
                ContentPlan, pk=plan_id, lesson=self.lesson
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lesson"] = self.lesson
        return kwargs

    def form_valid(self, form):
        form.instance.lesson = self.lesson
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        _sync_platform_status_from_publishing_record(form.instance)
        if self.content_plan:
            self.content_plan.mark_posted(form.instance)
        messages.success(
            self.request, "Publishing record saved and platform status updated."
        )
        return response

    def get_initial(self):
        initial = super().get_initial()
        platform = self.request.GET.get("platform")
        valid_platforms = {choice[0] for choice in PublishingRecord.Platform.choices}
        if platform in valid_platforms:
            initial["platform"] = platform
        caption_id = self.request.GET.get("caption")
        if caption_id:
            initial["caption"] = caption_id
        graphic_id = self.request.GET.get("graphic")
        if graphic_id:
            initial["graphic"] = graphic_id
        if self.content_plan:
            initial.setdefault("platform", self.content_plan.platform)
            initial.setdefault("published_at", self.content_plan.scheduled_at)
            if self.content_plan.caption_id:
                initial.setdefault("caption", self.content_plan.caption_id)
            if self.content_plan.graphic_id:
                initial.setdefault("graphic", self.content_plan.graphic_id)
        return initial

    def get_success_url(self):
        return self.lesson.get_absolute_url() + "#publishing"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.lesson
        context["form_title"] = "Add publishing record"
        context["content_plan"] = self.content_plan
        return context


class PublishingRecordUpdateView(StaffRequiredMixin, UpdateView):
    model = PublishingRecord
    form_class = PublishingRecordForm
    template_name = "studio/publishing_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lesson"] = self.object.lesson
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        _sync_platform_status_from_publishing_record(form.instance)
        messages.success(self.request, "Publishing record updated.")
        return response

    def get_success_url(self):
        return self.object.lesson.get_absolute_url() + "#publishing"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.lesson
        context["form_title"] = "Edit publishing record"
        return context


class PublishingRecordDeleteView(StaffRequiredMixin, DeleteView):
    model = PublishingRecord
    template_name = "studio/publishing_confirm_delete.html"

    def get_success_url(self):
        return self.object.lesson.get_absolute_url() + "#publishing"


def _sync_platform_status_from_publishing_record(record):
    field_by_platform = {
        PublishingRecord.Platform.FACEBOOK: "facebook_status",
        PublishingRecord.Platform.INSTAGRAM: "instagram_status",
        PublishingRecord.Platform.THREADS: "threads_status",
        PublishingRecord.Platform.WEBSITE: "website_status",
    }
    field_name = field_by_platform.get(record.platform)
    if not field_name:
        return
    Lesson.objects.filter(pk=record.lesson_id).update(
        **{field_name: Lesson.Status.PUBLISHED}
    )


class CaptionUpdateView(StaffRequiredMixin, UpdateView):
    model = CaptionDraft
    form_class = CaptionDraftForm
    template_name = "studio/caption_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Caption draft saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.lesson.get_absolute_url()


class BrandProfileUpdateView(StaffRequiredMixin, UpdateView):
    model = BrandProfile
    form_class = BrandProfileForm
    template_name = "studio/brand_form.html"
    success_url = reverse_lazy("studio:brand-update")

    def get_object(self, queryset=None):
        return BrandProfile.get_default()

    def form_valid(self, form):
        messages.success(self.request, "Brand settings saved.")
        return super().form_valid(form)


@staff_required
def move_block(request, pk, direction):
    block = get_object_or_404(LessonBlock, pk=pk)
    if request.method != "POST" or direction not in {"up", "down"}:
        return redirect(block.lesson)

    candidates = block.lesson.blocks.exclude(pk=block.pk)
    if direction == "up":
        neighbor = (
            candidates.filter(position__lt=block.position).order_by("-position").first()
        )
    else:
        neighbor = (
            candidates.filter(position__gt=block.position).order_by("position").first()
        )

    if neighbor:
        with transaction.atomic():
            temporary_position = (
                block.lesson.blocks.aggregate(maximum=Max("position"))["maximum"] or 0
            ) + 1
            original_position = block.position
            LessonBlock.objects.filter(pk=block.pk).update(position=temporary_position)
            LessonBlock.objects.filter(pk=neighbor.pk).update(
                position=original_position
            )
            LessonBlock.objects.filter(pk=block.pk).update(position=neighbor.position)
        messages.success(request, "Content block order updated.")
    return redirect(block.lesson)


@staff_required
def generate_captions(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method != "POST":
        return redirect(lesson)
    form = CaptionGenerationForm(request.POST)
    if form.is_valid():
        created = 0
        for platform in form.cleaned_data["platforms"]:
            try:
                generate_caption(lesson, platform)
                created += 1
            except OpenAIServiceError as exc:
                messages.error(request, f"Could not generate {platform} caption: {exc}")
        if created:
            messages.success(request, f"Generated {created} caption draft(s).")
    else:
        messages.error(request, "Choose at least one caption platform.")
    return redirect(lesson)


@staff_required
def generate_graphic_assets(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method != "POST":
        return redirect(lesson)
    form = GraphicGenerationForm(request.POST)
    if form.is_valid():
        try:
            assets = generate_graphics(
                lesson,
                form.cleaned_data["template"],
                form.cleaned_data["output_formats"],
            )
            messages.success(request, f"Generated {len(assets)} graphic asset(s).")
        except GraphicGenerationError as exc:
            messages.error(request, f"Graphic generation failed: {exc}")
    else:
        messages.error(request, "Choose a template and at least one output format.")
    return redirect(lesson)


@staff_required
def website_preview(request, slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related("category", "series").prefetch_related(
            "blocks", "tags", "assets"
        ),
        slug=slug,
    )
    html, _ = render_website_page(lesson, request=request, is_preview=True)
    return HttpResponse(html)


@staff_required
def create_website_export_view(request, slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related("category", "series").prefetch_related(
            "blocks", "tags", "assets"
        ),
        slug=slug,
    )
    if request.method != "POST":
        return redirect(lesson)
    export = create_website_export(lesson, request.user, request=request)
    messages.success(request, f"Created website export revision {export.revision}.")
    return redirect(lesson)


@staff_required
def download_website_export(request, pk, output_format):
    export = get_object_or_404(WebsiteExport.objects.select_related("lesson"), pk=pk)
    if output_format == "json":
        content = json.dumps(export.payload, ensure_ascii=False, indent=2)
        content_type = "application/json"
        extension = "json"
    elif output_format == "html":
        content = export.rendered_html
        content_type = "text/html"
        extension = "html"
    else:
        return HttpResponse("Unsupported export format.", status=404)
    response = HttpResponse(content, content_type=f"{content_type}; charset=utf-8")
    filename = f"{export.lesson.slug}-r{export.revision}.{extension}"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
