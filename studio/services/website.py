import hashlib
import json
import math
import re

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.template.loader import render_to_string
from django.utils import timezone

from studio.models import BrandProfile, Lesson, WebsiteExport

SCHEMA_VERSION = "1.0"


def _absolute_url(request, url):
    if not url:
        return ""
    return request.build_absolute_uri(url) if request else url


def _reading_minutes(lesson):
    words = len(re.findall(r"\b\w+\b", lesson.summary))
    words += sum(len(re.findall(r"\b\w+\b", block.content)) for block in lesson.blocks.all())
    return max(1, math.ceil(words / 200))


def serialize_lesson(lesson: Lesson, request=None) -> dict:
    brand = BrandProfile.get_default()
    blocks = [
        {
            "position": block.position,
            "type": block.block_type,
            "label": block.get_block_type_display(),
            "title": block.title,
            "content": block.content,
            "data": block.data,
        }
        for block in lesson.blocks.all()
    ]
    assets = [
        {
            "format": asset.output_format,
            "width": asset.width,
            "height": asset.height,
            "slide": asset.slide_number,
            "url": _absolute_url(request, asset.file.url if asset.file else ""),
            "alt_text": asset.alt_text,
        }
        for asset in lesson.assets.filter(status="ready")
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "content_type": "code_with_michael.lesson",
        "exported_at": timezone.now().isoformat(),
        "lesson": {
            "id": lesson.pk,
            "slug": lesson.slug,
            "title": lesson.title,
            "summary": lesson.summary,
            "difficulty": lesson.difficulty,
            "difficulty_label": lesson.get_difficulty_display(),
            "status": lesson.status,
            "category": (
                {"name": lesson.category.name, "slug": lesson.category.slug}
                if lesson.category
                else None
            ),
            "tags": [{"name": tag.name, "slug": tag.slug} for tag in lesson.tags.all()],
            "series": (
                {
                    "title": lesson.series.title,
                    "slug": lesson.series.slug,
                    "position": lesson.series_position,
                }
                if lesson.series
                else None
            ),
            "seo": {
                "title": lesson.seo_title or lesson.title,
                "description": lesson.seo_description or lesson.summary,
                "canonical_url": "",
            },
            "reading_minutes": _reading_minutes(lesson),
            "playground_enabled": lesson.enable_playground,
            "call_to_action": lesson.call_to_action or brand.default_call_to_action,
            "accent_color": lesson.resolved_accent_color,
            "blocks": blocks,
            "assets": assets,
            "updated_at": lesson.updated_at.isoformat(),
        },
        "brand": {"name": brand.name, "social_handle": brand.social_handle},
    }


def seo_diagnostics(lesson: Lesson) -> dict:
    title = lesson.seo_title or lesson.title
    description = lesson.seo_description or lesson.summary
    issues = []
    if not lesson.summary:
        issues.append({"level": "error", "message": "Add a lesson summary."})
    if not lesson.blocks.exists():
        issues.append({"level": "error", "message": "Add at least one content block."})
    if not lesson.seo_title:
        issues.append({"level": "warning", "message": "Add a dedicated SEO title."})
    elif not 30 <= len(title) <= 60:
        issues.append(
            {"level": "warning", "message": "Keep the SEO title between 30 and 60 characters."}
        )
    if not lesson.seo_description:
        issues.append({"level": "warning", "message": "Add a dedicated SEO description."})
    elif not 120 <= len(description) <= 160:
        issues.append(
            {
                "level": "warning",
                "message": "Keep the SEO description between 120 and 160 characters.",
            }
        )
    if not lesson.category_id:
        issues.append({"level": "warning", "message": "Choose a category."})
    if not lesson.tags.exists():
        issues.append({"level": "warning", "message": "Add at least one search tag."})
    penalty = sum(25 if issue["level"] == "error" else 10 for issue in issues)
    return {
        "title": title,
        "title_length": len(title),
        "description": description,
        "description_length": len(description),
        "score": max(0, 100 - penalty),
        "issues": issues,
        "is_ready": not any(issue["level"] == "error" for issue in issues),
    }


def render_website_page(lesson: Lesson, request=None, is_preview=False) -> tuple[str, dict]:
    payload = serialize_lesson(lesson, request=request)
    lesson_data = payload["lesson"]
    canonical_url = (
        f"{settings.CONTENT_WEBSITE_BASE_URL}/lessons/{lesson.slug}/"
        if settings.CONTENT_WEBSITE_BASE_URL
        else ""
    )
    lesson_data["seo"]["canonical_url"] = canonical_url
    structured_data = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": lesson_data["seo"]["title"],
        "description": lesson_data["seo"]["description"],
        "dateModified": lesson.updated_at.isoformat(),
        "author": {"@type": "Person", "name": "Michael"},
        "publisher": {"@type": "Organization", "name": payload["brand"]["name"]},
        "proficiencyLevel": lesson_data["difficulty_label"],
        "mainEntityOfPage": canonical_url,
    }
    structured_json = json.dumps(structured_data, ensure_ascii=False).replace("<", "\\u003c")
    html = render_to_string(
        "studio/website_page.html",
        {
            "lesson": lesson,
            "page": lesson_data,
            "brand": payload["brand"],
            "structured_json": structured_json,
            "is_preview": is_preview,
        },
    )
    return html, payload


def create_website_export(lesson: Lesson, user, request=None) -> WebsiteExport:
    html, payload = render_website_page(lesson, request=request)
    stable_payload = serialize_lesson(lesson)
    hash_payload = {
        "lesson": stable_payload["lesson"],
        "brand": stable_payload["brand"],
    }
    canonical_payload = json.dumps(hash_payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    with transaction.atomic():
        revision = (
            WebsiteExport.objects.select_for_update()
            .filter(lesson=lesson)
            .aggregate(maximum=Max("revision"))["maximum"]
            or 0
        ) + 1
        return WebsiteExport.objects.create(
            lesson=lesson,
            revision=revision,
            schema_version=SCHEMA_VERSION,
            content_hash=content_hash,
            payload=payload,
            rendered_html=html,
            created_by=user,
        )
