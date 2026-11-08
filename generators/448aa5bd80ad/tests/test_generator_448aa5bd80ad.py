"""Focused semantic and override regressions for generator 448aa5bd80ad."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import os
import random
import unittest
from collections import Counter
from pathlib import Path

TASK_ID = "448aa5bd80ad"
ROOT = Path(__file__).resolve().parents[1]
MODULE_FILE = os.environ.get("GENERATOR_448AA5BD80AD_FILE")
if MODULE_FILE:
    spec = importlib.util.spec_from_file_location(
        f"focused_{TASK_ID}_generator", MODULE_FILE
    )
    assert spec and spec.loader
    GENERATOR = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GENERATOR)
else:
    GENERATOR = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )

EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "n_nines",
    "blob_cells",
    "palette_kind",
}
EXPECTED_PALETTES = ("default", "warm", "cool", "varied")


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def blank_scene(*, n_nines=1, color=4, height=9, width=9):
    grid = [[0] * width for _ in range(height)]
    for col in range(n_nines):
        grid[0][col] = 9
    return grid


def body_cells(grid):
    return [
        (row, col)
        for row in range(2, len(grid))
        for col, value in enumerate(grid[row])
        if value != 0
    ]


class Generator448aa5bd80adTests(unittest.TestCase):
    def test_rule_hash_and_canonical_inputs(self):
        row = canonical_row()
        source = row["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(digest, "b0b8c9f3ea53")
        self.assertEqual(getattr(GENERATOR, "RULE_HASH", None), digest)
        pairs = row["train"] + row["test"]
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            self.assertEqual(GENERATOR.self_check(pair["input"]), [])

    def test_axis_surface_is_minimal_and_exactly_observable(self):
        self.assertEqual(set(GENERATOR.AXES), EXPECTED_AXES)
        for band in ("easy", "medium", "hard"):
            sample_index = 0
            for height in (7, 14):
                for width in (7, 14):
                    for n_nines in (1, 3):
                        for blob_cells in (4, 8):
                            for palette_kind in EXPECTED_PALETTES:
                                grid = GENERATOR.generate(
                                    6000 + sample_index,
                                    sample_index,
                                    difficulty=band,
                                    grid_h=height,
                                    grid_w=width,
                                    n_nines=n_nines,
                                    blob_cells=blob_cells,
                                    palette_kind=palette_kind,
                                )
                                self.assertEqual(GENERATOR.self_check(grid), [])
                                self.assertEqual(
                                    GENERATOR.observe_overrides(grid),
                                    {
                                        "grid_h": height,
                                        "grid_w": width,
                                        "n_nines": n_nines,
                                        "blob_cells": blob_cells,
                                        "palette_kind": palette_kind,
                                    },
                                )
                                sample_index += 1

    def test_each_semantic_branch_occurs_in_every_band(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            counts = Counter()
            inputs = set()
            for seed in range(180):
                grid = GENERATOR.generate(
                    100_000 + 10_000 * band_index + seed,
                    seed * 17 + band_index,
                    difficulty=band,
                )
                counts[sum(value == 9 for value in grid[0])] += 1
                inputs.add(tuple(map(tuple, grid)))
                self.assertEqual(GENERATOR.self_check(grid), [])
            self.assertEqual(set(counts), {1, 2, 3})
            self.assertTrue(all(counts[value] >= 35 for value in (1, 2, 3)))
            self.assertGreaterEqual(len(inputs), 175)

    def test_targeted_structural_impostors_are_rejected(self):
        valid = GENERATOR.generate(
            424242, 17, difficulty="medium", n_nines=2, blob_cells=6
        )
        color = next(
            value
            for row in valid[2:]
            for value in row
            if value not in (0, 9)
        )
        invalid = []

        row0_intruder = copy.deepcopy(valid)
        row0_intruder[0][next(i for i, value in enumerate(row0_intruder[0]) if value == 0)] = color
        invalid.append(row0_intruder)

        body_selector = copy.deepcopy(valid)
        body_selector[1][0] = 9
        invalid.append(body_selector)

        line = blank_scene(n_nines=1, color=color)
        for col in range(4):
            line[2][col] = color
        invalid.append(line)

        oversized = blank_scene(n_nines=1, color=color)
        for row, col in (
            [(2, c) for c in range(4)]
            + [(3, c) for c in range(4)]
            + [(4, 0)]
        ):
            oversized[row][col] = color
        invalid.append(oversized)

        disconnected = blank_scene(n_nines=1, color=color)
        for row, col in ((2, 1), (2, 2), (3, 1), (6, 6)):
            disconnected[row][col] = color
        invalid.append(disconnected)

        multicolor = blank_scene(n_nines=1, color=color)
        for row, col in ((2, 1), (2, 2), (3, 1), (3, 2)):
            multicolor[row][col] = color
        multicolor[3][2] = 1 if color != 1 else 2
        invalid.append(multicolor)

        transform_alias = blank_scene(n_nines=2, color=color)
        for row in (2, 3):
            for col in (1, 2, 3):
                transform_alias[row][col] = color
        invalid.append(transform_alias)

        for grid in invalid:
            self.assertTrue(GENERATOR.self_check(grid), grid)
            self.assertEqual(GENERATOR.observe_overrides(grid), {})

    def test_generated_body_is_connected_2d_and_transform_visible(self):
        for n_nines in (1, 2, 3):
            for seed in range(80):
                grid = GENERATOR.generate(
                    500_000 + seed,
                    seed * 23 + n_nines,
                    difficulty=("easy", "medium", "hard")[seed % 3],
                    n_nines=n_nines,
                )
                cells = body_cells(grid)
                min_row = min(row for row, _ in cells)
                min_col = min(col for _, col in cells)
                local = [(row - min_row, col - min_col) for row, col in cells]
                self.assertGreaterEqual(len({row for row, _ in local}), 2)
                self.assertGreaterEqual(len({col for _, col in local}), 2)
                self.assertFalse(
                    GENERATOR._selected_transform_is_identity(local, n_nines)
                )

    def test_invalid_and_unknown_overrides_reject_loudly(self):
        invalid = (
            {"grid_h": 6},
            {"grid_w": 15},
            {"n_nines": 0},
            {"n_nines": 4},
            {"blob_cells": 3},
            {"blob_cells": 9},
            {"palette_kind": "unknown"},
            {"texture": "helpful"},
        )
        for overrides in invalid:
            with self.assertRaises((TypeError, ValueError), msg=overrides):
                GENERATOR.generate(1, 2, **overrides)

    def test_determinism_fresh_returns_and_global_rng(self):
        random.seed(20260723)
        state = random.getstate()
        first = GENERATOR.generate(73, 109, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GENERATOR.generate(73, 109, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        third = GENERATOR.generate(73, 109, difficulty="hard")
        self.assertEqual(second, third)


if __name__ == "__main__":
    unittest.main()
