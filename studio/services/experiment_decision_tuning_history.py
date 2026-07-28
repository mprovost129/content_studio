"""Audit logging and rollback helpers for experiment decision-rule tuning."""

from __future__ import annotations

from typing import Any

from studio.models import ExperimentDecisionTuning, ExperimentDecisionTuningChangeLog


DECISION_TUNING_EXCLUDED_FIELDS = {"id", "created_at", "updated_at"}


def decision_tuning_field_names() -> list[str]:
    names: list[str] = []
    for field in ExperimentDecisionTuning._meta.fields:
        if field.name in DECISION_TUNING_EXCLUDED_FIELDS:
            continue
        names.append(field.name)
    return names


def decision_tuning_snapshot(tuning: ExperimentDecisionTuning) -> dict[str, Any]:
    return {name: getattr(tuning, name) for name in decision_tuning_field_names()}


def build_decision_tuning_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    keys = sorted(set(before.keys()) | set(after.keys()))
    for key in keys:
        old = before.get(key)
        new = after.get(key)
        if old != new:
            diff[key] = {"before": old, "after": new}
    return diff


def create_decision_tuning_change_log(
    tuning: ExperimentDecisionTuning,
    *,
    before: dict[str, Any],
    action: str,
    changed_by=None,
    reason: str = "",
    request_path: str = "",
    preset_key: str = "",
    preset_name: str = "",
    experiment_label: str = "",
    experiment_status: str = "",
    experiment_notes: str = "",
) -> ExperimentDecisionTuningChangeLog | None:
    after = decision_tuning_snapshot(tuning)
    diff = build_decision_tuning_diff(before, after)
    if not diff and action == ExperimentDecisionTuningChangeLog.Action.MANUAL_UPDATE:
        return None
    return ExperimentDecisionTuningChangeLog.objects.create(
        tuning=tuning,
        action=action,
        changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
        preset_key=preset_key,
        preset_name=preset_name,
        reason=reason,
        before=before,
        after=after,
        diff=diff,
        request_path=request_path,
        experiment_label=experiment_label,
        experiment_status=experiment_status or ExperimentDecisionTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        experiment_notes=experiment_notes,
    )


def restore_decision_tuning_snapshot(
    source_log: ExperimentDecisionTuningChangeLog,
    *,
    snapshot: str = "before",
    changed_by=None,
    reason: str = "",
    request_path: str = "",
) -> ExperimentDecisionTuningChangeLog | None:
    if snapshot not in {"before", "after"}:
        raise ValueError("snapshot must be 'before' or 'after'")
    active = ExperimentDecisionTuning.get_active()
    before = decision_tuning_snapshot(active)
    target = source_log.before if snapshot == "before" else source_log.after
    for field_name in decision_tuning_field_names():
        if field_name in target:
            setattr(active, field_name, target[field_name])
    active.save()
    return create_decision_tuning_change_log(
        active,
        before=before,
        action=ExperimentDecisionTuningChangeLog.Action.ROLLBACK_RESTORED,
        changed_by=changed_by,
        reason=reason or f"Restored {snapshot}-change decision-rule snapshot from log #{source_log.pk}.",
        request_path=request_path,
    )
