from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.models import Max

from studio.models import GraphicTemplate, Lesson, LessonBlock
from studio.services.graphics import generate_graphics


@dataclass(frozen=True)
class CarouselBlock:
    block_type: str
    title: str
    content: str
    data: dict[str, Any] | None = None


@dataclass(frozen=True)
class SocialCarouselTemplate:
    key: str
    name: str
    purpose: str
    description: str
    graphic_slug: str
    graphic_type: str
    graphic_name: str
    blocks: tuple[CarouselBlock, ...]


def _first_block(lesson: Lesson, *block_types: str) -> LessonBlock | None:
    return (
        lesson.blocks.filter(block_type__in=block_types)
        .order_by("position", "pk")
        .first()
    )


def _lesson_code(lesson: Lesson) -> str:
    if lesson.starter_code:
        return lesson.starter_code
    block = _first_block(lesson, LessonBlock.BlockType.CODE)
    if block and block.content:
        return block.content
    return '# Add the smallest example for this topic\nmessage = "I am learning Python"\nprint(message)'


def _lesson_output(lesson: Lesson) -> str:
    if lesson.expected_output:
        return lesson.expected_output
    block = _first_block(lesson, LessonBlock.BlockType.OUTPUT)
    if block and block.content:
        return block.content
    return "I am learning Python"


def _short_summary(lesson: Lesson) -> str:
    return (
        lesson.summary
        or lesson.learning_objective
        or f"Learn one beginner-friendly Python idea: {lesson.title}."
    )


def _takeaway(lesson: Lesson) -> str:
    return (
        lesson.beginner_takeaway
        or "Focus on one small idea, run the code, and read the output before moving on."
    )


def _mistake(lesson: Lesson) -> str:
    return (
        lesson.common_mistake
        or "A common beginner mistake is changing several things at once. Change one line, run the code, and check what changed."
    )


SOCIAL_CAROUSEL_TEMPLATES: tuple[SocialCarouselTemplate, ...] = (
    SocialCarouselTemplate(
        key="concept_explanation",
        name="Concept Explanation",
        purpose="Turn one beginner concept into a saveable carousel.",
        description="Adds a hook, plain-English explanation, code example, output reveal, and final takeaway.",
        graphic_slug="concept-explanation-carousel",
        graphic_type=GraphicTemplate.TemplateType.LESSON,
        graphic_name="Concept Explanation Carousel",
        blocks=(
            CarouselBlock(
                LessonBlock.BlockType.HEADING,
                "Slide 1 hook",
                "What does this Python concept actually mean?",
            ),
            CarouselBlock(
                LessonBlock.BlockType.TEXT,
                "Plain-English idea",
                "Use this slide to explain the concept without jargon. Make it feel approachable for someone brand new.",
            ),
            CarouselBlock(LessonBlock.BlockType.CODE, "Tiny example", "{code}"),
            CarouselBlock(LessonBlock.BlockType.OUTPUT, "What it prints", "{output}"),
            CarouselBlock(LessonBlock.BlockType.CALLOUT, "Remember", "{takeaway}"),
        ),
    ),
    SocialCarouselTemplate(
        key="beginner_mistake",
        name="Beginner Mistake",
        purpose="Teach through one error beginners are likely to make.",
        description="Adds the mistake, why it happens, wrong version, fixed version, and a memory hook.",
        graphic_slug="beginner-mistake-carousel",
        graphic_type=GraphicTemplate.TemplateType.ERROR,
        graphic_name="Beginner Mistake Carousel",
        blocks=(
            CarouselBlock(
                LessonBlock.BlockType.HEADING,
                "Beginner mistake",
                "A mistake new Python learners make with this topic",
            ),
            CarouselBlock(LessonBlock.BlockType.TEXT, "Why it happens", "{mistake}"),
            CarouselBlock(LessonBlock.BlockType.CODE, "Check this code", "{code}"),
            CarouselBlock(
                LessonBlock.BlockType.TEXT,
                "Slow down and inspect",
                "Read the variable names, data types, punctuation, and indentation before changing the code.",
            ),
            CarouselBlock(
                LessonBlock.BlockType.CALLOUT,
                "Fixing habit",
                "Change one thing at a time, run the code, and compare the output.",
            ),
        ),
    ),
    SocialCarouselTemplate(
        key="spot_the_bug",
        name="Spot the Bug",
        purpose="Create an interactive debugging post.",
        description="Adds a prediction prompt, buggy-code frame, clue, reveal, and engagement question.",
        graphic_slug="spot-the-bug-carousel",
        graphic_type=GraphicTemplate.TemplateType.SPOT_BUG,
        graphic_name="Spot the Bug Carousel",
        blocks=(
            CarouselBlock(
                LessonBlock.BlockType.HEADING,
                "Spot the bug",
                "Can you find the issue before running it?",
            ),
            CarouselBlock(
                LessonBlock.BlockType.CODE, "Buggy or suspicious code", "{code}"
            ),
            CarouselBlock(
                LessonBlock.BlockType.CALLOUT,
                "Clue",
                "Look closely at names, quotes, parentheses, data types, and indentation.",
            ),
            CarouselBlock(
                LessonBlock.BlockType.OUTPUT, "Expected direction", "{output}"
            ),
            CarouselBlock(
                LessonBlock.BlockType.CHALLENGE,
                "Comment your answer",
                "What would you change first? Explain it in one sentence.",
            ),
        ),
    ),
    SocialCarouselTemplate(
        key="code_output_quiz",
        name="Code Output Quiz",
        purpose="Make a quick engagement post where followers predict the output.",
        description="Adds code-first quiz slides, a pause prompt, output reveal, and takeaway.",
        graphic_slug="code-output-quiz-carousel",
        graphic_type=GraphicTemplate.TemplateType.CHALLENGE,
        graphic_name="Code Output Quiz Carousel",
        blocks=(
            CarouselBlock(
                LessonBlock.BlockType.HEADING,
                "Python output quiz",
                "What will this code print?",
            ),
            CarouselBlock(LessonBlock.BlockType.CODE, "Read the code first", "{code}"),
            CarouselBlock(
                LessonBlock.BlockType.QUIZ,
                "Make your prediction",
                "Do not run it yet. Say the output out loud, then check the reveal.",
            ),
            CarouselBlock(LessonBlock.BlockType.OUTPUT, "Answer", "{output}"),
            CarouselBlock(
                LessonBlock.BlockType.CALLOUT, "Why this matters", "{takeaway}"
            ),
        ),
    ),
    SocialCarouselTemplate(
        key="three_things",
        name="Three Things to Remember",
        purpose="Create a saveable reference post.",
        description="Adds a three-point reminder, example, output, and call-to-action slide.",
        graphic_slug="three-things-carousel",
        graphic_type=GraphicTemplate.TemplateType.COMPARISON,
        graphic_name="Three Things Carousel",
        blocks=(
            CarouselBlock(
                LessonBlock.BlockType.HEADING,
                "3 things to remember",
                "Save these beginner Python reminders",
            ),
            CarouselBlock(
                LessonBlock.BlockType.LIST,
                "The reminders",
                "- Start with one small example.\n- Run the code before changing more.\n- Read the output and error messages carefully.",
            ),
            CarouselBlock(LessonBlock.BlockType.CODE, "Example", "{code}"),
            CarouselBlock(LessonBlock.BlockType.OUTPUT, "Output", "{output}"),
            CarouselBlock(
                LessonBlock.BlockType.CALLOUT,
                "Next step",
                "Try changing one value in the code and run it again.",
            ),
        ),
    ),
)


