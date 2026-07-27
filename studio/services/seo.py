import json
from email.utils import format_datetime
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from studio.models import LearningResource, Lesson, Series

PUBLIC_STATUSES = [Lesson.Status.READY, Lesson.Status.PUBLISHED]
PUBLIC_RESOURCE_STATUSES = [LearningResource.Status.READY, LearningResource.Status.PUBLISHED]


def site_origin(request=None):
    configured = getattr(settings, "CONTENT_WEBSITE_BASE_URL", "").rstrip("/")
    if configured:
        return configured
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    return ""


def absolute_url(path, request=None):
    origin = site_origin(request)
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not origin:
        return path
    return urljoin(f"{origin}/", path.lstrip("/"))


def public_lessons():
    return (
        Lesson.objects.filter(website_status__in=PUBLIC_STATUSES)
        .exclude(status=Lesson.Status.ARCHIVED)
        .select_related("category", "series")
        .order_by("series__title", "series_position", "title")
    )


def public_series():
    return (
        Series.objects.filter(is_active=True, lessons__website_status__in=PUBLIC_STATUSES)
        .exclude(lessons__status=Lesson.Status.ARCHIVED)
        .distinct()
        .order_by("title")
    )


def public_resources():
    return (
        LearningResource.objects.filter(status__in=PUBLIC_RESOURCE_STATUSES)
        .select_related("category")
        .order_by("resource_type", "title")
    )


def resource_public_path(resource):
    return reverse("learn:resource-detail", kwargs={"slug": resource.slug})


def resource_canonical_url(resource, request=None):
    return absolute_url(resource_public_path(resource), request=request)


def lesson_public_path(lesson):
    return reverse("learn:lesson-detail", kwargs={"slug": lesson.slug})


def series_public_path(series):
    return reverse("learn:series-detail", kwargs={"slug": series.slug})


def lesson_canonical_url(lesson, request=None):
    return absolute_url(lesson_public_path(lesson), request=request)


def series_canonical_url(series, request=None):
    return absolute_url(series_public_path(series), request=request)


def json_ld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def organization_schema(request=None):
    return {
        "@type": "Organization",
        "name": "Code with Michael",
        "url": absolute_url(reverse("learn:home"), request=request),
    }


def website_schema(request=None):
    return json_ld(
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Code with Michael",
            "url": absolute_url(reverse("learn:home"), request=request),
            "description": "Beginner-friendly Python lessons, runnable examples, quizzes, and practice challenges.",
            "potentialAction": {
                "@type": "SearchAction",
                "target": absolute_url(reverse("learn:lesson-list"), request=request) + "?q={search_term_string}",
                "query-input": "required name=search_term_string",
            },
        }
    )


def lesson_schema(lesson, request=None):
    data = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": lesson.seo_title or lesson.title,
        "headline": lesson.title,
        "description": lesson.seo_description or lesson.summary,
        "url": lesson_canonical_url(lesson, request=request),
        "inLanguage": "en-US",
        "isAccessibleForFree": True,
        "learningResourceType": "Lesson",
        "educationalLevel": lesson.get_difficulty_display(),
        "teaches": lesson.learning_objective or lesson.beginner_takeaway or lesson.title,
        "dateCreated": lesson.created_at.date().isoformat() if lesson.created_at else None,
        "dateModified": lesson.updated_at.isoformat() if lesson.updated_at else None,
        "publisher": organization_schema(request=request),
        "author": organization_schema(request=request),
    }
    if lesson.series_id:
        data["isPartOf"] = {
            "@type": "Course",
            "name": lesson.series.title,
            "url": series_canonical_url(lesson.series, request=request),
        }
    if lesson.category_id:
        data["about"] = lesson.category.name
    return json_ld({key: value for key, value in data.items() if value not in (None, "")})


def resource_schema(resource, request=None):
    data = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": resource.seo_title or resource.title,
        "headline": resource.title,
        "description": resource.seo_description or resource.summary,
        "url": resource_canonical_url(resource, request=request),
        "inLanguage": "en-US",
        "isAccessibleForFree": True,
        "learningResourceType": resource.get_resource_type_display(),
        "educationalLevel": resource.get_difficulty_display(),
        "dateCreated": resource.created_at.date().isoformat() if resource.created_at else None,
        "dateModified": resource.updated_at.isoformat() if resource.updated_at else None,
        "publisher": organization_schema(request=request),
        "author": organization_schema(request=request),
    }
    if resource.category_id:
        data["about"] = resource.category.name
    return json_ld({key: value for key, value in data.items() if value not in (None, "")})


def series_schema(series, lessons, request=None):
    return json_ld(
        {
            "@context": "https://schema.org",
            "@type": "Course",
            "name": series.title,
            "description": series.description or "A beginner-friendly Python learning path from Code with Michael.",
            "url": series_canonical_url(series, request=request),
            "provider": organization_schema(request=request),
            "hasPart": [
                {
                    "@type": "LearningResource",
                    "name": lesson.title,
                    "url": lesson_canonical_url(lesson, request=request),
                    "position": lesson.series_position or index,
                }
                for index, lesson in enumerate(lessons, start=1)
            ],
        }
    )


def sitemap_xml(request=None):
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    def add(path, lastmod=None, changefreq="weekly", priority="0.7"):
        node = SubElement(urlset, "url")
        SubElement(node, "loc").text = absolute_url(path, request=request)
        if lastmod:
            SubElement(node, "lastmod").text = lastmod.date().isoformat() if hasattr(lastmod, "date") else str(lastmod)
        SubElement(node, "changefreq").text = changefreq
        SubElement(node, "priority").text = priority

    add(reverse("learn:home"), timezone.now(), "weekly", "1.0")
    add(reverse("learn:lesson-list"), timezone.now(), "weekly", "0.9")
    add(reverse("learn:playground"), timezone.now(), "monthly", "0.8")
    add(reverse("learn:resource-list"), timezone.now(), "weekly", "0.8")
    for series in public_series():
        add(series_public_path(series), series.updated_at, "weekly", "0.8")
    for lesson in public_lessons():
        add(lesson_public_path(lesson), lesson.updated_at, "weekly", "0.9")
    for resource in public_resources():
        add(resource_public_path(resource), resource.updated_at, "monthly", "0.7")

    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(urlset, encoding="utf-8")


def rss_xml(request=None, limit=20):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Code with Michael Python Lessons"
    SubElement(channel, "link").text = absolute_url(reverse("learn:home"), request=request)
    SubElement(channel, "description").text = "Beginner Python lessons, runnable code examples, quizzes, and practice challenges."
    SubElement(channel, "language").text = "en-us"
    SubElement(channel, "lastBuildDate").text = format_datetime(timezone.now())

    for lesson in public_lessons().order_by("-updated_at")[:limit]:
        item = SubElement(channel, "item")
        url = lesson_canonical_url(lesson, request=request)
        SubElement(item, "title").text = lesson.title
        SubElement(item, "link").text = url
        SubElement(item, "guid", isPermaLink="true").text = url
        SubElement(item, "description").text = lesson.seo_description or lesson.summary
        SubElement(item, "pubDate").text = format_datetime(lesson.updated_at or timezone.now())
        if lesson.category_id:
            SubElement(item, "category").text = lesson.category.name

    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(rss, encoding="utf-8")
