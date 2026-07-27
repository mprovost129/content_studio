from __future__ import annotations

import re
from dataclasses import dataclass

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils.text import slugify

from studio.models import (
    Category,
    ChallengeTestCase,
    CodeChallenge,
    Lesson,
    LessonBlock,
    QuizChoice,
    QuizQuestion,
    Series,
)


@dataclass(frozen=True)
class LessonIdeaDraft:
    topic: str
    audience: str
    objective: str
    category: Category | None = None
    series: Series | None = None
    include_quiz: bool = True
    include_challenge: bool = True
    created_by: AbstractBaseUser | None = None


def _sentence_case(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    if not value:
        return "Python Basics"
    return value[:1].upper() + value[1:]


def _safe_function_name(topic: str) -> str:
    base = slugify(topic).replace("-", "_") or "practice_python"
    base = re.sub(r"[^a-zA-Z0-9_]", "", base)
    if not base or base[0].isdigit():
        base = f"practice_{base}"
    return base[:40]


def _is_money_topic(topic: str) -> bool:
    keywords = ("money", "price", "cost", "budget", "sale", "sales", "tax", "tip", "discount", "dollar")
    lowered = topic.lower()
    return any(word in lowered for word in keywords)


def _example_code(topic: str) -> tuple[str, str]:
    lowered = topic.lower()
    if _is_money_topic(topic):
        code = (
            "item_price = 25\n"
            "quantity = 3\n"
            "total = item_price * quantity\n"
            "print(f\"Total: ${total}\")"
        )
        return code, "Total: $75"
    if "list" in lowered:
        code = (
            "favorite_languages = [\"Python\", \"JavaScript\", \"HTML\"]\n"
            "for language in favorite_languages:\n"
            "    print(language)"
        )
        return code, "Python\nJavaScript\nHTML"
    if "loop" in lowered:
        code = "for number in range(1, 4):\n    print(number)"
        return code, "1\n2\n3"
    if "function" in lowered:
        code = (
            "def greet(name):\n"
            "    return f\"Hello, {name}!\"\n\n"
            "print(greet(\"Michael\"))"
        )
        return code, "Hello, Michael!"
    if "condition" in lowered or "if" in lowered:
        code = "score = 85\nif score >= 70:\n    print(\"Passed\")\nelse:\n    print(\"Try again\")"
        return code, "Passed"
    code = "message = \"I am learning Python\"\nprint(message)"
    return code, "I am learning Python"


def _starter_solution(topic: str) -> tuple[str, str, str, str]:
    function_name = _safe_function_name(topic)
    if _is_money_topic(topic):
        starter = (
            "def calculate_total(price, quantity):\n"
            "    # TODO: return the total cost\n"
            "    pass\n"
        )
        solution = "def calculate_total(price, quantity):\n    return price * quantity\n"
        tests = "assert calculate_total(5, 3) == 15\nassert calculate_total(12, 2) == 24\nprint(\"passed\")"
        return starter, solution, tests, "passed"
    if "function" in topic.lower():
        starter = (
            "def greet(name):\n"
            "    # TODO: return a greeting using the name\n"
            "    pass\n"
        )
        solution = "def greet(name):\n    return f\"Hello, {name}!\"\n"
        tests = "assert greet(\"Michael\") == \"Hello, Michael!\"\nassert greet(\"Python\") == \"Hello, Python!\"\nprint(\"passed\")"
        return starter, solution, tests, "passed"
    starter = (
        f"def {function_name}():\n"
        "    # TODO: return a short message about what you learned\n"
        "    pass\n"
    )
    solution = f"def {function_name}():\n    return \"I can explain this Python idea.\"\n"
    tests = f"assert {function_name}() == \"I can explain this Python idea.\"\nprint(\"passed\")"
    return starter, solution, tests, "passed"


def build_lesson_outline(draft: LessonIdeaDraft) -> dict:
    topic = _sentence_case(draft.topic)
    audience = draft.audience or "absolute beginners"
    objective = draft.objective or f"Learner can explain and use {topic.lower()} in a small Python example."
    example_code, expected_output = _example_code(topic)
    starter_code, solution_code, test_code, test_expected_output = _starter_solution(topic)

    return {
        "title": topic,
        "summary": f"A beginner-friendly lesson for {audience} that explains {topic.lower()} with a small runnable Python example.",
        "learning_objective": objective,
        "beginner_takeaway": f"{topic} is easier when you focus on one small example, run it, and read the output line by line.",
        "common_mistake": "Beginners often copy the code without checking what each line changes. Encourage learners to predict the output before running it.",
        "practice_prompt": "Change the example so it uses your own values, then run it again and explain what changed in the output.",
        "starter_code": starter_code,
        "solution_code": solution_code,
        "expected_output": test_expected_output,
        "hint_1": "Start by reading the function name, parameters, and expected output.",
        "hint_2": "Return the final value from the function instead of only printing it.",
        "seo_title": f"{topic} in Python for Beginners"[:70],
        "seo_description": f"Learn {topic.lower()} in Python with a simple explanation, runnable example, beginner mistake, quiz, and practice challenge."[:170],
        "blocks": [
            {
                "position": 1,
                "block_type": LessonBlock.BlockType.TEXT,
                "title": "What this means",
                "content": (
                    f"In this lesson, learners practice {topic.lower()} without jumping too far ahead. "
                    "The goal is to understand the idea, run a small example, and connect the code to the output."
                ),
            },
            {
                "position": 2,
                "block_type": LessonBlock.BlockType.CODE,
                "title": "Try this code",
                "content": example_code,
            },
            {
                "position": 3,
                "block_type": LessonBlock.BlockType.OUTPUT,
                "title": "Expected output",
                "content": expected_output,
            },
            {
                "position": 4,
                "block_type": LessonBlock.BlockType.CALLOUT,
                "title": "Beginner tip",
                "content": "Before pressing Run, ask yourself: what do I think Python will print? That habit builds real understanding.",
            },
        ],
        "quiz": {
            "prompt": f"What is the best first step when learning {topic.lower()}?",
            "choices": [
                ("Run a small example and compare the output to what you expected.", True),
                ("Memorize every Python rule before writing any code.", False),
                ("Skip the output because only the code matters.", False),
            ],
            "explanation": "Small examples help beginners connect code, output, and meaning without overload.",
        },
        "challenge": {
            "title": f"Practice {topic}",
            "prompt": f"Complete the starter code so the function passes the tests for this {topic.lower()} lesson.",
            "starter_code": starter_code,
            "solution_code": solution_code,
            "expected_output": test_expected_output,
            "test_code": test_code,
            "test_expected_output": test_expected_output,
        },
    }


@transaction.atomic
def create_lesson_from_idea(draft: LessonIdeaDraft) -> Lesson:
    outline = build_lesson_outline(draft)
    lesson = Lesson.objects.create(
        title=outline["title"],
        summary=outline["summary"],
        status=Lesson.Status.DRAFT,
        difficulty=Lesson.Difficulty.BEGINNER,
        category=draft.category,
        series=draft.series,
        learning_objective=outline["learning_objective"],
        beginner_takeaway=outline["beginner_takeaway"],
        common_mistake=outline["common_mistake"],
        practice_prompt=outline["practice_prompt"],
        starter_code=outline["starter_code"],
        solution_code=outline["solution_code"],
        expected_output=outline["expected_output"],
        hint_1=outline["hint_1"],
        hint_2=outline["hint_2"],
        seo_title=outline["seo_title"],
        seo_description=outline["seo_description"],
        enable_playground=True,
        internal_notes=(
            "Generated from idea workflow. Review all code, output, quiz answers, "
            "challenge tests, captions, and SEO metadata before publishing."
        ),
        created_by=draft.created_by,
        updated_by=draft.created_by,
    )

    for block in outline["blocks"]:
        LessonBlock.objects.create(lesson=lesson, **block)

    if draft.include_quiz:
        quiz = outline["quiz"]
        question = QuizQuestion.objects.create(
            lesson=lesson,
            position=1,
            question_type=QuizQuestion.QuestionType.MULTIPLE_CHOICE,
            prompt=quiz["prompt"],
            explanation=quiz["explanation"],
            is_active=True,
        )
        for index, (choice_text, is_correct) in enumerate(quiz["choices"], start=1):
            QuizChoice.objects.create(
                question=question,
                position=index,
                text=choice_text,
                is_correct=is_correct,
            )

    if draft.include_challenge:
        challenge_outline = outline["challenge"]
        challenge = CodeChallenge.objects.create(
            lesson=lesson,
            position=1,
            title=challenge_outline["title"],
            prompt=challenge_outline["prompt"],
            starter_code=challenge_outline["starter_code"],
            solution_code=challenge_outline["solution_code"],
            expected_output=challenge_outline["expected_output"],
            hint_1=outline["hint_1"],
            hint_2=outline["hint_2"],
            validation_mode=CodeChallenge.ValidationMode.EXACT_OUTPUT,
            is_active=True,
        )
        ChallengeTestCase.objects.create(
            challenge=challenge,
            position=1,
            name="Core behavior",
            description="Checks the learner's function return values and prints passed when complete.",
            test_code=challenge_outline["test_code"],
            expected_output=challenge_outline["test_expected_output"],
            is_active=True,
        )

    return lesson
