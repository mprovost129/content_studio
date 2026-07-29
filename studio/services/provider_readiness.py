"""Email-provider sync readiness helpers.

This module keeps provider-integration preparation logic in one place so
Studio reports, CSV exports, and tests evaluate subscribers, segments, and
campaigns the same way.
"""

from dataclasses import dataclass
from typing import Iterable

from django.urls import reverse
from django.utils import timezone

from studio.models import (
    EmailProvider,
    NewsletterCampaign,
    NewsletterSubscriber,
    ProviderSyncStatus,
    SubscriberSegment,
)


@dataclass(frozen=True)
class ProviderReadinessRow:
    record_type: str
    label: str
    provider: str
    provider_label: str
    sync_status: str
    sync_status_label: str
    issue_key: str
    issue_label: str
    missing_fields: tuple[str, ...]
    external_id: str
    external_audience_id: str
    provider_url: str
    last_synced_at: object
    notes: str
    edit_url: str

    @property
    def last_synced_display(self) -> str:
        if not self.last_synced_at:
            return ""
        return timezone.localtime(self.last_synced_at).strftime("%Y-%m-%d %H:%M")


ISSUE_LABELS = {
    "not_connected": "Not connected",
    "missing_ids": "Missing provider IDs",
    "ready": "Ready to sync",
    "synced": "Synced",
    "needs_review": "Needs review",
    "error": "Error",
}


RECORD_TYPE_LABELS = {
    "subscriber": "Subscriber",
    "segment": "Segment",
    "campaign": "Campaign",
}


def _provider_label(value: str) -> str:
    return dict(EmailProvider.choices).get(value, value)


def _sync_label(value: str) -> str:
    return dict(ProviderSyncStatus.choices).get(value, value)


def _issue_for(provider: str, sync_status: str, missing_fields: list[str]) -> str:
    if provider == EmailProvider.NONE:
        return "not_connected"
    if sync_status == ProviderSyncStatus.ERROR:
        return "error"
    if sync_status == ProviderSyncStatus.NEEDS_REVIEW:
        return "needs_review"
    if missing_fields:
        return "missing_ids"
    if sync_status == ProviderSyncStatus.SYNCED:
        return "synced"
    return "ready"


def _subscriber_rows() -> Iterable[ProviderReadinessRow]:
    for subscriber in NewsletterSubscriber.objects.select_related(
        "source_lesson"
    ).order_by("email"):
        missing = []
        if subscriber.external_provider != EmailProvider.NONE:
            if not subscriber.external_contact_id:
                missing.append("External contact ID")
            if not subscriber.external_list_id:
                missing.append("External list/audience ID")
        issue = _issue_for(
            subscriber.external_provider, subscriber.provider_sync_status, missing
        )
        yield ProviderReadinessRow(
            record_type="subscriber",
            label=subscriber.email,
            provider=subscriber.external_provider,
            provider_label=subscriber.get_external_provider_display(),
            sync_status=subscriber.provider_sync_status,
            sync_status_label=subscriber.get_provider_sync_status_display(),
            issue_key=issue,
            issue_label=ISSUE_LABELS[issue],
            missing_fields=tuple(missing),
            external_id=subscriber.external_contact_id,
            external_audience_id=subscriber.external_list_id,
            provider_url="",
            last_synced_at=subscriber.provider_last_synced_at,
            notes=subscriber.provider_notes,
            edit_url=reverse(
                "studio:newsletter-subscriber-update", args=[subscriber.pk]
            ),
        )


def _segment_rows() -> Iterable[ProviderReadinessRow]:
    for segment in SubscriberSegment.objects.order_by("name"):
        missing = []
        if segment.external_provider != EmailProvider.NONE:
            if not segment.external_segment_id:
                missing.append("External segment/tag ID")
            if not segment.external_audience_id:
                missing.append("External audience/list ID")
        issue = _issue_for(
            segment.external_provider, segment.provider_sync_status, missing
        )
        yield ProviderReadinessRow(
            record_type="segment",
            label=segment.name,
            provider=segment.external_provider,
            provider_label=segment.get_external_provider_display(),
            sync_status=segment.provider_sync_status,
            sync_status_label=segment.get_provider_sync_status_display(),
            issue_key=issue,
            issue_label=ISSUE_LABELS[issue],
            missing_fields=tuple(missing),
            external_id=segment.external_segment_id,
            external_audience_id=segment.external_audience_id,
            provider_url="",
            last_synced_at=segment.provider_last_synced_at,
            notes=segment.provider_notes,
            edit_url=reverse("studio:subscriber-segment-update", args=[segment.pk]),
        )


def _campaign_rows() -> Iterable[ProviderReadinessRow]:
    for campaign in NewsletterCampaign.objects.select_related(
        "lesson", "saved_segment"
    ).order_by("-scheduled_at", "title"):
        missing = []
        if campaign.external_provider != EmailProvider.NONE:
            if not campaign.external_campaign_id:
                missing.append("External campaign ID")
            if not campaign.external_audience_id:
                missing.append("External audience/list ID")
        issue = _issue_for(
            campaign.external_provider, campaign.provider_sync_status, missing
        )
        yield ProviderReadinessRow(
            record_type="campaign",
            label=campaign.title,
            provider=campaign.external_provider,
            provider_label=campaign.get_external_provider_display(),
            sync_status=campaign.provider_sync_status,
            sync_status_label=campaign.get_provider_sync_status_display(),
            issue_key=issue,
            issue_label=ISSUE_LABELS[issue],
            missing_fields=tuple(missing),
            external_id=campaign.external_campaign_id,
            external_audience_id=campaign.external_audience_id,
            provider_url=campaign.provider_url,
            last_synced_at=campaign.provider_last_synced_at,
            notes=campaign.provider_notes,
            edit_url=reverse("studio:newsletter-campaign-update", args=[campaign.pk]),
        )


def provider_readiness_rows(record_type="", provider="", sync_status="", issue=""):
    builders = {
        "subscriber": _subscriber_rows,
        "segment": _segment_rows,
        "campaign": _campaign_rows,
    }
    selected = (
        [record_type]
        if record_type in builders
        else ["subscriber", "segment", "campaign"]
    )
    rows = []
    for key in selected:
        rows.extend(builders[key]())
    if provider:
        rows = [row for row in rows if row.provider == provider]
    if sync_status:
        rows = [row for row in rows if row.sync_status == sync_status]
    if issue:
        rows = [row for row in rows if row.issue_key == issue]
    return rows


def provider_readiness_summary(rows=None):
    rows = list(rows) if rows is not None else provider_readiness_rows()
    summary = {
        "total": len(rows),
        "not_connected": 0,
        "missing_ids": 0,
        "ready": 0,
        "synced": 0,
        "needs_review": 0,
        "error": 0,
    }
    by_type = {key: 0 for key in RECORD_TYPE_LABELS}
    by_provider = {
        value: {"label": label, "count": 0} for value, label in EmailProvider.choices
    }
    for row in rows:
        summary[row.issue_key] += 1
        by_type[row.record_type] = by_type.get(row.record_type, 0) + 1
        by_provider.setdefault(
            row.provider, {"label": _provider_label(row.provider), "count": 0}
        )["count"] += 1
    summary["by_type"] = by_type
    summary["by_provider"] = by_provider
    return summary
