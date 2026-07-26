import os
import ssl
import time
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from studio.models import AIGeneration, AIModelPricing, CaptionDraft, Lesson


class OpenAIServiceError(RuntimeError):
    pass


def _client(OpenAI):
    options = {"timeout": settings.OPENAI_REQUEST_TIMEOUT}
    if os.name == "nt":
        import httpx
        import truststore

        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        options["http_client"] = httpx.Client(
            verify=ssl_context,
            timeout=settings.OPENAI_REQUEST_TIMEOUT,
        )
    return OpenAI(**options)


def _lesson_context(lesson: Lesson) -> str:
    sections = [
        f"Title: {lesson.title}",
        f"Difficulty: {lesson.get_difficulty_display()}",
    ]
    if lesson.summary:
        sections.append(f"Summary: {lesson.summary}")
    if lesson.series_id:
        series_label = lesson.series.title
        if lesson.series_position:
            series_label += f" (lesson {lesson.series_position})"
        sections.append(f"Series: {series_label}")
    for block in lesson.blocks.all():
        label = block.title or block.get_block_type_display()
        sections.append(f"\n[{label}]\n{block.content}")
        if block.data:
            sections.append(f"Structured details: {block.data}")
    return "\n".join(sections)


def _pricing_snapshot(model: str) -> dict:
    price = (
        AIModelPricing.objects.filter(model=model, is_active=True)
        .order_by("-effective_from")
        .first()
    )
    if not price:
        return {
            "input_price_per_million": Decimal("0"),
            "cached_input_price_per_million": Decimal("0"),
            "output_price_per_million": Decimal("0"),
            "cache_write_multiplier": Decimal("1.250"),
        }
    return {
        "input_price_per_million": price.input_per_million,
        "cached_input_price_per_million": price.cached_input_per_million,
        "output_price_per_million": price.output_per_million,
        "cache_write_multiplier": price.cache_write_multiplier,
    }


def _nested_value(obj, *path, default=0):
    current = obj
    for part in path:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return default if current is None else current


def _platform_instructions(platform: str) -> str:
    specifics = {
        CaptionDraft.Platform.FACEBOOK: (
            "Write a helpful Facebook caption with a clear opening, a short explanation, "
            "one engagement question, and a restrained set of relevant hashtags."
        ),
        CaptionDraft.Platform.INSTAGRAM: (
            "Write an Instagram caption with a strong first line, scannable short paragraphs, "
            "a save/comment call to action, and 5-10 relevant hashtags."
        ),
        CaptionDraft.Platform.THREADS: (
            "Write a concise conversational Threads post. Avoid hashtag stuffing and invite "
            "a useful reply."
        ),
    }
    return (
        "You are the instructional content editor for Code with Michael. Preserve technical "
        "accuracy. Use plain language for beginner programmers, never invent code behavior, "
        "and do not claim the content has been published. Return only the finished caption. "
        + specifics[platform]
    )


def generate_caption(lesson: Lesson, platform: str) -> CaptionDraft:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAIServiceError(
            "The OpenAI SDK is not installed. Install project requirements first."
        ) from exc

    model = settings.OPENAI_MODEL
    reasoning_effort = settings.OPENAI_REASONING_EFFORT
    prompt = (
        f"Create a {CaptionDraft.Platform(platform).label} caption from this lesson.\n\n"
        f"{_lesson_context(lesson)}\n\n"
        f"Preferred call to action: {lesson.call_to_action or 'Use an appropriate soft call to action.'}"
    )
    generation = AIGeneration.objects.create(
        lesson=lesson,
        purpose=AIGeneration.Purpose.CAPTION,
        model=model,
        reasoning_effort=reasoning_effort,
        instructions=_platform_instructions(platform),
        prompt=prompt,
        **_pricing_snapshot(model),
    )
    started = time.monotonic()

    try:
        client = _client(OpenAI)
        response = client.responses.create(
            model=model,
            reasoning={"effort": reasoning_effort},
            instructions=generation.instructions,
            input=prompt,
        )
        usage = getattr(response, "usage", None)
        input_tokens = int(_nested_value(usage, "input_tokens"))
        cached_tokens = int(
            _nested_value(usage, "input_tokens_details", "cached_tokens")
        )
        cache_write_tokens = int(
            _nested_value(usage, "input_tokens_details", "cache_write_tokens")
        )
        output_tokens = int(_nested_value(usage, "output_tokens"))
        reasoning_tokens = int(
            _nested_value(usage, "output_tokens_details", "reasoning_tokens")
        )
        payload = response.model_dump(mode="json") if hasattr(response, "model_dump") else {}
        generation.status = AIGeneration.Status.SUCCEEDED
        generation.response_id = getattr(response, "id", "")
        generation.response_text = response.output_text.strip()
        generation.response_payload = payload
        generation.input_tokens = input_tokens
        generation.cached_input_tokens = cached_tokens
        generation.cache_write_tokens = cache_write_tokens
        generation.output_tokens = output_tokens
        generation.reasoning_tokens = reasoning_tokens
        generation.duration_ms = int((time.monotonic() - started) * 1000)
        generation.estimated_cost_usd = generation.calculate_estimated_cost()
        with transaction.atomic():
            generation.save()
            return CaptionDraft.objects.create(
                lesson=lesson,
                platform=platform,
                content=generation.response_text,
                generation=generation,
            )
    except Exception as exc:
        generation.status = AIGeneration.Status.FAILED
        generation.duration_ms = int((time.monotonic() - started) * 1000)
        generation.error_message = str(exc)
        generation.save(
            update_fields=("status", "duration_ms", "error_message", "updated_at")
        )
        raise OpenAIServiceError(str(exc)) from exc
