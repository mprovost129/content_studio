import csv
import io
import re
from dataclasses import dataclass, field

METRIC_ALIASES = {
    "actual_recipients": {
        "actual_recipients",
        "recipients",
        "recipient_count",
        "delivered",
        "delivered_count",
        "successful_deliveries",
        "sent",
        "total_sent",
        "emails_sent",
        "contacts_sent",
        "audience",
        "sends",
        "delivered_emails",
    },
    "opens": {"opens", "total_opens", "unique_opens", "opened", "open_count"},
    "clicks": {"clicks", "total_clicks", "unique_clicks", "clicked", "click_count"},
    "unsubscribes": {"unsubscribes", "unsubscribed", "unsubscribe_count", "unsubs"},
    "bounces": {"bounces", "bounced", "bounce_count", "hard_bounces", "soft_bounces"},
}

METRIC_FIELDS = ("actual_recipients", "opens", "clicks", "unsubscribes", "bounces")


@dataclass
class NewsletterMetricsParseResult:
    metrics: dict = field(default_factory=dict)
    matched_labels: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    rows_seen: int = 0

    @property
    def has_metrics(self):
        return any(self.metrics.get(field) is not None for field in METRIC_FIELDS)


def _normalize_key(value):
    value = str(value or "").strip().lower()
    value = value.replace("%", " percent")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _parse_int(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "").replace("%", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = float(match.group(0))
    if number < 0:
        return None
    return int(round(number))


def _metric_for_label(label):
    normalized = _normalize_key(label)
    for metric_field, aliases in METRIC_ALIASES.items():
        if normalized in aliases:
            return metric_field
    return None


def _apply_metric(result, field, raw_label, raw_value):
    value = _parse_int(raw_value)
    if value is None:
        return
    current = result.metrics.get(field)
    if current is None:
        result.metrics[field] = value
        result.matched_labels[field] = raw_label
    else:
        # Prefer the larger number when a provider includes both unique and total counts.
        result.metrics[field] = max(current, value)
        result.matched_labels[field] = f"{result.matched_labels[field]}, {raw_label}"


def parse_newsletter_metrics(text):
    """Parse pasted/exported email metrics from CSV or key-value text.

    Supports common Mailchimp/Beehiiv/ConvertKit-style column names without coupling
    the app to any one provider. The caller decides which campaign receives the data.
    """
    result = NewsletterMetricsParseResult(
        metrics={field: None for field in METRIC_FIELDS}
    )
    text = (text or "").strip()
    if not text:
        result.warnings.append("No import text was provided.")
        return result

    # First try CSV/TSV with headers.
    sample = text[:4096]
    delimiter = (
        "\t" if "\t" in sample and sample.count("\t") > sample.count(",") else ","
    )
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if reader.fieldnames:
            for row in reader:
                if not any(str(value or "").strip() for value in row.values()):
                    continue
                result.rows_seen += 1
                for label, raw_value in row.items():
                    field = _metric_for_label(label)
                    if field:
                        _apply_metric(result, field, label, raw_value)
                # Most exports put one campaign per row. Stop after the first metric-rich row.
                if result.has_metrics:
                    break
    except csv.Error as exc:
        result.warnings.append(f"CSV parsing warning: {exc}")

    if result.has_metrics:
        return result

    # Fall back to metric,value or Metric: value style pasted summaries.
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        result.rows_seen += 1
        if ":" in line:
            label, raw_value = line.split(":", 1)
        elif "," in line:
            label, raw_value = line.split(",", 1)
        elif "\t" in line:
            label, raw_value = line.split("\t", 1)
        else:
            continue
        field = _metric_for_label(label)
        if field:
            _apply_metric(result, field, label, raw_value)

    if not result.has_metrics:
        result.warnings.append(
            "No recognized metrics were found. Include columns or labels such as recipients, opens, clicks, unsubscribes, or bounces."
        )
    return result
