# Generated manually for phase 57.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("studio", "0040_report_template_recommendation_tuning_experiments"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportTemplateRecommendationTuningExperimentSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("window_days", models.PositiveSmallIntegerField(default=14)),
                ("before_start", models.DateTimeField(db_index=True)),
                ("before_end", models.DateTimeField(db_index=True)),
                ("after_start", models.DateTimeField(db_index=True)),
                ("after_end", models.DateTimeField(db_index=True)),
                ("before_metrics", models.JSONField(blank=True, default=dict)),
                ("after_metrics", models.JSONField(blank=True, default=dict)),
                ("deltas", models.JSONField(blank=True, default=dict)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("notes", models.TextField(blank=True)),
                ("generated_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("change_log", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="performance_snapshots", to="studio.reporttemplaterecommendationtuningchangelog")),
                ("generated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="report_template_recommendation_tuning_experiment_snapshots", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "report-template recommendation tuning experiment snapshot",
                "verbose_name_plural": "report-template recommendation tuning experiment snapshots",
                "ordering": ("-generated_at", "-pk"),
                "indexes": [models.Index(fields=("change_log", "generated_at"), name="studio_repo_change__cc7512_idx"), models.Index(fields=("before_start", "after_end"), name="studio_repo_before__4c99ac_idx")],
            },
        ),
    ]
