import io
import textwrap
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from studio.models import BrandProfile, GraphicAsset, GraphicTemplate, Lesson

FORMAT_SIZES = {
    GraphicAsset.Format.INSTAGRAM_SQUARE: (1080, 1080),
    GraphicAsset.Format.INSTAGRAM_PORTRAIT: (1080, 1350),
    GraphicAsset.Format.STORY: (1080, 1920),
    GraphicAsset.Format.FACEBOOK_LANDSCAPE: (1200, 630),
}


class GraphicGenerationError(RuntimeError):
    pass


@dataclass
class RenderBlock:
    block_type: str
    title: str
    content: str


def _rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _font(size: int, bold=False, mono=False):
    from PIL import ImageFont

    candidates = []
    if mono:
        candidates.extend(
            [
                "DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "C:/Windows/Fonts/consola.ttf",
            ]
        )
    elif bold:
        candidates.extend(
            [
                "DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_width: int):
    lines = []
    for paragraph in (text or "").splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _draw_python_mark_fallback(draw, x: int, y: int, size: int):
    blue = (55, 118, 171)
    yellow = (255, 212, 59)
    half = size // 2
    radius = max(size // 8, 5)
    draw.rounded_rectangle(
        (x, y, x + half + 8, y + half + 12), radius=radius, fill=blue
    )
    draw.rounded_rectangle(
        (x + half - 8, y + half - 12, x + size, y + size), radius=radius, fill=yellow
    )
    eye = max(size // 18, 3)
    draw.ellipse(
        (x + half - eye * 3, y + eye * 3, x + half - eye, y + eye * 5), fill=(8, 20, 35)
    )
    draw.ellipse(
        (x + half + eye, y + size - eye * 5, x + half + eye * 3, y + size - eye * 3),
        fill=(8, 20, 35),
    )


@lru_cache(maxsize=8)
def _python_logo(size: int):
    from PIL import Image

    logo_path = settings.BASE_DIR / "static" / "images" / "python-logo-only.png"
    if not logo_path.exists():
        return None
    with Image.open(logo_path) as source:
        logo = source.convert("RGBA")
    return logo.resize((size, size), Image.Resampling.LANCZOS)


def _paste_python_logo(image, draw, x: int, y: int, size: int):
    logo = _python_logo(size)
    if logo is None:
        _draw_python_mark_fallback(draw, x, y, size)
        return
    image.alpha_composite(logo, (x, y))


def _draw_background(image, draw, brand: BrandProfile, accent, width: int, height: int):
    from PIL import Image, ImageDraw

    base = _rgb(brand.background_color)
    for y in range(height):
        ratio = y / max(height, 1)
        color = tuple(min(255, int(channel + ratio * 14)) for channel in base)
        draw.line((0, y, width, y), fill=color)
    spacing = max(int(width / 20), 44)
    dot_color = (46, 104, 184)
    for x in range(0, width, spacing):
        for y in range(0, height, spacing):
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=dot_color)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    inset = int(width * 0.03)
    overlay_draw.ellipse(
        (inset, -int(height * 0.02), width - inset, height * 1.02), fill=(4, 7, 16, 105)
    )
    image.alpha_composite(overlay)
    bar = max(8, int(width * 0.008))
    draw.rectangle((0, 0, width, bar), fill=(55, 118, 171, 255))
    draw.rectangle((0, 0, width // 3, bar), fill=accent)
    draw.rectangle((0, height - bar, width, height), fill=(55, 118, 171, 255))
    draw.rectangle((width * 2 // 3, height - bar, width, height), fill=accent)


def _chunk_blocks(lesson: Lesson, output_format: str):
    max_lines = {
        GraphicAsset.Format.FACEBOOK_LANDSCAPE: 4,
        GraphicAsset.Format.INSTAGRAM_SQUARE: 13,
        GraphicAsset.Format.INSTAGRAM_PORTRAIT: 18,
        GraphicAsset.Format.STORY: 28,
    }[output_format]
    blocks = []
    for block in lesson.blocks.all():
        raw_lines = block.content.splitlines() or [""]
        if block.block_type not in {"code", "output"}:
            raw_lines = textwrap.wrap(block.content, width=72) or [""]
        for index in range(0, len(raw_lines), max_lines):
            chunk = "\n".join(raw_lines[index : index + max_lines])
            title = block.title
            if index:
                title = f"{title or block.get_block_type_display()} (continued)"
            blocks.append(RenderBlock(block.block_type, title, chunk))
    if not blocks and lesson.summary:
        blocks.append(RenderBlock("text", "What you'll learn", lesson.summary))
    return blocks


def _card_height(
    draw, block: RenderBlock, body_font, mono_font, width: int, padding: int
):
    font = mono_font if block.block_type in {"code", "output"} else body_font
    if block.block_type in {"code", "output"}:
        line_count = max(1, len(block.content.splitlines()))
    else:
        line_count = max(1, len(_wrap(draw, block.content, font, width - padding * 2)))
    title_height = int(body_font.size * 1.6) if block.title else 0
    return padding * 2 + title_height + line_count * int(font.size * 1.45)


def _draw_card(
    draw, block, x, y, width, height, accent, body_font, mono_font, small_bold
):
    colors = {
        "output": ((5, 36, 15, 245), (69, 190, 85, 255)),
        "challenge": ((31, 25, 5, 245), (244, 199, 42, 255)),
        "quiz": ((31, 25, 5, 245), (244, 199, 42, 255)),
        "callout": ((14, 28, 55, 245), accent),
    }
    fill, border = colors.get(block.block_type, ((13, 18, 37, 245), accent))
    radius = max(12, width // 60)
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=radius,
        fill=fill,
        outline=border,
        width=max(2, width // 350),
    )
    padding = max(18, width // 45)
    cursor = y + padding
    if block.title:
        draw.text((x + padding, cursor), block.title, font=small_bold, fill=border)
        cursor += int(small_bold.size * 1.6)
    font = mono_font if block.block_type in {"code", "output"} else body_font
    content_color = (226, 232, 244, 255)
    if block.block_type == "output":
        content_color = (157, 232, 163, 255)
    lines = (
        block.content.splitlines()
        if block.block_type in {"code", "output"}
        else _wrap(draw, block.content, font, width - padding * 2)
    )
    line_height = int(font.size * 1.45)
    for line in lines:
        draw.text((x + padding, cursor), line, font=font, fill=content_color)
        cursor += line_height


def _render_slide(
    lesson, brand, template, output_format, blocks, slide_number, total_slides
):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise GraphicGenerationError(
            "Pillow is not installed. Install project requirements first."
        ) from exc

    width, height = FORMAT_SIZES[output_format]
    accent = _rgb(lesson.resolved_accent_color) + (255,)
    image = Image.new("RGBA", (width, height), brand.background_color)
    draw = ImageDraw.Draw(image)
    _draw_background(image, draw, brand, accent, width, height)

    scale = width / 1080
    margin = max(34, int(52 * scale))
    logo_size = max(68, int(110 * scale))
    _paste_python_logo(image, draw, width - margin - logo_size, margin // 2, logo_size)

    label_font = _font(max(18, int(25 * scale)), bold=True)
    title_size = max(38, int((64 if height <= 700 else 72) * scale))
    if slide_number > 1:
        title_size = max(30, int(title_size * 0.62))
    title_font = _font(title_size, bold=True)
    body_font = _font(max(20, int(27 * scale)))
    small_bold = _font(max(18, int(23 * scale)), bold=True)
    mono_font = _font(max(18, int(24 * scale)), mono=True)
    handle_font = _font(max(22, int(34 * scale)), bold=True)

    label = template.get_template_type_display().upper()
    if lesson.series_id and lesson.series_position:
        total = (
            f" OF {lesson.series.total_lessons}" if lesson.series.total_lessons else ""
        )
        label = f"{lesson.series.title.upper()}  •  DAY {lesson.series_position}{total}"
    label_box = draw.textbbox((0, 0), label, font=label_font)
    label_width = min(width - margin * 2 - logo_size, label_box[2] + margin)
    label_height = int(label_font.size * 1.7)
    draw.rounded_rectangle(
        (margin, margin // 2, margin + label_width, margin // 2 + label_height),
        radius=label_height // 2,
        fill=accent,
    )
    draw.text(
        (margin + label_height // 2, margin // 2 + int(label_font.size * 0.2)),
        label,
        font=label_font,
        fill=(7, 12, 25, 255),
    )

    title = (
        lesson.title
        if slide_number == 1
        else f"{lesson.title}  •  {slide_number}/{total_slides}"
    )
    title_max_width = width - margin * 2
    title_lines = _wrap(draw, title, title_font, title_max_width)
    cursor = margin // 2 + label_height + max(18, int(25 * scale))
    title_line_height = int(title_font.size * 1.06)
    for line in title_lines[:3]:
        draw.text(
            (margin + 4, cursor + 5),
            line,
            font=title_font,
            fill=(26, 66, 140, 255),
        )
        draw.text((margin, cursor), line, font=title_font, fill=(225, 232, 243, 255))
        cursor += title_line_height
    draw.rectangle(
        (margin, cursor + 8, width - margin, cursor + 12), fill=(47, 76, 132, 255)
    )
    draw.rectangle(
        (margin, cursor + 8, margin + int((width - margin * 2) * 0.24), cursor + 12),
        fill=accent,
    )
    cursor += max(28, int(34 * scale))

    content_width = width - margin * 2
    padding = max(18, content_width // 45)
    gap = max(14, int(18 * scale))
    for block in blocks:
        card_height = _card_height(
            draw, block, body_font, mono_font, content_width, padding
        )
        _draw_card(
            draw,
            block,
            margin,
            cursor,
            content_width,
            card_height,
            accent,
            body_font,
            mono_font,
            small_bold,
        )
        cursor += card_height + gap

    footer_y = height - max(72, int(90 * scale))
    handle_box = draw.textbbox((0, 0), brand.social_handle, font=handle_font)
    handle_x = (width - (handle_box[2] - handle_box[0])) // 2
    draw.text(
        (handle_x + 3, footer_y + 3),
        brand.social_handle,
        font=handle_font,
        fill=(14, 63, 130, 255),
    )
    draw.text(
        (handle_x, footer_y),
        brand.social_handle,
        font=handle_font,
        fill=(76, 157, 240, 255),
    )
    return image.convert("RGB")


def _paginate(lesson, brand, template, output_format):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise GraphicGenerationError("Pillow is not installed.") from exc

    width, height = FORMAT_SIZES[output_format]
    probe = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(probe)
    scale = width / 1080
    body_font = _font(max(20, int(27 * scale)))
    mono_font = _font(max(18, int(24 * scale)), mono=True)
    content_width = width - max(68, int(104 * scale))
    padding = max(18, content_width // 45)
    available = int(height * (0.43 if height <= 700 else 0.57))
    pages = []
    current = []
    used = 0
    for block in _chunk_blocks(lesson, output_format):
        card_height = _card_height(
            draw, block, body_font, mono_font, content_width, padding
        )
        if current and used + card_height > available:
            pages.append(current)
            current = []
            used = 0
        current.append(block)
        used += card_height + max(14, int(18 * scale))
    if current or not pages:
        pages.append(current)
    probe.close()
    return pages


def generate_graphics(lesson: Lesson, template: GraphicTemplate, output_formats):
    brand = BrandProfile.get_default()
    created = []
    for output_format in output_formats:
        if output_format not in FORMAT_SIZES:
            raise GraphicGenerationError(f"Unsupported output format: {output_format}")
        pages = _paginate(lesson, brand, template, output_format)
        for slide_number, blocks in enumerate(pages, start=1):
            width, height = FORMAT_SIZES[output_format]
            asset = GraphicAsset.objects.create(
                lesson=lesson,
                template=template,
                output_format=output_format,
                width=width,
                height=height,
                slide_number=slide_number,
                status=GraphicAsset.Status.GENERATING,
                alt_text=f"{lesson.title}, slide {slide_number} of {len(pages)}",
            )
            try:
                image = _render_slide(
                    lesson,
                    brand,
                    template,
                    output_format,
                    blocks,
                    slide_number,
                    len(pages),
                )
                buffer = io.BytesIO()
                image.save(buffer, format="PNG", optimize=True)
                image.close()
                timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
                filename = (
                    f"{lesson.slug}-{output_format}-{slide_number}-{timestamp}.png"
                )
                with transaction.atomic():
                    asset.file.save(
                        filename, ContentFile(buffer.getvalue()), save=False
                    )
                    asset.status = GraphicAsset.Status.READY
                    asset.save()
                created.append(asset)
            except Exception as exc:
                asset.status = GraphicAsset.Status.FAILED
                asset.error_message = str(exc)
                asset.save(update_fields=("status", "error_message", "updated_at"))
                raise GraphicGenerationError(str(exc)) from exc
    return created
