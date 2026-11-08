"""Focused regression tests for generator d2d40680cd25."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import sys
import unittest
from itertools import product
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

gen = importlib.import_module(
    "puzzle_generators.per_puzzle.d2d40680cd25.generator"
)


def _normal(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


class GeneratorRegressionTests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_pairs(self):
        row = _canonical_row()
        actual_hash = hashlib.sha256(
            " ".join(row["program_solution"].split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(gen.RULE_HASH, actual_hash)
        tests = row.get("test") or []
        if isinstance(tests, dict):
            tests = [tests]
        for pair in list(row.get("train") or []) + list(tests):
            grid = _normal(pair["input"])
            self.assertEqual(gen.self_check(grid), [])
            self.assertEqual(gen.rule_mirror(grid), _normal(pair["output"]))

    def test_all_exact_axis_boundaries_and_modes(self):
        for index, values in enumerate(
            product(
                (9, 14),
                (10, 14),
                (2, 6),
                (2, 4),
                gen.PALETTE_KINDS,
                gen.WALL_POSITIONS,
                gen.INTERACTION_MODES,
            )
        ):
            h, w, wall_size, n_blobs, palette_kind, wall_position, interaction_mode = values
            grid = gen.generate(
                1000 + index,
                2000 + index,
                difficulty="easy",
                grid_h=h,
                grid_w=w,
                wall_size=wall_size,
                n_blobs=n_blobs,
                palette_kind=palette_kind,
                wall_position=wall_position,
                interaction_mode=interaction_mode,
            )
            self.assertEqual(gen.self_check(grid), [])
            self.assertEqual(
                gen.observe_overrides(grid),
                {
                    "wall_size": wall_size,
                    "n_blobs": n_blobs,
                    "palette_kind": palette_kind,
                    "wall_position": wall_position,
                    "interaction_mode": interaction_mode,
                },
            )

    def test_determinism_fresh_returns_and_global_rng(self):
        random.seed(220680)
        before = random.getstate()
        first = gen.generate(17, 9, difficulty="medium")
        after = random.getstate()
        second = gen.generate(17, 9, difficulty="medium")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)
        self.assertNotEqual(second, gen.generate(18, 9, difficulty="medium"))
        self.assertNotEqual(second, gen.generate(17, 10, difficulty="medium"))

    def test_wall_only_and_stacking_branches_are_real(self):
        wall_only = gen.generate(
            41,
            7,
            grid_h=12,
            grid_w=12,
            wall_size=4,
            n_blobs=3,
            palette_kind="mixed",
            wall_position="center",
            interaction_mode="wall_only",
        )
        stacked = gen.generate(
            42,
            8,
            grid_h=12,
            grid_w=12,
            wall_size=4,
            n_blobs=3,
            palette_kind="mixed",
            wall_position="center",
            interaction_mode="wall_and_stack",
        )
        wall_analysis = gen._scene_analysis(wall_only)
        stack_analysis = gen._scene_analysis(stacked)
        self.assertTrue(wall_analysis["wall_supported"])
        self.assertTrue(wall_analysis["floor_supported"])
        self.assertFalse(wall_analysis["stacked"])
        self.assertTrue(stack_analysis["wall_supported"])
        self.assertTrue(stack_analysis["stacked"])
        self.assertNotEqual(wall_only, gen.rule_mirror(wall_only))
        self.assertNotEqual(stacked, gen.rule_mirror(stacked))

    def test_targeted_impostors_are_rejected(self):
        base = gen.generate(
            901,
            77,
            difficulty="hard",
            grid_h=14,
            grid_w=14,
            wall_size=5,
            n_blobs=4,
            palette_kind="mixed",
            wall_position="center",
            interaction_mode="wall_and_stack",
        )
        mutations = []

        broken_wall = copy.deepcopy(base)
        wall = sorted(gen._scene_analysis(base)["wall_cells"])
        broken_wall[wall[len(wall) // 2][0]][wall[len(wall) // 2][1]] = 0
        mutations.append(broken_wall)

        second_wall = copy.deepcopy(base)
        second_wall[-1][0] = 8
        mutations.append(second_wall)

        singleton_color = copy.deepcopy(base)
        color, cells = gen._scene_analysis(base)["blob_components"][0]
        for r, c in list(cells)[1:]:
            singleton_color[r][c] = 0
        mutations.append(singleton_color)

        already_on_floor = copy.deepcopy(base)
        color, cells = gen._scene_analysis(base)["blob_components"][-1]
        delta = len(base) - 1 - max(r for r, _ in cells)
        for r, c in cells:
            already_on_floor[r][c] = 0
        for r, c in cells:
            already_on_floor[r + delta][c] = color
        mutations.append(already_on_floor)

        no_wall_support = gen.generate(
            123,
            456,
            grid_h=12,
            grid_w=12,
            wall_size=4,
            n_blobs=2,
            palette_kind="low",
            wall_position="center",
            interaction_mode="wall_only",
        )
        analysis = gen._scene_analysis(no_wall_support)
        support_color = next(iter(analysis["wall_supported"]))
        shifted = copy.deepcopy(no_wall_support)
        support_cells = dict(analysis["blob_components"])[support_color]
        for r, c in support_cells:
            shifted[r][c] = 0
        for r, c in support_cells:
            shifted[r][0 if c > 1 else len(shifted[0]) - 1] = support_color
        mutations.append(shifted)

        for mutation in mutations:
            self.assertTrue(gen.self_check(mutation))

    def test_absent_feature_recombination_is_distribution_invalid(self):
        base = gen.generate(
            333,
            444,
            difficulty="medium",
            grid_h=12,
            grid_w=12,
            wall_size=4,
            n_blobs=3,
            palette_kind="low",
            wall_position="left",
            interaction_mode="wall_only",
        )
        existing = {value for row in base for value in row}
        replacement = next(color for color in range(1, 10) if color not in existing)
        recombined = copy.deepcopy(base)
        wall = gen._scene_analysis(base)["wall_cells"]
        for r, c in wall:
            recombined[r][c] = replacement
        self.assertTrue(gen.self_check(recombined))
        # The test mirror, like the canonical Racket rule, can still execute a
        # malformed recombination; non-crash does not make it a valid lesson.
        self.assertEqual(len(gen.rule_mirror(recombined)), len(recombined))

    def test_invalid_calls_reject_loudly(self):
        with self.assertRaises(TypeError):
            gen.generate(1, 1, unknown_axis=3)
        with self.assertRaises(ValueError):
            gen.generate(1, 1, difficulty="extreme")
        with self.assertRaises(ValueError):
            gen.generate(1, 1, grid_h=8)
        with self.assertRaises(ValueError):
            gen.generate(1, 1, interaction_mode="floor_only")


if __name__ == "__main__":
    unittest.main(verbosity=2)
