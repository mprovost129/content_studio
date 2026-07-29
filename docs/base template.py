import io

import cairosvg
from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
cx, cy = SIZE // 2, SIZE // 2
PAD = 52

# ── Python logo (python-logo-only.svg) ────────────────────────────────────
PYTHON_SVG = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.0" id="svg2"
   width="83.371017pt" height="101.00108pt"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="linearGradient4671">
      <stop style="stop-color:#ffd43b;stop-opacity:1;" offset="0" />
      <stop style="stop-color:#ffe873;stop-opacity:1" offset="1" />
    </linearGradient>
    <linearGradient id="linearGradient4689">
      <stop style="stop-color:#5a9fd4;stop-opacity:1;" offset="0" />
      <stop style="stop-color:#306998;stop-opacity:1;" offset="1" />
    </linearGradient>
    <linearGradient x1="224.23996" y1="144.75717" x2="-65.308502" y2="144.75717"
       id="linearGradient2987" xlink:href="#linearGradient4671"
       gradientUnits="userSpaceOnUse" gradientTransform="translate(100.2702,99.61116)" />
    <linearGradient x1="172.94208" y1="77.475983" x2="26.670298" y2="76.313133"
       id="linearGradient2990" xlink:href="#linearGradient4689"
       gradientUnits="userSpaceOnUse" gradientTransform="translate(100.2702,99.61116)" />
  </defs>
  <path style="fill:url(#linearGradient2990);fill-opacity:1"
     d="M 54.918785,9.1927421e-4 C 50.335132,0.02221727 45.957846,0.41313697 42.106285,1.0946693 30.760069,3.0991731 28.700036,7.2947714 28.700035,15.032169 v 10.21875 h 26.8125 v 3.40625 h -26.8125 -10.0625 c -7.792459,0 -14.6157588,4.683717 -16.7499998,13.59375 -2.46181998,10.212966 -2.57101508,16.586023 0,27.25 1.9059283,7.937852 6.4575432,13.593748 14.2499998,13.59375 h 9.21875 v -12.25 c 0,-8.849902 7.657144,-16.656248 16.75,-16.65625 h 26.78125 c 7.454951,0 13.406253,-6.138164 13.40625,-13.625 v -25.53125 c 0,-7.2663386 -6.12998,-12.7247771 -13.40625,-13.9374997 C 64.281548,0.32794397 59.502438,-0.02037903 54.918785,9.1927421e-4 Z m -14.5,8.21875012579 c 2.769547,0 5.03125,2.2986456 5.03125,5.1249996 -2e-6,2.816336 -2.261703,5.09375 -5.03125,5.09375 -2.779476,-1e-6 -5.03125,-2.277415 -5.03125,-5.09375 -10e-7,-2.826353 2.251774,-5.1249996 5.03125,-5.1249996 z" />
  <path style="fill:url(#linearGradient2987);fill-opacity:1"
     d="m 85.637535,28.657169 v 11.90625 c 0,9.230755 -7.825895,16.999999 -16.75,17 h -26.78125 c -7.335833,0 -13.406249,6.278483 -13.40625,13.625 v 25.531247 c 0,7.266344 6.318588,11.540324 13.40625,13.625004 8.487331,2.49561 16.626237,2.94663 26.78125,0 6.750155,-1.95439 13.406253,-5.88761 13.40625,-13.625004 V 86.500919 h -26.78125 v -3.40625 h 26.78125 13.406254 c 7.792461,0 10.696251,-5.435408 13.406241,-13.59375 2.79933,-8.398886 2.68022,-16.475776 0,-27.25 -1.92578,-7.757441 -5.60387,-13.59375 -13.406241,-13.59375 z m -15.0625,64.65625 c 2.779478,3e-6 5.03125,2.277417 5.03125,5.093747 -2e-6,2.826354 -2.251775,5.125004 -5.03125,5.125004 -2.76955,0 -5.03125,-2.29865 -5.03125,-5.125004 2e-6,-2.81633 2.261697,-5.093747 5.03125,-5.093747 z" />