def get_social_carousel_template_choices() -> list[tuple[str, str]]:
    return [
        (template.key, f"{template.name} — {template.purpose}")
        for template in SOCIAL_CAROUSEL_TEMPLATES
    ]


def get_social_carousel_template(key: str) -> SocialCarouselTemplate | None:
    return next(
        (template for template in SOCIAL_CAROUSEL_TEMPLATES if template.key == key),
        None,
    )


def _render_placeholder(content: str, lesson: Lesson) -> str:
    values = {
        "title": lesson.title,
        "summary": _short_summary(lesson),
        "objective": lesson.learning_objective
        or f"Understand {lesson.title} well enough to explain it and run a small example.",
        "takeaway": _takeaway(lesson),
        "mistake": _mistake(lesson),
        "code": _lesson_code(lesson),
        "output": _lesson_output(lesson),
    }
    return content.format(**values)


def ensure_graphic_template(template: SocialCarouselTemplate) -> GraphicTemplate:
    graphic_template, _ = GraphicTemplate.objects.get_or_create(
        slug=template.graphic_slug,
        defaults={
            "name": template.graphic_name,
            "template_type": template.graphic_type,
            "description": template.description,
            "configuration": {
                "source": "social_carousel_template",
                "template_key": template.key,
            },
            "is_active": True,
        },
    )
    changed = False
    if not graphic_template.description:
        graphic_template.description = template.description
        changed = True
    if not graphic_template.configuration:
        graphic_template.configuration = {
            "source": "social_carousel_template",
            "template_key": template.key,
        }
        changed = True
    if changed:
        graphic_template.save(
            update_fields=("description", "configuration", "updated_at")
        )
    return graphic_template


def apply_social_carousel_template_to_lesson(
    lesson: Lesson,
    template: SocialCarouselTemplate,
    *,
    output_formats: list[str] | tuple[str, ...] = (),
    generate_now: bool = False,
) -> dict[str, int | str]:
    with transaction.atomic():
        next_position = (
            lesson.blocks.aggregate(maximum=Max("position"))["maximum"] or 0
        ) + 1
        blocks_created = 0
        for block in template.blocks:
            LessonBlock.objects.create(
                lesson=lesson,
                position=next_position,
                block_type=block.block_type,
                title=block.title,
                content=_render_placeholder(block.content, lesson),
                data=block.data or {},
            )
            next_position += 1
            blocks_created += 1

        graphic_template = ensure_graphic_template(template)

        updates = []
        for field in ("facebook_status", "instagram_status", "threads_status"):
            if getattr(lesson, field) == Lesson.Status.IDEA:
                setattr(lesson, field, Lesson.Status.DRAFT)
                updates.append(field)
        if updates:
            updates.append("updated_at")
            lesson.save(update_fields=updates)

    assets_created = 0
    if generate_now and output_formats:
        assets_created = len(
            generate_graphics(lesson, graphic_template, output_formats)
        )

    return {
        "blocks": blocks_created,
        "assets": assets_created,
        "graphic_template": graphic_template.slug,
    }
