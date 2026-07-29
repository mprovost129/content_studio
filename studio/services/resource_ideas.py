from __future__ import annotations

import re
from dataclasses import dataclass

from django.db import transaction

from studio.models import Category, LearningResource, Lesson


@dataclass(frozen=True)
class ResourceIdeaDraft:
    topic: str
    resource_type: str
    audience: str = "absolute beginners"
    category: Category | None = None
    related_lessons: list[Lesson] | None = None
    featured: bool = False
    created_by: object | None = None


def _clean(value: str, fallback: str) -> str:
    value = re.sub(r"\s+", " ", (value or "").strip())
    return value or fallback


def _title_case(value: str) -> str:
    cleaned = _clean(value, "Python basics")
    small_words = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "for",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
    words = []
    for index, word in enumerate(cleaned.split()):
        lowered = word.lower()
        words.append(
            lowered if index and lowered in small_words else word[:1].upper() + word[1:]
        )
    return " ".join(words)


def _is_money_topic(topic: str) -> bool:
    lowered = topic.lower()
    return any(
        word in lowered
        for word in (
            "money",
            "price",
            "cost",
            "budget",
            "sale",
            "tax",
            "tip",
            "discount",
            "dollar",
            "total",
        )
    )


def _code_example(topic: str) -> tuple[str, str]:
    lowered = topic.lower()
    if _is_money_topic(topic):
        return (
            'price = 19.99\nquantity = 2\ntotal = price * quantity\nprint(f"Total: ${total:.2f}")',
            "Total: $39.98",
        )
    if "list" in lowered:
        return (
            'tasks = ["read", "code", "practice"]\nprint(tasks[0])\nprint(len(tasks))',
            "read\n3",
        )
    if "loop" in lowered:
        return ("for number in range(1, 4):\n    print(number)", "1\n2\n3")
    if "function" in lowered:
        return (
            'def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("Michael"))',
            "Hello, Michael!",
        )
    if "error" in lowered or "nameerror" in lowered:
        return ('first_name = "Michael"\nprint(first_name)', "Michael")
    return (
        'message = "Python makes more sense one step at a time."\nprint(message)',
        "Python makes more sense one step at a time.",
    )


