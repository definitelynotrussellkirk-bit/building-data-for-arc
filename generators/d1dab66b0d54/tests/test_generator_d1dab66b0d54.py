"""Canonical sampler regressions for d1dab66b0d54."""
from __future__ import annotations

import copy
import importlib
import random
import unittest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d1dab66b0d54"
ROOT = find_root(__file__)
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _red_count(grid):
    return sum(cell == 2 for row in grid for cell in row)


class GuideShiftGeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_are_accepted_and_solved(self):
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            self.assertEqual(GEN.self_check(source), [])
            self.assertEqual(GEN.rule_mirror(source), pair["output"])
            self.assertEqual(source, pair["input"])

    def test_generated_red_ring_moves_forward_without_erasure(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                grid = GEN.generate(seed, seed * 13 + 7, difficulty=band)
                self.assertEqual(GEN.self_check(grid), [], (band, seed))
                output = GEN.rule_mirror(grid)
                self.assertEqual(_red_count(grid), 8)
                self.assertEqual(_red_count(output), 8)
                self.assertNotEqual(grid, output)
                self.assertEqual(GEN.self_check(output), [], (band, seed, "output"))

    def test_exact_joint_overrides_are_observable_and_30x30_is_meaningful(self):
        case = {
            "grid_h": 30,
            "grid_w": 30,
            "anchor_orientation": "row",
            "spacing": 5,
            "guide_count": 5,
            "source_index": 2,
        }
        grid = GEN.generate(17, 3, difficulty="hard", **case)
        self.assertEqual(GEN.self_check(grid), [])
        self.assertEqual(GEN.observe_overrides(grid), case)
        self.assertEqual((len(grid), len(grid[0])), (30, 30))
        occupied_rows = {r for r, row in enumerate(grid) if any(row)}
        occupied_cols = {
            c for c in range(len(grid[0])) if any(grid[r][c] for r in range(len(grid)))
        }
        self.assertGreaterEqual(max(occupied_cols) - min(occupied_cols), 20)
        self.assertGreaterEqual(len(occupied_rows), 3)

    def test_invalid_controls_and_incompatible_geometry_reject_loudly(self):
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 2, typo_axis=3)
        for name, value in (
            ("grid_h", True),
            ("grid_w", 10.0),
            ("spacing", "3"),
            ("guide_count", 2),
            ("source_index", -1),
            ("anchor_orientation", "diagonal"),
        ):
            with self.subTest(name=name, value=value), self.assertRaises((TypeError, ValueError)):
                GEN.generate(1, 2, **{name: value})
        with self.assertRaises(ValueError):
            GEN.generate(
                1,
                2,
                grid_h=7,
                grid_w=7,
                anchor_orientation="row",
                spacing=5,
                guide_count=5,
            )

    def test_validator_rejects_nonregular_guides_and_out_of_bounds_motion(self):
        valid = GEN.generate(
            9,
            4,
            grid_h=12,
            grid_w=16,
            anchor_orientation="row",
            spacing=3,
            guide_count=4,
            source_index=1,
        )
        greens = [(r, c) for r, row in enumerate(valid) for c, value in enumerate(row) if value == 3]
        irregular = copy.deepcopy(valid)
        r, c = greens[-1]
        irregular[r][c] = 0
        irregular[r - 1][c] = 3
        self.assertTrue(GEN.self_check(irregular))

        clipped = copy.deepcopy(valid)
        # Move the red ring to the last guide so another forward shift would clip.
        for r, row in enumerate(clipped):
            for c, value in enumerate(row):
                if value == 2:
                    clipped[r][c] = 0
        guide_row = greens[-1][0]
        guide_col = greens[-1][1]
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    clipped[guide_row + dr][guide_col + dc] = 2
        self.assertTrue(GEN.self_check(clipped))

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
