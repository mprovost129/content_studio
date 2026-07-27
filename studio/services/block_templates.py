from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.db.models import Max

from studio.models import CodeChallenge, ChallengeTestCase, Lesson, LessonBlock, QuizChoice, QuizQuestion


@dataclass(frozen=True)
class BlockTemplateBlock:
    block_type: str
    title: str
    content: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BlockTemplateQuizChoice:
    text: str
    is_correct: bool = False


@dataclass(frozen=True)
class BlockTemplateQuiz:
    prompt: str
    explanation: str
    choices: tuple[BlockTemplateQuizChoice, ...]
    question_type: str = QuizQuestion.QuestionType.MULTIPLE_CHOICE


@dataclass(frozen=True)
class BlockTemplateChallengeTest:
    name: str
    description: str
    test_code: str
    expected_output: str = ""


@dataclass(frozen=True)
class BlockTemplateChallenge:
    title: str
    prompt: str
    starter_code: str
    solution_code: str
    expected_output: str
    hint_1: str
    hint_2: str
    validation_mode: str = CodeChallenge.ValidationMode.EXACT_OUTPUT
    tests: tuple[BlockTemplateChallengeTest, ...] = ()


@dataclass(frozen=True)
class BlockTemplate:
    key: str
    name: str
    purpose: str
    description: str
    blocks: tuple[BlockTemplateBlock, ...] = ()
    quizzes: tuple[BlockTemplateQuiz, ...] = ()
    challenges: tuple[BlockTemplateChallenge, ...] = ()


BLOCK_TEMPLATES: tuple[BlockTemplate, ...] = (
    BlockTemplate(
        key="beginner_concept",
        name="Beginner Concept",
        purpose="Teach one small idea in plain English.",
        description="Adds an explanation, simple code example, output, beginner mistake, and practice prompt.",
        blocks=(
            BlockTemplateBlock(
                LessonBlock.BlockType.TEXT,
                "What this means",
                "Explain the concept like the learner has never coded before. Keep it concrete and connect it to something familiar.",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CODE,
                "Small example",
                '# Replace this with the smallest useful example\nmessage = "Hello, Python!"\nprint(message)',
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.OUTPUT,
                "Output",
                "Hello, Python!",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CALLOUT,
                "Common beginner mistake",
                "Do not skip this part. Call out one specific mistake beginners make and show how to avoid it.",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CHALLENGE,
                "Try it yourself",
                "Change one value in the example and run the code again. What changed in the output?",
            ),
        ),
    ),
    BlockTemplate(
        key="code_example",
        name="Code Example",
        purpose="Walk through finished code line by line.",
        description="Adds a setup explanation, code block, output block, and line-by-line breakdown.",
        blocks=(
            BlockTemplateBlock(
                LessonBlock.BlockType.TEXT,
                "Setup",
                "Introduce the problem this code solves before showing the code. Keep the problem small and beginner-friendly.",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CODE,
                "Example code",
                'price = 25\ntax = 2\ntotal = price + tax\nprint(total)',
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.OUTPUT,
                "Output",
                "27",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.LIST,
                "Line-by-line breakdown",
                "- Line 1 stores the price.\n- Line 2 stores the tax.\n- Line 3 adds them together.\n- Line 4 prints the result.",
            ),
        ),
    ),
    BlockTemplate(
        key="try_it_yourself",
        name="Try It Yourself",
        purpose="Turn a lesson into active practice.",
        description="Adds a structured challenge with starter code, hints, expected output, and a simple test case.",
        challenges=(
            BlockTemplateChallenge(
                title="Practice the skill",
                prompt="Complete the starter code so it produces the expected output.",
                starter_code='# TODO: update the value and print the result\nname = "Michael"\nprint(name)',
                solution_code='name = "Michael"\nprint(name)',
                expected_output="Michael",
                hint_1="Start by checking the variable name and the value stored inside it.",
                hint_2="Use print(...) to show the final value in the output area.",
                tests=(
                    BlockTemplateChallengeTest(
                        name="Expected output",
                        description="Checks that the submitted code prints the expected result.",
                        test_code='',
                        expected_output="Michael",
                    ),
                ),
            ),
        ),
    ),
    BlockTemplate(
        key="common_mistake",
        name="Common Mistake",
        purpose="Teach through a beginner error and correction.",
        description="Adds wrong code, error/output context, corrected code, and a takeaway.",
        blocks=(
            BlockTemplateBlock(
                LessonBlock.BlockType.TEXT,
                "The mistake",
                "Describe the mistake in plain English. Explain why it is easy to make when someone is new to Python.",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CODE,
                "Wrong version",
                'print("Hello, Python!"',
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.OUTPUT,
                "What Python is telling you",
                "SyntaxError: '(' was never closed",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CODE,
                "Fixed version",
                'print("Hello, Python!")',
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CALLOUT,
                "Remember",
                "When Python shows an error, read the message slowly. It often tells you exactly where to look first.",
            ),
        ),
    ),
    BlockTemplate(
        key="spot_the_bug",
        name="Spot the Bug",
        purpose="Create an interactive debugging lesson.",
        description="Adds a bug prompt, broken code, revealable fix, quiz question, and optional challenge.",
        blocks=(
            BlockTemplateBlock(
                LessonBlock.BlockType.TEXT,
                "Can you spot the bug?",
                "Ask the learner to read the code before running it. Tell them to predict what will happen.",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CODE,
                "Buggy code",
                'age = "12"\nnext_year = age + 1\nprint(next_year)',
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.OUTPUT,
                "Error",
                'TypeError: can only concatenate str (not "int") to str',
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.CODE,
                "Fixed code",
                'age = 12\nnext_year = age + 1\nprint(next_year)',
            ),
        ),
        quizzes=(
            BlockTemplateQuiz(
                prompt="Why did the buggy code fail?",
                explanation="The value was stored as text, but the code tried to add a number to it.",
                choices=(
                    BlockTemplateQuizChoice("The variable name was too short."),
                    BlockTemplateQuizChoice("Python cannot print numbers."),
                    BlockTemplateQuizChoice("The code mixed a string and an integer.", True),
                    BlockTemplateQuizChoice("The print function was missing."),
                ),
            ),
        ),
    ),
    BlockTemplate(
        key="mini_project",
        name="Mini Project",
        purpose="Package a lesson into a small finished build.",
        description="Adds project goal, requirements, starter code, solution, output, and a code challenge.",
        blocks=(
            BlockTemplateBlock(
                LessonBlock.BlockType.TEXT,
                "Project goal",
                "Build a tiny Python program that solves one clear problem. Keep it small enough to finish in one sitting.",
            ),
            BlockTemplateBlock(
                LessonBlock.BlockType.LIST,
                "Requirements",
                "- Store at least two values in variables.\n- Combine those values.\n- Print a clear result.\n- Run the code and compare the output.",
            ),
        ),
        challenges=(
            BlockTemplateChallenge(
                title="Build a total calculator",
                prompt="Create a small total calculator. Store an item price and a shipping cost, add them together, and print the total.",
                starter_code="# Use U.S. dollars for this practice example.\nitem_price = 20\nshipping = 5\n\n# TODO: create total and print it\n",
                solution_code="item_price = 20\nshipping = 5\ntotal = item_price + shipping\nprint(total)",
                expected_output="25",
                hint_1="Create a variable named total.",
                hint_2="Set total equal to item_price + shipping, then print total.",
                tests=(
                    BlockTemplateChallengeTest(
                        name="Prints total",
                        description="Checks that the learner prints the expected total.",
                        test_code='',
                        expected_output="25",
                    ),
                ),
            ),
        ),
    ),
)