def build_resource_outline(draft: ResourceIdeaDraft) -> dict:
    topic = _title_case(draft.topic)
    audience = _clean(draft.audience, "absolute beginners")
    resource_type = draft.resource_type or LearningResource.ResourceType.CHEAT_SHEET
    code, output = _code_example(topic)

    if resource_type == LearningResource.ResourceType.COMMON_ERROR:
        title = f"How to Fix {topic} in Python"
        summary = f"A beginner-friendly troubleshooting guide for {audience} who are stuck on {topic.lower()}."
        beginner_tip = "Read the full error message from top to bottom before changing code. The last line usually tells you what Python noticed."
        content = f"""What this error usually means
{topic} usually happens when Python cannot do exactly what the code is asking. The safest first move is to slow down and identify the line number, the error type, and the name or value mentioned in the message.

Beginner checklist
1. Read the last line of the error message.
2. Find the line number Python points to.
3. Check spelling, capitalization, quotation marks, parentheses, and indentation.
4. Run the smallest possible version of the code.
5. Change one thing at a time.

Tiny example
```python
{code}
```

Expected output
```text
{output}
```

Practice
Create the same kind of error on purpose, then fix it. That turns debugging from guessing into a skill.
"""
    elif resource_type == LearningResource.ResourceType.SETUP_GUIDE:
        title = f"{topic} Setup Guide for Beginners"
        summary = (
            f"A simple setup reference for {audience} getting ready to practice Python."
        )
        beginner_tip = (
            "Do one setup step at a time and test it before moving to the next step."
        )
        content = f"""Before you start
This guide keeps {topic.lower()} simple so beginners can get to practice faster.

Setup checklist
1. Confirm Python is installed.
2. Open your editor or browser playground.
3. Create a small test file.
4. Run one print statement.
5. Save the file in a folder you can find again.

Test code
```python
print("Python is working")
```

Expected output
```text
Python is working
```

Common beginner issue
If the command does not run, check whether Python is installed, whether the file is saved, and whether you are running the correct file.
"""
    elif resource_type == LearningResource.ResourceType.GLOSSARY:
        title = f"{topic} Vocabulary for Python Beginners"
        summary = f"Plain-English definitions for {audience} learning {topic.lower()}."
        beginner_tip = "Do not memorize every word at once. Learn the word, run an example, then explain it out loud."
        content = f"""Key terms
Term: {topic}
Meaning: A Python idea that becomes easier when you connect the word to a small code example.

Example
```python
{code}
```

Expected output
```text
{output}
```

How to remember it
Use the term in a sentence after you run the code. Example: I used {topic.lower()} to make the program do one clear thing.

Practice
Write your own one-sentence definition, then create a two-line code example that matches it.
"""
    elif resource_type == LearningResource.ResourceType.PRACTICE_REFERENCE:
        title = f"{topic} Practice Reference"
        summary = f"A quick practice guide for {audience} who want repetition with {topic.lower()}."
        beginner_tip = "Practice works best when you change one value, predict the output, and run the code again."
        content = f"""Practice goal
Use this reference to practice {topic.lower()} in small, repeatable steps.

Start here
```python
{code}
```

Expected output
```text
{output}
```

Try these changes
1. Change one variable value.
2. Rename one variable clearly.
3. Add one more print statement.
4. Predict the output before running the code.
5. Explain what changed in one sentence.

Reflection question
What part of the code controls the output?
"""
    elif resource_type == LearningResource.ResourceType.DOWNLOAD:
        title = f"{topic} Downloadable Reference"
        summary = f"A printable-style beginner reference for {audience} learning {topic.lower()}."
        beginner_tip = "Keep this reference nearby while practicing, but type the examples yourself instead of only reading them."
        content = f"""Reference overview
This resource can be used as the body for a future downloadable PDF or handout about {topic.lower()}.

Remember
- Start with one small example.
- Run the code.
- Read the output.
- Change one thing.
- Run it again.

Example
```python
{code}
```

Expected output
```text
{output}
```

Mini challenge
Create a second example that uses your own words or values.
"""
    else:
        title = f"{topic} Cheat Sheet for Python Beginners"
        summary = f"A skimmable cheat sheet for {audience} learning {topic.lower()} in Python."
        beginner_tip = "A cheat sheet should help you practice faster, not replace practice. Run the examples yourself."
        content = f"""What to remember
{topic} is easier when you connect the idea to a small working example.

Basic pattern
```python
{code}
```

Expected output
```text
{output}
```

Beginner checklist
1. Read the code one line at a time.
2. Predict the output.
3. Run the code.
4. Compare your prediction to the result.
5. Change one value and run it again.

Common mistake
Beginners often copy the example without testing changes. Make one small edit so you can see how Python responds.

Practice prompt
Create your own example using a name, number, or value that means something to you.
"""

    return {
        "title": title[:220],
        "summary": summary,
        "resource_type": resource_type,
        "difficulty": Lesson.Difficulty.BEGINNER,
        "content": content.strip(),
        "beginner_tip": beginner_tip[:240],
        "estimated_read_minutes": 5,
        "seo_title": title[:70],
        "seo_description": summary[:170],
        "pdf_download_enabled": resource_type
        in {
            LearningResource.ResourceType.CHEAT_SHEET,
            LearningResource.ResourceType.PRACTICE_REFERENCE,
            LearningResource.ResourceType.DOWNLOAD,
        },
        "pdf_footer_note": "Print this reference, type the example yourself, and change one value before moving on.",
        "internal_notes": "Generated from resource idea workflow. Review all examples, links, downloads, SEO metadata, PDF settings, and related lessons before publishing.",
    }


@transaction.atomic
def create_resource_from_idea(draft: ResourceIdeaDraft) -> LearningResource:
    outline = build_resource_outline(draft)
    resource = LearningResource.objects.create(
        title=outline["title"],
        summary=outline["summary"],
        resource_type=outline["resource_type"],
        status=LearningResource.Status.DRAFT,
        difficulty=outline["difficulty"],
        category=draft.category,
        featured=draft.featured,
        content=outline["content"],
        beginner_tip=outline["beginner_tip"],
        estimated_read_minutes=outline["estimated_read_minutes"],
        seo_title=outline["seo_title"],
        seo_description=outline["seo_description"],
        pdf_download_enabled=outline["pdf_download_enabled"],
        pdf_footer_note=outline["pdf_footer_note"],
        internal_notes=outline["internal_notes"],
        created_by=draft.created_by,
        updated_by=draft.created_by,
    )
    if draft.related_lessons:
        resource.related_lessons.set(draft.related_lessons)
    return resource
