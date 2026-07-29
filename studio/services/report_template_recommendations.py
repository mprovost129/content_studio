"""Recommendation helpers for saved decision-rule comparison report templates."""

from dataclasses import dataclass, field

from django.utils import timezone

from studio.models import (
    ExperimentDecisionTuningExperimentSnapshot,
    ExperimentDecisionTuningSnapshotComparisonReport,
    ExperimentDecisionTuningSnapshotComparisonReportTemplate,
    ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback,
    ReportTemplateRecommendationTuning,
)


@dataclass
class TemplateRecommendation:
    template: ExperimentDecisionTuningSnapshotComparisonReportTemplate
    score: int
    score_parts: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    suggested_snapshots: list[ExperimentDecisionTuningExperimentSnapshot] = field(
        default_factory=list
    )
    recent_reports: list[ExperimentDecisionTuningSnapshotComparisonReport] = field(
        default_factory=list
    )
    recommendation_key: str = ""
    feedback_adjustment: int = 0
    feedback_notes: list[str] = field(default_factory=list)
    high_priority_threshold: int = 80
    medium_priority_threshold: int = 55

    @property
    def priority(self) -> str:
        if self.score >= self.high_priority_threshold:
            return "High"
        if self.score >= self.medium_priority_threshold:
            return "Medium"
        return "Low"

    @property
    def create_url_hint(self) -> str:
        return self.template.slug


def recommendation_key_for_template(template):
    return f"report-template:{template.pk}:type:{template.template_type}:window:{template.recommended_window_days}:snapshots:{template.recommended_snapshot_count}"


def _feedback_score(template, recommendation_key, tuning):
    """Return feedback adjustment and plain-English notes for a recommendation."""
    feedback = list(
        ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.objects.filter(
            template=template
        ).order_by("-last_seen_at")[:50]
    )
    exact = [item for item in feedback if item.recommendation_key == recommendation_key]

    score = 0
    notes = []
    useful_count = sum(1 for item in exact if item.status == item.Status.USEFUL)
    dismissed_count = sum(1 for item in exact if item.status == item.Status.DISMISSED)
    revisit_count = sum(1 for item in exact if item.status == item.Status.REVISIT)
    ignored_count = sum(1 for item in exact if item.is_ignored_signal)

    if useful_count:
        score += min(tuning.exact_useful_cap, useful_count * tuning.exact_useful_boost)
        notes.append(f"Exact recommendation was marked useful {useful_count} time(s).")
    if dismissed_count:
        score -= min(
            tuning.exact_dismissed_cap, dismissed_count * tuning.exact_dismissed_penalty
        )
        notes.append(f"Exact recommendation was dismissed {dismissed_count} time(s).")
    if revisit_count:
        score += min(
            tuning.exact_revisit_cap, revisit_count * tuning.exact_revisit_boost
        )
        notes.append(
            f"Exact recommendation was marked revisit later {revisit_count} time(s)."
        )
    if ignored_count:
        score -= min(
            tuning.exact_ignored_cap, ignored_count * tuning.exact_ignored_penalty
        )
        notes.append("This recommendation has been shown repeatedly without action.")

    type_feedback = [
        item for item in feedback if item.recommendation_key != recommendation_key
    ]
    type_useful = sum(1 for item in type_feedback if item.status == item.Status.USEFUL)
    type_dismissed = sum(
        1 for item in type_feedback if item.status == item.Status.DISMISSED
    )
    type_revisit = sum(
        1 for item in type_feedback if item.status == item.Status.REVISIT
    )
    if type_useful:
        score += min(
            tuning.similar_useful_cap, type_useful * tuning.similar_useful_boost
        )
        notes.append(
            "Similar recommendations for this template have been useful before."
        )
    if type_dismissed:
        score -= min(
            tuning.similar_dismissed_cap,
            type_dismissed * tuning.similar_dismissed_penalty,
        )
        notes.append(
            "Similar recommendations for this template have been dismissed before."
        )
    if type_revisit:
        score += min(
            tuning.similar_revisit_cap, type_revisit * tuning.similar_revisit_boost
        )
        notes.append("Similar recommendations were marked as worth revisiting.")

    return max(
        tuning.feedback_adjustment_floor, min(tuning.feedback_adjustment_ceiling, score)
    ), notes[:4]


def record_template_recommendation_shown(recommendation, user=None):
    feedback, created = (
        ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.objects.get_or_create(
            template=recommendation.template,
            recommendation_key=recommendation.recommendation_key,
            created_by=user if getattr(user, "is_authenticated", False) else None,
            defaults={
                "status": ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.SHOWN,
                "score": recommendation.score,
                "priority": recommendation.priority,
                "reasons": list(recommendation.reasons),
                "suggested_snapshot_ids": [
                    snapshot.pk for snapshot in recommendation.suggested_snapshots
                ],
                "updated_by": user
                if getattr(user, "is_authenticated", False)
                else None,
            },
        )
    )
    if not created and feedback.status == feedback.Status.SHOWN:
        feedback.times_shown += 1
        feedback.score = recommendation.score
        feedback.priority = recommendation.priority
        feedback.reasons = list(recommendation.reasons)
        feedback.suggested_snapshot_ids = [
            snapshot.pk for snapshot in recommendation.suggested_snapshots
        ]
        feedback.last_seen_at = timezone.now()
        feedback.updated_by = (
            user if getattr(user, "is_authenticated", False) else feedback.updated_by
        )
        feedback.save(
            update_fields=[
                "times_shown",
                "score",
                "priority",
                "reasons",
                "suggested_snapshot_ids",
                "last_seen_at",
                "updated_by",
                "updated_at",
            ]
        )
    return feedback


