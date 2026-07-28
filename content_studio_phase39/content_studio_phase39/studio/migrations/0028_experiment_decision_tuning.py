from django.db import migrations, models
import django.core.validators


def seed_default_experiment_decision_tuning(apps, schema_editor):
    ExperimentDecisionTuning = apps.get_model('studio', 'ExperimentDecisionTuning')
    ExperimentDecisionTuning.objects.get_or_create(
        pk=1,
        defaults={
            'name': 'Default experiment decision tuning',
            'is_active': True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('studio', '0027_recommendation_tuning_experiment_snapshots'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentDecisionTuning',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(default='Default experiment decision tuning', max_length=120)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('keep_score_threshold', models.FloatField(default=6.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('keep_primary_positive_min', models.PositiveSmallIntegerField(default=2, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ('keep_high_confidence_score', models.FloatField(default=12.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(200)])),
                ('rollback_score_threshold', models.FloatField(default=-5.0, validators=[django.core.validators.MinValueValidator(-100), django.core.validators.MaxValueValidator(0)])),
                ('rollback_primary_negative_min', models.PositiveSmallIntegerField(default=2, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ('rollback_high_confidence_score', models.FloatField(default=-10.0, validators=[django.core.validators.MinValueValidator(-200), django.core.validators.MaxValueValidator(0)])),
                ('low_confidence_abs_score', models.FloatField(default=4.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('max_metric_change_magnitude', models.FloatField(default=3.0, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(100)])),
                ('social_new_followers_weight', models.FloatField(default=2.0, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('social_engagements_weight', models.FloatField(default=1.4, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('social_reach_weight', models.FloatField(default=0.8, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('social_clicks_weight', models.FloatField(default=1.2, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('resources_pdf_downloads_weight', models.FloatField(default=1.6, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('resources_pdf_unlocks_weight', models.FloatField(default=1.3, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('resources_subscribers_weight', models.FloatField(default=2.0, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('newsletter_clicks_weight', models.FloatField(default=1.7, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('newsletter_open_rate_weight', models.FloatField(default=0.8, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('ctas_cta_clicks_weight', models.FloatField(default=1.8, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('conversions_total_conversions_weight', models.FloatField(default=2.5, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('conversions_lesson_views_weight', models.FloatField(default=1.2, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('conversions_quiz_attempts_weight', models.FloatField(default=1.5, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('conversions_challenge_attempts_weight', models.FloatField(default=1.7, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('conversions_lesson_completions_weight', models.FloatField(default=2.2, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('newsletter_unsubscribes_penalty_weight', models.FloatField(default=2.0, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('newsletter_bounces_penalty_weight', models.FloatField(default=1.5, validators=[django.core.validators.MinValueValidator(-20), django.core.validators.MaxValueValidator(20)])),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'experiment decision tuning',
                'verbose_name_plural': 'experiment decision tuning',
                'ordering': ('-is_active', 'name'),
            },
        ),
        migrations.RunPython(seed_default_experiment_decision_tuning, migrations.RunPython.noop),
    ]
