"""Regression tests for the exact-axis crop-to-nonzero-bbox generator repair."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

TASK_ID = "fb6fb24e9ccf"
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


class CropNonzeroBBoxGeneratorTests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_inputs(self):
        row = canonical_row()
        digest = hashlib.sha256(
            " ".join(row["program_solution"].split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(GENERATOR.RULE_HASH, digest)
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 5)
        for pair in pairs:
            self.assertEqual([], GENERATOR.self_check(pair["input"]))
            self.assertEqual(pair["output"], crop_nonzero(pair["input"]))

    def test_four_demo_schedule_has_every_decisive_branch(self):
        expected_components = [1, 1, 2, 1]
        expected_colors = [1, 3, 1, 2]
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                observed = [
                    GENERATOR.observe_overrides(
                        GENERATOR.generate(seed, index, difficulty=band)
                    )
                    for index in range(4)
                ]
                self.assertEqual(
                    expected_components,
                    [row["n_components"] for row in observed],
                )
                self.assertEqual(
                    expected_colors,
                    [row["n_distinct_colors"] for row in observed],
                )
                positions = []
                for index in range(4):
                    grid = GENERATOR.generate(seed, index, difficulty=band)
                    box = GENERATOR._bbox(grid)
                    positions.append((box[0], box[1]))
                self.assertEqual(4, len(set(positions)))

    def test_regression_seed_no_longer_splits_two_motifs_into_four(self):
        grid = GENERATOR.generate(110007, 109, difficulty="medium")
        observed = GENERATOR.observe_overrides(grid)
        self.assertIn(observed["n_components"], (1, 2))
        self.assertEqual([], GENERATOR.self_check(grid))

    def test_exact_axes_are_observable_at_boundaries(self):
        cases = [
            {"grid_h": 5},
            {"grid_h": 20},
            {"grid_w": 5},
            {"grid_w": 22},
            {"bbox_h": 2},
            {"bbox_h": 8},
            {"bbox_w": 2},
            {"bbox_w": 8},
            {"n_components": 1},
            {"n_components": 2},
            {"n_distinct_colors": 1},
            {"n_distinct_colors": 3},
            {
                "grid_h": 20,
                "grid_w": 22,
                "bbox_h": 8,
                "bbox_w": 8,
                "n_components": 2,
                "n_distinct_colors": 3,
            },
        ]
        for band in ("easy", "medium", "hard"):
            for seed in range(10):
                for case in cases:
                    with self.subTest(band=band, seed=seed, case=case):
                        grid = GENERATOR.generate(
                            seed,
                            seed * 17 + 3,
                            difficulty=band,
                            **case,
                        )
                        observed = GENERATOR.observe_overrides(grid)
                        for key, value in case.items():
                            self.assertEqual(value, observed[key])
                        self.assertEqual([], GENERATOR.self_check(grid))

    def test_200_draw_semantic_census_per_band(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            branches = {"one": 0, "two": 0, "multi": 0, "holes": 0}
            inputs = set()
            outputs = set()
            for i in range(200):
                grid = GENERATOR.generate(
                    500000 + band_index * 10000 + i,
                    i * 13 + 17,
                    difficulty=band,
                )
                self.assertEqual([], GENERATOR.self_check(grid))
                observed = GENERATOR.observe_overrides(grid)
                branches["one"] += observed["n_components"] == 1
                branches["two"] += observed["n_components"] == 2
                branches["multi"] += observed["n_distinct_colors"] > 1
                box = GENERATOR._bbox(grid)
                area = (box[2] - box[0] + 1) * (box[3] - box[1] + 1)
                nonzero = sum(value != 0 for row in grid for value in row)
                branches["holes"] += nonzero < area
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, crop_nonzero(grid))))
            self.assertEqual(branches["holes"], 200)
            self.assertGreater(branches["one"], 0)
            self.assertGreater(branches["two"], 0)
            self.assertGreater(branches["multi"], 0)
            self.assertGreater(len(inputs), 190)
            self.assertGreater(len(outputs), 180)

    def test_self_check_rejects_targeted_impostors(self):
        blank = [[0] * 8 for _ in range(8)]
        full_grid = [
            [4 if r in (0, 7) or c in (0, 7) else 0 for c in range(8)]
            for r in range(8)
        ]
        solid = [[0] * 8 for _ in range(8)]
        for r in range(2, 5):
            for c in range(2, 5):
                solid[r][c] = 5
        three = [[0] * 9 for _ in range(9)]
        for r, c in ((2, 2), (4, 4), (6, 6)):
            three[r][c] = 5
        four_colors = [[0] * 9 for _ in range(9)]
        for i, value in enumerate((2, 3, 4, 5)):
            four_colors[2 + i][2 + i] = value
        for name, grid in {
            "blank": blank,
            "full_grid": full_grid,
            "solid": solid,
            "three_components": three,
            "four_colors": four_colors,
        }.items():
            with self.subTest(name=name):
                self.assertTrue(GENERATOR.self_check(grid))

    def test_determinism_fresh_returns_global_rng_and_loud_conflicts(self):
        random.seed(1729)
        state = random.getstate()
        first = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        saved = copy.deepcopy(first)
        first[0][0] = 9
        self.assertEqual(saved, GENERATOR.generate(17, 23, difficulty="hard"))
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, grid_h=5, bbox_h=8)
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, n_components=2, bbox_h=2)
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, unknown_axis=3)


if __name__ == "__main__":
    unittest.main()
