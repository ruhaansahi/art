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
    dependencies = source.read_bytes() + b"".join(path.read_bytes() for path in sorted((root / "src").glob("*.hpp")))
    signature = hashlib.sha256(dependencies + compiler.encode()).hexdigest()
    stamp = directory / "source.sha256"
    if not binary.exists() or not stamp.exists() or stamp.read_text() != signature:
        subprocess.run([compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic",
                        str(source), "-o", str(binary)], check=True)
        stamp.write_text(signature)
    return binary


def validate(recipe):
    if not isinstance(recipe, dict):
        raise ValueError("Recipe must be a JSON object")
    if recipe.get("engine") == "math":
        return validate_math(recipe)
    for key, low, high in (("rows", 1, 20), ("cols", 1, 20), ("size", 5, 81)):
        value = recipe.get(key)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{key} must be an integer in {low}..{high}")
    capacity = recipe["rows"] * recipe["cols"]
    if capacity > 100:
        raise ValueError("At most 100 cells are supported")
    sequence = recipe.get("sequence")
    if not isinstance(sequence, list) or not sequence or len(sequence) > capacity:
        raise ValueError("Provide 1..grid capacity ordered shapes")
    if any(item not in (*SHAPES, "_") for item in sequence):
        raise ValueError("Unknown shape in recipe")
    if recipe.get("style") not in ("filled", "outline"):
        raise ValueError("Style must be filled or outline")
    return recipe


def render(recipe, binary=None):
    validate(recipe)
    binary = binary or build()
    if recipe.get("engine") == "math":
        arguments = [str(binary), "--shape", recipe["shape"], "--matrix", recipe["matrix"],
                     "--shading", recipe["shading"], "--resolution", *map(str, recipe["resolution"]),
                     "--transform", *map(str, recipe["transform"]), "--time", str(recipe["time"]),
                     "--seed", str(recipe["seed"]), "--ramp", recipe["ramp"]]
    else:
        arguments = [str(binary), "--rows", str(recipe["rows"]), "--cols", str(recipe["cols"]),
                     "--size", str(recipe["size"]), "--style", recipe["style"],
                     "--sequence", ",".join(recipe["sequence"])]
    return subprocess.run(arguments, check=True, capture_output=True, text=True).stdout


def grid(text):
    pieces = text.lower().split("x")
    if len(pieces) != 2:
        raise ValueError("Grid must be ROWSxCOLS, for example 4x5")
    return tuple(map(int, pieces))


def selection(text):
    sequence = []
    for part in text.split(","):
        name, separator, quantity = part.strip().partition(":")
        if name not in SHAPES:
            raise ValueError(f"Unknown shape: {name}")
        count = int(quantity) if separator else 1
        if not 1 <= count <= 100:
            raise ValueError("Each quantity must be 1..100")
        sequence.extend([name] * count)
    return sequence


def validate_math(recipe):
    if recipe.get("shape") not in MATH_SHAPES or recipe.get("matrix") not in MATRICES or recipe.get("shading") not in SHADING:
        raise ValueError("Unknown math shape, matrix, or shading")
    resolution = recipe.get("resolution")
    if (not isinstance(resolution, list) or len(resolution) != 2 or
            any(type(value) is not int for value in resolution) or
            not 16 <= resolution[0] <= 400 or not 8 <= resolution[1] <= 160):
        raise ValueError("Resolution must be WIDTH HEIGHT in 16..400 by 8..160")
    transform = recipe.get("transform")
    if (not isinstance(transform, list) or len(transform) != 4 or
            any(type(value) not in (int, float) or not math.isfinite(value) for value in transform)):
        raise ValueError("Transform requires four finite numbers: SCALE ANGLE SKEW_X SKEW_Y")
    scale, angle, skew_x, skew_y = transform
    if (not .05 <= scale <= 20 or abs(angle) > 360000 or abs(skew_x) > 3 or abs(skew_y) > 3 or
            abs(1 - skew_x * skew_y) < .05):
        raise ValueError("Invalid or singular transform")
    ramp = recipe.get("ramp")
    if not isinstance(ramp, str) or not 2 <= len(ramp) <= 32 or any(not 32 <= ord(char) <= 126 for char in ramp):
        raise ValueError("Ramp must contain 2..32 printable ASCII characters")
    if type(recipe.get("seed")) is not int or not 0 <= recipe["seed"] <= 2147483647:
        raise ValueError("Seed must be an integer in 0..2147483647")
    moment = recipe.get("time")
    if type(moment) not in (int, float) or not math.isfinite(moment) or abs(moment) > 1e6:
        raise ValueError("Time must be a finite number between -1000000 and 1000000")
    return recipe


