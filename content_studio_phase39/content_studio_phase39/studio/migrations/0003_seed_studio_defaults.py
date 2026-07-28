from datetime import date
from decimal import Decimal

from django.db import migrations


def seed_defaults(apps, schema_editor):
    BrandProfile = apps.get_model("studio", "BrandProfile")
    Category = apps.get_model("studio", "Category")
    GraphicTemplate = apps.get_model("studio", "GraphicTemplate")
    AIModelPricing = apps.get_model("studio", "AIModelPricing")

    BrandProfile.objects.get_or_create(
        pk=1,
        defaults={
            "name": "Code with Michael",
            "social_handle": "@code_with_michael",
            "default_accent": "#3776AB",
            "background_color": "#0A0C16",
            "default_call_to_action": "Save this post and follow for more Python lessons.",
        },
    )

    for name, slug, color in (
        ("Python Basics", "python-basics", "#3776AB"),
        ("Strings", "strings", "#D64A9B"),
        ("Collections", "collections", "#29B6D6"),
        ("Control Flow", "control-flow", "#F08B32"),
        ("Loops", "loops", "#45C86B"),
        ("Functions", "functions", "#2DB9D6"),
        ("Object-Oriented Python", "object-oriented-python", "#9B61DF"),
        ("Projects", "projects", "#F5C431"),
        ("Errors and Debugging", "errors-debugging", "#EF5B5B"),
        ("Django", "django", "#44B878"),
    ):
        Category.objects.get_or_create(
            slug=slug, defaults={"name": name, "accent_color": color}
        )

    templates = (
        ("Lesson Explainer", "lesson-explainer", "lesson"),
        ("Project Series", "project-series", "project"),
        ("Challenge or Quiz", "challenge-quiz", "challenge"),
        ("Answer", "answer", "answer"),
        ("Spot the Bug", "spot-the-bug", "spot_bug"),
        ("Mini Program", "mini-program", "mini_program"),
        ("Comparison or Cheat Sheet", "comparison-cheat-sheet", "comparison"),
        ("Errors and Common Mistakes", "errors-common-mistakes", "error"),
        ("Community or Celebration", "community-celebration", "community"),
    )
    for name, slug, template_type in templates:
        GraphicTemplate.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "template_type": template_type, "is_active": True},
        )

    AIModelPricing.objects.get_or_create(
        model="gpt-5.6-terra",
        effective_from=date(2026, 7, 26),
        defaults={
            "input_per_million": Decimal("2.5000"),
            "cached_input_per_million": Decimal("0.2500"),
            "output_per_million": Decimal("15.0000"),
            "cache_write_multiplier": Decimal("1.250"),
            "source_url": "https://developers.openai.com/api/docs/models/gpt-5.6-terra",
            "is_active": True,
        },
    )


def unseed_defaults(apps, schema_editor):
    # Seed data is intentionally retained on reverse to avoid deleting user edits.
    pass


class Migration(migrations.Migration):
    dependencies = [("studio", "0002_initial")]

    operations = [migrations.RunPython(seed_defaults, unseed_defaults)]
