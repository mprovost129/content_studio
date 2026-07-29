# Generated for Code with Michael Content Studio phase 54.

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def seed_default_report_template_recommendation_tuning(apps, schema_editor):
    Tuning = apps.get_model("studio", "ReportTemplateRecommendationTuning")
    Tuning.objects.get_or_create(
        pk=1,
        defaults={
            "name": "Default report-template recommendation tuning",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("studio", "0037_report_template_recommendation_feedback"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportTemplateRecommendationTuning",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(default="Default report-template recommendation tuning", max_length=120)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("base_template_score", models.IntegerField(default=25, validators=[MinValueValidator(-100), MaxValueValidator(200)])),
                ("high_priority_threshold", models.IntegerField(default=80, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("medium_priority_threshold", models.IntegerField(default=55, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("matching_window_weight", models.IntegerField(default=5, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("matching_window_cap", models.IntegerField(default=15, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("unused_template_bonus", models.IntegerField(default=18, validators=[MinValueValidator(-100), MaxValueValidator(200)])),
                ("keep_decision_weight", models.IntegerField(default=7, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("keep_decision_cap", models.IntegerField(default=20, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("watch_decision_weight", models.IntegerField(default=4, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("watch_decision_cap", models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("rollback_decision_penalty", models.IntegerField(default=5, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("rollback_decision_cap", models.IntegerField(default=14, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("underused_family_bonus", models.IntegerField(default=8, validators=[MinValueValidator(-100), MaxValueValidator(200)])),
                ("focus_area_weight", models.IntegerField(default=2, validators=[MinValueValidator(0), MaxValueValidator(50)])),
                ("focus_area_cap", models.IntegerField(default=8, validators=[MinValueValidator(0), MaxValueValidator(200)])),
                ("preset_default_weight", models.IntegerField(default=3, validators=[MinValueValidator(0), MaxValueValidator(50)])),
                ("preset_default_cap", models.IntegerField(default=7, validators=[MinValueValidator(0), MaxValueValidator(200)])),
                ("exact_useful_boost", models.IntegerField(default=12, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("exact_useful_cap", models.IntegerField(default=24, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("exact_dismissed_penalty", models.IntegerField(default=18, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("exact_dismissed_cap", models.IntegerField(default=36, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("exact_revisit_boost", models.IntegerField(default=4, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("exact_revisit_cap", models.IntegerField(default=8, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("exact_ignored_penalty", models.IntegerField(default=4, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("exact_ignored_cap", models.IntegerField(default=12, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("similar_useful_boost", models.IntegerField(default=3, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("similar_useful_cap", models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("similar_dismissed_penalty", models.IntegerField(default=4, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("similar_dismissed_cap", models.IntegerField(default=14, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("similar_revisit_boost", models.IntegerField(default=2, validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ("similar_revisit_cap", models.IntegerField(default=6, validators=[MinValueValidator(0), MaxValueValidator(300)])),
                ("feedback_adjustment_floor", models.IntegerField(default=-40, validators=[MinValueValidator(-500), MaxValueValidator(0)])),
                ("feedback_adjustment_ceiling", models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(500)])),
                ("notes", models.TextField(blank=True)),
            ],
            options={"ordering": ("-is_active", "name"), "verbose_name": "report-template recommendation tuning", "verbose_name_plural": "report-template recommendation tuning"},
        ),
        migrations.RunPython(seed_default_report_template_recommendation_tuning, migrations.RunPython.noop),
    ]
