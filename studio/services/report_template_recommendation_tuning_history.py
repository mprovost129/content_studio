"""Audit logging and rollback helpers for report-template recommendation tuning."""

from __future__ import annotations

from typing import Any

from studio.models import (
    ReportTemplateRecommendationTuning,
    ReportTemplateRecommendationTuningChangeLog,
)

EXCLUDED_FIELDS = {"id", "created_at", "updated_at"}


def report_template_tuning_field_names() -> list[str]:
    return [
        field.name
        for field in ReportTemplateRecommendationTuning._meta.fields
        if field.name not in EXCLUDED_FIELDS
    ]


def report_template_tuning_snapshot(
    tuning: ReportTemplateRecommendationTuning,
) -> dict[str, Any]:
    return {
        name: getattr(tuning, name) for name in report_template_tuning_field_names()
    }


def build_report_template_tuning_diff(
    before: dict[str, Any], after: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    for key in sorted(set(before.keys()) | set(after.keys())):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            diff[key] = {"before": old, "after": new}
    return diff


def create_report_template_tuning_change_log(
    tuning: ReportTemplateRecommendationTuning,
    *,
    before: dict[str, Any],
    action: str,
    changed_by=None,
    reason: str = "",
    request_path: str = "",
    experiment_label: str = "",
    experiment_status: str = "",
    experiment_notes: str = "",
) -> ReportTemplateRecommendationTuningChangeLog | None:
    after = report_template_tuning_snapshot(tuning)
    diff = build_report_template_tuning_diff(before, after)
    if (
        not diff
        and action == ReportTemplateRecommendationTuningChangeLog.Action.MANUAL_UPDATE
    ):
        return None
    return ReportTemplateRecommendationTuningChangeLog.objects.create(
        tuning=tuning,
        action=action,
        changed_by=changed_by
        if getattr(changed_by, "is_authenticated", False)
        else None,
        reason=reason,
        before=before,
        after=after,
        diff=diff,
        request_path=request_path[:300],
        experiment_label=experiment_label,
        experiment_status=experiment_status
        or ReportTemplateRecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        experiment_notes=experiment_notes,
    )


def restore_report_template_tuning_snapshot(
    source_log: ReportTemplateRecommendationTuningChangeLog,
    *,
    snapshot: str = "before",
    changed_by=None,
    reason: str = "",
    request_path: str = "",
) -> ReportTemplateRecommendationTuningChangeLog | None:
    if snapshot not in {"before", "after"}:
        raise ValueError("snapshot must be 'before' or 'after'")
    active = ReportTemplateRecommendationTuning.get_active()
    before = report_template_tuning_snapshot(active)
    target = source_log.before if snapshot == "before" else source_log.after
    for field_name in report_template_tuning_field_names():
        if field_name in target:
            setattr(active, field_name, target[field_name])
    active.is_active = True
    active.save()
    return create_report_template_tuning_change_log(
        active,
        before=before,
        action=ReportTemplateRecommendationTuningChangeLog.Action.ROLLBACK_RESTORED,
        changed_by=changed_by,
        reason=reason
        or f"Restored {snapshot}-change report-template recommendation tuning snapshot from log #{source_log.pk}.",
        request_path=request_path,
    )