def get_block_template_choices() -> list[tuple[str, str]]:
    return [(template.key, f"{template.name} — {template.purpose}") for template in BLOCK_TEMPLATES]


def get_block_template(key: str) -> BlockTemplate | None:
    return next((template for template in BLOCK_TEMPLATES if template.key == key), None)


def apply_block_template_to_lesson(lesson: Lesson, template: BlockTemplate) -> dict[str, int]:
    """Append a reusable teaching template to a lesson."""
    next_block_position = (lesson.blocks.aggregate(maximum=Max("position"))["maximum"] or 0) + 1
    blocks_created = 0
    for block in template.blocks:
        LessonBlock.objects.create(
            lesson=lesson,
            position=next_block_position,
            block_type=block.block_type,
            title=block.title,
            content=block.content,
            data=block.data,
        )
        next_block_position += 1
        blocks_created += 1

    next_question_position = (lesson.quiz_questions.aggregate(maximum=Max("position"))["maximum"] or 0) + 1
    quizzes_created = 0
    choices_created = 0
    for quiz in template.quizzes:
        question = QuizQuestion.objects.create(
            lesson=lesson,
            position=next_question_position,
            question_type=quiz.question_type,
            prompt=quiz.prompt,
            explanation=quiz.explanation,
            is_active=True,
        )
        next_question_position += 1
        quizzes_created += 1
        for index, choice in enumerate(quiz.choices, start=1):
            QuizChoice.objects.create(
                question=question,
                position=index,
                text=choice.text,
                is_correct=choice.is_correct,
            )
            choices_created += 1

    next_challenge_position = (lesson.code_challenges.aggregate(maximum=Max("position"))["maximum"] or 0) + 1
    challenges_created = 0
    tests_created = 0
    for challenge_template in template.challenges:
        challenge = CodeChallenge.objects.create(
            lesson=lesson,
            position=next_challenge_position,
            title=challenge_template.title,
            prompt=challenge_template.prompt,
            starter_code=challenge_template.starter_code,
            solution_code=challenge_template.solution_code,
            expected_output=challenge_template.expected_output,
            hint_1=challenge_template.hint_1,
            hint_2=challenge_template.hint_2,
            validation_mode=challenge_template.validation_mode,
            is_active=True,
        )
        next_challenge_position += 1
        challenges_created += 1
        for index, test in enumerate(challenge_template.tests, start=1):
            ChallengeTestCase.objects.create(
                challenge=challenge,
                position=index,
                name=test.name,
                description=test.description,
                test_code=test.test_code,
                expected_output=test.expected_output,
                is_active=True,
            )
            tests_created += 1

    return {
        "blocks": blocks_created,
        "quizzes": quizzes_created,
        "choices": choices_created,
        "challenges": challenges_created,
        "tests": tests_created,
    }
