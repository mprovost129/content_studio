"""Launch-readiness and maintenance checks for the private Content Studio."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from django.db.models import Count, Q, Sum
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from studio.models import (
    CodeChallenge,
    ContentPlan,
    ExperimentDecisionTuning,
    ExperimentDecisionTuningChangeLog,
    ExperimentDecisionTuningSnapshotComparisonReport,
    ExperimentDecisionTuningSnapshotComparisonReportTemplate,
    LearningResource,
    Lesson,
    NewsletterCampaign,
    NewsletterSubscriber,
    PublishingRecord,
    RecommendationTuning,
    RecommendationTuningChangeLog,
    ReportTemplateRecommendationTuning,
    ReportTemplateRecommendationTuningChangeLog,
    ReportTemplateRecommendationTuningDecisionRules,
    ReportTemplateRecommendationTuningDecisionRulesChangeLog,
    ResourceLeadMagnetAccess,
    SubscriberSegment,
)


@dataclass(frozen=True)
class HealthCheck:
    section: str
    status: str
    title: str
    detail: str
    action_label: str = ""
    action_url: str = ""
    count: int | float | None = None

    @property
    def css_class(self) -> str:
        return {
            "good": "success",
            "watch": "warning",
            "action": "danger",
            "info": "info",
        }.get(self.status, "secondary")


_STATUS_RANK = {"action": 0, "watch": 1, "info": 2, "good": 3}


def _safe_reverse(name: str, *args, **kwargs) -> str:
    try:
        return reverse(name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ""


def _check(
    section: str,
    status: str,
    title: str,
    detail: str,
    *,
    action_label: str = "",
    action_url: str = "",
    count=None,
) -> HealthCheck:
    return HealthCheck(
        section=section,
        status=status,
        title=title,
        detail=detail,
        action_label=action_label,
        action_url=action_url,
        count=count,
    )


def _lesson_checks() -> list[HealthCheck]:
    public_lessons = Lesson.objects.filter(
        website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED]
    ).exclude(status=Lesson.Status.ARCHIVED)
    draft_lessons = Lesson.objects.filter(
        status__in=[Lesson.Status.IDEA, Lesson.Status.DRAFT, Lesson.Status.REVIEW]
    )
    ready_without_website = Lesson.objects.filter(
        status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED]
    ).exclude(website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED])
    missing_learning_fields = Lesson.objects.exclude(
        status=Lesson.Status.ARCHIVED
    ).filter(Q(learning_objective="") | Q(beginner_takeaway="") | Q(practice_prompt=""))
    published_without_blocks = (
        Lesson.objects.filter(
            website_status__in=[Lesson.Status.READY, Lesson.Status.PUBLISHED]
        )
        .annotate(block_count=Count("blocks"))
        .filter(block_count=0)
    )

    checks = [
        _check(
            "Learner site",
            "good" if public_lessons.exists() else "action",
            "Public lesson inventory",
            f"{public_lessons.count()} lesson(s) are eligible for the public /learn/ site.",
            action_label="Lessons",
            action_url=_safe_reverse("studio:lesson-list"),
            count=public_lessons.count(),
        ),
        _check(
            "Learner site",
            "watch" if draft_lessons.count() else "good",
            "Draft lesson backlog",
            f"{draft_lessons.count()} lesson(s) are still in idea, draft, or review status.",
            action_label="Lessons",
            action_url=_safe_reverse("studio:lesson-list"),
            count=draft_lessons.count(),
        ),
        _check(
            "Learner site",
            "watch" if ready_without_website.exists() else "good",
            "Website publish status alignment",
            f"{ready_without_website.count()} ready/published lesson(s) are not marked ready for the website.",
            action_label="Calendar",
            action_url=_safe_reverse("studio:content-calendar"),
            count=ready_without_website.count(),
        ),
        _check(
            "Lesson quality",
            "watch" if missing_learning_fields.exists() else "good",
            "Beginner learning fields",
            f"{missing_learning_fields.count()} active lesson(s) are missing an objective, takeaway, or practice prompt.",
            action_label="Lessons",
            action_url=_safe_reverse("studio:lesson-list"),
            count=missing_learning_fields.count(),
        ),
        _check(
            "Lesson quality",
            "action" if published_without_blocks.exists() else "good",
            "Published lessons with no blocks",
            f"{published_without_blocks.count()} public lesson(s) have no lesson blocks.",
            action_label="Lessons",
            action_url=_safe_reverse("studio:lesson-list"),
            count=published_without_blocks.count(),
        ),
    ]
    return checks


def _challenge_checks() -> list[HealthCheck]:
    active = CodeChallenge.objects.filter(is_active=True)
    no_tests_or_output = active.annotate(
        test_count=Count("test_cases", filter=Q(test_cases__is_active=True))
    ).filter(test_count=0, expected_output="")
    no_solution = active.filter(solution_code="")
    return [
        _check(
            "Practice system",
            "good" if active.exists() else "watch",
            "Active coding challenges",
            f"{active.count()} active challenge(s) are available across lessons.",
            action_label="Lessons",
            action_url=_safe_reverse("studio:lesson-list"),
            count=active.count(),
        ),
        _check(
            "Practice system",
            "watch" if no_tests_or_output.exists() else "good",
            "Challenge validation coverage",
            f"{no_tests_or_output.count()} active challenge(s) have neither active test cases nor expected output.",
            action_label="Lessons",
            action_url=_safe_reverse("studio:lesson-list"),
            count=no_tests_or_output.count(),
        ),
        _check(
            "Practice system",
            "watch" if no_solution.exists() else "good",
            "Challenge solution coverage",
            f"{no_solution.count()} active challenge(s) do not have reviewed solution code yet.",
            action_label="Lessons",
            action_url=_safe_reverse("studio:lesson-list"),
            count=no_solution.count(),
        ),
    ]


def _resource_checks() -> list[HealthCheck]:
    public_resources = LearningResource.objects.filter(
        status__in=[LearningResource.Status.READY, LearningResource.Status.PUBLISHED]
    )
    gated = LearningResource.objects.filter(
        pdf_download_enabled=True, pdf_requires_email=True
    ).exclude(status=LearningResource.Status.ARCHIVED)
    gated_missing_copy = gated.filter(
        Q(pdf_lead_magnet_headline="") | Q(pdf_lead_magnet_description="")
    )
    resources_without_cta = public_resources.annotate(
        cta_count=Count("cta_blocks", filter=Q(cta_blocks__is_active=True))
    ).filter(cta_count=0)
    downloads = (
        ResourceLeadMagnetAccess.objects.aggregate(total=Sum("download_count")).get(
            "total"
        )
        or 0
    )
    return [
        _check(
            "Resource library",
            "good" if public_resources.exists() else "watch",
            "Public resource inventory",
            f"{public_resources.count()} resource(s) are ready or published.",
            action_label="Resources",
            action_url=_safe_reverse("studio:resource-list"),
            count=public_resources.count(),
        ),
        _check(
            "Resource library",
            "watch" if gated_missing_copy.exists() else "good",
            "Lead magnet copy",
            f"{gated_missing_copy.count()} gated PDF resource(s) are missing unlock headline or description copy.",
            action_label="Resources",
            action_url=_safe_reverse("studio:resource-list"),
            count=gated_missing_copy.count(),
        ),
        _check(
            "Resource library",
            "watch" if resources_without_cta.exists() else "good",
            "Resource CTA coverage",
            f"{resources_without_cta.count()} public resource(s) have no active CTA blocks.",
            action_label="Resource CTAs",
            action_url=_safe_reverse("studio:resource-cta-report"),
            count=resources_without_cta.count(),
        ),
        _check(
            "Resource library",
            "info" if downloads else "watch",
            "Lead magnet downloads",
            f"{downloads} tracked gated-PDF download(s) have been recorded.",
            action_label="Resource reports",
            action_url=_safe_reverse("studio:resource-performance-report"),
            count=downloads,
        ),
    ]


def _content_ops_checks() -> list[HealthCheck]:
    now = timezone.now()
    next_14 = now + timedelta(days=14)
    upcoming = ContentPlan.objects.filter(
        scheduled_at__gte=now, scheduled_at__lte=next_14
    ).exclude(status__in=[ContentPlan.Status.POSTED, ContentPlan.Status.SKIPPED])
    overdue = ContentPlan.objects.filter(scheduled_at__lt=now).exclude(
        status__in=[ContentPlan.Status.POSTED, ContentPlan.Status.SKIPPED]
    )
    published_missing_url = PublishingRecord.objects.exclude(
        platform=PublishingRecord.Platform.WEBSITE
    ).filter(post_url="")
    published_missing_metrics = PublishingRecord.objects.filter(
        impressions=0, reach=0, likes=0, comments=0, saves=0, shares=0, clicks=0
    )
    return [
        _check(
            "Content operations",
            "good" if upcoming.exists() else "watch",
            "Upcoming planned content",
            f"{upcoming.count()} planned post(s) are scheduled for the next 14 days.",
            action_label="Planner",
            action_url=_safe_reverse("studio:content-planner"),
            count=upcoming.count(),
        ),
        _check(
            "Content operations",
            "action" if overdue.exists() else "good",
            "Overdue planned content",
            f"{overdue.count()} planned post(s) are past due and not marked posted or skipped.",
            action_label="Planner",
            action_url=_safe_reverse("studio:content-planner"),
            count=overdue.count(),
        ),
        _check(
            "Content operations",
            "watch" if published_missing_url.exists() else "good",
            "Published post URLs",
            f"{published_missing_url.count()} non-website publishing record(s) are missing a post URL.",
            action_label="Performance report",
            action_url=_safe_reverse("studio:performance-report"),
            count=published_missing_url.count(),
        ),
        _check(
            "Content operations",
            "watch" if published_missing_metrics.exists() else "good",
            "Publishing metric coverage",
            f"{published_missing_metrics.count()} publishing record(s) have no recorded engagement metrics yet.",
            action_label="Performance report",
            action_url=_safe_reverse("studio:performance-report"),
            count=published_missing_metrics.count(),
        ),
    ]


def _newsletter_checks() -> list[HealthCheck]:
    active_subscribers = NewsletterSubscriber.objects.filter(
        status=NewsletterSubscriber.Status.ACTIVE
    )
    segments = SubscriberSegment.objects.filter(is_active=True)
    campaigns = NewsletterCampaign.objects.exclude(
        status=NewsletterCampaign.Status.ARCHIVED
    )
    ready_without_schedule = campaigns.filter(
        status__in=[
            NewsletterCampaign.Status.READY,
            NewsletterCampaign.Status.SCHEDULED,
        ],
        scheduled_at__isnull=True,
    )
    sent_without_metrics = campaigns.filter(
        status=NewsletterCampaign.Status.SENT, actual_recipients=0, opens=0, clicks=0
    )
    return [
        _check(
            "Newsletter",
            "good" if active_subscribers.exists() else "watch",
            "Active subscribers",
            f"{active_subscribers.count()} active newsletter subscriber(s) are available.",
            action_label="Subscribers",
            action_url=_safe_reverse("studio:newsletter-subscriber-list"),
            count=active_subscribers.count(),
        ),
        _check(
            "Newsletter",
            "info" if segments.exists() else "watch",
            "Saved segments",
            f"{segments.count()} active saved segment(s) exist for targeting.",
            action_label="Segments",
            action_url=_safe_reverse("studio:subscriber-segment-list"),
            count=segments.count(),
        ),
        _check(
            "Newsletter",
            "watch" if ready_without_schedule.exists() else "good",
            "Campaign scheduling",
            f"{ready_without_schedule.count()} ready/scheduled campaign(s) are missing a scheduled date.",
            action_label="Campaigns",
            action_url=_safe_reverse("studio:newsletter-campaign-list"),
            count=ready_without_schedule.count(),
        ),
        _check(
            "Newsletter",
            "watch" if sent_without_metrics.exists() else "good",
            "Campaign metric imports",
            f"{sent_without_metrics.count()} sent campaign(s) have no recipient/open/click metrics yet.",
            action_label="Import metrics",
            action_url=_safe_reverse("studio:newsletter-metric-import"),
            count=sent_without_metrics.count(),
        ),
    ]


def _recommendation_checks() -> list[HealthCheck]:
    active_profiles = [
        (
            "CTA tuning",
            RecommendationTuning.objects.filter(is_active=True).count(),
            _safe_reverse("studio:recommendation-tuning"),
        ),
        (
            "Decision rules",
            ExperimentDecisionTuning.objects.filter(is_active=True).count(),
            _safe_reverse("studio:experiment-decision-tuning"),
        ),
        (
            "Template tuning",
            ReportTemplateRecommendationTuning.objects.filter(is_active=True).count(),
            _safe_reverse("studio:report-template-recommendation-tuning"),
        ),
        (
            "Template decision rules",
            ReportTemplateRecommendationTuningDecisionRules.objects.filter(
                is_active=True
            ).count(),
            _safe_reverse(
                "studio:report-template-recommendation-tuning-decision-rules"
            ),
        ),
    ]
    checks = [
        _check(
            "Recommendation system",
            "good" if count == 1 else "action",
            title,
            f"{count} active profile(s) found. Exactly one active profile is recommended.",
            action_label="Open",
            action_url=url,
            count=count,
        )
        for title, count, url in active_profiles
    ]
    open_experiments = (
        RecommendationTuningChangeLog.objects.filter(
            experiment_status__in=["planned", "running"]
        ).count()
        + ExperimentDecisionTuningChangeLog.objects.filter(
            experiment_status__in=["planned", "running"]
        ).count()
        + ReportTemplateRecommendationTuningChangeLog.objects.filter(
            experiment_status__in=["planned", "running"]
        ).count()
        + ReportTemplateRecommendationTuningDecisionRulesChangeLog.objects.filter(
            experiment_status__in=["planned", "running"]
        ).count()
    )
    checks.append(
        _check(
            "Recommendation system",
            "info" if open_experiments else "good",
            "Open recommendation experiments",
            f"{open_experiments} recommendation or decision experiment(s) are currently planned/running.",
            action_label="Tuning history",
            action_url=_safe_reverse("studio:recommendation-tuning-history"),
            count=open_experiments,
        )
    )
    reports_without_decision = ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
        decision_status=ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.UNDECIDED
    ).count()
    checks.append(
        _check(
            "Recommendation system",
            "watch" if reports_without_decision else "good",
            "Saved comparison decisions",
            f"{reports_without_decision} saved comparison report(s) still have no decision status.",
            action_label="Saved comparisons",
            action_url=_safe_reverse(
                "studio:experiment-decision-tuning-snapshot-comparison-reports"
            ),
            count=reports_without_decision,
        )
    )
    templates = ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.filter(
        is_active=True
    ).count()
    checks.append(
        _check(
            "Recommendation system",
            "good" if templates else "watch",
            "Active saved-report templates",
            f"{templates} active comparison-report template(s) are available.",
            action_label="Report templates",
            action_url=_safe_reverse(
                "studio:experiment-decision-tuning-snapshot-comparison-report-templates"
            ),
            count=templates,
        )
    )
    return checks


def build_project_health_checks() -> list[HealthCheck]:
    checks: list[HealthCheck] = []
    for builder in (
        _lesson_checks,
        _challenge_checks,
        _resource_checks,
        _content_ops_checks,
        _newsletter_checks,
        _recommendation_checks,
    ):
        checks.extend(builder())
    return sorted(
        checks,
        key=lambda check: (
            _STATUS_RANK.get(check.status, 9),
            check.section,
            check.title,
        ),
    )


def project_health_summary(checks: Iterable[HealthCheck]) -> dict[str, int]:
    summary = {"action": 0, "watch": 0, "good": 0, "info": 0, "total": 0}
    for check in checks:
        summary[check.status] = summary.get(check.status, 0) + 1
        summary["total"] += 1
    return summary


def grouped_project_health(
    checks: Iterable[HealthCheck],
) -> dict[str, list[HealthCheck]]:
    grouped: dict[str, list[HealthCheck]] = {}
    for check in checks:
        grouped.setdefault(check.section, []).append(check)
    return grouped
