from __future__ import annotations

import copy
import json
import importlib
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root

gen = importlib.import_module("puzzle_generators.per_puzzle.22e428cda452.generator")


ROOT = find_root(__file__)


class Generator22e428cda452Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = None
        with canonical_path(ROOT).open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == gen.TASK_ID:
                    cls.canonical = row
                    break
        assert cls.canonical is not None

    def test_all_official_inputs_pass_and_match_complete_profiles(self):
        pairs = list(self.canonical["train"]) + list(self.canonical["test"])
        signatures = []
        for pair in pairs:
            grid = pair["input"]
            before = copy.deepcopy(grid)
            self.assertEqual(gen.self_check(grid), [])
            self.assertEqual(grid, before)
            signatures.append(gen.canonical_profile_signature(grid))
        self.assertEqual(
            set(signatures),
            {(8, 8, 1, 1), (8, 8, 2, 1), (8, 8, 4, 1),
             (8, 8, 8, 1), (8, 8, 15, 4)},
        )

    def test_default_draws_are_deterministic_fresh_and_rng_isolated(self):
        state = random.getstate()
        first = gen.generate(17, 9, difficulty="medium")
        self.assertEqual(random.getstate(), state)
        second = gen.generate(17, 9, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 7
        self.assertEqual(second, gen.generate(17, 9, difficulty="medium"))

    def test_generated_content_is_corner_only_and_self_checked(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(100):
                grid = gen.generate(seed, seed * 7 + 3, difficulty=band)
                self.assertEqual(gen.self_check(grid), [])
                h, w = len(grid), len(grid[0])
                allowed = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
                actual = {
                    (r, c)
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if value != 7
                }
                self.assertTrue(actual)
                self.assertLessEqual(len(actual), 4)
                self.assertTrue(actual <= allowed)

    def test_exact_overrides_are_observable(self):
        cases = (
            dict(grid_h=8, grid_w=18, corner_mask=1, palette_size=1),
            dict(grid_h=18, grid_w=8, corner_mask=15, palette_size=4),
            dict(grid_h=11, grid_w=13, corner_mask=6, palette_size=2),
            dict(palette_size=4),
            dict(corner_mask=1),
        )
        for band in ("easy", "medium", "hard"):
            for i, overrides in enumerate(cases):
                grid = gen.generate(200 + i, 31 + i, difficulty=band, **overrides)
                self.assertEqual(gen.self_check(grid), [])
                observed = gen.observe_overrides(grid)
                if "grid_h" in overrides:
                    self.assertEqual(len(grid), overrides["grid_h"])
                if "grid_w" in overrides:
                    self.assertEqual(len(grid[0]), overrides["grid_w"])
                for axis in ("corner_mask", "palette_size"):
                    if axis in overrides:
                        self.assertEqual(observed[axis], overrides[axis])
        with self.assertRaisesRegex(ValueError, "exceeds selected corner count"):
            gen.generate(0, 0, corner_mask=1, palette_size=4)

    def test_official_profiles_are_reachable_in_every_band(self):
        expected = {(8, 8, 1, 1), (8, 8, 2, 1), (8, 8, 4, 1),
                    (8, 8, 8, 1), (8, 8, 15, 4)}
        for band in ("easy", "medium", "hard"):
            seen = {
                sig
                for seed in range(1000)
                if (sig := gen.canonical_profile_signature(
                    gen.generate(seed, seed + 101, difficulty=band)
                )) is not None
            }
            self.assertEqual(seen, expected)

    def test_near_miss_recombination_is_not_an_official_profile(self):
        grid = gen.generate(
            4, 5, difficulty="medium",
            grid_h=8, grid_w=8, corner_mask=3, palette_size=2,
        )
        self.assertEqual(gen.self_check(grid), [])
        self.assertEqual(gen.feature_signature(grid), (8, 8, 3, 2))
        self.assertIsNone(gen.canonical_profile_signature(grid))

    def test_self_check_rejects_minimal_semantic_mutations(self):
        control = gen.generate(
            1, 2, grid_h=8, grid_w=8, corner_mask=1, palette_size=1
        )
        self.assertEqual(gen.self_check(control), [])

        all_background = [[7] * 8 for _ in range(8)]
        center_singleton = copy.deepcopy(all_background)
        center_singleton[4][4] = 2
        edge_noncorner = copy.deepcopy(all_background)
        edge_noncorner[0][3] = 2
        solid_2x2 = copy.deepcopy(all_background)
        solid_2x2[0][0] = solid_2x2[0][1] = 2
        solid_2x2[1][0] = solid_2x2[1][1] = 2
        too_small = [[7] * 7 for _ in range(7)]
        too_small[0][0] = 2

        for mutated in (
            all_background, center_singleton, edge_noncorner, solid_2x2, too_small
        ):
            self.assertTrue(gen.self_check(mutated), mutated)


if __name__ == "__main__":
    unittest.main()
