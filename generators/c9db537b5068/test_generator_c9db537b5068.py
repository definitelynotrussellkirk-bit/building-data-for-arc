"""Focused regressions for the c9db537b5068 four-corner curriculum."""
from __future__ import annotations

import copy
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.per_puzzle.c9db537b5068 import generator as gen


class GeneratorTests(unittest.TestCase):
    def test_defaults_are_structural_and_cover_shape_branches(self):
        branches = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                grid = gen.generate(seed, seed * 11 + 5, difficulty=band)
                self.assertEqual([], gen.self_check(grid, difficulty=band))
                facts, errors = gen._analyze(grid)
                self.assertEqual([], errors)
                self.assertEqual(4, facts["nonbg_count"])
                if facts["bbox_h"] == facts["bbox_w"]:
                    branches.add("square")
                elif facts["bbox_h"] < facts["bbox_w"]:
                    branches.add("wide")
                else:
                    branches.add("tall")
        self.assertEqual({"square", "wide", "tall"}, branches)

    def test_exact_override_boundaries_are_observable(self):
        cases = (
            {"grid_h": 6},
            {"grid_h": 13},
            {"grid_w": 8},
            {"grid_w": 14},
            {"color": 2},
            {"color": 9},
            {"grid_h": 6, "grid_w": 8, "color": 2},
            {"grid_h": 13, "grid_w": 14, "color": 9},
        )
        for band in ("easy", "medium", "hard"):
            for index, overrides in enumerate(cases):
                grid = gen.generate(101 + index, 501 + index, difficulty=band, **overrides)
                observed = gen.observe_overrides(grid)
                for axis, expected in overrides.items():
                    self.assertEqual(expected, observed[axis])
                self.assertEqual(
                    [],
                    gen.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": overrides},
                    ),
                )

    def test_determinism_fresh_returns_cache_isolation_and_rng_purity(self):
        state = random.getstate()
        first = gen.generate(717, 19, difficulty="hard")
        self.assertEqual(state, random.getstate())
        replay = gen.generate(717, 19, difficulty="hard")
        self.assertEqual(first, replay)
        self.assertIsNot(first, replay)
        self.assertTrue(all(a is not b for a, b in zip(first, replay)))

        expected = copy.deepcopy(replay)
        first[0][0] = 9
        self.assertEqual(expected, gen.generate(717, 19, difficulty="hard"))
        self.assertNotEqual(expected, gen.generate(717, 20, difficulty="hard"))

    def test_self_check_rejects_targeted_impostors(self):
        grid = gen.generate(991337, 42, difficulty="medium")
        facts, errors = gen._analyze(grid)
        self.assertEqual([], errors)
        top, left, bottom, right = facts["bbox"]
        color = facts["color"]
        height, width = len(grid), len(grid[0])

        impostors = {}
        impostors["full_one_color"] = [[color] * width for _ in range(height)]

        missing = copy.deepcopy(grid)
        missing[top][left] = 0
        impostors["missing_corner"] = missing

        extra = copy.deepcopy(grid)
        extra[top + 1][left + 1] = color
        impostors["extra_interior_witness"] = extra

        mixed = copy.deepcopy(grid)
        mixed[top][left] = 9 if color != 9 else 8
        impostors["mixed_corner_color"] = mixed

        shifted = copy.deepcopy(grid)
        shifted[top][left] = 0
        shifted[top + 1][left + 1] = color
        impostors["off_corner_recombination"] = shifted

        flat = [[0] * width for _ in range(height)]
        for col in range(1, 5):
            flat[2][col] = color
        impostors["flat_aligned_markers"] = flat

        for name, candidate in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(gen.self_check(candidate), name)

    def test_canonical_inputs_remain_in_distribution(self):
        root = Path(__file__).resolve().parents[3]
        row = None
        with (root / "data/canonical/puzzles.jsonl").open() as handle:
            for line in handle:
                candidate = json.loads(line)
                if candidate.get("task_id") == gen.TASK_ID:
                    row = candidate
                    break
        self.assertIsNotNone(row)
        pairs = list(row["train"])
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        pairs.extend(test)
        for pair in pairs:
            grid = [[int(value) for value in text] for text in pair["input"]]
            self.assertEqual([], gen.self_check(grid))

    def test_unknown_override_rejects_loudly(self):
        with self.assertRaisesRegex(ValueError, "unsupported override"):
            gen.generate(1, 1, texture="warm")


if __name__ == "__main__":
    unittest.main()
