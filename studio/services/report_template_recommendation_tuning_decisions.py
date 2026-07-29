"""Decision recommendations for report-template recommendation tuning snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone

from studio.models import (
    ReportTemplateRecommendationTuningChangeLog,
    ReportTemplateRecommendationTuningDecisionRules,
    ReportTemplateRecommendationTuningExperimentSnapshot,
)


@dataclass(frozen=True)
class TemplateRecommendationTuningDecision:
    decision: str
    label: str
    confidence: str
    score: float
    weighted_signals: list[dict[str, object]]
    recommended_status: str
    recommended_outcome: str
    decision_rules_name: str
    rule_thresholds: dict[str, object]
    summary: str
    positives: list[str]
    negatives: list[str]
    neutral_notes: list[str]
    next_steps: list[str]

    @property
    def css_class(self) -> str:
        if self.decision == "keep":
            return "success"
        if self.decision == "rollback":
            return "danger"
        return "warning"


SECTION_LABELS = {
    "template_usage": "Template usage",
    "saved_reports": "Saved reports",
    "decision_outcomes": "Report decisions",
    "recommendation_feedback": "Recommendation feedback",
}

METRIC_LABELS = {
    "reports_created": "reports created",
    "snapshots_attached": "snapshots attached",
    "presets_attached": "preset profiles attached",
    "keep_decisions": "Keep decisions",
    "rollback_decisions": "Roll back decisions",
    "watch_decisions": "Watch decisions",
    "archived_decisions": "Archived decisions",
    "undecided_reports": "undecided reports",
    "recommendations_shown": "recommendations shown",
    "useful_feedback": "useful feedback",
    "dismissed_feedback": "dismissed feedback",
    "revisit_feedback": "revisit-later feedback",
    "ignored_feedback": "ignored recommendations",
    "total_feedback_actions": "total feedback actions",
}

# Positive weights indicate signals that the template-ranking change helped Studio pick better report templates.
POSITIVE_WEIGHTS = {
    ("template_usage", "reports_created"): 3.0,
    ("saved_reports", "reports_created"): 2.2,
    ("saved_reports", "snapshots_attached"): 1.0,
    ("saved_reports", "presets_attached"): 0.7,
    ("decision_outcomes", "keep_decisions"): 3.4,
    ("decision_outcomes", "watch_decisions"): 1.2,
    ("recommendation_feedback", "useful_feedback"): 4.0,
    ("recommendation_feedback", "revisit_feedback"): 1.0,
    ("recommendation_feedback", "total_feedback_actions"): 0.8,
}

# Negative weights indicate friction or poor recommendation quality.
NEGATIVE_WEIGHTS = {
    ("decision_outcomes", "rollback_decisions"): 3.6,
    ("decision_outcomes", "archived_decisions"): 1.0,
    ("recommendation_feedback", "dismissed_feedback"): 4.0,
    ("recommendation_feedback", "ignored_feedback"): 1.6,
}

KEEP_THRESHOLD = 8.0
ROLLBACK_THRESHOLD = -7.0
PRIMARY_KEEP_MIN = 1
PRIMARY_ROLLBACK_MIN = 1
HIGH_CONFIDENCE_KEEP = 18.0
HIGH_CONFIDENCE_ROLLBACK = -16.0
LOW_CONFIDENCE_ABS = 5.0
MAX_CHANGE_MAGNITUDE = 25.0


def _change(
    snapshot: ReportTemplateRecommendationTuningExperimentSnapshot,
    section: str,
    metric: str,
) -> float:
    values = (snapshot.deltas or {}).get(section, {}).get(metric, {})
    raw = values.get("change")
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def _display_change(change: float) -> str:
    if change == int(change):
        return f"{int(change):+d}"
    return f"{change:+.2f}"


def _metric_note(section: str, metric: str, change: float) -> str:
    return f"{SECTION_LABELS.get(section, section.replace('_', ' ').title())}: {METRIC_LABELS.get(metric, metric.replace('_', ' '))} {_display_change(change)}"


def _weighted_row(
    section: str, metric: str, change: float, weight: float, contribution: float
) -> dict[str, object]:
    return {
        "section": SECTION_LABELS.get(section, section.replace("_", " ").title()),
        "metric": METRIC_LABELS.get(metric, metric.replace("_", " ")),
        "change": round(change, 4),
        "weight": weight,
        "contribution": round(contribution, 4),
        "direction": "positive"
        if contribution > 0
        else "negative"
        if contribution < 0
        else "neutral",
    }


def recommend_report_template_tuning_decision(
    snapshot: ReportTemplateRecommendationTuningExperimentSnapshot,
    decision_rules: ReportTemplateRecommendationTuningDecisionRules | None = None,
) -> TemplateRecommendationTuningDecision:
    """Return deterministic keep/rollback/watch guidance for a template-ranking tuning snapshot."""
    decision_rules = (
        decision_rules or ReportTemplateRecommendationTuningDecisionRules.get_active()
    )
    positives: list[str] = []
    negatives: list[str] = []
    neutral_notes: list[str] = []
    weighted_signals: list[dict[str, object]] = []
    score = 0.0

    for (section, metric), weight in decision_rules.positive_weight_items().items():
        change = _change(snapshot, section, metric)
        contribution = 0.0
        if change > 0:
            contribution = (
                min(decision_rules.max_metric_change_magnitude, change) * weight
            )
            positives.append(_metric_note(section, metric, change))
        elif change < 0:
            contribution = (
                max(-decision_rules.max_metric_change_magnitude, change) * weight
            )
            negatives.append(_metric_note(section, metric, change))
        score += contribution
        if change:
            weighted_signals.append(
                _weighted_row(section, metric, change, weight, contribution)
            )

    for (section, metric), weight in decision_rules.negative_weight_items().items():
        change = _change(snapshot, section, metric)
        contribution = 0.0
        if change > 0:
            contribution = (
                -min(decision_rules.max_metric_change_magnitude, change) * weight
            )
            negatives.append(_metric_note(section, metric, change))
        elif change < 0:
            contribution = (
                min(decision_rules.max_metric_change_magnitude, abs(change)) * weight
            )
            positives.append(_metric_note(section, metric, change))
        score += contribution
        if change:
            weighted_signals.append(
                _weighted_row(section, metric, change, weight, contribution)
            )

    weighted_signals.sort(
        key=lambda item: abs(float(item.get("contribution") or 0)), reverse=True
    )

    useful_feedback = _change(snapshot, "recommendation_feedback", "useful_feedback")
    dismissed_feedback = _change(
        snapshot, "recommendation_feedback", "dismissed_feedback"
    )
    ignored_feedback = _change(snapshot, "recommendation_feedback", "ignored_feedback")
    template_reports = _change(snapshot, "template_usage", "reports_created")
    keep_decisions = _change(snapshot, "decision_outcomes", "keep_decisions")
    rollback_decisions = _change(snapshot, "decision_outcomes", "rollback_decisions")

    primary_positive_count = sum(
        1 for value in [useful_feedback, template_reports, keep_decisions] if value > 0
    )
    primary_negative_count = sum(
        1
        for value in [dismissed_feedback, ignored_feedback, rollback_decisions]
        if value > 0
    )

    if not positives and not negatives:
        neutral_notes.append(
            "No meaningful before/after movement was detected for template usage or recommendation feedback."
        )

    if (
        score >= decision_rules.keep_score_threshold
        and primary_positive_count >= decision_rules.keep_primary_positive_min
    ):
        decision = "keep"
        label = "Keep changes"
        confidence = (
            "High" if score >= decision_rules.keep_high_confidence_score else "Medium"
        )
        recommended_status = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.KEEP
        )
        recommended_outcome = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentOutcome.POSITIVE
        )
        summary = "The after-window shows stronger template use, better recommendation feedback, or more favorable saved-report decisions."
        next_steps = [
            "Record the experiment outcome as positive.",
            "Keep the current report-template recommendation tuning active for the next reporting cycle.",
            "Create another snapshot after more reports are created to confirm the pattern is repeatable.",
        ]
    elif (
        score <= decision_rules.rollback_score_threshold
        and primary_negative_count >= decision_rules.rollback_primary_negative_min
    ):
        decision = "rollback"
        label = "Rollback recommended"
        confidence = (
            "High"
            if score <= decision_rules.rollback_high_confidence_score
            else "Medium"
        )
        recommended_status = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.ROLLBACK
        )
        recommended_outcome = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentOutcome.NEGATIVE
        )
        summary = "The after-window shows more dismissed/ignored recommendations, weaker template use, or more rollback-oriented saved reports."
        next_steps = [
            "Record the experiment outcome as negative.",
            "Use the rollback screen to restore the prior template-recommendation tuning snapshot if this was the main change.",
            "Try a narrower tuning adjustment before running another template-ranking experiment.",
        ]
    else:
        decision = "watch"
        label = "Keep watching"
        confidence = (
            "Low" if abs(score) < decision_rules.low_confidence_abs_score else "Medium"
        )
        recommended_status = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.INCONCLUSIVE
        )
        recommended_outcome = (
            ReportTemplateRecommendationTuningChangeLog.ExperimentOutcome.INCONCLUSIVE
        )
        summary = "The snapshot does not yet show enough evidence to confidently keep or roll back the template-recommendation tuning change."
        next_steps = [
            "Let the experiment run through another reporting cycle.",
            "Create a longer 30- or 60-day snapshot if template-report volume is low.",
            "Avoid rolling back unless the qualitative report-template suggestions also feel worse.",
        ]

    return TemplateRecommendationTuningDecision(
        decision=decision,
        label=label,
        confidence=confidence,
        score=round(score, 2),
        weighted_signals=weighted_signals[:12],
        recommended_status=recommended_status,
        recommended_outcome=recommended_outcome,
        decision_rules_name=decision_rules.name,
        rule_thresholds=decision_rules.threshold_summary(),
        summary=summary,
        positives=positives[:8],
        negatives=negatives[:8],
        neutral_notes=neutral_notes,
        next_steps=next_steps,
    )


def apply_report_template_tuning_decision_to_change_log(
    *,
    snapshot: ReportTemplateRecommendationTuningExperimentSnapshot,
    user=None,
    note: str = "",
) -> ReportTemplateRecommendationTuningChangeLog:
    """Save the snapshot recommendation back to the template-recommendation tuning change log."""
    recommendation = recommend_report_template_tuning_decision(snapshot)
    change_log = snapshot.change_log
    recommendation_note = (
        f"Report-template recommendation tuning decision from snapshot #{snapshot.pk}: {recommendation.label} "
        f"(confidence: {recommendation.confidence}, score: {recommendation.score}). {recommendation.summary}"
    )
    if note:
        recommendation_note = f"{recommendation_note}\n\nStaff note: {note}"
    if change_log.experiment_notes:
        change_log.experiment_notes = (
            f"{change_log.experiment_notes}\n\n{recommendation_note}"
        )
    else:
        change_log.experiment_notes = recommendation_note
    change_log.experiment_status = recommendation.recommended_status
    change_log.experiment_outcome = recommendation.recommended_outcome
    change_log.outcome_recorded_at = timezone.now()
    change_log.outcome_recorded_by = (
        user if getattr(user, "is_authenticated", False) else None
    )
    change_log.save(
        update_fields=[
            "experiment_status",
            "experiment_outcome",
            "experiment_notes",
            "outcome_recorded_at",
            "outcome_recorded_by",
            "updated_at",
        ]
    )
    return change_log
