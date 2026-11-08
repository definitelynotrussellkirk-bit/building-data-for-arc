"""Independent literal labels executed by the proposed Racket programs."""
import importlib.util
from pathlib import Path
import unittest

from reviewer_support import canonical_pairs, find_root


SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("_marker_area_racket_test", SOURCE)
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def witness():
    grid = [[8] * 15 for _ in range(11)]
    for r in range(1, 10):
        for c in range(1, 14):
            grid[r][c] = 1
    for top in (2, 6):
        for left in (2, 6, 10):
            for r in range(top, top + 3):
                for c in range(left, left + 3):
                    grid[r][c] = 8
    # Repeated color 2 has total area 4, but neither room reaches area 4.
    for top, left, height, width, color in (
        (3, 3, 1, 1, 2), (3, 6, 1, 2, 3), (2, 11, 2, 1, 5),
        (6, 3, 3, 1, 2), (6, 6, 2, 2, 6),
    ):
        for r in range(top, top + height):
            for c in range(left, left + width):
                grid[r][c] = color
    return grid


class MarkerAreaRacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = prototype.RacketRunner().__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.runner.__exit__(None, None, None)

    def test_exact_area_boundaries_and_repeated_colors(self):
        expected = {
            1: [[2, 3, 5], [2, 6, 8]],
            2: [[8, 3, 5], [2, 6, 8]],
            4: [[8, 8, 8], [8, 6, 8]],
        }
        for minimum, output in expected.items():
            setting = {"minimum_marker_area": minimum}
            with self.subTest(minimum=minimum):
                self.assertEqual(self.runner(prototype.program(setting), witness()), output)
                self.assertEqual(prototype.transform(witness(), setting), output)

    def test_default_replays_four_distinct_canonical_pairs(self):
        pairs = canonical_pairs("36b22ff07a2e", root=find_root(__file__), labeled_only=True)
        distinct = {str((p["input"], p["output"])): p for p in pairs}
        self.assertEqual(len(distinct), 4)
        setting = {"minimum_marker_area": 1}
        self.assertEqual(prototype.program(setting), prototype.canonical_program())
        for pair in distinct.values():
            self.assertEqual(self.runner(prototype.program(setting), pair["input"]), pair["output"])
            self.assertEqual(prototype.transform(pair["input"], setting), pair["output"])


if __name__ == "__main__":
    unittest.main()
