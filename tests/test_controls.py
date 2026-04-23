import unittest
from artlab.__main__ import grid, selection, validate


class ControlTests(unittest.TestCase):
    def test_order_and_quantities(self):
        self.assertEqual(selection("star:2,heart"), ["star", "star", "heart"])
        self.assertEqual(grid("4x5"), (4, 5))

    def test_invalid_settings(self):
        good = dict(rows=1, cols=1, size=9, style="filled", sequence=["circle"])
        for change in ({"rows": True}, {"sequence": []}, {"size": 4}, {"style": "bad"}):
            with self.assertRaises(ValueError):
                validate({**good, **change})


if __name__ == "__main__":
    unittest.main()
