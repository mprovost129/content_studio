"""Audit logging and rollback helpers for report-template recommendation decision rules."""

from __future__ import annotations

from typing import Any

from studio.models import (
    ReportTemplateRecommendationTuningDecisionRules,
    ReportTemplateRecommendationTuningDecisionRulesChangeLog,
)


EXCLUDED_FIELDS = {"id", "created_at", "updated_at"}


def report_template_decision_rule_field_names() -> list[str]:
    return [
        field.name
        for field in ReportTemplateRecommendationTuningDecisionRules._meta.fields
        if field.name not in EXCLUDED_FIELDS
    ]


def report_template_decision_rule_snapshot(rules: ReportTemplateRecommendationTuningDecisionRules) -> dict[str, Any]:
    return {name: getattr(rules, name) for name in report_template_decision_rule_field_names()}


def build_report_template_decision_rule_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    for key in sorted(set(before.keys()) | set(after.keys())):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            diff[key] = {"before": old, "after": new}
    return diff


def create_report_template_decision_rule_change_log(
    rules: ReportTemplateRecommendationTuningDecisionRules,
    *,
    before: dict[str, Any],
    action: str,
    changed_by=None,
    reason: str = "",
    request_path: str = "",
    experiment_label: str = "",
    experiment_status: str = "",
    experiment_notes: str = "",
) -> ReportTemplateRecommendationTuningDecisionRulesChangeLog | None:
    after = report_template_decision_rule_snapshot(rules)
    diff = build_report_template_decision_rule_diff(before, after)
    if not diff and action == ReportTemplateRecommendationTuningDecisionRulesChangeLog.Action.MANUAL_UPDATE:
        return None
    return ReportTemplateRecommendationTuningDecisionRulesChangeLog.objects.create(
        decision_rules=rules,
        action=action,
        changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
        reason=reason,
        before=before,
        after=after,
        diff=diff,
        request_path=request_path[:300],
        experiment_label=(experiment_label or "").strip(),
        experiment_status=experiment_status or ReportTemplateRecommendationTuningDecisionRulesChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        experiment_notes=(experiment_notes or "").strip(),
    )


def restore_report_template_decision_rule_snapshot(
    source_log: ReportTemplateRecommendationTuningDecisionRulesChangeLog,
    *,
    snapshot: str = "before",
    changed_by=None,
    reason: str = "",
    request_path: str = "",
) -> ReportTemplateRecommendationTuningDecisionRulesChangeLog | None:
    if snapshot not in {"before", "after"}:
        raise ValueError("snapshot must be 'before' or 'after'")
    active = ReportTemplateRecommendationTuningDecisionRules.get_active()
    before = report_template_decision_rule_snapshot(active)
    target = source_log.before if snapshot == "before" else source_log.after
    for field_name in report_template_decision_rule_field_names():
        if field_name in target:
            setattr(active, field_name, target[field_name])
    active.is_active = True
    active.save()
    return create_report_template_decision_rule_change_log(
        active,
        before=before,
        action=ReportTemplateRecommendationTuningDecisionRulesChangeLog.Action.ROLLBACK_RESTORED,
        changed_by=changed_by,
        reason=reason or f"Restored {snapshot}-change template-recommendation decision-rule snapshot from log #{source_log.pk}.",
        request_path=request_path,
    )
