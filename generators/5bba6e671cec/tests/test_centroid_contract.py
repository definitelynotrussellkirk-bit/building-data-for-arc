"""Portable regressions for centroid evidence and sampler call boundaries."""
from __future__ import annotations

import itertools
import math
import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "5bba6e671cec"
ROOT = find_root(__file__)
generator, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = ("easy", "medium", "hard")


def angle_cycle(grid, *, first_cell=False):
    """Use either every pixel or one first pixel as the color's position."""
    colors = sorted({v for row in grid for v in row} - {4, 7})
    center_r, center_c = (len(grid) - 1) / 2, (len(grid[0]) - 1) / 2

    def angle(color):
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if first_cell:
            r, c = min(cells)
        else:
            r = sum(r for r, _ in cells) / len(cells)
            c = sum(c for _, c in cells) / len(cells)
        return math.atan2(c - center_c, -(r - center_r)) % (2 * math.pi)

    ordered = sorted(colors, key=angle)
    mapping = {color: ordered[(i - 1) % len(ordered)] for i, color in enumerate(ordered)}
    return [[mapping.get(v, v) for v in row] for row in grid]


class CentroidContractTests(unittest.TestCase):
    def test_first_cell_angle_is_a_canonical_fitting_declared_shortcut(self):
        self.assertIn("first_cell_angle", generator.CANONICAL_SHORTCUTS)
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            self.assertEqual(angle_cycle(pair["input"]), pair["output"])
            self.assertEqual(angle_cycle(pair["input"], first_cell=True), pair["output"])

    def test_every_query_rotation_retains_full_centroid_counterevidence(self):
        # Reverting the quadrant profile's second first-cell counterexample
        # leaves only one distinguishing pair; holding it out must fail here.
        for band, seed, start in itertools.product(BANDS, range(20), range(4)):
            grids = [generator.generate(seed, start + i, difficulty=band) for i in range(4)]
            differs = [angle_cycle(a, first_cell=True) != angle_cycle(a) for a in grids]
            for query_index in range(4):
                with self.subTest(band=band, seed=seed, start=start, query_index=query_index):
                    self.assertTrue(any(differs[i] for i in range(4) if i != query_index))

    def test_period_is_exposed_under_shared_census_contract(self):
        self.assertEqual(getattr(generator, "LESSON_SCHEDULE_PERIOD", None), 4)
        self.assertEqual(generator.SCHEDULE_PERIOD, generator.LESSON_SCHEDULE_PERIOD)

    def test_sample_index_is_nonnegative_while_seeds_remain_signed(self):
        for function in (generator.generate, generator.schedule_profile):
            for band in BANDS:
                with self.subTest(function=function.__name__, band=band):
                    with self.assertRaises(ValueError):
                        function(0, -1, difficulty=band)
                    function(-17, 0, difficulty=band)
                    for bad in (True, 1.0, "1", None):
                        with self.assertRaises(TypeError):
                            function(bad, 0, difficulty=band)
                        with self.assertRaises(TypeError):
                            function(0, bad, difficulty=band)


if __name__ == "__main__":
    unittest.main()
