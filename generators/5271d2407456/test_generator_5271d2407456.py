"""Focused regression tests for generator 5271d2407456."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(MODULE_ROOT))

import generator as gen  # noqa: E402


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _normal(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


class GeneratorRegressionTests(unittest.TestCase):
    def test_rule_hash_pin_and_public_rule_mirror(self):
        row = _canonical_row()
        actual = hashlib.sha256(
            " ".join(row["program_solution"].split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(gen.RULE_HASH, actual)
        pairs = list(row["train"]) + [row["test"]]
        for pair in pairs:
            self.assertEqual(
                gen.rule_mirror(_normal(pair["input"])),
                _normal(pair["output"]),
            )

    def test_every_layout_and_boundary_override_is_exact(self):
        for height in (9, 14):
            for width in (12, 16):
                for index, layout in enumerate(gen.LAYOUTS):
                    grid = gen.generate(
                        2000 + index,
                        index,
                        difficulty="hard",
                        grid_h=height,
                        grid_w=width,
                        layout=layout,
                    )
                    self.assertEqual(gen.self_check(grid), [])
                    self.assertEqual(
                        gen.observe_overrides(grid),
                        {"grid_h": height, "grid_w": width, "layout": layout},
                    )
                    self.assertNotEqual(gen.rule_mirror(grid), grid)

    def test_determinism_fresh_returns_and_global_rng(self):
        random.seed(741)
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

        keyed = {
            "grid_h": 12,
            "grid_w": 15,
            "layout": "staggered_vertical_4",
        }
        baseline = gen.generate(170, 90, difficulty="medium", **keyed)
        self.assertNotEqual(
            baseline, gen.generate(171, 90, difficulty="medium", **keyed)
        )
        self.assertNotEqual(
            baseline, gen.generate(170, 91, difficulty="medium", **keyed)
        )

    def test_default_prior_reaches_every_canonical_wall_profile(self):
        seen = set()
        canonical_draws = 0
        for seed in range(600):
            grid = gen.generate(seed, seed + 1000, difficulty="medium")
            profile = gen._analyze_scene(grid)["canonical_profile"]
            if profile is not None:
                seen.add(profile)
                canonical_draws += 1
        self.assertEqual(
            seen,
            {str(profile["name"]) for profile in gen._CANONICAL_PROFILES},
        )
        self.assertGreaterEqual(canonical_draws, 120)
        self.assertLessEqual(canonical_draws, 240)

    def test_targeted_impostors_are_rejected(self):
        base = gen.generate(
            999,
            1,
            difficulty="hard",
            layout="cross_4",
            grid_h=12,
            grid_w=14,
        )
        analysis = gen._analyze_scene(base)
        self.assertEqual(analysis["errors"], [])
        seeds = [
            (room_index, *seed)
            for room_index, room in enumerate(analysis["chambers"])
            for seed in room["seeds"]
        ]
        mutations = []

        missing = copy.deepcopy(base)
        _, row, column, _ = seeds[0]
        missing[row][column] = 0
        mutations.append(missing)

        double = copy.deepcopy(base)
        source_room, row, column, color = seeds[0]
        target_room = analysis["chambers"][seeds[1][0]]
        destination = target_room["zeros"][0]
        double[row][column] = 0
        double[destination[0]][destination[1]] = color
        mutations.append(double)

        broken = copy.deepcopy(base)
        wall = next(
            (row, column)
            for row in range(2, len(base) - 2)
            for column in range(2, len(base[0]) - 2)
            if base[row][column] == 8
        )
        broken[wall[0]][wall[1]] = 0
        mutations.append(broken)

        stray = copy.deepcopy(base)
        zero = analysis["chambers"][0]["zeros"][0]
        stray[zero[0]][zero[1]] = 8
        mutations.append(stray)

        exterior = copy.deepcopy(base)
        exterior[0][0] = 8
        mutations.append(exterior)

        duplicate = copy.deepcopy(base)
        _, row, column, _ = seeds[1]
        duplicate[row][column] = seeds[0][3]
        mutations.append(duplicate)

        for mutation in mutations:
            self.assertTrue(gen.self_check(mutation))

    def test_invalid_calls_reject_loudly(self):
        with self.assertRaises(TypeError):
            gen.generate(1, 1, unknown_axis=3)
        with self.assertRaises(ValueError):
            gen.generate(1, 1, difficulty="extreme")
        with self.assertRaises(ValueError):
            gen.generate(1, 1, grid_h=8)
        with self.assertRaises(ValueError):
            gen.generate(1, 1, layout="not_a_layout")


if __name__ == "__main__":
    unittest.main(verbosity=2)
