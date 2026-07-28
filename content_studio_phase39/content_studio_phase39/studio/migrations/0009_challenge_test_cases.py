from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("studio", "0008_learner_progress_badges"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChallengeTestCase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("position", models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(999)])),
                ("name", models.CharField(blank=True, max_length=140)),
                ("description", models.TextField(blank=True, help_text="Plain-English explanation of what this test checks.")),
                ("test_code", models.TextField(help_text="Python code appended after the learner's submitted code. Use print(...) or assertions to check function return values.")),
                ("expected_output", models.TextField(blank=True, help_text="Optional stdout expected from this individual test case.")),
                ("is_active", models.BooleanField(default=True)),
                ("challenge", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="test_cases", to="studio.codechallenge")),
            ],
            options={"ordering": ("position", "pk")},
        ),
        migrations.AddField(
            model_name="challengeattempt",
            name="test_results",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="challengeattempt",
            name="tests_passed",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="challengeattempt",
            name="tests_total",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddConstraint(
            model_name="challengetestcase",
            constraint=models.UniqueConstraint(fields=("challenge", "position"), name="unique_challenge_test_position"),
        ),
    ]
