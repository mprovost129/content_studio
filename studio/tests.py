import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    AIGeneration,
    AIModelPricing,
    CaptionDraft,
    CodeChallenge,
    ContentPlan,
    EmailProvider,
    ExperimentDecisionTuning,
    ExperimentDecisionTuningChangeLog,
    ExperimentDecisionTuningExperimentSnapshot,
    ExperimentDecisionTuningSnapshotComparisonReport,
    GraphicAsset,
    GraphicTemplate,
    LearningResource,
    Lesson,
    LessonBlock,
    NewsletterCampaign,
    NewsletterSubscriber,
    ProviderSyncStatus,
    PublishingRecord,
    QuizChoice,
    QuizQuestion,
    RecommendationTuning,
    RecommendationTuningChangeLog,
    RecommendationTuningExperimentSnapshot,
    ResourceCTA,
    ResourceCTAClickEvent,
    ResourceCTARecommendationFeedback,
    ResourceLeadMagnetAccess,
    ResourceLessonConversionEvent,
    ResourcePerformanceEvent,
    SubscriberSegment,
    Tag,
    WebsiteExport,
)
from .services.graphics import _python_logo, generate_graphics
from .services.openai import generate_caption
from .services.resource_pdfs import resource_pdf_filename
from .services.resource_recommendations import build_resource_cta_recommendations
from .services.social_carousels import (
    apply_social_carousel_template_to_lesson,
    get_social_carousel_template,
)
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

    def test_supplied_python_logo_is_available_to_renderer(self):
        logo = _python_logo(110)

        self.assertIsNotNone(logo)
        self.assertEqual(logo.mode, "RGBA")
        self.assertEqual(logo.size, (110, 110))
        self.assertIsNotNone(logo.getbbox())


class SocialCarouselTemplateTests(TestCase):
    def test_applies_carousel_blocks_and_creates_matching_graphic_template(self):
        lesson = Lesson.objects.create(
            title="Python Variables",
            summary="Variables store values for later use.",
            beginner_takeaway="A variable is a named container for a value.",
            expected_output="Michael",
        )
        LessonBlock.objects.create(
            lesson=lesson,
            position=1,
            block_type=LessonBlock.BlockType.CODE,
            title="variables.py",
            content='name = "Michael"\nprint(name)',
        )

        template = get_social_carousel_template("code_output_quiz")
        created = apply_social_carousel_template_to_lesson(lesson, template)

        self.assertEqual(created["blocks"], 5)
        self.assertEqual(lesson.blocks.count(), 6)
        self.assertTrue(GraphicTemplate.objects.filter(slug="code-output-quiz-carousel").exists())
        lesson.refresh_from_db()
        self.assertEqual(lesson.instagram_status, Lesson.Status.DRAFT)


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
        request = client_class.return_value.responses.create.call_args.kwargs
        self.assertIn("do not use Markdown code fences", request["instructions"])


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

        self.assertEqual(payload["schema_version"], "1.6")
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