def math_recipe(shape="moire", matrix="grid", shading="solid", resolution=None,
                transform=None, seed=20261022, moment=0, ramp=" .:-=+*#%@"):
    return validate(dict(engine="math", shape=shape, matrix=matrix, shading=shading,
                         resolution=list(resolution or (120, 40)), transform=list(transform or (1, 0, 0, 0)),
                         seed=seed, time=moment, ramp=ramp))


def describe_artwork(recipe):
    if recipe.get("engine") == "math":
        width, height = recipe["resolution"]
        return f"{width}x{height} {recipe['matrix']} {recipe['shape']} ({recipe['shading']})"
    counts = Counter(shape for shape in recipe["sequence"] if shape != "_")
    shapes = ", ".join(f"{name} x{count}" for name, count in counts.items())
    return f"{recipe['size']}px {recipe['style']} {recipe['rows']}x{recipe['cols']} grid: {shapes}"


def artwork_title(recipes, variation=None):
    if not recipes:
        raise ValueError("An artwork title requires at least one recipe")
    functional = [{key: value for key, value in recipe.items() if key != "metadata"} for recipe in recipes]
    digest = hashlib.sha256(json.dumps(functional, sort_keys=True).encode()).digest()
    variant = (int.from_bytes(digest[:4], "big") if variation is None else variation) % 6
    names = {"circle": "circle", "star": "star", "metaball": "metaball field", "donut": "3D torus",
             "fractal": "Mandelbrot set", "wave": "flow field", "moire": "moire pattern",
             "julia": "Julia set", "clifford": "Clifford attractor"}
    def joined(items):
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]
    if len(recipes) == 1:
        recipe = recipes[0]
        if recipe.get("engine") == "math":
            name = names[recipe["shape"]]
            capital = name[:1].upper() + name[1:]
            layout = {"chaos": "noise-warped"}.get(recipe["matrix"], recipe["matrix"])
            shading = {"solid": "solid asterisks", "binary": "a high-contrast fill",
                       "gradient-linear": "a smooth light-to-dark ramp", "gradient-radial": "radial shading"}[recipe["shading"]]
            width, height = recipe["resolution"]
            return (f"Render the {name} in a {layout} layout",
                    f"A {layout} take on the {name}",
                    f"Draw the {name} at {width}x{height}",
                    f"{capital} with {shading}",
                    f"Play with a {layout} {name}",
                    f"{capital}, arranged as a {layout}")[variant]
        counts = Counter(shape for shape in recipe["sequence"] if shape != "_")
        plural = {"cross": "crosses", "hourglass": "hourglasses"}
        labels = []
        for shape, count in counts.items():
            name = shape.replace("-", " ")
            article = "an" if name[0] in "aeiou" or shape == "hourglass" else "a"
            labels.append(f"{article} {name}" if count == 1 else f"{count} {plural.get(shape, name + 's')}")
        total = sum(counts.values())
        label = "blank cells" if not labels else joined(labels) if len(labels) <= 3 else f"a mix of {total} shapes"
        style = "outlined" if recipe["style"] == "outline" else "filled"
        rows, cols = recipe["rows"], recipe["cols"]
        action = "Outline" if style == "outlined" else "Fill in"
        return (f"Draw {label} in a {rows}x{cols} grid",
                f"Arrange {label} as ASCII art",
                f"{style.capitalize()} shapes in a {rows}x{cols} layout",
                f"A {rows}x{cols} grid of {label}",
                f"{action} {label}",
                f"Render {label} using the {style} style")[variant]
    modes = list(dict.fromkeys(names.get(recipe.get("shape"), "shape grids") for recipe in recipes))
    label = joined(modes) if len(modes) <= 3 else "shapes and mathematical patterns"
    count = len(recipes)
    return (f"Put together {count} ASCII sketches",
            f"Mix {label} in an ASCII collection",
            f"A few more renders: {label}",
            f"Save {count} more pieces for the gallery",
            f"{count} new ASCII scenes",
            f"Bring {label} together in one render set")[variant]


