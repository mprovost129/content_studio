# Generated manually for Content Studio beginner-learning workflow updates.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("studio", "0005_lesson_enable_playground"),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="learning_objective",
            field=models.CharField(
                blank=True,
                help_text="One clear outcome the beginner should reach by the end of the lesson.",
                max_length=240,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="beginner_takeaway",
            field=models.CharField(
                blank=True,
                help_text="The plain-English idea the learner should remember after finishing.",
                max_length=240,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="common_mistake",
            field=models.TextField(
                blank=True,
                help_text="A likely beginner error to call out in the lesson, caption, or carousel.",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="practice_prompt",
            field=models.TextField(
                blank=True,
                help_text="A short learner task that can become a challenge block or social post.",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="starter_code",
            field=models.TextField(
                blank=True,
                help_text="Optional code the learner starts from in the playground or challenge.",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="solution_code",
            field=models.TextField(
                blank=True,
                help_text="Optional reviewed solution code. Keep this hidden from the first learner view.",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="expected_output",
            field=models.TextField(
                blank=True,
                help_text="Optional output used for manual review or simple code-checking later.",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="hint_1",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="lesson",
            name="hint_2",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="lesson",
            name="next_lesson",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional lesson to recommend after this one.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="previous_lessons",
                to="studio.lesson",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="facebook_status",
            field=models.CharField(
                choices=[
                    ("idea", "Idea"),
                    ("draft", "Draft"),
                    ("review", "In review"),
                    ("ready", "Ready"),
                    ("published", "Published"),
                    ("archived", "Archived"),
                ],
                db_index=True,
                default="idea",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="instagram_status",
            field=models.CharField(
                choices=[
                    ("idea", "Idea"),
                    ("draft", "Draft"),
                    ("review", "In review"),
                    ("ready", "Ready"),
                    ("published", "Published"),
                    ("archived", "Archived"),
                ],
                db_index=True,
                default="idea",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="threads_status",
            field=models.CharField(
                choices=[
                    ("idea", "Idea"),
                    ("draft", "Draft"),
                    ("review", "In review"),
                    ("ready", "Ready"),
                    ("published", "Published"),
                    ("archived", "Archived"),
                ],
                db_index=True,
                default="idea",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="website_status",
            field=models.CharField(
                choices=[
                    ("idea", "Idea"),
                    ("draft", "Draft"),
                    ("review", "In review"),
                    ("ready", "Ready"),
                    ("published", "Published"),
                    ("archived", "Archived"),
                ],
                db_index=True,
                default="idea",
                max_length=20,
            ),
        ),
    ]
