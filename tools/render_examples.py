"""Render the README images from real program output (Pillow is only needed here)."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from artlab.__main__ import SHAPES, MATH_SHAPES, MATRICES, SHADING, build, math_recipe, render


def fonts(size):
    from PIL import ImageFont
    for name in ("C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    raise RuntimeError("Install Consolas or DejaVu Sans Mono to regenerate the previews")


def tile(text, title, font_size=11):
    from PIL import Image, ImageDraw
    font, heading = fonts(font_size), fonts(16)
    lines = text.splitlines()
    line_height = math.ceil(font_size * 1.25)
    width = max(220, math.ceil(max(map(len, lines)) * font.getlength("M")) + 32,
                math.ceil(heading.getlength(title)) + 32)
    height = 54 + len(lines) * line_height
    image = Image.new("RGB", (width, height), "#0d1520")
    draw = ImageDraw.Draw(image)
    draw.text((16, 12), title, font=heading, fill="#74e1d2")
    for row, line in enumerate(lines):
        draw.text((16, 42 + row * line_height), line, font=font, fill="#e0eaf3")
    return image


def board(images, columns):
    from PIL import Image
    width = max(image.width for image in images)
    height = max(image.height for image in images)
    rows = math.ceil(len(images) / columns)
    result = Image.new("RGB", (columns * width + (columns + 1) * 12,
                               rows * height + (rows + 1) * 12), "#070c13")
    for index, image in enumerate(images):
        result.paste(image, (12 + (index % columns) * (width + 12),
                             12 + (index // columns) * (height + 12)))
    return result


def generate(destination):
    destination.mkdir(parents=True, exist_ok=True)
    binary = build()
    entries, grouped = [], defaultdict(list)

    def save(identifier, label, group, recipe, font_size=11):
        text = render(recipe, binary)
        (destination / f"{identifier}.txt").write_text(text, encoding="utf-8", newline="\n")
        (destination / f"{identifier}.json").write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
        image = tile(text, label, font_size)
        image.save(destination / f"{identifier}.png")
        entries.append(dict(id=identifier, label=label, group=group, recipe=f"{identifier}.json",
                            text=f"{identifier}.txt", image=f"{identifier}.png"))
        grouped[group].append(image)

    for style in ("filled", "outline"):
        for shape in SHAPES:
            save(f"{style}-{shape}", shape.replace("-", " "), f"shapes-{style}",
                 dict(rows=1, cols=1, size=13, style=style, sequence=[shape], seed=42), 12)
    boards = []
    for group, images in grouped.items():
        if group == "mixed-grid":
            continue
        columns = 4 if group.startswith("shapes-") else 2 if group == "transforms" else 3
        filename = f"{group}.png"
        board(images, columns).save(destination / filename)
        boards.append(filename)