</svg>"""

# ── Standard colors ────────────────────────────────────────────────────────
PY_BLUE = (55, 118, 171)
YELLOW = (255, 212, 59)
# Swap ACCENT_COL to change the post theme color
ACCENT_COL = PY_BLUE  # e.g. (255,140,60) for orange, (180,120,255) for purple


# ── Fonts ──────────────────────────────────────────────────────────────────
def F(name, size):
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}.ttf", size)
    except OSError:
        return ImageFont.load_default()


fuser = F("DejaVuSans-Bold", 38)


# ── Helper functions ───────────────────────────────────────────────────────
def glow_text(draw, x, y, text, font, fill, glow_col, spread=5):
    for dx in range(-spread, spread + 1, 2):
        for dy in range(-spread, spread + 1, 2):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=glow_col)
    draw.text((x, y), text, font=font, fill=fill)


def centered_glow(draw, y, text, font, fill, glow_col, spread=5):
    bb = draw.textbbox((0, 0), text, font=font)
    x = (SIZE - (bb[2] - bb[0])) // 2
    glow_text(draw, x, y, text, font, fill, glow_col, spread)


def centered(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    x = (SIZE - (bb[2] - bb[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)


def code_line(draw, x, y, segments, font):
    lx = x
    for text, col in segments:
        draw.text((lx, y), text, font=font, fill=col)
        bb = draw.textbbox((0, 0), text, font=font)
        lx += bb[2] - bb[0]


# ── Canvas ─────────────────────────────────────────────────────────────────
canvas = Image.new("RGB", (SIZE, SIZE), (10, 12, 22))
d = ImageDraw.Draw(canvas)

# Dark gradient background top to bottom
for y in range(SIZE):
    t = y / SIZE
    d.line(
        [(0, y), (SIZE, y)], fill=(int(10 + t * 10), int(12 + t * 8), int(22 + t * 22))
    )

# Dot grid
for gx in range(0, SIZE, 54):
    for gy in range(0, SIZE, 54):
        d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(55, 110, 190))

# ── Top accent bar (left third = accent, rest = PY_BLUE) ──────────────────
d.rectangle([0, 0, SIZE, 9], fill=PY_BLUE)
d.rectangle([0, 0, SIZE // 3, 9], fill=ACCENT_COL)

# ── Bottom accent bar (right third = accent, rest = PY_BLUE) ──────────────
d.rectangle([0, SIZE - 9, SIZE, SIZE], fill=PY_BLUE)
d.rectangle([SIZE * 2 // 3, SIZE - 9, SIZE, SIZE], fill=ACCENT_COL)

# ── Python logo top right ──────────────────────────────────────────────────
lsz = 110
svg_bytes = cairosvg.svg2png(
    bytestring=PYTHON_SVG.encode(), output_width=lsz, output_height=lsz
)
logo = Image.open(io.BytesIO(svg_bytes)).convert("RGBA")
ca = canvas.convert("RGBA")
ca.paste(logo, (SIZE - lsz - 48, 22), logo)
canvas = ca.convert("RGB")
d = ImageDraw.Draw(canvas)

# ── Vignette (dark edges, bright center) ──────────────────────────────────
vig = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
vd = ImageDraw.Draw(vig)
for r in range(SIZE // 2, SIZE // 3, -1):
    t = (r - SIZE // 3) / (SIZE // 6)
    a = int(min(1, t) * 80)
    vd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, a))

# ── @code_with_michael username ────────────────────────────────────────────
# Move this y value to position the username on the page
username_y = SIZE - 120
ub = d.textbbox((0, 0), "@code_with_michael", font=fuser)
ux = (SIZE - (ub[2] - ub[0])) // 2
for dx in range(-3, 4):
    for dy in range(-3, 4):
        if dx or dy:
            d.text(
                (ux + dx, username_y + dy),
                "@code_with_michael",
                font=fuser,
                fill=(0, 80, 170),
            )
d.text((ux, username_y), "@code_with_michael", font=fuser, fill=(100, 175, 255))

# ── Composite vignette and save ────────────────────────────────────────────
final = canvas.convert("RGBA")
final = Image.alpha_composite(final, vig)
final = final.convert("RGB")

final.save("/mnt/user-data/outputs/base_template.png", "PNG", quality=95)
print("Saved base_template.png")

# ===========================================================================
# HOW TO USE THIS TEMPLATE
# ===========================================================================
# 1. Copy this file and rename it for your new post (e.g. functions_post.py)
# 2. Change ACCENT_COL to your lesson color:
#       Blue    = (55, 118, 171)   -- Variables
#       Green   = (39, 120, 80)    -- Integers
#       Orange  = (255, 140, 60)   -- Floats
#       Purple  = (140, 82, 220)   -- Booleans
#       Teal    = (0, 185, 185)    -- Type Checking
#       Pink    = (200, 60, 130)   -- f-Strings
#       Sky     = (40, 180, 220)   -- Lists
#       Amber   = (230, 120, 40)   -- if/elif/else
#       Lime    = (80, 200, 100)   -- Loops
#       Gold    = (255, 200, 40)   -- Challenges
# 3. Add a lesson pill below the top bar:
#       d.rounded_rectangle([PAD,26,PAD+pw,64], radius=19, fill=ACCENT_COL)
#       d.text((PAD+18,30), "BEGINNER  *  LESSON X", font=ftiny, fill=(255,255,255))
# 4. Add your hero title with glow_text() starting around y=80
# 5. Add your content blocks (definition box, code block, cards, pills)
# 6. Set username_y to just below your last content block
# ===========================================================================
