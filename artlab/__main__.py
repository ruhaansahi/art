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


def main():
    parser = argparse.ArgumentParser(description="Build the terminal renderer")
    parser.add_argument("command", choices=("build",))
    parser.parse_args()
    print(build())


if __name__ == "__main__":
    main()
