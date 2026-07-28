from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from studio.models import RecommendationTuning, RecommendationTuningChangeLog

TUNING_WEIGHT_FIELDS = (
    "lesson_cta_bonus",
    "quiz_cta_bonus",
    "challenge_cta_bonus",
    "pdf_open_bonus",
    "pdf_lead_magnet_bonus",
    "newsletter_cta_bonus",
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


@dataclass(frozen=True)
class RecommendationTuningPreset:
    key: str
    name: str
    description: str
    values: dict[str, int]


PRESETS: tuple[RecommendationTuningPreset, ...] = (
    RecommendationTuningPreset(
        key="lead_magnet_growth",
        name="Lead Magnet Growth",
        description="Prioritizes gated PDFs and newsletter CTAs for growing the email list from high-intent resource readers.",
        values={
            "lesson_cta_bonus": 15,
            "quiz_cta_bonus": 25,
            "challenge_cta_bonus": 25,
            "pdf_open_bonus": 45,
            "pdf_lead_magnet_bonus": 95,
            "newsletter_cta_bonus": 70,
            "conversion_weight": 8,
            "conversion_cap": 60,
            "cta_click_weight": 5,
            "cta_click_cap": 40,
        },
    ),
    RecommendationTuningPreset(
        key="lesson_completion",
        name="Lesson Completion",
        description="Prioritizes matching lessons and related paths so resource readers move into full beginner lessons.",
        values={
            "lesson_cta_bonus": 65,
            "quiz_cta_bonus": 25,
            "challenge_cta_bonus": 30,
            "pdf_open_bonus": 25,
            "pdf_lead_magnet_bonus": 35,
            "newsletter_cta_bonus": 20,
            "related_lesson_weight": 105,
            "category_match_weight": 45,
            "difficulty_match_weight": 28,
            "topic_overlap_weight": 10,
            "topic_overlap_cap": 55,
            "conversion_weight": 9,
            "conversion_cap": 75,
        },
    ),
    RecommendationTuningPreset(
        key="quiz_engagement",
        name="Quiz Engagement",
        description="Pushes quick checks after reading so beginners can confirm that the concept clicked.",
        values={
            "lesson_cta_bonus": 25,
            "quiz_cta_bonus": 90,
            "challenge_cta_bonus": 35,
            "pdf_open_bonus": 25,
            "pdf_lead_magnet_bonus": 35,
            "newsletter_cta_bonus": 25,
            "active_quiz_weight": 35,
            "active_challenge_weight": 10,
            "practice_code_weight": 8,
            "cta_click_weight": 4,
            "cta_click_cap": 36,
        },
    ),
    RecommendationTuningPreset(
        key="challenge_practice",
        name="Challenge Practice",
        description="Prioritizes runnable coding challenges and hands-on practice after a learner reads a resource.",
        values={
            "lesson_cta_bonus": 25,
            "quiz_cta_bonus": 30,
            "challenge_cta_bonus": 100,
            "pdf_open_bonus": 20,
            "pdf_lead_magnet_bonus": 30,
            "newsletter_cta_bonus": 20,
            "active_quiz_weight": 12,
            "active_challenge_weight": 42,
            "practice_code_weight": 28,
            "related_lesson_weight": 85,
            "difficulty_match_weight": 25,
            "conversion_weight": 8,
            "conversion_cap": 64,
        },
    ),
)

PRESET_CHOICES = tuple((preset.key, preset.name) for preset in PRESETS)


TUNING_TRACKED_FIELDS = ("name", "is_active", *TUNING_WEIGHT_FIELDS, "notes")


def tuning_snapshot(tuning: RecommendationTuning) -> dict[str, object]:
    return {field: getattr(tuning, field) for field in TUNING_TRACKED_FIELDS}


def tuning_diff(before: dict[str, object], after: dict[str, object]) -> dict[str, dict[str, object]]:
    diff = {}
    for field in TUNING_TRACKED_FIELDS:
        old = before.get(field)
        new = after.get(field)
        if old != new:
            diff[field] = {"before": old, "after": new}
    return diff


def create_tuning_change_log(
    tuning: RecommendationTuning,
    *,
    before: dict[str, object],
    action: str,
    changed_by=None,
    preset: RecommendationTuningPreset | None = None,
    reason: str = "",
    request_path: str = "",
    experiment_label: str = "",
    experiment_status: str = "",
    experiment_notes: str = "",
) -> RecommendationTuningChangeLog | None:
    after = tuning_snapshot(tuning)
    diff = tuning_diff(before, after)
    if not diff:
        return None
    return RecommendationTuningChangeLog.objects.create(
        tuning=tuning,
        action=action,
        changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
        preset_key=preset.key if preset else "",
        preset_name=preset.name if preset else "",
        reason=reason,
        before=before,
        after=after,
        diff=diff,
        request_path=request_path[:300],
        experiment_label=(experiment_label or "")[:160],
        experiment_status=experiment_status or RecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        experiment_notes=experiment_notes or "",
    )


def get_preset(key: str) -> RecommendationTuningPreset | None:
    return next((preset for preset in PRESETS if preset.key == key), None)


def clone_tuning(tuning: RecommendationTuning, *, name: str | None = None, preset: RecommendationTuningPreset | None = None) -> RecommendationTuning:
    clone = RecommendationTuning(name=name or tuning.name, is_active=False, notes=tuning.notes)
    for field in TUNING_WEIGHT_FIELDS:
        setattr(clone, field, getattr(tuning, field))
    if preset:
        for field, value in preset.values.items():
            setattr(clone, field, value)
        clone.name = preset.name
        clone.notes = preset.description
    return clone


def apply_preset_to_active_tuning(
    preset: RecommendationTuningPreset,
    *,
    changed_by=None,
    reason: str = "",
    request_path: str = "",
    experiment_label: str = "",
    experiment_status: str = "",
    experiment_notes: str = "",
) -> RecommendationTuning:
    tuning = RecommendationTuning.get_active()
    before = tuning_snapshot(tuning)
    for field, value in preset.values.items():
        setattr(tuning, field, value)
    tuning.name = preset.name
    tuning.notes = preset.description
    tuning.is_active = True
    tuning.save()
    create_tuning_change_log(
        tuning,
        before=before,
        action=RecommendationTuningChangeLog.Action.PRESET_APPLIED,
        changed_by=changed_by,
        preset=preset,
        reason=reason,
        request_path=request_path,
        experiment_label=experiment_label,
        experiment_status=experiment_status,
        experiment_notes=experiment_notes,
    )
    return tuning


def preset_rows(active_tuning: RecommendationTuning | None = None) -> list[dict[str, object]]:
    active_tuning = active_tuning or RecommendationTuning.get_active()
    rows = []
    for preset in PRESETS:
        changes = []
        for field, value in preset.values.items():
            current = getattr(active_tuning, field)
            if current != value:
                changes.append({"field": field, "current": current, "preset": value, "delta": value - current})
        rows.append({"preset": preset, "changes": changes, "change_count": len(changes)})
    return rows


def build_tuning_from_preset_key(key: str | None) -> RecommendationTuning:
    active = RecommendationTuning.get_active()
    preset = get_preset(key or "")
    if not preset:
        return clone_tuning(active, name=f"Active: {active.name}")
    return clone_tuning(active, preset=preset)


def restore_tuning_snapshot(
    source_log: RecommendationTuningChangeLog,
    *,
    snapshot: str = "before",
    changed_by=None,
    reason: str = "",
    request_path: str = "",
) -> RecommendationTuning:
    """Restore the active recommendation tuning profile from a saved audit snapshot."""
    active = RecommendationTuning.get_active()
    before = tuning_snapshot(active)
    source = source_log.before if snapshot == "before" else source_log.after
    for field in TUNING_TRACKED_FIELDS:
        if field in source:
            setattr(active, field, source[field])
    active.is_active = True
    active.save()
    restore_label = "before" if snapshot == "before" else "after"
    default_reason = f"Restored the {restore_label} snapshot from tuning change #{source_log.pk}."
    create_tuning_change_log(
        active,
        before=before,
        action=RecommendationTuningChangeLog.Action.ROLLBACK_RESTORED,
        changed_by=changed_by,
        reason=reason or default_reason,
        request_path=request_path,
        experiment_label=source_log.experiment_label,
        experiment_status=RecommendationTuningChangeLog.ExperimentStatus.ROLLBACK,
        experiment_notes=f"Rollback from experiment: {source_log.experiment_notes}" if source_log.experiment_notes else "",
    )
    return active
