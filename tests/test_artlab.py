import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil

from artlab.__main__ import ROOT, SHAPES, MATH_SHAPES, MATRICES, SHADING, artwork_title, build, describe_artwork, grid, math_recipe, render, selection, validate


class ArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = build()

    def recipe(self, sequence=None):
        return dict(rows=1, cols=1, size=21, style="filled", sequence=sequence or ["heart"])

    def test_all_shapes_and_styles(self):
        for shape in SHAPES:
            outputs = {}
            for style in ("filled", "outline"):
                recipe = {**self.recipe([shape]), "style": style}
                output = render(recipe, self.binary)
                self.assertEqual(len(output.splitlines()), 21)
                self.assertTrue(all(len(line) == 42 for line in output.splitlines()))
                self.assertTrue(set(output) <= {"*", " ", "\n"})
                self.assertIn("*", output)
                outputs[style] = output
            self.assertLess(outputs["outline"].count("*"), outputs["filled"].count("*"), shape)

    def test_grid_and_order(self):
        recipe = dict(rows=4, cols=5, size=9, style="filled", sequence=list(SHAPES))
        lines = render(recipe, self.binary).splitlines()
        self.assertEqual(len(lines), 4 * 9 + 3)
        self.assertEqual(len(lines[0]), 5 * 18 + 4 * 4)
        first = render(dict(rows=1, cols=1, size=9, style="filled", sequence=[SHAPES[0]]), self.binary)
        self.assertEqual([line[:18] for line in lines[:9]], first.splitlines())

    def test_blank_cells(self):
        recipe = dict(rows=1, cols=2, size=9, style="filled", sequence=["circle"])
        self.assertTrue(all(line[-18:] == " " * 18 for line in render(recipe, self.binary).splitlines()))

    def test_round_trip(self):
        recipe = self.recipe()
        self.assertEqual(render(recipe, self.binary), render(json.loads(json.dumps(recipe)), self.binary))

    def test_validation(self):
        for change in ({"sequence": ["unknown"]}, {"sequence": ["star", "heart"]},
                       {"size": 0}, {"rows": True}, {"style": "bad"}):
            with self.assertRaises(ValueError):
                validate({**self.recipe(), **change})
        self.assertEqual(selection("heart:2,star"), ["heart", "heart", "star"])
        self.assertEqual(grid("4x5"), (4, 5))
        with self.assertRaises(ValueError):
            selection("star:0")

    def test_titles_describe_actual_recipes(self):
        classic = self.recipe(["heart"])
        math = math_recipe(shape="donut", matrix="radial", resolution=(80, 28), shading="gradient-linear")
        self.assertIn("heart x1", describe_artwork(classic))
        for recipes in ([classic], [math], [classic, math], [{**classic, "sequence": ["_"]}]):
            variants = {artwork_title(recipes, variation=index) for index in range(6)}
            self.assertGreaterEqual(len(variants), 5)
            for title in variants:
                self.assertNotIn("recipe", title.lower())
                self.assertNotIn("daily", title.lower())
                self.assertNotIn("\n", title)
                self.assertGreater(len(title), 10)
            self.assertEqual(artwork_title(recipes), artwork_title(json.loads(json.dumps(recipes))))
        self.assertIn("80x28", artwork_title([math], variation=2))
        for index in range(6):
            self.assertIn("torus", artwork_title([math], variation=index))
        self.assertEqual(artwork_title([math]), artwork_title([{**math, "metadata": {"generated_at": "ignored"}}]))


class MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = build()

    def test_engines_shading_resolution_and_roundtrip(self):
        for shape in MATH_SHAPES:
            for shading in SHADING:
                recipe = math_recipe(shape=shape, shading=shading, resolution=(64, 24))
                result = render(recipe, self.binary)
                self.assertEqual(len(result.splitlines()), 24, (shape, shading))
                self.assertTrue(all(len(line) == 64 for line in result.splitlines()))
                self.assertTrue(result.strip(), (shape, shading))
                if shading in ("solid", "binary"):
                    self.assertTrue(set(result) <= {"*", " ", "\n"})
        recipe = math_recipe(shape="donut", shading="gradient-linear", resolution=(64, 24))
        self.assertEqual(render(recipe, self.binary), render(json.loads(json.dumps(recipe)), self.binary))
        self.assertGreater(len(set(render(recipe, self.binary).strip())), 3)

    def test_arrangements_and_transform_have_visible_effect(self):
        outputs = {render(math_recipe(shape="metaball", matrix=matrix, resolution=(64, 24)), self.binary) for matrix in MATRICES}
        self.assertEqual(len(outputs), len(MATRICES))
        normal = math_recipe(shape="star", resolution=(64, 24))
        transformed = {**normal, "transform": [1.2, 31, .2, -.1]}
        self.assertNotEqual(render(normal, self.binary), render(transformed, self.binary))

    def test_animation_and_noise_seed(self):
        for shape in ("donut", "metaball", "wave", "moire"):
            one = math_recipe(shape=shape, shading="gradient-linear", resolution=(64, 24))
            self.assertNotEqual(render(one, self.binary), render({**one, "time": 1.5}, self.binary), shape)
        one = math_recipe(shape="wave", resolution=(64, 24))
        self.assertNotEqual(render(one, self.binary), render({**one, "seed": 42}, self.binary))

    def test_invalid_math_configuration(self):
        recipe = math_recipe()
        for change in ({"transform": [0, 0, 0, 0]}, {"transform": [1, 0, 1, 1]},
                       {"transform": [1, float("nan"), 0, 0]}, {"resolution": [400, 0]},
                       {"seed": -1}, {"ramp": "\033*"}, {"time": float("inf")}, {"matrix": "unknown"}):
            with self.assertRaises(ValueError):
                validate({**recipe, **change})


class ExampleTests(unittest.TestCase):
    def test_documentation_covers_every_mode_and_settings_roundtrip(self):
        directory = ROOT / "docs/examples"
        manifest = json.loads((directory / "manifest.json").read_text())
        examples = manifest["examples"]
        self.assertEqual(len(examples), 46)
        groups = {}
        binary = build()
        for entry in examples:
            recipe = json.loads((directory / entry["recipe"]).read_text())
            groups.setdefault(entry["group"], []).append(recipe)
            self.assertEqual(render(recipe, binary), (directory / entry["text"]).read_text())
            self.assertTrue((directory / entry["text"]).read_text().strip())
            self.assertEqual((directory / entry["image"]).read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        for style in ("filled", "outline"):
            self.assertEqual({recipe["sequence"][0] for recipe in groups[f"shapes-{style}"]}, set(SHAPES))
        self.assertEqual({recipe["shape"] for recipe in groups["math-modes"]}, set(MATH_SHAPES))
        self.assertEqual({recipe["matrix"] for recipe in groups["arrangements"]}, set(MATRICES))
        self.assertEqual({recipe["shading"] for recipe in groups["shading"]}, set(SHADING))

    def test_readme_images_and_animations_exist(self):
        import re
        directory = ROOT / "docs/examples"
        readme = (ROOT / "README.md").read_text()
        links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme)
        self.assertEqual(len(links), 9)
        for link in links:
            path = ROOT / link
            self.assertTrue(path.is_file(), link)
            header = path.read_bytes()[:8]
            self.assertTrue(header.startswith(b"\x89PNG") or header.startswith(b"GIF8"), link)
        manifest = json.loads((directory / "manifest.json").read_text())
        self.assertEqual({entry["shape"] for entry in manifest["animations"]}, {"donut", "metaball"})
        for entry in manifest["animations"]:
            self.assertTrue((directory / entry["image"]).read_bytes().startswith(b"GIF8"))
            self.assertGreater(entry["frames"], 16)


if __name__ == "__main__":
    unittest.main()
