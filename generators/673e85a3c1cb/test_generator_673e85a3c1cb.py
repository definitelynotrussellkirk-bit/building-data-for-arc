"""Focused regression tests for generator 673e85a3c1cb."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

gen = importlib.import_module(
    "puzzle_generators.per_puzzle.673e85a3c1cb.generator"
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
        pairs = list(row["train"]) + [row["test"]]
        for pair in pairs:
            grid = _normal(pair["input"])
            self.assertEqual(gen.self_check(grid), [])
            self.assertEqual(gen.rule_mirror(grid), _normal(pair["output"]))

    def test_every_exact_axis_boundary_and_command(self):
        for grid_size in (7, 11):
            for palette_size in (1, 3):
                for occupancy in ("sparse", "balanced", "dense"):
                    for index, command in enumerate(gen._COMMANDS):
                        grid = gen.generate(
                            1000 + index,
                            2000 + grid_size + palette_size,
                            difficulty="easy",
                            grid_size=grid_size,
                            palette_size=palette_size,
                            occupancy=occupancy,
                            command=command,
                        )
                        self.assertEqual(gen.self_check(grid), [])
                        self.assertEqual(
                            gen.observe_overrides(grid),
                            {
                                "grid_size": grid_size,
                                "command": command,
                                "palette_size": palette_size,
                                "occupancy": occupancy,
                            },
                        )

    def test_determinism_fresh_returns_and_global_rng(self):
        random.seed(67385)
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
        self.assertNotEqual(
            second,
            gen.generate(18, 9, difficulty="medium"),
        )
        self.assertNotEqual(
            second,
            gen.generate(17, 10, difficulty="medium"),
        )

    def test_targeted_impostors_are_rejected(self):
        base = gen.generate(
            901,
            77,
            difficulty="hard",
            grid_size=11,
            palette_size=2,
            occupancy="balanced",
            command="cw",
        )
        q = len(base) // 2
        mutations = []

        broken_cross = copy.deepcopy(base)
        broken_cross[q][0] = 0
        mutations.append(broken_cross)

        occupied_answer_panel = copy.deepcopy(base)
        occupied_answer_panel[q + 1][q + 1] = 7
        mutations.append(occupied_answer_panel)

        unrelated_top_right = copy.deepcopy(base)
        unrelated_top_right[0][q + 1] = 8
        mutations.append(unrelated_top_right)

        ambiguous_top = copy.deepcopy(base)
        for row in range(q):
            ambiguous_top[row][q + 1 :] = ambiguous_top[row][:q]
        mutations.append(ambiguous_top)

        palette_mismatch = copy.deepcopy(base)
        bottom_color = next(
            palette_mismatch[row][column]
            for row in range(q + 1, len(base))
            for column in range(q)
            if palette_mismatch[row][column] not in (0, 9)
        )
        for row in range(q + 1, len(base)):
            for column in range(q):
                if palette_mismatch[row][column] == bottom_color:
                    palette_mismatch[row][column] = 8 if bottom_color != 8 else 7
        mutations.append(palette_mismatch)

        copyable_bottom = copy.deepcopy(base)
        for row in range(q):
            copyable_bottom[q + 1 + row][:q] = copyable_bottom[row][:q]
        mutations.append(copyable_bottom)

        for mutation in mutations:
            self.assertTrue(gen.self_check(mutation))

    def test_absent_feature_recombination_is_distribution_invalid(self):
        base = gen.generate(
            333,
            444,
            difficulty="medium",
            grid_size=9,
            palette_size=1,
            occupancy="balanced",
            command="anti",
        )
        q = len(base) // 2
        existing = {
            value
            for row in base
            for value in row
            if value not in (0, 9)
        }
        replacement_color = next(color for color in range(1, 9) if color not in existing)
        recombined = copy.deepcopy(base)
        for row in range(q):
            for column in range(q + 1, len(base)):
                recombined[row][column] = 0
        recombined[0][q + 1] = replacement_color
        self.assertTrue(gen.self_check(recombined))

    def test_invalid_calls_reject_loudly(self):
        with self.assertRaises(TypeError):
            gen.generate(1, 1, unknown_axis=3)
        with self.assertRaises(ValueError):
            gen.generate(1, 1, difficulty="extreme")
        with self.assertRaises(ValueError):
            gen.generate(1, 1, grid_size=8)
        with self.assertRaises(ValueError):
            gen.generate(1, 1, command="ccw")


if __name__ == "__main__":
    unittest.main(verbosity=2)
