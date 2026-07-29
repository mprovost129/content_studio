"""Presets and simulation helpers for experiment decision-rule tuning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from studio.models import ExperimentDecisionTuning, ExperimentDecisionTuningChangeLog
from studio.services.experiment_decision_tuning_history import (
    create_decision_tuning_change_log,
    decision_tuning_field_names,
    decision_tuning_snapshot,
)

DECISION_TUNING_WEIGHT_FIELDS = tuple(
    field
    for field in decision_tuning_field_names()
    if field not in {"name", "is_active", "notes"}
)


@dataclass(frozen=True)
class ExperimentDecisionTuningPreset:
    key: str
    name: str
    description: str
    values: dict[str, Any]


DECISION_PRESETS: tuple[ExperimentDecisionTuningPreset, ...] = (
    ExperimentDecisionTuningPreset(
        key="aggressive_growth",
        name="Aggressive Growth",
        description="Favors keep decisions when follower growth, clicks, and learner conversions improve, even if minor quality signals are mixed.",
        values={
            "keep_score_threshold": 4.5,
            "keep_primary_positive_min": 1,
            "keep_high_confidence_score": 10.0,
            "rollback_score_threshold": -8.0,
            "rollback_primary_negative_min": 3,
            "rollback_high_confidence_score": -14.0,
            "social_new_followers_weight": 3.1,
            "social_clicks_weight": 2.0,
            "ctas_cta_clicks_weight": 2.4,
            "conversions_total_conversions_weight": 3.2,
            "conversions_lesson_views_weight": 1.6,
            "newsletter_unsubscribes_penalty_weight": 1.4,
            "newsletter_bounces_penalty_weight": 1.1,
        },
    ),
    ExperimentDecisionTuningPreset(
        key="conservative_quality",
        name="Conservative Quality",
        description="Requires stronger positive evidence before keeping a change and reacts more quickly to unsubscribes, bounces, or broad performance declines.",
        values={
            "keep_score_threshold": 9.0,
            "keep_primary_positive_min": 3,
            "keep_high_confidence_score": 16.0,
            "rollback_score_threshold": -4.0,
            "rollback_primary_negative_min": 1,
            "rollback_high_confidence_score": -8.0,
            "low_confidence_abs_score": 5.5,
            "newsletter_unsubscribes_penalty_weight": 3.4,
            "newsletter_bounces_penalty_weight": 2.8,
            "newsletter_open_rate_weight": 1.4,
            "resources_subscribers_weight": 2.2,
            "conversions_lesson_completions_weight": 2.8,
        },
    ),
    ExperimentDecisionTuningPreset(
        key="balanced_learning",
        name="Balanced Learning",
        description="Balances audience growth with deeper learner behavior: lesson views, quiz attempts, challenge attempts, and completions.",
        values={
            "keep_score_threshold": 6.0,
            "keep_primary_positive_min": 2,
            "keep_high_confidence_score": 12.0,
            "rollback_score_threshold": -5.0,
            "rollback_primary_negative_min": 2,
            "rollback_high_confidence_score": -10.0,
            "social_new_followers_weight": 1.8,
            "social_engagements_weight": 1.3,
            "resources_pdf_downloads_weight": 1.5,
            "newsletter_clicks_weight": 1.6,
            "ctas_cta_clicks_weight": 1.7,
            "conversions_total_conversions_weight": 2.4,
            "conversions_lesson_views_weight": 1.8,
            "conversions_quiz_attempts_weight": 2.0,
            "conversions_challenge_attempts_weight": 2.1,
            "conversions_lesson_completions_weight": 2.7,
        },
    ),
    ExperimentDecisionTuningPreset(
        key="lead_magnet_focus",
        name="Lead Magnet Focus",
        description="Prioritizes PDF unlocks, PDF downloads, new subscribers, and newsletter clicks when judging resource-led experiments.",
        values={
            "keep_score_threshold": 5.5,
            "keep_primary_positive_min": 2,
            "keep_high_confidence_score": 11.0,
            "rollback_score_threshold": -5.0,
            "resources_pdf_downloads_weight": 2.8,
            "resources_pdf_unlocks_weight": 2.5,
            "resources_subscribers_weight": 3.2,
            "newsletter_clicks_weight": 2.4,
            "newsletter_open_rate_weight": 1.2,
            "social_reach_weight": 0.6,
            "social_engagements_weight": 1.0,
            "conversions_total_conversions_weight": 2.0,
            "newsletter_unsubscribes_penalty_weight": 2.2,
        },
    ),
)

DECISION_PRESET_CHOICES = tuple(
    (preset.key, preset.name) for preset in DECISION_PRESETS
)


def get_decision_preset(key: str) -> ExperimentDecisionTuningPreset | None:
    return next((preset for preset in DECISION_PRESETS if preset.key == key), None)


def clone_decision_tuning(
    tuning: ExperimentDecisionTuning,
    *,
    name: str | None = None,
    preset: ExperimentDecisionTuningPreset | None = None,
) -> ExperimentDecisionTuning:
    clone = ExperimentDecisionTuning(
        name=name or tuning.name, is_active=False, notes=tuning.notes
    )
    for field in DECISION_TUNING_WEIGHT_FIELDS:
        setattr(clone, field, getattr(tuning, field))
    if preset:
        for field, value in preset.values.items():
            setattr(clone, field, value)
        clone.name = preset.name
        clone.notes = preset.description
    return clone


def build_decision_tuning_from_preset_key(key: str | None) -> ExperimentDecisionTuning:
    active = ExperimentDecisionTuning.get_active()
    preset = get_decision_preset(key or "")
    if not preset:
        return clone_decision_tuning(active, name=f"Active: {active.name}")
    return clone_decision_tuning(active, preset=preset)


def apply_decision_preset_to_active_tuning(
    preset: ExperimentDecisionTuningPreset,
    *,
    changed_by=None,
    reason: str = "",
    request_path: str = "",
    experiment_label: str = "",
    experiment_status: str = "",
    experiment_notes: str = "",
) -> ExperimentDecisionTuning:
    tuning = ExperimentDecisionTuning.get_active()
    before = decision_tuning_snapshot(tuning)
    for field, value in preset.values.items():
        setattr(tuning, field, value)
    tuning.name = preset.name
    tuning.notes = preset.description
    tuning.is_active = True
    tuning.save()
    create_decision_tuning_change_log(
        tuning,
        before=before,
        action=ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED,
        changed_by=changed_by,
        preset_key=preset.key,
        preset_name=preset.name,
        reason=reason or f"Applied decision-rule preset: {preset.name}.",
        request_path=request_path,
        experiment_label=experiment_label,
        experiment_status=experiment_status
        or ExperimentDecisionTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        experiment_notes=experiment_notes,
    )
    return tuning


def decision_preset_rows(
    active_tuning: ExperimentDecisionTuning | None = None,
) -> list[dict[str, object]]:
    active_tuning = active_tuning or ExperimentDecisionTuning.get_active()
    rows: list[dict[str, object]] = []
    for preset in DECISION_PRESETS:
        changes = []
        for field, value in preset.values.items():
            current = getattr(active_tuning, field)
            if current != value:
                delta = None
                if isinstance(current, (int, float)) and isinstance(
                    value, (int, float)
                ):
                    delta = value - current
                changes.append(
                    {
                        "field": field,
                        "current": current,
                        "preset": value,
                        "delta": delta,
                    }
                )
        rows.append(
            {"preset": preset, "changes": changes, "change_count": len(changes)}
        )
    return rows