def math_study(seed, ordinal):
    rng = random.Random(seed)
    return math_recipe(shape=MATH_SHAPES[ordinal % len(MATH_SHAPES)],
                       matrix=MATRICES[(ordinal // len(MATH_SHAPES)) % len(MATRICES)],
                       shading=SHADING[(ordinal // 45) % len(SHADING)],
                       resolution=rng.choice(((80, 28), (100, 34), (120, 40))),
                       transform=(round(rng.uniform(.8, 1.3), 3), round(rng.uniform(-35, 35), 2),
                                  round(rng.uniform(-.25, .25), 3), round(rng.uniform(-.25, .25), 3)),
                       seed=rng.randrange(2147483648), moment=round(rng.uniform(0, 12), 3))


def main():
    parser = argparse.ArgumentParser(description="C++ asterisk art with Python recipes")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("shapes")
    commands.add_parser("build")
    for command in ("render", "math"):
        drawing = commands.add_parser(command)
        sources = drawing.add_mutually_exclusive_group()
        sources.add_argument("--shapes", help="heart:4,star:6,circle:10; expanded in listed order")
        sources.add_argument("--sequence", help="Explicit comma-separated cell order")
        sources.add_argument("--recipe", type=Path)
        sources.add_argument("--shape", choices=MATH_SHAPES, help="Mathematical canvas engine")
        drawing.add_argument("--grid", default="4x5", help="ROWSxCOLS")
        drawing.add_argument("--size", type=int, default=21)
        drawing.add_argument("--style", choices=("filled", "outline"), default="filled")
        drawing.add_argument("--seed", type=int, default=20261022)
        drawing.add_argument("--shuffle", action="store_true")
        drawing.add_argument("--matrix", choices=MATRICES, default="grid")
        drawing.add_argument("--shading", choices=SHADING, default="solid")
        drawing.add_argument("--resolution", type=int, nargs=2, default=[120, 40], metavar=("WIDTH", "HEIGHT"))
        drawing.add_argument("--transform", type=float, nargs=4, default=[1, 0, 0, 0], metavar=("SCALE", "ANGLE", "SKEW_X", "SKEW_Y"))
        drawing.add_argument("--ramp", default=" .:-=+*#%@")
        drawing.add_argument("--time", type=float, default=0)
        drawing.add_argument("--frames", type=int, default=1)
        drawing.add_argument("--fps", type=float, default=12)
        drawing.add_argument("--output", type=Path)
        drawing.add_argument("--write-recipe", type=Path)
    parser.set_defaults(**{})
    args = parser.parse_args()
    try:
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
            if not 1 <= args.frames <= 300 or not math.isfinite(args.fps) or not 1 <= args.fps <= 60:
                raise ValueError("Frames must be 1..300 and fps must be 1..60")
            if args.frames > 1 and recipe.get("engine") != "math":
                raise ValueError("Animation requires a math recipe")
            frames = []
            for frame in range(args.frames):
                current = dict(recipe, time=recipe.get("time", 0) + frame / args.fps) if args.frames > 1 else recipe
                output = render(current)
                if args.frames > 1 and not args.output and sys.stdout.isatty():
                    print("\033[H\033[2J" + output, end="", flush=True)
                    time.sleep(1 / args.fps)
                else:
                    frames.append(output)
            result = "\n".join(frames)
            if args.output:
                args.output.write_text(result, encoding="utf-8")
            else:
                print(result, end="")
            if args.write_recipe:
                args.write_recipe.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"artlab: {error}\n")


if __name__ == "__main__":
    main()