class PublicSEOTests(TestCase):
    def setUp(self):
        self.lesson = Lesson.objects.create(
            title="SEO Python Lesson",
            summary="A public beginner Python lesson for SEO testing.",
            website_status=Lesson.Status.PUBLISHED,
            seo_title="SEO Python Lesson for Beginners",
            seo_description="Learn a beginner Python concept with runnable examples and practice.",
        )

    def test_public_sitemap_lists_public_lessons(self):
        response = self.client.get(reverse("core:sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml; charset=utf-8")
        self.assertContains(response, "/learn/", status_code=200)
        self.assertContains(response, f"/learn/{self.lesson.slug}/", status_code=200)

    def test_robots_points_to_sitemap_and_blocks_private_routes(self):
        response = self.client.get(reverse("core:robots"))

        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("Disallow: /studio/", response.content.decode())
        self.assertIn("Sitemap:", response.content.decode())

    def test_rss_feed_lists_latest_public_lessons(self):
        response = self.client.get(reverse("core:feed"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertContains(response, self.lesson.title, status_code=200)

    def test_public_lesson_has_canonical_and_json_ld(self):
        response = self.client.get(reverse("learn:lesson-detail", args=[self.lesson.slug]))

        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, 'LearningResource')


class StudioViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="michael@example.com", password="test-password", is_staff=True
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("studio:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_shows_first_use_checklist(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("studio:dashboard"))

        self.assertContains(response, "GETTING STARTED")
        self.assertContains(response, "1 of 10 setup steps complete")
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


    def test_user_can_record_publishing_metrics_and_update_platform_status(self):
        lesson = Lesson.objects.create(title="Posted Lesson", instagram_status=Lesson.Status.READY)
        caption = CaptionDraft.objects.create(
            lesson=lesson,
            platform=CaptionDraft.Platform.INSTAGRAM,
            content="Final Instagram caption",
            status=CaptionDraft.Status.APPROVED,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("studio:publishing-create", args=[lesson.slug]),
            {
                "platform": PublishingRecord.Platform.INSTAGRAM,
                "published_at": "2026-07-26T10:30",
                "post_url": "https://example.com/post",
                "caption": caption.pk,
                "caption_text": "",
                "notes": "Posted as a carousel.",
                "impressions": 1000,
                "reach": 800,
                "likes": 120,
                "comments": 10,
                "saves": 20,
                "shares": 5,
                "clicks": 15,
                "new_followers": 7,
                "follower_count_after": 148,
            },
        )

        record = PublishingRecord.objects.get(lesson=lesson)
        lesson.refresh_from_db()
        self.assertRedirects(response, lesson.get_absolute_url() + "#publishing")
        self.assertEqual(record.caption_text, "Final Instagram caption")
        self.assertEqual(record.engagement_total, 170)
        self.assertEqual(lesson.instagram_status, Lesson.Status.PUBLISHED)


    def test_performance_report_groups_posts_by_content_format(self):
        lesson = Lesson.objects.create(title="Report Lesson")
        record = PublishingRecord.objects.create(
            lesson=lesson,
            platform=PublishingRecord.Platform.INSTAGRAM,
            impressions=1200,
            reach=900,
            likes=120,
            comments=8,
            saves=30,
            shares=12,
            clicks=20,
            new_followers=11,
        )
        ContentPlan.objects.create(
            lesson=lesson,
            platform=ContentPlan.Platform.INSTAGRAM,
            scheduled_at=record.published_at,
            status=ContentPlan.Status.POSTED,
            carousel_template="code_output_quiz",
            publishing_record=record,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("studio:performance-report"))

        self.assertContains(response, "Performance by content format")
        self.assertContains(response, "Code Output Quiz")
        self.assertContains(response, "11")

    def test_performance_report_exports_filtered_csv(self):
        instagram_lesson = Lesson.objects.create(title="Instagram Report Lesson")
        facebook_lesson = Lesson.objects.create(title="Facebook Report Lesson")
        instagram_record = PublishingRecord.objects.create(
            lesson=instagram_lesson,
            platform=PublishingRecord.Platform.INSTAGRAM,
            impressions=1200,
            reach=900,
            likes=120,
            comments=8,
            saves=30,
            shares=12,
            clicks=20,
            new_followers=11,
            caption_text="Instagram caption",
        )
        PublishingRecord.objects.create(
            lesson=facebook_lesson,
            platform=PublishingRecord.Platform.FACEBOOK,
            impressions=2000,
            reach=1500,
            likes=60,
        )
        ContentPlan.objects.create(
            lesson=instagram_lesson,
            platform=ContentPlan.Platform.INSTAGRAM,
            scheduled_at=instagram_record.published_at,
            status=ContentPlan.Status.POSTED,
            carousel_template="code_output_quiz",
            publishing_record=instagram_record,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("studio:performance-report-export"),
            {"platform": PublishingRecord.Platform.INSTAGRAM, "section": "posts"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment;", response["Content-Disposition"])
        csv_text = response.content.decode("utf-8-sig")
        self.assertIn("Published At,Lesson,Platform,Content Format", csv_text)
        self.assertIn("Instagram Report Lesson", csv_text)
        self.assertIn("Code Output Quiz", csv_text)
        self.assertNotIn("Facebook Report Lesson", csv_text)

    def test_performance_report_exports_format_summary_csv(self):
        lesson = Lesson.objects.create(title="Format Summary Lesson")
        record = PublishingRecord.objects.create(
            lesson=lesson,
            platform=PublishingRecord.Platform.INSTAGRAM,
            reach=1000,
            likes=100,
            comments=10,
            saves=20,
            shares=5,
            clicks=15,
            new_followers=9,
        )
        ContentPlan.objects.create(
            lesson=lesson,
            platform=ContentPlan.Platform.INSTAGRAM,
            scheduled_at=record.published_at,
            status=ContentPlan.Status.POSTED,
            carousel_template="beginner_mistake",
            publishing_record=record,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("studio:performance-report-export"), {"section": "formats"}
        )

        csv_text = response.content.decode("utf-8-sig")
        self.assertIn("Format,Source,Posts,Impressions,Reach", csv_text)
        self.assertIn("Beginner Mistake", csv_text)
        self.assertIn("9", csv_text)


    def test_user_can_create_newsletter_campaign_from_lesson(self):
        lesson = Lesson.objects.create(
            title="Python Variables",
            summary="Variables save values for later use.",
            learning_objective="Create and print a variable.",
            beginner_takeaway="A variable is a name attached to a value.",
            practice_prompt="Create a variable named score and print it.",
        )
        NewsletterSubscriber.objects.create(email="learner@example.com")
        self.client.force_login(self.user)

        response = self.client.get(reverse("studio:newsletter-campaign-create-for-lesson", args=[lesson.slug]))

        self.assertContains(response, "Weekly Python: Python Variables")
        self.assertContains(response, "Create and print a variable")

    def test_user_can_mark_newsletter_campaign_sent(self):
        lesson = Lesson.objects.create(title="Email Lesson")
        campaign = NewsletterCampaign.objects.create(
            lesson=lesson,
            title="Weekly Python: Email Lesson",
            subject="Practice Python: Email Lesson",
            body="Try this lesson.",
            status=NewsletterCampaign.Status.SCHEDULED,
            estimated_recipients=25,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("studio:newsletter-campaign-mark-sent", args=[campaign.pk]))

        campaign.refresh_from_db()
        self.assertRedirects(response, reverse("studio:newsletter-campaign-list"))
        self.assertEqual(campaign.status, NewsletterCampaign.Status.SENT)
        self.assertEqual(campaign.actual_recipients, 25)
        self.assertIsNotNone(campaign.sent_at)

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
        self.assertContains(json_download, '"schema_version": "1.5"')
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

class NewsletterSubscriberTests(TestCase):
    def test_public_newsletter_signup_creates_active_subscriber(self):
        response = self.client.post(
            reverse("learn:newsletter-signup"),
            {
                "email": "Learner@Example.com",
                "first_name": "Learner",
                "source": "learn_home",
                "next": reverse("learn:home"),
            },
        )
        self.assertEqual(response.status_code, 302)
        subscriber = NewsletterSubscriber.objects.get(email="learner@example.com")
        self.assertEqual(subscriber.status, NewsletterSubscriber.Status.ACTIVE)
        self.assertEqual(subscriber.source, NewsletterSubscriber.Source.LEARN_HOME)

    def test_staff_can_export_newsletter_subscribers(self):
        user = get_user_model().objects.create_user(email="staff@example.com", password="testpass", is_staff=True)
        NewsletterSubscriber.objects.create(email="learner@example.com", first_name="Learner")
        self.client.force_login(user)

        response = self.client.get(reverse("studio:newsletter-subscriber-export"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertContains(response, "learner@example.com")

class NewsletterMetricImportTests(TestCase):
    def test_staff_can_import_newsletter_campaign_metrics_from_pasted_summary(self):
        user = get_user_model().objects.create_user(email="staff2@example.com", password="testpass", is_staff=True)
        lesson = Lesson.objects.create(title="Python Newsletter Lesson")
        campaign = NewsletterCampaign.objects.create(
            lesson=lesson,
            title="Weekly Python",
            subject="Practice Python",
            body="Try this lesson.",
            estimated_recipients=400,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("studio:newsletter-metric-import-for-campaign", args=[campaign.pk]),
            {
                "campaign": campaign.pk,
                "provider": "manual",
                "pasted_metrics": "Recipients: 421\nOpens: 212\nClicks: 38\nUnsubscribes: 1\nBounces: 0",
                "mark_sent": "on",
            },
        )

        self.assertRedirects(response, reverse("studio:newsletter-campaign-list"))
        campaign.refresh_from_db()
        self.assertEqual(campaign.actual_recipients, 421)
        self.assertEqual(campaign.opens, 212)
        self.assertEqual(campaign.clicks, 38)
        self.assertEqual(campaign.unsubscribes, 1)
        self.assertEqual(campaign.bounces, 0)
        self.assertEqual(campaign.status, NewsletterCampaign.Status.SENT)
        self.assertEqual(campaign.metric_imports.count(), 1)

    def test_staff_can_import_newsletter_campaign_metrics_from_csv(self):
        user = get_user_model().objects.create_user(email="staff3@example.com", password="testpass", is_staff=True)
        campaign = NewsletterCampaign.objects.create(
            title="Standalone Email",
            subject="Python tip",
            body="Tip body.",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("studio:newsletter-metric-import"),
            {
                "campaign": campaign.pk,
                "provider": "mailchimp",
                "pasted_metrics": "recipients,opens,clicks,unsubscribes,bounces\n100,50,12,0,1",
            },
        )

        self.assertRedirects(response, reverse("studio:newsletter-campaign-list"))
        campaign.refresh_from_db()
        self.assertEqual(campaign.actual_recipients, 100)
        self.assertEqual(campaign.opens, 50)
        self.assertEqual(campaign.clicks, 12)
        self.assertEqual(campaign.bounces, 1)


class SubscriberSegmentTests(TestCase):
    def test_segment_matches_subscribers_by_source_and_status(self):
        staff = get_user_model().objects.create_user(email="segment-staff@example.com", password="testpass", is_staff=True)
        lesson = Lesson.objects.create(title="Segment Lesson")
        NewsletterSubscriber.objects.create(email="active@example.com", source=NewsletterSubscriber.Source.LESSON, source_lesson=lesson)
        NewsletterSubscriber.objects.create(email="other@example.com", source=NewsletterSubscriber.Source.LEARN_HOME)
        NewsletterSubscriber.objects.create(email="unsub@example.com", status=NewsletterSubscriber.Status.UNSUBSCRIBED, source=NewsletterSubscriber.Source.LESSON, source_lesson=lesson)
        segment = SubscriberSegment.objects.create(
            name="Active lesson signups",
            source_filter=NewsletterSubscriber.Source.LESSON,
            source_lesson=lesson,
            created_by=staff,
        )

        self.assertEqual(segment.subscriber_count, 1)
        self.assertEqual(segment.matching_subscribers().first().email, "active@example.com")

    def test_staff_can_export_segment_subscribers(self):
        staff = get_user_model().objects.create_user(email="segment-export@example.com", password="testpass", is_staff=True)
        NewsletterSubscriber.objects.create(email="learner@example.com")
        segment = SubscriberSegment.objects.create(name="All active")
        self.client.force_login(staff)

        response = self.client.get(reverse("studio:subscriber-segment-export", args=[segment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertContains(response, "learner@example.com")

    def test_campaign_can_use_saved_segment_for_estimated_recipients(self):
        staff = get_user_model().objects.create_user(email="campaign-segment@example.com", password="testpass", is_staff=True)
        NewsletterSubscriber.objects.create(email="one@example.com")
        NewsletterSubscriber.objects.create(email="two@example.com")
        segment = SubscriberSegment.objects.create(name="Active audience")
        self.client.force_login(staff)

        response = self.client.post(
            reverse("studio:newsletter-campaign-create"),
            {
                "title": "Segment email",
                "subject": "Python practice",
                "body": "Try this beginner Python exercise.",
                "status": NewsletterCampaign.Status.DRAFT,
                "target_segment": NewsletterCampaign.Segment.ALL_ACTIVE,
                "saved_segment": segment.pk,
                "estimated_recipients": 0,
                "actual_recipients": 0,
                "opens": 0,
                "clicks": 0,
                "unsubscribes": 0,
                "bounces": 0,
            },
        )

        self.assertRedirects(response, reverse("studio:newsletter-campaign-list"))
        campaign = NewsletterCampaign.objects.get(title="Segment email")
        self.assertEqual(campaign.saved_segment, segment)
        self.assertEqual(campaign.estimated_recipients, 2)



class ProviderSyncReadinessTests(TestCase):
    def test_readiness_report_flags_missing_provider_ids(self):
        staff = get_user_model().objects.create_user(email="sync-report@example.com", password="testpass", is_staff=True)
        NewsletterSubscriber.objects.create(
            email="mapped@example.com",
            external_provider=EmailProvider.MAILCHIMP,
            provider_sync_status=ProviderSyncStatus.READY,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("studio:provider-sync-readiness"), {"issue": "missing_ids"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mapped@example.com")
        self.assertContains(response, "External contact ID")
        self.assertContains(response, "External list/audience ID")

    def test_readiness_csv_export_includes_campaign_provider_mapping(self):
        staff = get_user_model().objects.create_user(email="sync-export@example.com", password="testpass", is_staff=True)
        NewsletterCampaign.objects.create(
            title="Provider test",
            subject="Python practice",
            body="Practice this week.",
            external_provider=EmailProvider.BEEHIIV,
            external_campaign_id="camp_123",
            external_audience_id="pub_456",
            provider_sync_status=ProviderSyncStatus.SYNCED,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("studio:provider-sync-readiness-export"), {"record_type": "campaign"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertContains(response, "Provider test")
        self.assertContains(response, "camp_123")
        self.assertContains(response, "pub_456")



class LearningResourceTests(TestCase):
    def test_public_resource_library_lists_published_resources(self):
        LearningResource.objects.create(
            title="Python List Cheat Sheet",
            summary="A quick reference for beginner list operations.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Use append() to add one item to a list.",
        )

        response = self.client.get(reverse("learn:resource-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python List Cheat Sheet")

    def test_staff_can_create_resource(self):
        staff = get_user_model().objects.create_user(email="resource-staff@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)

        response = self.client.post(
            reverse("studio:resource-create"),
            {
                "title": "Common NameError Fixes",
                "summary": "How beginners can fix undefined variable errors.",
                "resource_type": LearningResource.ResourceType.COMMON_ERROR,
                "status": LearningResource.Status.READY,
                "difficulty": Lesson.Difficulty.BEGINNER,
                "content": "Check spelling and make sure the variable is created before you use it.",
                "estimated_read_minutes": 4,
            },
        )

        resource = LearningResource.objects.get(title="Common NameError Fixes")
        self.assertRedirects(response, resource.get_absolute_url())
        self.assertEqual(resource.created_by, staff)

    def test_staff_can_generate_resource_from_idea(self):
        staff = get_user_model().objects.create_user(email="resource-generator@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)

        response = self.client.post(
            reverse("studio:resource-generate"),
            {
                "topic": "calculating a total price",
                "resource_type": LearningResource.ResourceType.CHEAT_SHEET,
                "audience": "absolute beginners",
            },
        )

        resource = LearningResource.objects.get(title="Calculating a Total Price Cheat Sheet for Python Beginners")
        self.assertRedirects(response, resource.get_absolute_url())
        self.assertEqual(resource.status, LearningResource.Status.DRAFT)
        self.assertEqual(resource.created_by, staff)
        self.assertIn("Total: $39.98", resource.content)
        self.assertIn("${total:.2f}", resource.content)

    def test_staff_can_generate_common_error_resource_from_idea(self):
        staff = get_user_model().objects.create_user(email="resource-error-generator@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)

        response = self.client.post(
            reverse("studio:resource-generate"),
            {
                "topic": "NameError",
                "resource_type": LearningResource.ResourceType.COMMON_ERROR,
                "audience": "Facebook followers",
            },
        )

        self.assertEqual(response.status_code, 302)
        resource = LearningResource.objects.get(title="How to Fix NameError in Python")
        self.assertIn("Beginner checklist", resource.content)
        self.assertEqual(resource.resource_type, LearningResource.ResourceType.COMMON_ERROR)

    def test_public_pdf_download_for_enabled_resource(self):
        resource = LearningResource.objects.create(
            title="Python Variables Cheat Sheet",
            summary="A printable beginner reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="""What to remember
Variables store values.

```python
name = "Michael"
print(name)
```
""",
            pdf_download_enabled=True,
        )

        response = self.client.get(reverse("learn:resource-pdf", kwargs={"slug": resource.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(resource_pdf_filename(resource), response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_public_pdf_redirects_when_disabled(self):
        resource = LearningResource.objects.create(
            title="Private PDF Disabled",
            summary="No generated PDF yet.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Read this online.",
            pdf_download_enabled=False,
        )

        response = self.client.get(reverse("learn:resource-pdf", kwargs={"slug": resource.slug}))

        self.assertRedirects(response, resource.public_url)

    def test_generated_download_resource_enables_pdf_by_default(self):
        staff = get_user_model().objects.create_user(email="pdf-resource-generator@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)

        response = self.client.post(
            reverse("studio:resource-generate"),
            {
                "topic": "loops",
                "resource_type": LearningResource.ResourceType.DOWNLOAD,
                "audience": "absolute beginners",
            },
        )

        self.assertEqual(response.status_code, 302)
        resource = LearningResource.objects.get(title="Loops Downloadable Reference")
        self.assertTrue(resource.pdf_download_enabled)
        self.assertIn("Print this reference", resource.pdf_footer_note)


    def test_gated_resource_pdf_requires_email_before_download(self):
        resource = LearningResource.objects.create(
            title="Python Lists PDF Lead Magnet",
            summary="A gated beginner PDF reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Lists store multiple values.",
            pdf_download_enabled=True,
            pdf_requires_email=True,
            pdf_lead_magnet_headline="Get the Python Lists PDF",
        )

        response = self.client.get(reverse("learn:resource-pdf", kwargs={"slug": resource.slug}))
        self.assertRedirects(response, reverse("learn:resource-pdf-gate", kwargs={"slug": resource.slug}))

        unlock = self.client.post(
            reverse("learn:resource-pdf-gate", kwargs={"slug": resource.slug}),
            {"email": "learner@example.com", "first_name": "Learner"},
        )
        self.assertRedirects(unlock, reverse("learn:resource-pdf", kwargs={"slug": resource.slug}))

        subscriber = NewsletterSubscriber.objects.get(email="learner@example.com")
        self.assertEqual(subscriber.source, NewsletterSubscriber.Source.RESOURCE)
        self.assertEqual(subscriber.source_resource, resource)

        pdf = self.client.get(reverse("learn:resource-pdf", kwargs={"slug": resource.slug}))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        access = ResourceLeadMagnetAccess.objects.get(resource=resource, email="learner@example.com")
        self.assertEqual(access.download_count, 1)

    def test_open_resource_pdf_still_downloads_without_email_gate(self):
        resource = LearningResource.objects.create(
            title="Open Variables PDF",
            summary="Open PDF reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Variables store values.",
            pdf_download_enabled=True,
            pdf_requires_email=False,
        )

        response = self.client.get(reverse("learn:resource-pdf", kwargs={"slug": resource.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


    def test_resource_performance_events_track_view_unlock_and_download(self):
        resource = LearningResource.objects.create(
            title="Tracked Lists PDF",
            summary="Track this gated PDF.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Lists store many values.",
            pdf_download_enabled=True,
            pdf_requires_email=True,
        )

        detail = self.client.get(reverse("learn:resource-detail", kwargs={"slug": resource.slug}))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(ResourcePerformanceEvent.objects.filter(resource=resource, event_type=ResourcePerformanceEvent.EventType.VIEW).count(), 1)

        self.client.post(
            reverse("learn:resource-pdf-gate", kwargs={"slug": resource.slug}),
            {"email": "tracked@example.com", "first_name": "Tracked"},
        )
        self.assertEqual(ResourcePerformanceEvent.objects.filter(resource=resource, event_type=ResourcePerformanceEvent.EventType.PDF_UNLOCK).count(), 1)

        self.client.get(reverse("learn:resource-pdf", kwargs={"slug": resource.slug}))
        self.assertEqual(ResourcePerformanceEvent.objects.filter(resource=resource, event_type=ResourcePerformanceEvent.EventType.PDF_DOWNLOAD).count(), 1)

    def test_resource_performance_report_export_contains_resource_metrics(self):
        staff = get_user_model().objects.create_user(email="resource-report@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        resource = LearningResource.objects.create(
            title="Tracked Variables Resource",
            summary="Variables reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Variables store values.",
        )
        ResourcePerformanceEvent.objects.create(resource=resource, event_type=ResourcePerformanceEvent.EventType.VIEW)

        response = self.client.get(reverse("studio:resource-performance-report-export"), {"section": "resources"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Tracked Variables Resource", response.content.decode())


    def test_resource_attribution_tracks_lesson_view_conversion(self):
        resource = LearningResource.objects.create(
            title="Variables Cheat Sheet",
            summary="A quick variables reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Variables store values.",
        )
        lesson = Lesson.objects.create(
            title="Variables Lesson",
            summary="Learn variables.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
        )

        self.client.get(reverse("learn:resource-detail", kwargs={"slug": resource.slug}))
        response = self.client.get(reverse("learn:lesson-detail", kwargs={"slug": lesson.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ResourceLessonConversionEvent.objects.filter(
                resource=resource,
                lesson=lesson,
                event_type=ResourceLessonConversionEvent.EventType.LESSON_VIEW,
            ).count(),
            1,
        )

    def test_resource_conversion_report_export_contains_conversion_metrics(self):
        staff = get_user_model().objects.create_user(email="conversion-report@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        resource = LearningResource.objects.create(
            title="Loops Cheat Sheet",
            summary="Loop reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Loops repeat code.",
        )
        lesson = Lesson.objects.create(
            title="Loops Lesson",
            summary="Learn loops.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
        )
        ResourceLessonConversionEvent.objects.create(
            resource=resource,
            lesson=lesson,
            event_type=ResourceLessonConversionEvent.EventType.LESSON_VIEW,
        )

        response = self.client.get(reverse("studio:resource-conversion-report-export"), {"section": "resources"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Loops Cheat Sheet", response.content.decode())


    def test_resource_cta_click_tracks_and_attributes_conversion(self):
        resource = LearningResource.objects.create(
            title="CTA Variables Resource",
            summary="A quick variables reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Variables store values.",
        )
        lesson = Lesson.objects.create(
            title="CTA Variables Lesson",
            summary="Learn variables.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
        )
        cta = ResourceCTA.objects.create(
            resource=resource,
            position=1,
            target_type=ResourceCTA.TargetType.LESSON,
            title="Start the matching lesson",
            button_label="Start lesson",
            target_lesson=lesson,
        )

        response = self.client.get(reverse("learn:resource-cta-click", kwargs={"resource_slug": resource.slug, "pk": cta.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ResourceCTAClickEvent.objects.filter(cta=cta, resource=resource).count(), 1)

        self.client.get(reverse("learn:lesson-detail", kwargs={"slug": lesson.slug}))
        conversion = ResourceLessonConversionEvent.objects.filter(resource=resource, lesson=lesson, cta=cta).first()
        self.assertIsNotNone(conversion)
        self.assertEqual(conversion.event_type, ResourceLessonConversionEvent.EventType.LESSON_VIEW)

    def test_resource_cta_report_export_contains_cta_metrics(self):
        staff = get_user_model().objects.create_user(email="cta-report@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        resource = LearningResource.objects.create(
            title="CTA Report Resource",
            summary="CTA report reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            content="Practice next.",
        )
        lesson = Lesson.objects.create(
            title="CTA Report Lesson",
            summary="Learn with a CTA.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
        )
        cta = ResourceCTA.objects.create(
            resource=resource,
            position=1,
            target_type=ResourceCTA.TargetType.CHALLENGE,
            title="Practice with a challenge",
            button_label="Practice now",
            target_lesson=lesson,
        )
        ResourceCTAClickEvent.objects.create(resource=resource, cta=cta, target_lesson=lesson, target_url="/learn/example/")

        response = self.client.get(reverse("studio:resource-cta-report-export"), {"section": "ctas"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Practice with a challenge", response.content.decode())


class ResourceCTARecommendationTests(TestCase):
    def test_resource_detail_recommends_and_applies_matching_lesson_cta(self):
        staff = get_user_model().objects.create_user(email="cta-recommend@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        lesson = Lesson.objects.create(
            title="Python Lists for Beginners",
            summary="Lists store multiple values in order.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
            learning_objective="Create and read values from a Python list.",
        )
        resource = LearningResource.objects.create(
            title="Python Lists Cheat Sheet",
            summary="A quick list reference for beginners.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Lists store multiple values and keep them in order.",
        )
        resource.related_lessons.add(lesson)

        recommendations = build_resource_cta_recommendations(resource)
        self.assertTrue(any(item.key == f"lesson:{lesson.pk}" for item in recommendations))

        response = self.client.post(
            reverse("studio:resource-cta-recommendation-apply", kwargs={"slug": resource.slug}),
            {"recommendation_key": f"lesson:{lesson.pk}"},
        )

        self.assertRedirects(response, resource.get_absolute_url())
        cta = ResourceCTA.objects.get(resource=resource, target_type=ResourceCTA.TargetType.LESSON)
        self.assertEqual(cta.target_lesson, lesson)
        self.assertIn("Start the matching lesson", cta.title)

    def test_resource_recommendations_include_quiz_and_challenge_when_available(self):
        lesson = Lesson.objects.create(
            title="Python Conditionals",
            summary="Use if statements to make decisions.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
        )
        question = QuizQuestion.objects.create(lesson=lesson, position=1, prompt="What keyword starts a condition?")
        QuizChoice.objects.create(question=question, position=1, text="if", is_correct=True)
        CodeChallenge.objects.create(
            lesson=lesson,
            position=1,
            title="Check a score",
            prompt="Print Pass when a score is at least 70.",
            starter_code="score = 72",
            expected_output="Pass",
        )
        resource = LearningResource.objects.create(
            title="Conditionals Cheat Sheet",
            summary="A decision-making reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Use if statements to make decisions.",
        )
        resource.related_lessons.add(lesson)

        keys = {item.key for item in build_resource_cta_recommendations(resource, limit=10)}

        self.assertIn(f"quiz:{lesson.pk}", keys)
        self.assertIn(f"challenge:{lesson.pk}", keys)


    def test_recommendation_feedback_records_shown_and_dismissed(self):
        staff = get_user_model().objects.create_user(email="cta-feedback@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        lesson = Lesson.objects.create(
            title="Python Dictionaries",
            summary="Dictionaries store key value pairs.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
        )
        resource = LearningResource.objects.create(
            title="Dictionaries Cheat Sheet",
            summary="A key value reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Dictionaries store values by key.",
        )
        resource.related_lessons.add(lesson)

        self.client.get(reverse("studio:resource-detail", kwargs={"slug": resource.slug}))
        feedback = ResourceCTARecommendationFeedback.objects.get(resource=resource, recommendation_key=f"lesson:{lesson.pk}")
        self.assertEqual(feedback.status, ResourceCTARecommendationFeedback.Status.SHOWN)

        response = self.client.post(
            reverse("studio:resource-cta-recommendation-dismiss", kwargs={"slug": resource.slug}),
            {"recommendation_key": f"lesson:{lesson.pk}"},
        )

        self.assertRedirects(response, resource.get_absolute_url())
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, ResourceCTARecommendationFeedback.Status.DISMISSED)
        self.assertIsNotNone(feedback.dismissed_at)

    def test_applying_recommendation_marks_feedback_accepted(self):
        staff = get_user_model().objects.create_user(email="cta-accepted@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        lesson = Lesson.objects.create(
            title="Python Tuples",
            summary="Tuples store ordered values.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
        )
        resource = LearningResource.objects.create(
            title="Tuples Cheat Sheet",
            summary="Tuple quick reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Tuples store ordered values.",
        )
        resource.related_lessons.add(lesson)

        self.client.post(
            reverse("studio:resource-cta-recommendation-apply", kwargs={"slug": resource.slug}),
            {"recommendation_key": f"lesson:{lesson.pk}"},
        )

        feedback = ResourceCTARecommendationFeedback.objects.get(resource=resource, recommendation_key=f"lesson:{lesson.pk}")
        self.assertEqual(feedback.status, ResourceCTARecommendationFeedback.Status.ACCEPTED)
        self.assertIsNotNone(feedback.applied_cta)

    def test_exact_feedback_adjusts_recommendation_score(self):
        lesson = Lesson.objects.create(
            title="Python Sets",
            summary="Sets store unique values.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
        )
        resource = LearningResource.objects.create(
            title="Sets Cheat Sheet",
            summary="Unique values reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Sets store unique values.",
        )
        resource.related_lessons.add(lesson)
        initial = next(item for item in build_resource_cta_recommendations(resource, limit=10) if item.key == f"lesson:{lesson.pk}")
        ResourceCTARecommendationFeedback.objects.create(
            resource=resource,
            recommendation_key=f"lesson:{lesson.pk}",
            target_type=ResourceCTA.TargetType.LESSON,
            target_lesson=lesson,
            title="Start the matching lesson: Python Sets",
            score=initial.score,
            reasons=[],
            status=ResourceCTARecommendationFeedback.Status.DISMISSED,
        )

        adjusted = next(item for item in build_resource_cta_recommendations(resource, limit=10) if item.key == f"lesson:{lesson.pk}")

        self.assertLess(adjusted.feedback_adjustment, 0)
        self.assertLess(adjusted.score, adjusted.base_score)
        self.assertTrue(adjusted.is_dismissed)
        self.assertTrue(any("dismissed" in note for note in adjusted.ranking_notes))

    def test_accepted_patterns_boost_similar_recommendations(self):
        accepted_lesson = Lesson.objects.create(
            title="Python Lists",
            summary="Lists keep values in order.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
        )
        source_resource = LearningResource.objects.create(
            title="Lists Cheat Sheet",
            summary="List reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Lists keep values in order.",
        )
        ResourceCTARecommendationFeedback.objects.create(
            resource=source_resource,
            recommendation_key=f"lesson:{accepted_lesson.pk}",
            target_type=ResourceCTA.TargetType.LESSON,
            target_lesson=accepted_lesson,
            title="Start the matching lesson: Python Lists",
            score=100,
            reasons=[],
            status=ResourceCTARecommendationFeedback.Status.ACCEPTED,
        )

        target_lesson = Lesson.objects.create(
            title="Python Tuples",
            summary="Tuples keep ordered values.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
        )
        target_resource = LearningResource.objects.create(
            title="Tuples Cheat Sheet",
            summary="Tuple reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Tuples keep ordered values.",
        )
        target_resource.related_lessons.add(target_lesson)

        recommendation = next(item for item in build_resource_cta_recommendations(target_resource, limit=10) if item.key == f"lesson:{target_lesson.pk}")

        self.assertGreater(recommendation.feedback_adjustment, 0)
        self.assertGreater(recommendation.score, recommendation.base_score)
        self.assertTrue(any("accepted" in note for note in recommendation.ranking_notes))


    def test_recommendation_tuning_changes_cta_bonus(self):
        tuning = RecommendationTuning.get_active()
        tuning.lesson_cta_bonus = 1
        tuning.quiz_cta_bonus = 90
        tuning.save()
        lesson = Lesson.objects.create(
            title="Python Boolean Quiz",
            summary="Booleans use True and False.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
        )
        QuizQuestion.objects.create(lesson=lesson, prompt="Which value is a Boolean?", explanation="True is a Boolean.")
        resource = LearningResource.objects.create(
            title="Boolean Cheat Sheet",
            summary="Boolean reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Booleans use True and False.",
        )
        resource.related_lessons.add(lesson)

        recommendations = build_resource_cta_recommendations(resource, limit=10)
        lesson_rec = next(item for item in recommendations if item.key == f"lesson:{lesson.pk}")
        quiz_rec = next(item for item in recommendations if item.key == f"quiz:{lesson.pk}")

        self.assertGreater(quiz_rec.score, lesson_rec.score)

    def test_recommendation_tuning_view_updates_active_profile(self):
        staff = get_user_model().objects.create_user(email="tuning@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        response = self.client.post(
            reverse("studio:recommendation-tuning"),
            {
                "name": "Growth tuning",
                "is_active": "on",
                "lesson_cta_bonus": 25,
                "quiz_cta_bonus": 45,
                "challenge_cta_bonus": 55,
                "pdf_open_bonus": 35,
                "pdf_lead_magnet_bonus": 80,
                "newsletter_cta_bonus": 30,
                "related_lesson_weight": 80,
                "category_match_weight": 30,
                "difficulty_match_weight": 18,
                "topic_overlap_weight": 8,
                "topic_overlap_cap": 40,
                "active_quiz_weight": 10,
                "active_challenge_weight": 12,
                "practice_code_weight": 5,
                "conversion_weight": 6,
                "conversion_cap": 48,
                "cta_click_weight": 3,
                "cta_click_cap": 24,
                "exact_accepted_boost": 60,
                "exact_dismissed_penalty": 90,
                "ignored_per_show_penalty": 8,
                "ignored_penalty_cap": 40,
                "similar_accepted_boost": 6,
                "similar_accepted_cap": 30,
                "similar_dismissed_penalty": 8,
                "similar_dismissed_cap": 40,
                "similar_ignored_penalty": 3,
                "similar_ignored_cap": 18,
                "same_lesson_accepted_boost": 5,
                "same_lesson_accepted_cap": 20,
                "same_lesson_dismissed_penalty": 6,
                "same_lesson_dismissed_cap": 24,
                "feedback_adjustment_floor": -120,
                "feedback_adjustment_ceiling": 90,
                "notes": "Favor lead magnets and challenge practice.",
            },
        )

        self.assertRedirects(response, reverse("studio:recommendation-tuning"))
        tuning.refresh_from_db()
        self.assertEqual(tuning.name, "Growth tuning")
        self.assertEqual(tuning.challenge_cta_bonus, 55)
        log = RecommendationTuningChangeLog.objects.latest("created_at")
        self.assertEqual(log.action, RecommendationTuningChangeLog.Action.MANUAL_UPDATE)
        self.assertEqual(log.changed_by, staff)
        self.assertIn("name", log.diff)
        self.assertIn("challenge_cta_bonus", log.diff)

    def test_apply_recommendation_tuning_preset_updates_active_profile(self):
        staff = get_user_model().objects.create_user(email="preset@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        tuning.pdf_lead_magnet_bonus = 10
        tuning.newsletter_cta_bonus = 10
        tuning.save()

        response = self.client.post(
            reverse("studio:recommendation-tuning-preset-apply"),
            {"preset_key": "lead_magnet_growth", "next": reverse("studio:recommendation-tuning")},
        )

        self.assertRedirects(response, reverse("studio:recommendation-tuning"))
        tuning.refresh_from_db()
        self.assertEqual(tuning.name, "Lead Magnet Growth")
        self.assertEqual(tuning.pdf_lead_magnet_bonus, 95)
        self.assertEqual(tuning.newsletter_cta_bonus, 70)
        log = RecommendationTuningChangeLog.objects.latest("created_at")
        self.assertEqual(log.action, RecommendationTuningChangeLog.Action.PRESET_APPLIED)
        self.assertEqual(log.preset_key, "lead_magnet_growth")
        self.assertEqual(log.changed_by, staff)
        self.assertIn("pdf_lead_magnet_bonus", log.diff)


    def test_recommendation_tuning_history_view_and_export(self):
        staff = get_user_model().objects.create_user(email="history@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"lesson_cta_bonus": 20},
            after={"lesson_cta_bonus": 30},
            diff={"lesson_cta_bonus": {"before": 20, "after": 30}},
            reason="Testing history report.",
        )

        response = self.client.get(reverse("studio:recommendation-tuning-history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Testing history report.")

        export = self.client.get(reverse("studio:recommendation-tuning-history-export"))
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/csv", export["Content-Type"])
        self.assertContains(export, "lesson_cta_bonus")

    def test_recommendation_tuning_simulation_view_compares_presets_without_saving(self):
        staff = get_user_model().objects.create_user(email="simulate@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        tuning.name = "Original tuning"
        tuning.challenge_cta_bonus = 5
        tuning.save()
        lesson = Lesson.objects.create(
            title="Python Practice",
            summary="Practice Python variables.",
            status=Lesson.Status.READY,
            website_status=Lesson.Status.PUBLISHED,
            difficulty=Lesson.Difficulty.BEGINNER,
            starter_code="name = 'Michael'",
        )
        CodeChallenge.objects.create(lesson=lesson, prompt="Print the name variable.")
        resource = LearningResource.objects.create(
            title="Variables Cheat Sheet",
            summary="Variables reference.",
            status=LearningResource.Status.PUBLISHED,
            resource_type=LearningResource.ResourceType.CHEAT_SHEET,
            difficulty=Lesson.Difficulty.BEGINNER,
            content="Variables store reusable values.",
        )
        resource.related_lessons.add(lesson)

        response = self.client.post(
            reverse("studio:recommendation-tuning-simulation"),
            {"resource": resource.pk, "preset_keys": ["challenge_practice"], "limit": 6},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Challenge Practice")
        self.assertContains(response, "Active: Original tuning")
        tuning.refresh_from_db()
        self.assertEqual(tuning.name, "Original tuning")
        self.assertEqual(tuning.challenge_cta_bonus, 5)

    def test_recommendation_tuning_rollback_restores_before_snapshot(self):
        staff = get_user_model().objects.create_user(email="rollback@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        tuning.name = "Experiment"
        tuning.lesson_cta_bonus = 99
        tuning.quiz_cta_bonus = 88
        tuning.save()
        log = RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"name": "Original", "is_active": True, "lesson_cta_bonus": 20, "quiz_cta_bonus": 35},
            after={"name": "Experiment", "is_active": True, "lesson_cta_bonus": 99, "quiz_cta_bonus": 88},
            diff={"lesson_cta_bonus": {"before": 20, "after": 99}},
            reason="Testing rollback.",
        )

        response = self.client.post(
            reverse("studio:recommendation-tuning-rollback", args=[log.pk]),
            {"snapshot": "before", "rollback_reason": "Restore original weights."},
        )

        self.assertRedirects(response, reverse("studio:recommendation-tuning-history"))
        tuning.refresh_from_db()
        self.assertEqual(tuning.name, "Original")
        self.assertEqual(tuning.lesson_cta_bonus, 20)
        self.assertEqual(tuning.quiz_cta_bonus, 35)
        rollback_log = RecommendationTuningChangeLog.objects.latest("created_at")
        self.assertEqual(rollback_log.action, RecommendationTuningChangeLog.Action.ROLLBACK_RESTORED)
        self.assertIn("lesson_cta_bonus", rollback_log.diff)
        self.assertEqual(rollback_log.reason, "Restore original weights.")


    def test_recommendation_tuning_experiment_outcome_update(self):
        staff = get_user_model().objects.create_user(email="experiment@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        log = RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"lesson_cta_bonus": 20},
            after={"lesson_cta_bonus": 45},
            diff={"lesson_cta_bonus": {"before": 20, "after": 45}},
            reason="Test experiment outcome.",
            experiment_label="August Instagram growth test",
            experiment_status=RecommendationTuningChangeLog.ExperimentStatus.RUNNING,
        )

        response = self.client.post(
            reverse("studio:recommendation-tuning-experiment", args=[log.pk]),
            {
                "experiment_label": "August Instagram growth test",
                "experiment_status": RecommendationTuningChangeLog.ExperimentStatus.KEEP,
                "experiment_outcome": RecommendationTuningChangeLog.ExperimentOutcome.POSITIVE,
                "experiment_notes": "Follower growth improved, keep these weights.",
            },
        )

        self.assertRedirects(response, reverse("studio:recommendation-tuning-history"))
        log.refresh_from_db()
        self.assertEqual(log.experiment_status, RecommendationTuningChangeLog.ExperimentStatus.KEEP)
        self.assertEqual(log.experiment_outcome, RecommendationTuningChangeLog.ExperimentOutcome.POSITIVE)
        self.assertEqual(log.outcome_recorded_by, staff)
        self.assertIsNotNone(log.outcome_recorded_at)

    def test_recommendation_tuning_history_filters_experiments(self):
        staff = get_user_model().objects.create_user(email="experiment-filter@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"lesson_cta_bonus": 20},
            after={"lesson_cta_bonus": 45},
            diff={"lesson_cta_bonus": {"before": 20, "after": 45}},
            experiment_label="August Instagram growth test",
            experiment_status=RecommendationTuningChangeLog.ExperimentStatus.RUNNING,
            experiment_outcome=RecommendationTuningChangeLog.ExperimentOutcome.POSITIVE,
        )
        RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"quiz_cta_bonus": 35},
            after={"quiz_cta_bonus": 10},
            diff={"quiz_cta_bonus": {"before": 35, "after": 10}},
            experiment_label="Archive test",
            experiment_status=RecommendationTuningChangeLog.ExperimentStatus.COMPLETE,
            experiment_outcome=RecommendationTuningChangeLog.ExperimentOutcome.NEGATIVE,
        )

        response = self.client.get(reverse("studio:recommendation-tuning-history"), {"experiment_status": "running", "experiment_label": "Instagram"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "August Instagram growth test")
        self.assertNotContains(response, "Archive test")

        export = self.client.get(reverse("studio:recommendation-tuning-history-export"), {"experiment_outcome": "positive"})
        self.assertEqual(export.status_code, 200)
        self.assertContains(export, "experiment_label")
        self.assertContains(export, "August Instagram growth test")

    def test_recommendation_tuning_rollback_review_page(self):
        staff = get_user_model().objects.create_user(email="rollback-view@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        log = RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.PRESET_APPLIED,
            changed_by=staff,
            before={"lesson_cta_bonus": 20},
            after={"lesson_cta_bonus": 65},
            diff={"lesson_cta_bonus": {"before": 20, "after": 65}},
        )

        response = self.client.get(reverse("studio:recommendation-tuning-rollback", args=[log.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Restore before-change snapshot")
        self.assertContains(response, "lesson_cta_bonus")


    def test_recommendation_tuning_experiment_snapshot_create_and_export(self):
        staff = get_user_model().objects.create_user(email="snapshot@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        log = RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"lesson_cta_bonus": 20},
            after={"lesson_cta_bonus": 45},
            diff={"lesson_cta_bonus": {"before": 20, "after": 45}},
            reason="Test snapshot.",
            experiment_label="August Instagram growth test",
            experiment_status=RecommendationTuningChangeLog.ExperimentStatus.RUNNING,
        )
        lesson = Lesson.objects.create(title="Snapshot lesson")
        PublishingRecord.objects.create(
            lesson=lesson,
            platform=PublishingRecord.Platform.FACEBOOK,
            published_at=log.created_at,
            reach=100,
            likes=10,
            clicks=5,
            new_followers=3,
        )

        response = self.client.post(
            reverse("studio:recommendation-tuning-experiment-snapshot-create", args=[log.pk]),
            {"window_days": 14, "notes": "Compare after launch."},
        )

        snapshot = RecommendationTuningExperimentSnapshot.objects.get(change_log=log)
        self.assertRedirects(response, reverse("studio:recommendation-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        self.assertEqual(snapshot.window_days, 14)
        self.assertEqual(snapshot.after_metrics["social"]["new_followers"], 3)
        self.assertEqual(snapshot.deltas["social"]["new_followers"]["change"], 3)

        detail = self.client.get(reverse("studio:recommendation-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Social publishing")

        export = self.client.get(reverse("studio:recommendation-tuning-experiment-snapshot-export", args=[snapshot.pk]))
        self.assertEqual(export.status_code, 200)
        self.assertContains(export, "experiment_label")
        self.assertContains(export, "New followers")


    def test_experiment_snapshot_recommends_keep_and_can_record_decision(self):
        staff = get_user_model().objects.create_user(email="decision@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        log = RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"lesson_cta_bonus": 20},
            after={"lesson_cta_bonus": 55},
            diff={"lesson_cta_bonus": {"before": 20, "after": 55}},
            experiment_label="Decision test",
            experiment_status=RecommendationTuningChangeLog.ExperimentStatus.RUNNING,
        )
        now = timezone.now()
        snapshot = RecommendationTuningExperimentSnapshot.objects.create(
            change_log=log,
            window_days=14,
            before_start=now - timedelta(days=14),
            before_end=now,
            after_start=now,
            after_end=now + timedelta(days=14),
            before_metrics={},
            after_metrics={},
            deltas={
                "social": {"new_followers": {"before": 1, "after": 5, "change": 4, "pct": 400}},
                "resources": {"pdf_downloads": {"before": 2, "after": 8, "change": 6, "pct": 300}},
                "newsletter": {"clicks": {"before": 1, "after": 3, "change": 2, "pct": 200}},
                "ctas": {"cta_clicks": {"before": 1, "after": 7, "change": 6, "pct": 600}},
                "conversions": {"total_conversions": {"before": 1, "after": 6, "change": 5, "pct": 500}},
            },
            summary={},
            generated_by=staff,
        )

        detail = self.client.get(reverse("studio:recommendation-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "DECISION RECOMMENDATION")
        self.assertContains(detail, "Keep changes")

        response = self.client.post(
            reverse("studio:recommendation-tuning-experiment-snapshot-detail", args=[snapshot.pk]),
            {"action": "apply_decision_recommendation", "decision_note": "Looks strong."},
        )
        self.assertRedirects(response, reverse("studio:recommendation-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        log.refresh_from_db()
        self.assertEqual(log.experiment_status, RecommendationTuningChangeLog.ExperimentStatus.KEEP)
        self.assertEqual(log.experiment_outcome, RecommendationTuningChangeLog.ExperimentOutcome.POSITIVE)
        self.assertIn("Decision recommendation from snapshot", log.experiment_notes)

    def test_experiment_snapshot_recommends_rollback_for_declines(self):
        staff = get_user_model().objects.create_user(email="rollback-decision@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = RecommendationTuning.get_active()
        log = RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            before={"challenge_cta_bonus": 45},
            after={"challenge_cta_bonus": 5},
            diff={"challenge_cta_bonus": {"before": 45, "after": 5}},
            experiment_label="Rollback decision test",
            experiment_status=RecommendationTuningChangeLog.ExperimentStatus.RUNNING,
        )
        now = timezone.now()
        snapshot = RecommendationTuningExperimentSnapshot.objects.create(
            change_log=log,
            window_days=14,
            before_start=now - timedelta(days=14),
            before_end=now,
            after_start=now,
            after_end=now + timedelta(days=14),
            before_metrics={},
            after_metrics={},
            deltas={
                "social": {"new_followers": {"before": 8, "after": 2, "change": -6, "pct": -75}},
                "resources": {"pdf_downloads": {"before": 9, "after": 2, "change": -7, "pct": -77.78}},
                "newsletter": {"clicks": {"before": 5, "after": 1, "change": -4, "pct": -80}, "unsubscribes": {"before": 0, "after": 3, "change": 3, "pct": None}},
                "ctas": {"cta_clicks": {"before": 12, "after": 3, "change": -9, "pct": -75}},
                "conversions": {"total_conversions": {"before": 10, "after": 2, "change": -8, "pct": -80}},
            },
            summary={},
            generated_by=staff,
        )

        detail = self.client.get(reverse("studio:recommendation-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Rollback recommended")


    def test_experiment_decision_tuning_page_updates_thresholds(self):
        staff = get_user_model().objects.create_user(email="decision-rules@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        tuning = ExperimentDecisionTuning.get_active()

        response = self.client.post(reverse("studio:experiment-decision-tuning"), {
            "name": tuning.name,
            "is_active": "on",
            "keep_score_threshold": "8",
            "keep_primary_positive_min": "3",
            "keep_high_confidence_score": "14",
            "rollback_score_threshold": "-6",
            "rollback_primary_negative_min": "2",
            "rollback_high_confidence_score": "-12",
            "low_confidence_abs_score": "5",
            "max_metric_change_magnitude": "4",
            "social_new_followers_weight": "3",
            "social_engagements_weight": "1.4",
            "social_reach_weight": "0.8",
            "social_clicks_weight": "1.2",
            "resources_pdf_downloads_weight": "1.6",
            "resources_pdf_unlocks_weight": "1.3",
            "resources_subscribers_weight": "2",
            "newsletter_clicks_weight": "1.7",
            "newsletter_open_rate_weight": "0.8",
            "ctas_cta_clicks_weight": "1.8",
            "conversions_total_conversions_weight": "2.5",
            "conversions_lesson_views_weight": "1.2",
            "conversions_quiz_attempts_weight": "1.5",
            "conversions_challenge_attempts_weight": "1.7",
            "conversions_lesson_completions_weight": "2.2",
            "newsletter_unsubscribes_penalty_weight": "2",
            "newsletter_bounces_penalty_weight": "1.5",
            "notes": "Require stronger signal before keep decisions.",
        })

        self.assertRedirects(response, reverse("studio:experiment-decision-tuning"))
        tuning.refresh_from_db()
        self.assertEqual(tuning.keep_score_threshold, 8.0)
        self.assertEqual(tuning.keep_primary_positive_min, 3)
        self.assertEqual(tuning.social_new_followers_weight, 3.0)

    def test_experiment_decision_tuning_changes_recommendation_threshold(self):
        staff = get_user_model().objects.create_user(email="strict-rules@example.com", password="testpass", is_staff=True)
        self.client.force_login(staff)
        decision_tuning = ExperimentDecisionTuning.get_active()
        decision_tuning.keep_score_threshold = 50
        decision_tuning.keep_primary_positive_min = 2
        decision_tuning.save()
        tuning = RecommendationTuning.get_active()
        log = RecommendationTuningChangeLog.objects.create(
            tuning=tuning,
            action=RecommendationTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=staff,
            experiment_label="Strict threshold test",
            experiment_status=RecommendationTuningChangeLog.ExperimentStatus.RUNNING,
        )
        now = timezone.now()
        snapshot = RecommendationTuningExperimentSnapshot.objects.create(
            change_log=log,
            window_days=14,
            before_start=now - timedelta(days=14),
            before_end=now,
            after_start=now,
            after_end=now + timedelta(days=14),
            before_metrics={},
            after_metrics={},
            deltas={
                "social": {"new_followers": {"change": 4}},
                "resources": {"pdf_downloads": {"change": 6}},
                "conversions": {"total_conversions": {"change": 5}},
            },
            summary={},
            generated_by=staff,
        )

        detail = self.client.get(reverse("studio:recommendation-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Inconclusive")
        self.assertContains(detail, "Decision rules")



class ExperimentDecisionTuningHistoryTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            email="decision-history@example.com",
            password="testpass",
            is_staff=True,
        )
        self.client.force_login(self.staff)

    def _post_payload(self, **overrides):
        tuning = ExperimentDecisionTuning.get_active()
        payload = {
            "name": tuning.name,
            "is_active": "on",
            "keep_score_threshold": tuning.keep_score_threshold,
            "keep_primary_positive_min": tuning.keep_primary_positive_min,
            "keep_high_confidence_score": tuning.keep_high_confidence_score,
            "rollback_score_threshold": tuning.rollback_score_threshold,
            "rollback_primary_negative_min": tuning.rollback_primary_negative_min,
            "rollback_high_confidence_score": tuning.rollback_high_confidence_score,
            "low_confidence_abs_score": tuning.low_confidence_abs_score,
            "max_metric_change_magnitude": tuning.max_metric_change_magnitude,
            "social_new_followers_weight": tuning.social_new_followers_weight,
            "social_engagements_weight": tuning.social_engagements_weight,
            "social_reach_weight": tuning.social_reach_weight,
            "social_clicks_weight": tuning.social_clicks_weight,
            "resources_pdf_downloads_weight": tuning.resources_pdf_downloads_weight,
            "resources_pdf_unlocks_weight": tuning.resources_pdf_unlocks_weight,
            "resources_subscribers_weight": tuning.resources_subscribers_weight,
            "newsletter_clicks_weight": tuning.newsletter_clicks_weight,
            "newsletter_open_rate_weight": tuning.newsletter_open_rate_weight,
            "ctas_cta_clicks_weight": tuning.ctas_cta_clicks_weight,
            "conversions_total_conversions_weight": tuning.conversions_total_conversions_weight,
            "conversions_lesson_views_weight": tuning.conversions_lesson_views_weight,
            "conversions_quiz_attempts_weight": tuning.conversions_quiz_attempts_weight,
            "conversions_challenge_attempts_weight": tuning.conversions_challenge_attempts_weight,
            "conversions_lesson_completions_weight": tuning.conversions_lesson_completions_weight,
            "newsletter_unsubscribes_penalty_weight": tuning.newsletter_unsubscribes_penalty_weight,
            "newsletter_bounces_penalty_weight": tuning.newsletter_bounces_penalty_weight,
            "notes": tuning.notes,
            "change_reason": "Testing decision-rule audit logging.",
        }
        payload.update(overrides)
        return payload

    def test_decision_rule_save_creates_audit_log(self):
        response = self.client.post(
            reverse("studio:experiment-decision-tuning"),
            self._post_payload(keep_score_threshold="8.5"),
        )
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning"))
        log = ExperimentDecisionTuningChangeLog.objects.latest("created_at")
        self.assertEqual(log.action, ExperimentDecisionTuningChangeLog.Action.MANUAL_UPDATE)
        self.assertIn("keep_score_threshold", log.diff)
        self.assertEqual(log.changed_by, self.staff)

    def test_decision_rule_history_and_export(self):
        tuning = ExperimentDecisionTuning.get_active()
        ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.staff,
            before={"keep_score_threshold": 6.0},
            after={"keep_score_threshold": 7.0},
            diff={"keep_score_threshold": {"before": 6.0, "after": 7.0}},
            reason="History test",
        )
        response = self.client.get(reverse("studio:experiment-decision-tuning-history"))
        self.assertContains(response, "Decision-rule audit log")
        export = self.client.get(reverse("studio:experiment-decision-tuning-history-export"))
        self.assertContains(export, "keep_score_threshold")
        self.assertEqual(export["Content-Type"], "text/csv")

    def test_decision_rule_rollback_restores_snapshot(self):
        tuning = ExperimentDecisionTuning.get_active()
        before = {field.name: getattr(tuning, field.name) for field in ExperimentDecisionTuning._meta.fields if field.name not in {"id", "created_at", "updated_at"}}
        after = before.copy()
        before["keep_score_threshold"] = 4.0
        after["keep_score_threshold"] = 9.0
        log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.staff,
            before=before,
            after=after,
            diff={"keep_score_threshold": {"before": 4.0, "after": 9.0}},
        )
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-rollback", args=[log.pk]),
            {"snapshot": "before", "rollback_reason": "Undo test"},
        )
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning-history"))
        tuning.refresh_from_db()
        self.assertEqual(tuning.keep_score_threshold, 4.0)
        rollback = ExperimentDecisionTuningChangeLog.objects.latest("created_at")
        self.assertEqual(rollback.action, ExperimentDecisionTuningChangeLog.Action.ROLLBACK_RESTORED)


    def test_decision_rule_preset_application_creates_audit_log(self):
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-preset-apply"),
            {"preset_key": "aggressive_growth", "change_reason": "Testing preset apply"},
        )
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning"))
        tuning = ExperimentDecisionTuning.get_active()
        self.assertEqual(tuning.name, "Aggressive Growth")
        self.assertEqual(tuning.keep_primary_positive_min, 1)
        log = ExperimentDecisionTuningChangeLog.objects.latest("created_at")
        self.assertEqual(log.action, ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED)
        self.assertIn("social_new_followers_weight", log.diff)

    def test_decision_rule_simulation_does_not_change_active_rules(self):
        tuning = ExperimentDecisionTuning.get_active()
        original_name = tuning.name
        change_log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.staff,
            before={},
            after={},
            diff={},
            experiment_label="Simulation test",
            experiment_status=ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING,
        )
        now = timezone.now()
        snapshot = ExperimentDecisionTuningExperimentSnapshot.objects.create(
            change_log=change_log,
            window_days=7,
            before_start=now - timedelta(days=14),
            before_end=now - timedelta(days=7),
            after_start=now - timedelta(days=7),
            after_end=now,
            deltas={
                "social": {"new_followers": {"change": 4}, "clicks": {"change": 2}},
                "resources": {"pdf_downloads": {"change": 3}, "subscribers": {"change": 2}},
                "conversions": {"total_conversions": {"change": 5}},
            },
            generated_by=self.staff,
        )
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-simulation"),
            {"snapshot": snapshot.pk, "preset_keys": ["aggressive_growth", "conservative_quality"]},
        )
        self.assertContains(response, "Aggressive Growth")
        self.assertContains(response, "Conservative Quality")
        tuning.refresh_from_db()
        self.assertEqual(tuning.name, original_name)

    def test_decision_rule_manual_change_can_be_labeled_as_experiment(self):
        response = self.client.post(
            reverse("studio:experiment-decision-tuning"),
            self._post_payload(
                keep_score_threshold="8.75",
                experiment_label="August decision rule test",
                experiment_status=ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING,
                experiment_notes="Hypothesis: stricter keep rules improve quality.",
            ),
        )
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning"))
        log = ExperimentDecisionTuningChangeLog.objects.latest("created_at")
        self.assertEqual(log.experiment_label, "August decision rule test")
        self.assertEqual(log.experiment_status, ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING)
        self.assertTrue(log.is_experiment)

    def test_decision_rule_preset_can_start_named_experiment(self):
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-preset-apply"),
            {
                "preset_key": "lead_magnet_focus",
                "experiment_label": "Lead magnet decision test",
                "experiment_status": ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING,
                "experiment_notes": "Hypothesis: lead magnet rules produce better keep decisions for resources.",
            },
        )
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning"))
        log = ExperimentDecisionTuningChangeLog.objects.latest("created_at")
        self.assertEqual(log.action, ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED)
        self.assertEqual(log.preset_key, "lead_magnet_focus")
        self.assertEqual(log.preset_name, "Lead Magnet Focus")
        self.assertEqual(log.experiment_label, "Lead magnet decision test")
        self.assertEqual(log.experiment_status, ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING)

    def test_decision_rule_experiment_outcome_page_updates_log(self):
        tuning = ExperimentDecisionTuning.get_active()
        log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED,
            changed_by=self.staff,
            preset_key="balanced_learning",
            preset_name="Balanced Learning",
            experiment_label="Balanced decision test",
            experiment_status=ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING,
        )
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-experiment", args=[log.pk]),
            {
                "experiment_label": "Balanced decision test",
                "experiment_status": ExperimentDecisionTuningChangeLog.ExperimentStatus.KEEP,
                "experiment_outcome": ExperimentDecisionTuningChangeLog.ExperimentOutcome.POSITIVE,
                "experiment_notes": "Keep this preset. Snapshot performance improved.",
            },
        )
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning-history"))
        log.refresh_from_db()
        self.assertEqual(log.experiment_status, ExperimentDecisionTuningChangeLog.ExperimentStatus.KEEP)
        self.assertEqual(log.experiment_outcome, ExperimentDecisionTuningChangeLog.ExperimentOutcome.POSITIVE)
        self.assertEqual(log.outcome_recorded_by, self.staff)
        self.assertIsNotNone(log.outcome_recorded_at)

    def test_decision_rule_history_filters_and_exports_experiment_fields(self):
        tuning = ExperimentDecisionTuning.get_active()
        ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED,
            changed_by=self.staff,
            preset_key="aggressive_growth",
            preset_name="Aggressive Growth",
            experiment_label="Growth rules test",
            experiment_status=ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING,
            experiment_outcome=ExperimentDecisionTuningChangeLog.ExperimentOutcome.NOT_RECORDED,
        )
        response = self.client.get(reverse("studio:experiment-decision-tuning-history"), {"experiment_label": "Growth"})
        self.assertContains(response, "Growth rules test")
        export = self.client.get(reverse("studio:experiment-decision-tuning-history-export"), {"experiment_label": "Growth"})
        self.assertContains(export, "preset_key")
        self.assertContains(export, "aggressive_growth")
        self.assertContains(export, "Growth rules test")


    def test_decision_rule_experiment_snapshot_create_and_export(self):
        tuning = ExperimentDecisionTuning.get_active()
        log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED,
            changed_by=self.staff,
            preset_key="lead_magnet_focus",
            preset_name="Lead Magnet Focus",
            experiment_label="Lead magnet decision snapshot",
            experiment_status=ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING,
        )
        PublishingRecord.objects.create(
            lesson=Lesson.objects.create(title="Snapshot lesson", summary="Test"),
            platform="facebook",
            published_at=timezone.now() + timedelta(days=1),
            new_followers=4,
            reach=100,
            likes=10,
        )
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-experiment-snapshot-create", args=[log.pk]),
            {"window_days": 14, "notes": "Review lead magnet decision rules."},
        )
        snapshot = ExperimentDecisionTuningExperimentSnapshot.objects.get(change_log=log)
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        self.assertEqual(snapshot.window_days, 14)
        self.assertEqual(snapshot.deltas["social"]["new_followers"]["change"], 4)

        detail = self.client.get(reverse("studio:experiment-decision-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        self.assertContains(detail, "Decision recommendation")
        export = self.client.get(reverse("studio:experiment-decision-tuning-experiment-snapshot-export", args=[snapshot.pk]))
        self.assertContains(export, "Lead magnet decision snapshot")
        self.assertContains(export, "New followers")

    def test_decision_rule_snapshot_can_record_recommendation(self):
        tuning = ExperimentDecisionTuning.get_active()
        log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.MANUAL_UPDATE,
            changed_by=self.staff,
            experiment_label="Decision keep test",
            experiment_status=ExperimentDecisionTuningChangeLog.ExperimentStatus.RUNNING,
        )
        now = timezone.now()
        snapshot = ExperimentDecisionTuningExperimentSnapshot.objects.create(
            change_log=log,
            window_days=7,
            before_start=now - timedelta(days=14),
            before_end=now - timedelta(days=7),
            after_start=now - timedelta(days=7),
            after_end=now,
            deltas={
                "social": {"new_followers": {"change": 5}, "clicks": {"change": 3}},
                "resources": {"pdf_downloads": {"change": 2}},
                "newsletter": {"clicks": {"change": 2}},
                "ctas": {"cta_clicks": {"change": 3}},
                "conversions": {"total_conversions": {"change": 4}},
            },
            generated_by=self.staff,
        )
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-experiment-snapshot-detail", args=[snapshot.pk]),
            {"action": "apply_decision_recommendation", "decision_note": "Looks strong."},
        )
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning-experiment-snapshot-detail", args=[snapshot.pk]))
        log.refresh_from_db()
        self.assertEqual(log.experiment_outcome, ExperimentDecisionTuningChangeLog.ExperimentOutcome.POSITIVE)
        self.assertIn("Decision-rule experiment recommendation from snapshot", log.experiment_notes)


    def test_decision_rule_snapshot_comparison_page_and_export(self):
        tuning = ExperimentDecisionTuning.get_active()
        first_log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED,
            changed_by=self.staff,
            preset_key="aggressive_growth",
            preset_name="Aggressive Growth",
            experiment_label="Aggressive rules test",
        )
        second_log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED,
            changed_by=self.staff,
            preset_key="balanced_learning",
            preset_name="Balanced Learning",
            experiment_label="Balanced rules test",
        )
        now = timezone.now()
        first = ExperimentDecisionTuningExperimentSnapshot.objects.create(
            change_log=first_log,
            window_days=7,
            before_start=now - timedelta(days=14),
            before_end=now - timedelta(days=7),
            after_start=now - timedelta(days=7),
            after_end=now,
            deltas={
                "social": {"new_followers": {"before": 1, "after": 5, "change": 4, "pct": 400}},
                "resources": {"pdf_downloads": {"before": 0, "after": 2, "change": 2, "pct": None}},
                "newsletter": {"clicks": {"before": 0, "after": 1, "change": 1, "pct": None}},
                "ctas": {"cta_clicks": {"before": 0, "after": 3, "change": 3, "pct": None}},
                "conversions": {"total_conversions": {"before": 0, "after": 4, "change": 4, "pct": None}},
            },
            summary={"primary_social_delta": {"change": 4}, "primary_conversion_delta": {"change": 4}},
            generated_by=self.staff,
        )
        second = ExperimentDecisionTuningExperimentSnapshot.objects.create(
            change_log=second_log,
            window_days=14,
            before_start=now - timedelta(days=28),
            before_end=now - timedelta(days=14),
            after_start=now - timedelta(days=14),
            after_end=now,
            deltas={"social": {"new_followers": {"before": 5, "after": 3, "change": -2, "pct": -40}}},
            summary={"primary_social_delta": {"change": -2}},
            generated_by=self.staff,
        )
        params = {"snapshots": [first.pk, second.pk], "preset_keys": ["lead_magnet_focus"]}
        response = self.client.get(reverse("studio:experiment-decision-tuning-experiment-snapshot-compare"), params)
        self.assertContains(response, "Compare decision-rule snapshots")
        self.assertContains(response, "Aggressive rules test")
        self.assertContains(response, "Balanced rules test")
        self.assertContains(response, "Lead Magnet Focus")
        self.assertContains(response, "Visual comparison charts")
        self.assertContains(response, "Largest metric movements")

        export = self.client.get(reverse("studio:experiment-decision-tuning-experiment-snapshot-compare-export"), params)
        self.assertContains(export, "Summary comparison")
        self.assertContains(export, "Aggressive rules test")
        self.assertContains(export, "Decision recommendations")
        self.assertContains(export, "Chart data - top metric deltas")
        self.assertContains(export, "Chart data - decision counts")

    def test_saved_decision_rule_snapshot_comparison_report_create_detail_and_export(self):
        tuning = ExperimentDecisionTuning.get_active()
        log = ExperimentDecisionTuningChangeLog.objects.create(
            tuning=tuning,
            action=ExperimentDecisionTuningChangeLog.Action.PRESET_APPLIED,
            changed_by=self.staff,
            preset_key="lead_magnet_focus",
            preset_name="Lead Magnet Focus",
            experiment_label="Lead magnet decision test",
        )
        now = timezone.now()
        snapshot = ExperimentDecisionTuningExperimentSnapshot.objects.create(
            change_log=log,
            window_days=14,
            before_start=now - timedelta(days=28),
            before_end=now - timedelta(days=14),
            after_start=now - timedelta(days=14),
            after_end=now,
            deltas={"resources": {"pdf_downloads": {"before": 1, "after": 5, "change": 4, "pct": 400}}},
            summary={"primary_resource_delta": {"change": 4}},
            generated_by=self.staff,
        )
        response = self.client.post(
            reverse("studio:experiment-decision-tuning-snapshot-comparison-report-create"),
            {
                "title": "Lead magnet snapshot review",
                "description": "Compare resource-focused rule changes.",
                "snapshots": [snapshot.pk],
                "preset_keys": ["lead_magnet_focus"],
                "notes": "Keep an eye on downloads and learner conversions.",
            },
        )
        report = ExperimentDecisionTuningSnapshotComparisonReport.objects.get(title="Lead magnet snapshot review")
        self.assertRedirects(response, reverse("studio:experiment-decision-tuning-snapshot-comparison-report-detail", args=[report.pk]))
        self.assertEqual(report.snapshots.count(), 1)
        self.assertEqual(report.preset_keys, ["lead_magnet_focus"])
        self.assertEqual(report.decision_status, ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.UNDECIDED)

        update = self.client.post(
            reverse("studio:experiment-decision-tuning-snapshot-comparison-report-update", args=[report.pk]),
            {
                "title": "Lead magnet snapshot review",
                "description": "Compare resource-focused rule changes.",
                "snapshots": [snapshot.pk],
                "preset_keys": ["lead_magnet_focus"],
                "notes": "Keep an eye on downloads and learner conversions.",
                "decision_status": ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.WATCH,
                "decision_summary": "Watch this rule set for another content cycle.",
                "decision_notes": "Downloads improved, but learner conversions need more time.",
                "decision_owner": self.staff.pk,
            },
        )
        self.assertRedirects(update, reverse("studio:experiment-decision-tuning-snapshot-comparison-report-detail", args=[report.pk]))
        report.refresh_from_db()
        self.assertEqual(report.decision_status, ExperimentDecisionTuningSnapshotComparisonReport.DecisionStatus.WATCH)
        self.assertEqual(report.decision_owner, self.staff)
        self.assertEqual(report.decision_recorded_by, self.staff)
        self.assertIsNotNone(report.decision_recorded_at)

        detail = self.client.get(reverse("studio:experiment-decision-tuning-snapshot-comparison-report-detail", args=[report.pk]))
        self.assertContains(detail, "Lead magnet snapshot review")
        self.assertContains(detail, "Lead Magnet Focus")
        self.assertContains(detail, "Resource downloads")
        self.assertContains(detail, "Visual comparison charts")
        self.assertContains(detail, "Decision score chart")
        self.assertContains(detail, "Printable report")
        self.assertContains(detail, "Report decision")
        self.assertContains(detail, "Watch this rule set")

        printable = self.client.get(reverse("studio:experiment-decision-tuning-snapshot-comparison-report-print", args=[report.pk]))
        self.assertContains(printable, "Code with Michael · Decision-Rule Comparison Report")
        self.assertContains(printable, "Print / Save as PDF")
        self.assertContains(printable, "Executive summary")
        self.assertContains(printable, "Largest metric movements")
        self.assertContains(printable, "Prepared in Code with Michael Content Studio")

        export = self.client.get(reverse("studio:experiment-decision-tuning-snapshot-comparison-report-export", args=[report.pk]))
        self.assertContains(export, "Saved comparison report")
        self.assertContains(export, "Lead magnet snapshot review")
        self.assertContains(export, "decision_status")
        self.assertContains(export, "Watch this rule set")
        self.assertContains(export, "Decision recommendations")
        self.assertContains(export, "Chart data - decision counts")
        self.assertContains(export, "Chart data - top metric deltas")

