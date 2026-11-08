"""Focused regression tests for generator 4295e17d5995."""
from __future__ import annotations

import copy
import importlib
import unittest
from pathlib import Path

from scripts.canonical_profile_gate import canonical_pairs

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.4295e17d5995.generator"
)
ROOT = Path(__file__).resolve().parents[1]


class MatchingWallGeneratorTests(unittest.TestCase):
    def test_python_rule_matches_every_canonical_pair(self) -> None:
        pairs = canonical_pairs(MODULE.TASK_ID)
        self.assertEqual(6, len(pairs))
        for pair in pairs:
            self.assertEqual(pair["output"], MODULE.rule_mirror(pair["input"]))

    def test_declared_override_boundaries_are_exact_and_observable(self) -> None:
        cases = {
            "grid_h": (9, 16),
            "grid_w": (9, 18),
            "left_objects": (1, 4),
            "right_objects": (1, 4),
            "palette_kind": MODULE.PALETTE_KINDS,
        }
        for band in ("easy", "medium", "hard"):
            for axis, values in cases.items():
                for value in values:
                    with self.subTest(band=band, axis=axis, value=value):
                        grid = MODULE.generate(31, 17, difficulty=band, **{axis: value})
                        self.assertEqual([], MODULE.self_check(grid))
                        self.assertEqual(value, MODULE.observe_overrides(grid)[axis])

    def test_minimum_canvas_supports_all_eight_objects_regression(self) -> None:
        grid = MODULE.generate(
            27,
            0,
            difficulty="easy",
            grid_h=9,
            grid_w=9,
            left_objects=4,
            right_objects=4,
        )
        self.assertEqual([], MODULE.self_check(grid))
        observed = MODULE.observe_overrides(grid)
        self.assertEqual(9, observed["grid_h"])
        self.assertEqual(9, observed["grid_w"])
        self.assertEqual(4, observed["left_objects"])
        self.assertEqual(4, observed["right_objects"])

    def test_unknown_override_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown override"):
            MODULE.generate(0, 0, typo_axis=3)

    def test_self_check_rejects_structural_mutations(self) -> None:
        grid = MODULE.generate(7, 7, difficulty="medium")
        mutations = []

        same_walls = copy.deepcopy(grid)
        for row in same_walls:
            row[-1] = row[0]
        mutations.append(same_walls)

        broken_wall = copy.deepcopy(grid)
        broken_wall[len(broken_wall) // 2][0] = 7
        mutations.append(broken_wall)

        foreign_color = copy.deepcopy(grid)
        foreign_color[0][2] = 0
        mutations.append(foreign_color)

        no_left_objects = copy.deepcopy(grid)
        left = no_left_objects[0][0]
        for r, row in enumerate(no_left_objects):
            for c in range(1, len(row) - 1):
                if no_left_objects[r][c] == left:
                    no_left_objects[r][c] = 7
        mutations.append(no_left_objects)

        for mutated in mutations:
            self.assertTrue(MODULE.self_check(mutated))

    def test_every_four_demo_window_falsifies_named_competitors(self) -> None:
        for seed in range(12):
            for start in range(12):
                demos = []
                for index in range(start, start + MODULE.EXAMPLES_NEEDED):
                    grid = MODULE.generate(seed, index, difficulty="medium")
                    demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
                query_grid = MODULE.generate(seed, start + MODULE.EXAMPLES_NEEDED, difficulty="medium")
                query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
                self.assertEqual([], MODULE.lesson_identifiable(demos, query))


if __name__ == "__main__":
    unittest.main()
