import tempfile
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    AIGeneration,
    AIModelPricing,
    CaptionDraft,
    GraphicAsset,
    GraphicTemplate,
    Lesson,
    LessonBlock,
    Tag,
    WebsiteExport,
)
from .services.graphics import generate_graphics
from .services.openai import generate_caption
from .services.website import create_website_export, seo_diagnostics, serialize_lesson


class StudioModelTests(TestCase):
    def test_lesson_generates_unique_slugs(self):
        first = Lesson.objects.create(title="Python Variables")
        second = Lesson.objects.create(title="Python Variables")

        self.assertEqual(first.slug, "python-variables")
        self.assertEqual(second.slug, "python-variables-2")

    def test_ai_generation_cost_uses_cached_and_uncached_rates(self):
        generation = AIGeneration(
            purpose=AIGeneration.Purpose.CAPTION,
            model="gpt-5.6-terra",
            prompt="test",
            input_tokens=1_000_000,
            cached_input_tokens=200_000,
            output_tokens=100_000,
            input_price_per_million=Decimal("2.50"),
            cached_input_price_per_million=Decimal("0.25"),
            output_price_per_million=Decimal("15.00"),
        )

        self.assertEqual(generation.calculate_estimated_cost(), Decimal("3.550000"))


class GraphicServiceTests(TestCase):
    def setUp(self):
        self.lesson = Lesson.objects.create(
            title="Python Variables Explained",
            summary="A variable stores a value in memory.",
            status=Lesson.Status.DRAFT,
        )
        LessonBlock.objects.create(
            lesson=self.lesson,
            position=1,
            block_type=LessonBlock.BlockType.CODE,
            title="variables.py",
            content='name = "Michael"\nage = 22\nprint(name, age)',
        )
        LessonBlock.objects.create(
            lesson=self.lesson,
            position=2,
            block_type=LessonBlock.BlockType.OUTPUT,
            title="Output",
            content="Michael 22",
        )
        self.template = GraphicTemplate.objects.get(slug="lesson-explainer")

    def test_generates_square_png_asset(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                assets = generate_graphics(
                    self.lesson,
                    self.template,
                    [GraphicAsset.Format.INSTAGRAM_SQUARE],
                )
                self.assertGreaterEqual(len(assets), 1)
                asset = assets[0]
                self.assertEqual(asset.status, GraphicAsset.Status.READY)
                self.assertEqual((asset.width, asset.height), (1080, 1080))
                self.assertTrue(Path(asset.file.path).exists())


class OpenAIServiceTests(TestCase):
    def setUp(self):
        self.lesson = Lesson.objects.create(
            title="For Loops", summary="Repeat code for each item in a sequence."
        )
        AIModelPricing.objects.update_or_create(
            model="gpt-5.6-terra",
            effective_from="2026-07-26",
            defaults={
                "input_per_million": Decimal("2.50"),
                "cached_input_per_million": Decimal("0.25"),
                "output_per_million": Decimal("15.00"),
                "is_active": True,
            },
        )

    @patch("openai.OpenAI")
    def test_caption_records_response_usage_and_cost(self, client_class):
        usage = SimpleNamespace(
            input_tokens=1000,
            input_tokens_details=SimpleNamespace(cached_tokens=100, cache_write_tokens=0),
            output_tokens=200,
            output_tokens_details=SimpleNamespace(reasoning_tokens=20),
        )
        response = SimpleNamespace(
            id="resp_test",
            output_text="Loops repeat code. What will you build? #Python",
            usage=usage,
            model_dump=lambda mode: {"id": "resp_test"},
        )
        client_class.return_value.responses.create.return_value = response

        caption = generate_caption(self.lesson, CaptionDraft.Platform.INSTAGRAM)

        self.assertEqual(caption.platform, CaptionDraft.Platform.INSTAGRAM)
        self.assertEqual(caption.generation.response_id, "resp_test")
        self.assertEqual(caption.generation.status, AIGeneration.Status.SUCCEEDED)
        self.assertGreater(caption.generation.estimated_cost_usd, 0)


class WebsiteServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="publisher@example.com", password="test-password"
        )
        self.lesson = Lesson.objects.create(
            title="Python Functions",
            summary="Learn how reusable functions organize Python programs.",
            status=Lesson.Status.READY,
            seo_title="Python Functions for Beginners",
            seo_description=(
                "Learn how Python functions organize reusable logic with a clear beginner "
                "example, practical explanation, and runnable code you can adapt."
            ),
        )
        LessonBlock.objects.create(
            lesson=self.lesson,
            position=1,
            block_type=LessonBlock.BlockType.CODE,
            title="greeting.py",
            content='def greet(name):\n    return f"Hello, {name}"',
        )

    def test_serializes_versioned_website_contract(self):
        payload = serialize_lesson(self.lesson)

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["content_type"], "code_with_michael.lesson")
        self.assertEqual(payload["lesson"]["blocks"][0]["type"], "code")
        self.assertEqual(payload["lesson"]["reading_minutes"], 1)
        self.assertFalse(payload["lesson"]["playground_enabled"])

    def test_export_revisions_keep_stable_content_hash(self):
        first = create_website_export(self.lesson, self.user)
        second = create_website_export(self.lesson, self.user)

        self.assertEqual((first.revision, second.revision), (1, 2))
        self.assertEqual(first.content_hash, second.content_hash)

    def test_seo_diagnostics_flags_missing_required_content(self):
        incomplete = Lesson.objects.create(title="Incomplete")

        diagnostics = seo_diagnostics(incomplete)

        self.assertFalse(diagnostics["is_ready"])
        self.assertLess(diagnostics["score"], 100)


class StudioViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="michael@example.com", password="test-password"
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("studio:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_shows_first_use_checklist(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("studio:dashboard"))

        self.assertContains(response, "GETTING STARTED")
        self.assertContains(response, "1 of 6 setup steps complete")
        self.assertContains(response, "Open the complete step-by-step guide")

    def test_help_guide_is_private_and_explains_complete_workflow(self):
        help_url = reverse("studio:help")
        self.assertEqual(self.client.get(help_url).status_code, 302)
        self.client.force_login(self.user)

        response = self.client.get(help_url)

        self.assertContains(response, "How to use Content Studio")
        self.assertContains(response, "The recommended daily workflow")
        self.assertContains(response, "Generate downloadable graphics")
        self.assertContains(response, "Nothing auto-publishes")

    def test_authenticated_user_can_create_lesson(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("studio:lesson-create"),
            {
                "title": "Python Lists",
                "summary": "Store ordered values.",
                "status": Lesson.Status.DRAFT,
                "difficulty": Lesson.Difficulty.BEGINNER,
            },
        )
        lesson = Lesson.objects.get(title="Python Lists")
        self.assertRedirects(response, lesson.get_absolute_url())
        self.assertEqual(lesson.created_by, self.user)

    def test_user_can_edit_and_approve_caption(self):
        lesson = Lesson.objects.create(title="List Comprehensions")
        caption = CaptionDraft.objects.create(
            lesson=lesson,
            platform=CaptionDraft.Platform.THREADS,
            content="First draft",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("studio:caption-update", args=[caption.pk]),
            {"content": "Approved copy", "status": CaptionDraft.Status.APPROVED},
        )

        caption.refresh_from_db()
        self.assertRedirects(response, lesson.get_absolute_url())
        self.assertEqual(caption.content, "Approved copy")
        self.assertEqual(caption.status, CaptionDraft.Status.APPROVED)

    def test_user_can_reorder_content_blocks(self):
        lesson = Lesson.objects.create(title="Dictionaries")
        first = LessonBlock.objects.create(
            lesson=lesson,
            position=1,
            block_type=LessonBlock.BlockType.TEXT,
            content="First",
        )
        second = LessonBlock.objects.create(
            lesson=lesson,
            position=2,
            block_type=LessonBlock.BlockType.CODE,
            content="Second",
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("studio:block-move", args=[second.pk, "up"]))

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertRedirects(response, lesson.get_absolute_url())
        self.assertEqual((first.position, second.position), (2, 1))

    @patch("openai.OpenAI")
    def test_complete_draft_to_download_workflow(self, client_class):
        usage = SimpleNamespace(
            input_tokens=800,
            input_tokens_details=SimpleNamespace(cached_tokens=0, cache_write_tokens=0),
            output_tokens=120,
            output_tokens_details=SimpleNamespace(reasoning_tokens=10),
        )
        client_class.return_value.responses.create.return_value = SimpleNamespace(
            id="resp_workflow",
            output_text="A clean Python example, ready to review. #Python",
            usage=usage,
            model_dump=lambda mode: {"id": "resp_workflow"},
        )
        self.client.force_login(self.user)

        self.client.post(
            reverse("studio:lesson-create"),
            {
                "title": "End-to-end Python Lesson",
                "summary": "A complete studio workflow.",
                "status": Lesson.Status.DRAFT,
                "difficulty": Lesson.Difficulty.BEGINNER,
            },
        )
        lesson = Lesson.objects.get(title="End-to-end Python Lesson")
        self.client.post(
            reverse("studio:block-create", args=[lesson.slug]),
            {
                "block_type": LessonBlock.BlockType.CODE,
                "title": "lesson.py",
                "content": 'message = "Hello, Michael"\nprint(message)',
                "data": "{}",
            },
        )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                caption_response = self.client.post(
                    reverse("studio:caption-generate", args=[lesson.slug]),
                    {"platforms": [CaptionDraft.Platform.INSTAGRAM]},
                )
                graphic_response = self.client.post(
                    reverse("studio:graphic-generate", args=[lesson.slug]),
                    {
                        "template": GraphicTemplate.objects.get(
                            slug="lesson-explainer"
                        ).pk,
                        "output_formats": [GraphicAsset.Format.INSTAGRAM_SQUARE],
                    },
                )
                asset = lesson.assets.get()
                self.assertTrue(Path(asset.file.path).exists())

        self.assertRedirects(caption_response, lesson.get_absolute_url())
        self.assertRedirects(graphic_response, lesson.get_absolute_url())
        self.assertEqual(lesson.captions.count(), 1)
        self.assertEqual(lesson.assets.count(), 1)
        self.assertContains(self.client.get(lesson.get_absolute_url()), lesson.title)

    def test_search_matches_block_content_and_tags(self):
        lesson = Lesson.objects.create(title="Collections")
        LessonBlock.objects.create(
            lesson=lesson,
            position=1,
            block_type=LessonBlock.BlockType.CODE,
            content="from collections import Counter",
        )
        tag = Tag.objects.create(name="Data structures")
        lesson.tags.add(tag)
        self.client.force_login(self.user)

        by_code = self.client.get(reverse("studio:lesson-list"), {"q": "Counter"})
        by_tag = self.client.get(reverse("studio:lesson-list"), {"q": "Data structures"})

        self.assertContains(by_code, lesson.title)
        self.assertContains(by_tag, lesson.title)

    def test_website_preview_and_revision_downloads_are_private(self):
        lesson = Lesson.objects.create(
            title="Website Export",
            summary="Preview and export this lesson.",
            seo_title="Website Export Lesson",
            seo_description="A complete website export lesson description for private preview testing.",
        )
        LessonBlock.objects.create(
            lesson=lesson,
            position=1,
            block_type=LessonBlock.BlockType.TEXT,
            content="Website-ready lesson content.",
        )
        preview_url = reverse("studio:website-preview", args=[lesson.slug])
        self.assertEqual(self.client.get(preview_url).status_code, 302)
        self.client.force_login(self.user)

        preview = self.client.get(preview_url)
        export_response = self.client.post(
            reverse("studio:website-export", args=[lesson.slug])
        )
        export = WebsiteExport.objects.get(lesson=lesson)
        json_download = self.client.get(
            reverse("studio:website-export-download", args=[export.pk, "json"])
        )
        html_download = self.client.get(
            reverse("studio:website-export-download", args=[export.pk, "html"])
        )

        self.assertContains(preview, "Private website preview")
        self.assertContains(preview, "application/ld+json")
        self.assertRedirects(export_response, lesson.get_absolute_url())
        self.assertEqual(json_download["Content-Type"], "application/json; charset=utf-8")
        self.assertContains(json_download, '"schema_version": "1.0"')
        self.assertEqual(html_download["Content-Type"], "text/html; charset=utf-8")
        self.assertContains(html_download, "Website-ready lesson content.")

    def test_opt_in_website_preview_contains_browser_python_playground(self):
        lesson = Lesson.objects.create(
            title="Runnable Python",
            summary="Run this example in the browser.",
            enable_playground=True,
        )
        LessonBlock.objects.create(
            lesson=lesson,
            position=1,
            block_type=LessonBlock.BlockType.CODE,
            title="hello.py",
            content='print("Hello from Python")',
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("studio:website-preview", args=[lesson.slug])
        )

        self.assertContains(response, "Run code")
        self.assertContains(response, "data-python-playground")
        self.assertContains(response, "pyodide-worker.js")
        self.assertContains(response, "playground.js")