def record_template_recommendation_response(
    template,
    recommendation_key,
    status,
    user=None,
    score=0,
    priority="",
    reasons=None,
    suggested_snapshot_ids=None,
    notes="",
):
    valid = {
        ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.USEFUL,
        ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.DISMISSED,
        ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.REVISIT,
    }
    if status not in valid:
        raise ValueError("Invalid recommendation feedback status.")
    feedback, _created = (
        ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.objects.get_or_create(
            template=template,
            recommendation_key=recommendation_key,
            created_by=user if getattr(user, "is_authenticated", False) else None,
            defaults={
                "status": ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback.Status.SHOWN,
                "created_by": user
                if getattr(user, "is_authenticated", False)
                else None,
            },
        )
    )
    feedback.status = status
    feedback.score = score or feedback.score
    feedback.priority = priority or feedback.priority
    feedback.reasons = list(reasons or feedback.reasons or [])
    feedback.suggested_snapshot_ids = list(
        suggested_snapshot_ids or feedback.suggested_snapshot_ids or []
    )
    if notes:
        feedback.notes = notes
    feedback.responded_at = timezone.now()
    feedback.last_seen_at = timezone.now()
    feedback.updated_by = (
        user if getattr(user, "is_authenticated", False) else feedback.updated_by
    )
    feedback.save()
    return feedback


def _change(snapshot, key):
    try:
        return (snapshot.summary or {}).get(key, {}).get("change", 0) or 0
    except AttributeError:
        return 0


def _snapshot_focus_score(template, snapshots, tuning):
    """Score a template based on the type of recent snapshot movement available."""
    if not snapshots:
        return 0, ["No recent snapshots are available yet."]

    template_type = template.template_type
    score = 0
    reasons = []

    recent = snapshots[: max(1, template.recommended_snapshot_count or 1)]
    matching_window = [
        s for s in snapshots if s.window_days == template.recommended_window_days
    ]
    if matching_window:
        score += min(
            tuning.matching_window_cap,
            len(matching_window) * tuning.matching_window_weight,
        )
        reasons.append(
            f"Has {len(matching_window)} recent snapshot(s) with the recommended {template.recommended_window_days}-day window."
        )

    totals = {
        "social": sum(_change(s, "primary_social_delta") for s in recent),
        "resources": sum(_change(s, "primary_resource_delta") for s in recent),
        "newsletter": sum(_change(s, "primary_newsletter_delta") for s in recent),
        "cta": sum(_change(s, "primary_cta_delta") for s in recent),
        "conversions": sum(_change(s, "primary_conversion_delta") for s in recent),
    }

    if (
        template_type
        == ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.LEAD_MAGNET
    ):
        focus_total = totals["resources"] + totals["newsletter"] + totals["cta"]
        if focus_total > 0:
            score += min(28, 12 + focus_total * 2)
            reasons.append(
                "Recent snapshots show lead-magnet activity through resource downloads, newsletter clicks, or CTA clicks."
            )
    elif (
        template_type
        == ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.INSTAGRAM_EXPERIMENT
    ):
        focus_total = totals["social"]
        if focus_total > 0:
            score += min(25, 10 + focus_total * 2)
            reasons.append(
                "Recent snapshots include social follower-growth movement worth reviewing."
            )
    elif (
        template_type
        == ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.LEARNING_CONVERSION
    ):
        focus_total = totals["conversions"] + totals["cta"]
        if focus_total > 0:
            score += min(28, 12 + focus_total * 2)
            reasons.append("Recent snapshots show learner-conversion or CTA movement.")
    elif (
        template_type
        == ExperimentDecisionTuningSnapshotComparisonReportTemplate.TemplateType.MONTHLY_GROWTH
    ):
        focus_total = sum(value for value in totals.values() if value > 0)
        if focus_total > 0:
            score += min(25, 8 + focus_total)
            reasons.append(
                "Recent snapshots show broad movement across growth or learning metrics."
            )
    else:
        score += 6
        reasons.append("Custom template is available for a manual review structure.")

    return score, reasons


