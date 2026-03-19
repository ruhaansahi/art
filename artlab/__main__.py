import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SHAPES = ("square", "rectangle", "triangle", "inverted-triangle", "diamond", "circle",
          "heart", "star", "arrow", "cross", "hourglass", "hexagon")
MATH_SHAPES = ("circle", "star", "metaball", "donut", "fractal", "wave", "moire", "julia", "clifford")
MATRICES = ("grid", "radial", "sine-wave", "vortex", "chaos")
SHADING = ("solid", "binary", "gradient-linear", "gradient-radial")


def build(root=ROOT):
    compiler = shutil.which("g++")
    if not compiler:
        raise ValueError("Install g++ (MSYS2 UCRT64 on Windows) and put it on PATH")
    directory = root / ".build"
    directory.mkdir(exist_ok=True)
    binary = directory / ("art.exe" if os.name == "nt" else "art")
    source = root / "src/art.cpp"
    subprocess.run([compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic",
                        str(source), "-o", str(binary)], check=True)
    return binary


def validate(recipe):
    if not isinstance(recipe, dict):
        raise ValueError("Recipe must be a JSON object")
    return recipe


def render(recipe, binary=None):
    validate(recipe)
    binary = binary or build()
    arguments = [str(binary), "--rows", str(recipe["rows"]), "--cols", str(recipe["cols"]),
                     "--size", str(recipe["size"]), "--style", recipe["style"],
                     "--sequence", ",".join(recipe["sequence"])]
    return subprocess.run(arguments, check=True, capture_output=True, text=True).stdout


def grid(text):
    return tuple(map(int, text.lower().split("x")))


def selection(text):
    sequence = []
    for part in text.split(","):
        name, separator, quantity = part.strip().partition(":")
        if name not in SHAPES:
            raise ValueError(f"Unknown shape: {name}")
        count = int(quantity) if separator else 1
        sequence.extend([name] * count)
    return sequence


def main():
    parser = argparse.ArgumentParser(description="C++ asterisk art with Python recipes")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("shapes")
    commands.add_parser("build")
    for command in ("render",):
        drawing = commands.add_parser(command)
        sources = drawing.add_mutually_exclusive_group()
        sources.add_argument("--shapes", help="heart:4,star:6,circle:10; expanded in listed order")
        sources.add_argument("--sequence", help="Explicit comma-separated cell order")
        drawing.add_argument("--grid", default="4x5", help="ROWSxCOLS")
        drawing.add_argument("--size", type=int, default=21)
        drawing.add_argument("--style", choices=("filled", "outline"), default="filled")
        drawing.add_argument("--output", type=Path)
    parser.set_defaults(**{'recipe': None, 'shape': None, 'seed': 20261022, 'shuffle': False, 'matrix': 'grid', 'shading': 'solid', 'resolution': [120, 40], 'transform': [1, 0, 0, 0], 'ramp': ' .:-=+*#%@', 'time': 0, 'frames': 1, 'fps': 12, 'write_recipe': None})
    args = parser.parse_args()
    if args.command == "shapes":
        print("\n".join(SHAPES))
    elif args.command == "build":
        print(build())
    elif args.command in (None, "interactive"):
        parser.print_help()
    else:
        if args.recipe:
            recipe = json.loads(args.recipe.read_text(encoding="utf-8"))
        elif args.shape or args.command == "math":
            if args.shapes or args.sequence:
                raise ValueError("Use render for classic shape grids")
            recipe = math_recipe(args.shape or "moire", args.matrix, args.shading,
                                 args.resolution, args.transform, args.seed, args.time, args.ramp)
        else:
            rows, cols = grid(args.grid)
            sequence = selection(args.shapes or "heart,star,circle,diamond") if not args.sequence else args.sequence.split(",")
            recipe = dict(rows=rows, cols=cols, size=args.size, style=args.style,
                          sequence=sequence, seed=args.seed)
        if args.shuffle:
            if recipe.get("engine") == "math":
                raise ValueError("Use --matrix to arrange a mathematical canvas")
            recipe = dict(recipe, sequence=list(recipe["sequence"]))
            random.Random(args.seed).shuffle(recipe["sequence"])
            recipe["seed"] = args.seed
        frames = []
        for frame in range(args.frames):
            current = dict(recipe, time=recipe.get("time", 0) + frame / args.fps) if args.frames > 1 else recipe
            output = render(current)
            frames.append(output)
        result = "\n".join(frames)
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result, end="")
        if args.write_recipe:
            args.write_recipe.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
