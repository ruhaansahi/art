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


