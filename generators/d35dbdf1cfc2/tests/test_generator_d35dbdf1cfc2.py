"""Canonical sampler regressions for d35dbdf1cfc2."""
from __future__ import annotations

import copy
import importlib
import random
import unittest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d35dbdf1cfc2"
ROOT = find_root(__file__)
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _shape(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _object_distance(a, b):
    return min(max(abs(ar - br), abs(ac - bc))
               for ar, ac in a for br, bc in b)


class MotifPackGeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_are_accepted_and_solved(self):
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        self.assertEqual(len(pairs), 5)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            self.assertEqual(GEN.self_check(source), [])
            self.assertEqual(GEN.rule_mirror(source), pair["output"])
            self.assertEqual(source, pair["input"])

    def test_generated_scenes_have_diverse_separated_motifs_and_no_fallbacks(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                grid = GEN.generate(seed, seed * 17 + 5, difficulty=band)
                self.assertEqual(GEN.self_check(grid), [], (band, seed))
                objects = GEN._extract_objects(grid)
                self.assertIn(len(objects), range(3, 6))
                self.assertGreaterEqual(len({len(obj["cells"]) for obj in objects}), 2)
                self.assertGreaterEqual(len({_shape(obj["cells"]) for obj in objects}), 2)
                for index, obj in enumerate(objects):
                    self.assertIn(len(obj["cells"]), range(3, 6))
                    for other in objects[index + 1:]:
                        self.assertGreater(_object_distance(obj["cells"], other["cells"]), 1)
                output = GEN.rule_mirror(grid)
                self.assertTrue(output and output[0])
                self.assertEqual(
                    sum(cell != 0 for row in output for cell in row),
                    sum(len(obj["cells"]) for obj in objects),
                )

    def test_exact_joint_overrides_are_observable_and_30x30_is_meaningful(self):
        case = {"grid_h": 30, "grid_w": 30, "n": 5, "palette_kind": "varied"}
        grid = GEN.generate(17, 3, difficulty="hard", **case)
        self.assertEqual(GEN.self_check(grid), [])
        self.assertEqual(GEN.observe_overrides(grid), case)
        self.assertEqual((len(grid), len(grid[0])), (30, 30))
        occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        rows = {r for r, _ in occupied}
        cols = {c for _, c in occupied}
        self.assertGreaterEqual(max(rows) - min(rows), 24)
        self.assertGreaterEqual(max(cols) - min(cols), 24)
        self.assertTrue(any(r in (0, 29) or c in (0, 29) for r, c in occupied))

    def test_invalid_controls_and_incompatible_geometry_reject_loudly(self):
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 2, typo_axis=3)
        for name, value in (
            ("grid_h", True),
            ("grid_w", 10.0),
            ("n", "3"),
            ("n", 2),
            ("palette_kind", "neon"),
        ):
            with self.subTest(name=name, value=value), self.assertRaises((TypeError, ValueError)):
                GEN.generate(1, 2, **{name: value})
        with self.assertRaises(ValueError):
            GEN.generate(1, 2, grid_h=7, grid_w=7, n=5)

    def test_validator_rejects_shape_clones_and_touching_motifs(self):
        clones = [[0] * 15 for _ in range(15)]
        for color, (r0, c0) in zip((2, 4, 6), ((1, 1), (6, 2), (10, 10))):
            for dr, dc in ((0, 0), (1, 0), (1, 1)):
                clones[r0 + dr][c0 + dc] = color
        self.assertTrue(any("shape" in error for error in GEN.self_check(clones)))

        touching = [[0] * 12 for _ in range(12)]
        for r, c in ((1, 1), (2, 1), (2, 2)):
            touching[r][c] = 2
        for r, c in ((3, 3), (3, 4), (3, 5), (3, 6)):
            touching[r][c] = 4
        for r, c in ((7, 8), (8, 7), (8, 8), (8, 9), (9, 8)):
            touching[r][c] = 6
        self.assertTrue(any("buffer" in error or "touch" in error for error in GEN.self_check(touching)))

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(20261024)
        state = random.getstate()
        first = GEN.generate(31, 9, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GEN.generate(31, 9, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = 9
        self.assertEqual(second, GEN.generate(31, 9, difficulty="hard"))


if __name__ == "__main__":
    unittest.main()
