"""Performance snapshots for recommendation tuning experiments."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Sum
from django.utils import timezone

from studio.models import (
    ExperimentDecisionTuningChangeLog,
    ExperimentDecisionTuningExperimentSnapshot,
    ExperimentDecisionTuningSnapshotComparisonReport,
    ExperimentDecisionTuningSnapshotComparisonReportTemplate,
    ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback,
    NewsletterCampaign,
    PublishingRecord,
    RecommendationTuningChangeLog,
    RecommendationTuningExperimentSnapshot,
    ReportTemplateRecommendationTuningChangeLog,
    ReportTemplateRecommendationTuningDecisionRulesChangeLog,
    ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot,
    ReportTemplateRecommendationTuningExperimentSnapshot,
    ResourceCTAClickEvent,
    ResourceLessonConversionEvent,
    ResourcePerformanceEvent,
)

SECTION_LABELS = {
    "social": "Social publishing",
    "resources": "Resource library",
    "newsletter": "Newsletter",
    "ctas": "Resource CTA clicks",
    "conversions": "Resource-to-lesson conversions",
}

METRIC_LABELS = {
    "posts": "Posts",
    "impressions": "Impressions",
    "reach": "Reach",
    "engagements": "Engagements",
    "engagement_rate": "Engagement rate",
    "clicks": "Clicks",
    "new_followers": "New followers",
    "views": "Resource views",
    "pdf_unlocks": "PDF unlocks",
    "pdf_downloads": "PDF downloads",
    "subscribers": "Resource subscribers",
    "campaigns": "Campaigns sent",
    "recipients": "Recipients",
    "opens": "Opens",
    "open_rate": "Open rate",
    "unsubscribes": "Unsubscribes",
    "bounces": "Bounces",
    "cta_clicks": "CTA clicks",
    "lesson_views": "Lesson views",
    "account_signups": "Account signups",
    "quiz_attempts": "Quiz attempts",
    "challenge_attempts": "Challenge attempts",
    "lesson_completions": "Lesson completions",
    "total_conversions": "Total conversions",
}

PERCENT_METRICS = {"engagement_rate", "open_rate"}


def _sum_dict(queryset, *fields: str) -> dict[str, int]:
    aggregated = queryset.aggregate(**{field: Sum(field) for field in fields})
    return {field: int(aggregated.get(field) or 0) for field in fields}


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if not denominator:
        return None
    return round(numerator / denominator * 100, 2)


def _count_by(queryset, field: str) -> dict[str, int]:
    return {
        row[field]: row["count"]
        for row in queryset.values(field).annotate(count=Count("id"))
    }


def _metrics_for_window(start, end) -> dict[str, dict[str, Any]]:
    publishing = PublishingRecord.objects.filter(
        published_at__gte=start, published_at__lt=end
    )
    social_sums = _sum_dict(
        publishing,
        "impressions",
        "reach",
        "likes",
        "comments",
        "saves",
        "shares",
        "clicks",
        "new_followers",
    )
    engagements = (
        social_sums["likes"]
        + social_sums["comments"]
        + social_sums["saves"]
        + social_sums["shares"]
        + social_sums["clicks"]
    )
    social = {
        "posts": publishing.count(),
        "impressions": social_sums["impressions"],
        "reach": social_sums["reach"],
        "engagements": engagements,
        "engagement_rate": _safe_rate(
            engagements, social_sums["reach"] or social_sums["impressions"]
        ),
        "clicks": social_sums["clicks"],
        "new_followers": social_sums["new_followers"],
    }

    resource_events = ResourcePerformanceEvent.objects.filter(
        occurred_at__gte=start, occurred_at__lt=end
    )
    resource_counts = _count_by(resource_events, "event_type")
    resources = {
        "views": resource_counts.get(ResourcePerformanceEvent.EventType.VIEW, 0),
        "pdf_unlocks": resource_counts.get(
            ResourcePerformanceEvent.EventType.PDF_UNLOCK, 0
        ),
        "pdf_downloads": resource_counts.get(
            ResourcePerformanceEvent.EventType.PDF_DOWNLOAD, 0
        ),
        "subscribers": resource_events.filter(subscriber__isnull=False)
        .values("subscriber_id")
        .distinct()
        .count(),
    }

    campaigns = NewsletterCampaign.objects.filter(
        status=NewsletterCampaign.Status.SENT, sent_at__gte=start, sent_at__lt=end
    )
    campaign_sums = _sum_dict(
        campaigns, "actual_recipients", "opens", "clicks", "unsubscribes", "bounces"
    )
    newsletter = {
        "campaigns": campaigns.count(),
        "recipients": campaign_sums["actual_recipients"],
        "opens": campaign_sums["opens"],
        "open_rate": _safe_rate(
            campaign_sums["opens"], campaign_sums["actual_recipients"]
        ),
        "clicks": campaign_sums["clicks"],
        "unsubscribes": campaign_sums["unsubscribes"],
        "bounces": campaign_sums["bounces"],
    }

    cta_clicks = ResourceCTAClickEvent.objects.filter(
        occurred_at__gte=start, occurred_at__lt=end
    )
    ctas = {"cta_clicks": cta_clicks.count()}

    conversion_events = ResourceLessonConversionEvent.objects.filter(
        occurred_at__gte=start, occurred_at__lt=end
    )
    conversion_counts = _count_by(conversion_events, "event_type")
    conversions = {
        "lesson_views": conversion_counts.get(
            ResourceLessonConversionEvent.EventType.LESSON_VIEW, 0
        ),
        "account_signups": conversion_counts.get(
            ResourceLessonConversionEvent.EventType.ACCOUNT_SIGNUP, 0
        ),
        "quiz_attempts": conversion_counts.get(
            ResourceLessonConversionEvent.EventType.QUIZ_ATTEMPT, 0
        ),
        "challenge_attempts": conversion_counts.get(
            ResourceLessonConversionEvent.EventType.CHALLENGE_ATTEMPT, 0
        ),
        "lesson_completions": conversion_counts.get(
            ResourceLessonConversionEvent.EventType.LESSON_COMPLETE, 0
        ),
        "total_conversions": conversion_events.count(),
    }

    return {
        "social": social,
        "resources": resources,
        "newsletter": newsletter,
        "ctas": ctas,
        "conversions": conversions,
    }


def _delta_value(before: Any, after: Any) -> dict[str, Any]:
    before_num = 0 if before is None else before
    after_num = 0 if after is None else after
    change = round(after_num - before_num, 2)
    pct = None
    if before_num:
        pct = round(change / before_num * 100, 2)
    return {"before": before, "after": after, "change": change, "pct": pct}


def build_snapshot_payload(
    change_log: RecommendationTuningChangeLog, window_days: int
) -> dict[str, Any]:
    anchor = change_log.created_at
    before_start = anchor - timedelta(days=window_days)
    before_end = anchor
    after_start = anchor
    after_end = anchor + timedelta(days=window_days)
    before_metrics = _metrics_for_window(before_start, before_end)
    after_metrics = _metrics_for_window(after_start, after_end)
    deltas: dict[str, dict[str, Any]] = {}
    for section_key, section_metrics in before_metrics.items():
        deltas[section_key] = {}
        for metric_key, before_value in section_metrics.items():
            deltas[section_key][metric_key] = _delta_value(
                before_value, after_metrics.get(section_key, {}).get(metric_key)
            )
    summary = {
        "primary_social_delta": deltas["social"].get("new_followers", {}),
        "primary_resource_delta": deltas["resources"].get("pdf_downloads", {}),
        "primary_newsletter_delta": deltas["newsletter"].get("clicks", {}),
        "primary_cta_delta": deltas["ctas"].get("cta_clicks", {}),
        "primary_conversion_delta": deltas["conversions"].get("total_conversions", {}),
    }
    return {
        "before_start": before_start,
        "before_end": before_end,
        "after_start": after_start,
        "after_end": after_end,
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "deltas": deltas,
        "summary": summary,
    }


def create_experiment_snapshot(
    *,
    change_log: RecommendationTuningChangeLog,
    window_days: int = 14,
    generated_by=None,
    notes: str = "",
) -> RecommendationTuningExperimentSnapshot:
    payload = build_snapshot_payload(change_log, window_days)
    return RecommendationTuningExperimentSnapshot.objects.create(
        change_log=change_log,
        window_days=window_days,
        generated_by=generated_by,
        generated_at=timezone.now(),
        notes=notes,
        **payload,
    )


def create_decision_rule_experiment_snapshot(
    *,
    change_log: ExperimentDecisionTuningChangeLog,
    window_days: int = 14,
    generated_by=None,
    notes: str = "",
) -> ExperimentDecisionTuningExperimentSnapshot:
    payload = build_snapshot_payload(change_log, window_days)
    return ExperimentDecisionTuningExperimentSnapshot.objects.create(
        change_log=change_log,
        window_days=window_days,
        generated_by=generated_by,
        generated_at=timezone.now(),
        notes=notes,
        **payload,
    )


def snapshot_section_rows(
    snapshot: RecommendationTuningExperimentSnapshot,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, metrics in (snapshot.deltas or {}).items():
        for metric_key, values in metrics.items():
            rows.append(
                {
                    "section_key": section_key,
                    "section_label": SECTION_LABELS.get(
                        section_key, section_key.replace("_", " ").title()
                    ),
                    "metric_key": metric_key,
                    "metric_label": METRIC_LABELS.get(
                        metric_key, metric_key.replace("_", " ").title()
                    ),
                    "before": values.get("before"),
                    "after": values.get("after"),
                    "change": values.get("change"),
                    "pct": values.get("pct"),
                    "is_percent_metric": metric_key in PERCENT_METRICS,
                }
            )
    return rows


TEMPLATE_SECTION_LABELS = {
    "template_usage": "Template usage",
    "saved_reports": "Saved comparison reports",
    "decision_outcomes": "Report decisions",
    "recommendation_feedback": "Recommendation feedback",
}

TEMPLATE_METRIC_LABELS = {
    "active_templates": "Active templates",
    "reports_created": "Reports created",
    "snapshots_attached": "Snapshots attached",
    "presets_attached": "Preset profiles attached",
    "keep_decisions": "Keep decisions",
    "rollback_decisions": "Roll back decisions",
    "watch_decisions": "Watch decisions",
    "archived_decisions": "Archived decisions",
    "undecided_reports": "Undecided reports",
    "recommendations_shown": "Recommendations shown",
    "useful_feedback": "Useful feedback",
    "dismissed_feedback": "Dismissed feedback",
    "revisit_feedback": "Revisit-later feedback",
    "ignored_feedback": "Ignored recommendations",
    "total_feedback_actions": "Total feedback actions",
}


def _template_metrics_for_window(start, end) -> dict[str, dict[str, Any]]:
    reports = ExperimentDecisionTuningSnapshotComparisonReport.objects.filter(
        created_at__gte=start, created_at__lt=end
    )
    reports_with_templates = reports.filter(source_template__isnull=False)
    decision_counts = _count_by(reports, "decision_status")
    snapshots_attached = sum(report.snapshots.count() for report in reports)
    presets_attached = sum(len(report.preset_keys or []) for report in reports)

    feedback = ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.objects.filter(
        last_seen_at__gte=start, last_seen_at__lt=end
    )
    feedback_counts = _count_by(feedback, "status")

    template_usage = {
        "active_templates": ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.filter(
            is_active=True
        ).count(),
        "reports_created": reports_with_templates.count(),
    }
    saved_reports = {
        "reports_created": reports.count(),
        "snapshots_attached": snapshots_attached,
        "presets_attached": presets_attached,
    }
    decision_outcomes = {
        "keep_decisions": decision_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.KEEP, 0
        ),
        "rollback_decisions": decision_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.ROLL_BACK, 0
        ),
        "watch_decisions": decision_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.WATCH, 0
        ),
        "archived_decisions": decision_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.ARCHIVED, 0
        ),
        "undecided_reports": decision_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.UNDECIDED, 0
        ),
    }
    recommendation_feedback = {
        "recommendations_shown": feedback.aggregate(total=Sum("times_shown")).get(
            "total"
        )
        or 0,
        "useful_feedback": feedback_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.USEFUL,
            0,
        ),
        "dismissed_feedback": feedback_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.DISMISSED,
            0,
        ),
        "revisit_feedback": feedback_counts.get(
            ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.REVISIT,
            0,
        ),
        "ignored_feedback": feedback.filter(
            status=ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.SHOWN,
            times_shown__gte=3,
        ).count(),
        "total_feedback_actions": feedback.exclude(
            status=ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.SHOWN
        ).count(),
    }
    return {
        "template_usage": template_usage,
        "saved_reports": saved_reports,
        "decision_outcomes": decision_outcomes,
        "recommendation_feedback": recommendation_feedback,
    }


def build_report_template_recommendation_tuning_snapshot_payload(
    change_log: ReportTemplateRecommendationTuningChangeLog, window_days: int
) -> dict[str, Any]:
    anchor = change_log.created_at
    before_start = anchor - timedelta(days=window_days)
    before_end = anchor
    after_start = anchor
    after_end = anchor + timedelta(days=window_days)
    before_metrics = _template_metrics_for_window(before_start, before_end)
    after_metrics = _template_metrics_for_window(after_start, after_end)
    deltas: dict[str, dict[str, Any]] = {}
    for section_key, section_metrics in before_metrics.items():
        deltas[section_key] = {}
        for metric_key, before_value in section_metrics.items():
            deltas[section_key][metric_key] = _delta_value(
                before_value, after_metrics.get(section_key, {}).get(metric_key)
            )
    summary = {
        "primary_template_delta": deltas["template_usage"].get("reports_created", {}),
        "primary_report_delta": deltas["saved_reports"].get("reports_created", {}),
        "primary_decision_delta": deltas["decision_outcomes"].get("keep_decisions", {}),
        "primary_feedback_delta": deltas["recommendation_feedback"].get(
            "useful_feedback", {}
        ),
    }
    return {
        "before_start": before_start,
        "before_end": before_end,
        "after_start": after_start,
        "after_end": after_end,
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "deltas": deltas,
        "summary": summary,
    }


def create_report_template_recommendation_tuning_experiment_snapshot(
    *,
    change_log: ReportTemplateRecommendationTuningChangeLog,
    window_days: int = 14,
    generated_by=None,
    notes: str = "",
) -> ReportTemplateRecommendationTuningExperimentSnapshot:
    payload = build_report_template_recommendation_tuning_snapshot_payload(
        change_log, window_days
    )
    return ReportTemplateRecommendationTuningExperimentSnapshot.objects.create(
        change_log=change_log,
        window_days=window_days,
        generated_by=generated_by,
        generated_at=timezone.now(),
        notes=notes,
        **payload,
    )


def report_template_snapshot_section_rows(
    snapshot: ReportTemplateRecommendationTuningExperimentSnapshot,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, metrics in (snapshot.deltas or {}).items():
        for metric_key, values in metrics.items():
            rows.append(
                {
                    "section_key": section_key,
                    "section_label": TEMPLATE_SECTION_LABELS.get(
                        section_key, section_key.replace("_", " ").title()
                    ),
                    "metric_key": metric_key,
                    "metric_label": TEMPLATE_METRIC_LABELS.get(
                        metric_key, metric_key.replace("_", " ").title()
                    ),
                    "before": values.get("before"),
                    "after": values.get("after"),
                    "change": values.get("change"),
                    "pct": values.get("pct"),
                    "is_percent_metric": False,
                }
            )
    return rows


def build_report_template_recommendation_decision_rule_snapshot_payload(
    change_log: ReportTemplateRecommendationTuningDecisionRulesChangeLog,
    window_days: int,
) -> dict[str, Any]:
    """Build before/after metrics for template-recommendation decision-rule experiments."""
    return build_report_template_recommendation_tuning_snapshot_payload(
        change_log, window_days
    )


def create_report_template_recommendation_decision_rule_experiment_snapshot(
    *,
    change_log: ReportTemplateRecommendationTuningDecisionRulesChangeLog,
    window_days: int = 14,
    generated_by=None,
    notes: str = "",
) -> ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot:
    payload = build_report_template_recommendation_decision_rule_snapshot_payload(
        change_log, window_days
    )
    return ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot.objects.create(
        change_log=change_log,
        window_days=window_days,
        generated_by=generated_by,
        generated_at=timezone.now(),
        notes=notes,
        **payload,
    )


def report_template_decision_rule_snapshot_section_rows(
    snapshot: ReportTemplateRecommendationTuningDecisionRulesExperimentSnapshot,
) -> list[dict[str, Any]]:
    return report_template_snapshot_section_rows(snapshot)
