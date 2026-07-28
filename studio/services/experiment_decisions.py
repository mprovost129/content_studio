"""Decision recommendations for recommendation tuning experiment snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from studio.models import ExperimentDecisionTuning, RecommendationTuningChangeLog, RecommendationTuningExperimentSnapshot


@dataclass(frozen=True)
class DecisionRecommendation:
    decision: str
    label: str
    confidence: str
    score: float
    tuning: ExperimentDecisionTuning
    weighted_signals: list[dict[str, object]]
    recommended_status: str
    recommended_outcome: str
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


POSITIVE_WEIGHTS = {
    ("social", "new_followers"): 2.0,
    ("social", "engagements"): 1.4,
    ("social", "reach"): 0.8,
    ("social", "clicks"): 1.2,
    ("resources", "pdf_downloads"): 1.6,
    ("resources", "pdf_unlocks"): 1.3,
    ("resources", "subscribers"): 2.0,
    ("newsletter", "clicks"): 1.7,
    ("newsletter", "open_rate"): 0.8,
    ("ctas", "cta_clicks"): 1.8,
    ("conversions", "total_conversions"): 2.5,
    ("conversions", "lesson_views"): 1.2,
    ("conversions", "quiz_attempts"): 1.5,
    ("conversions", "challenge_attempts"): 1.7,
    ("conversions", "lesson_completions"): 2.2,
}

NEGATIVE_WEIGHTS = {
    ("newsletter", "unsubscribes"): 2.0,
    ("newsletter", "bounces"): 1.5,
}

SECTION_LABELS = {
    "social": "Social",
    "resources": "Resources",
    "newsletter": "Newsletter",
    "ctas": "CTA",
    "conversions": "Learner conversion",
}

METRIC_LABELS = {
    "new_followers": "new followers",
    "engagements": "engagements",
    "reach": "reach",
    "clicks": "clicks",
    "pdf_downloads": "PDF downloads",
    "pdf_unlocks": "PDF unlocks",
    "subscribers": "subscribers",
    "open_rate": "open rate",
    "cta_clicks": "CTA clicks",
    "total_conversions": "total conversions",
    "lesson_views": "lesson views",
    "quiz_attempts": "quiz attempts",
    "challenge_attempts": "challenge attempts",
    "lesson_completions": "lesson completions",
    "unsubscribes": "unsubscribes",
    "bounces": "bounces",
}


def _change(snapshot: RecommendationTuningExperimentSnapshot, section: str, metric: str) -> float:
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
    return f"{SECTION_LABELS.get(section, section.title())}: {METRIC_LABELS.get(metric, metric.replace('_', ' '))} {_display_change(change)}"


def recommend_experiment_decision(
    snapshot: RecommendationTuningExperimentSnapshot,
    tuning: ExperimentDecisionTuning | None = None,
) -> DecisionRecommendation:
    """Return a deterministic keep/rollback/inconclusive recommendation for a snapshot."""
    tuning = tuning or ExperimentDecisionTuning.get_active()
    positives: list[str] = []
    negatives: list[str] = []
    neutral_notes: list[str] = []
    weighted_signals: list[dict[str, object]] = []
    score = 0.0
    max_change = tuning.max_metric_change_magnitude

    for (section, metric), weight in tuning.positive_weight_items().items():
        change = _change(snapshot, section, metric)
        contribution = 0.0
        if change > 0:
            contribution = min(max_change, change) * weight
            positives.append(_metric_note(section, metric, change))
        elif change < 0:
            contribution = max(-max_change, change) * weight
            negatives.append(_metric_note(section, metric, change))
        score += contribution
        if change:
            weighted_signals.append({
                "section": SECTION_LABELS.get(section, section.title()),
                "metric": METRIC_LABELS.get(metric, metric.replace("_", " ")),
                "change": round(change, 4),
                "weight": weight,
                "contribution": round(contribution, 4),
                "direction": "positive" if contribution > 0 else "negative" if contribution < 0 else "neutral",
            })

    for (section, metric), weight in tuning.negative_weight_items().items():
        change = _change(snapshot, section, metric)
        contribution = 0.0
        if change > 0:
            contribution = -min(max_change, change) * weight
            negatives.append(_metric_note(section, metric, change))
        elif change < 0:
            contribution = min(max_change, abs(change)) * weight
            positives.append(_metric_note(section, metric, change))
        score += contribution
        if change:
            weighted_signals.append({
                "section": SECTION_LABELS.get(section, section.title()),
                "metric": METRIC_LABELS.get(metric, metric.replace("_", " ")),
                "change": round(change, 4),
                "weight": weight,
                "contribution": round(contribution, 4),
                "direction": "positive" if contribution > 0 else "negative" if contribution < 0 else "neutral",
            })

    weighted_signals.sort(key=lambda item: abs(float(item.get("contribution") or 0)), reverse=True)

    if not positives and not negatives:
        neutral_notes.append("No meaningful before/after movement was detected inside this snapshot window.")

    total_conversions = _change(snapshot, "conversions", "total_conversions")
    new_followers = _change(snapshot, "social", "new_followers")
    cta_clicks = _change(snapshot, "ctas", "cta_clicks")
    resource_downloads = _change(snapshot, "resources", "pdf_downloads")
    newsletter_clicks = _change(snapshot, "newsletter", "clicks")

    primary_positive_count = sum(1 for value in [total_conversions, new_followers, cta_clicks, resource_downloads, newsletter_clicks] if value > 0)
    primary_negative_count = sum(1 for value in [total_conversions, new_followers, cta_clicks, resource_downloads, newsletter_clicks] if value < 0)

    if score >= tuning.keep_score_threshold and primary_positive_count >= tuning.keep_primary_positive_min:
        decision = "keep"
        label = "Keep changes"
        confidence = "High" if score >= tuning.keep_high_confidence_score else "Medium"
        recommended_status = RecommendationTuningChangeLog.ExperimentStatus.KEEP
        recommended_outcome = RecommendationTuningChangeLog.ExperimentOutcome.POSITIVE
        summary = "The after-window improved across enough growth signals to justify keeping this tuning configuration."
        next_steps = [
            "Record the experiment outcome as positive.",
            "Keep the current tuning profile active for another content cycle.",
            "Create a fresh snapshot after the next posting window to confirm the lift is repeatable.",
        ]
    elif score <= tuning.rollback_score_threshold and primary_negative_count >= tuning.rollback_primary_negative_min:
        decision = "rollback"
        label = "Rollback recommended"
        confidence = "High" if score <= tuning.rollback_high_confidence_score else "Medium"
        recommended_status = RecommendationTuningChangeLog.ExperimentStatus.ROLLBACK
        recommended_outcome = RecommendationTuningChangeLog.ExperimentOutcome.NEGATIVE
        summary = "The after-window declined across multiple important signals, so the safer recommendation is to roll back or revise the tuning weights."
        next_steps = [
            "Record the experiment outcome as negative.",
            "Use the rollback screen to restore the before-change snapshot if this was the only major change in the window.",
            "Run a narrower preset or smaller weight change before testing again.",
        ]
    else:
        decision = "inconclusive"
        label = "Inconclusive"
        confidence = "Low" if abs(score) < tuning.low_confidence_abs_score else "Medium"
        recommended_status = RecommendationTuningChangeLog.ExperimentStatus.INCONCLUSIVE
        recommended_outcome = RecommendationTuningChangeLog.ExperimentOutcome.INCONCLUSIVE
        summary = "The snapshot does not show a strong enough signal to confidently keep or roll back the tuning change."
        next_steps = [
            "Extend the experiment window or create another snapshot after more posts and learner activity are recorded.",
            "Check whether other changes, seasonal traffic, or posting volume affected the before/after comparison.",
            "Avoid rolling back solely from this snapshot unless the qualitative content review also looks worse.",
        ]

    return DecisionRecommendation(
        decision=decision,
        label=label,
        confidence=confidence,
        score=round(score, 2),
        tuning=tuning,
        weighted_signals=weighted_signals[:12],
        recommended_status=recommended_status,
        recommended_outcome=recommended_outcome,
        summary=summary,
        positives=positives[:8],
        negatives=negatives[:8],
        neutral_notes=neutral_notes,
        next_steps=next_steps,
    )


def apply_decision_to_change_log(*, snapshot: RecommendationTuningExperimentSnapshot, user=None, note: str = "") -> RecommendationTuningChangeLog:
    """Save the recommendation back to the change log as the recorded experiment outcome."""
    recommendation = recommend_experiment_decision(snapshot)
    change_log = snapshot.change_log
    recommendation_note = (
        f"Decision recommendation from snapshot #{snapshot.pk}: {recommendation.label} "
        f"(confidence: {recommendation.confidence}, score: {recommendation.score}). {recommendation.summary}"
    )
    if note:
        recommendation_note = f"{recommendation_note}\n\nStaff note: {note}"
    if change_log.experiment_notes:
        change_log.experiment_notes = f"{change_log.experiment_notes}\n\n{recommendation_note}"
    else:
        change_log.experiment_notes = recommendation_note
    change_log.experiment_status = recommendation.recommended_status
    change_log.experiment_outcome = recommendation.recommended_outcome
    change_log.outcome_recorded_at = timezone.now()
    change_log.outcome_recorded_by = user if getattr(user, "is_authenticated", False) else None
    change_log.save(update_fields=[
        "experiment_status",
        "experiment_outcome",
        "experiment_notes",
        "outcome_recorded_at",
        "outcome_recorded_by",
        "updated_at",
    ])
    return change_log