def _usage_score(template, reports_for_template, all_rows, tuning):
    score = 0
    reasons = []
    report_count = len(reports_for_template)
    if not report_count:
        score += tuning.unused_template_bonus
        reasons.append(
            "This active template has not been used yet, so it is a good candidate for coverage."
        )
    else:
        keep_count = sum(
            1
            for r in reports_for_template
            if r.decision_status
            == ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.KEEP
        )
        rollback_count = sum(
            1
            for r in reports_for_template
            if r.decision_status
            == ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.ROLL_BACK
        )
        watch_count = sum(
            1
            for r in reports_for_template
            if r.decision_status
            == ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.WATCH
        )
        if keep_count:
            score += min(
                tuning.keep_decision_cap, keep_count * tuning.keep_decision_weight
            )
            reasons.append(
                f"Prior reports from this template produced {keep_count} Keep decision(s)."
            )
        if watch_count:
            score += min(
                tuning.watch_decision_cap, watch_count * tuning.watch_decision_weight
            )
            reasons.append(
                f"Prior reports produced {watch_count} Watch decision(s), suggesting this template is useful for follow-up."
            )
        if rollback_count:
            score -= min(
                tuning.rollback_decision_cap,
                rollback_count * tuning.rollback_decision_penalty,
            )
            reasons.append(
                f"Prior reports produced {rollback_count} Roll back decision(s), so use this template more carefully."
            )

    type_report_counts = [
        row["total_reports"]
        for row in all_rows
        if row["template"].template_type == template.template_type
    ]
    if type_report_counts:
        average_for_type = sum(type_report_counts) / len(type_report_counts)
        if report_count < average_for_type:
            score += tuning.underused_family_bonus
            reasons.append(
                "This template is underused compared with others in the same family."
            )
    return score, reasons


def build_report_template_recommendations(user=None, limit=8, tuning=None):
    """Return ranked report-template recommendations for the next saved comparison report."""
    tuning = tuning or ReportTemplateRecommendationTuning.get_active()
    templates = list(
        ExperimentDecisionTuningSnapshotComparisonReportTemplate.objects.filter(
            is_active=True
        ).order_by("template_type", "title")
    )
    snapshots = list(
        ExperimentDecisionTuningExperimentSnapshot.objects.select_related(
            "change_log"
        ).order_by("-generated_at", "-pk")[:20]
    )
    reports = list(
        ExperimentDecisionTuningSnapshotComparisonReport.objects.select_related(
            "source_template"
        )
        .prefetch_related("snapshots")
        .order_by("-updated_at", "-pk")
    )
    reports_by_template = {}
    for report in reports:
        if report.source_template_id:
            reports_by_template.setdefault(report.source_template_id, []).append(report)

    usage_rows = []
    for template in templates:
        template_reports = reports_by_template.get(template.pk, [])
        usage_rows.append(
            {"template": template, "total_reports": len(template_reports)}
        )

    recommendations = []
    for template in templates:
        score = tuning.base_template_score
        score_parts = {"base": score}
        reasons = ["Active saved-report template is available."]
        template_reports = reports_by_template.get(template.pk, [])

        focus_score, focus_reasons = _snapshot_focus_score(template, snapshots, tuning)
        usage_score, usage_reasons = _usage_score(
            template, template_reports, usage_rows, tuning
        )
        score += focus_score + usage_score
        score_parts.update(
            {"snapshot_focus": focus_score, "usage_history": usage_score}
        )
        reasons.extend(focus_reasons)
        reasons.extend(usage_reasons)

        if template.focus_areas:
            focus_area_score = min(
                tuning.focus_area_cap,
                len(template.focus_areas) * tuning.focus_area_weight,
            )
            score += focus_area_score
            score_parts["focus_areas"] = focus_area_score
            reasons.append("Template includes defined focus areas for faster review.")
        if template.default_preset_keys:
            preset_default_score = min(
                tuning.preset_default_cap,
                len(template.default_preset_keys) * tuning.preset_default_weight,
            )
            score += preset_default_score
            score_parts["preset_defaults"] = preset_default_score
            reasons.append("Template already includes default decision-rule presets.")

        suggested = [
            s for s in snapshots if s.window_days == template.recommended_window_days
        ]
        if not suggested:
            suggested = snapshots
        suggested = suggested[: max(1, template.recommended_snapshot_count or 1)]

        recommendation_key = recommendation_key_for_template(template)
        feedback_adjustment, feedback_notes = _feedback_score(
            template, recommendation_key, tuning
        )
        score += feedback_adjustment
        score_parts["feedback"] = feedback_adjustment
        display_reasons = reasons[:6]
        if feedback_notes:
            display_reasons.extend(feedback_notes[:2])

        recommendations.append(
            TemplateRecommendation(
                template=template,
                score=max(0, int(score)),
                score_parts=score_parts,
                reasons=display_reasons[:8],
                suggested_snapshots=suggested,
                recent_reports=template_reports[:3],
                recommendation_key=recommendation_key,
                feedback_adjustment=feedback_adjustment,
                feedback_notes=feedback_notes,
                high_priority_threshold=tuning.high_priority_threshold,
                medium_priority_threshold=tuning.medium_priority_threshold,
            )
        )

    return sorted(
        recommendations,
        key=lambda item: (
            -item.score,
            item.template.get_template_type_display(),
            item.template.title,
        ),
    )[:limit]
