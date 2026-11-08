from __future__ import annotations

import copy
import importlib
import unittest


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.8bc2bc6a9bb8.generator"
)


class ShapeInventoryGeneratorTests(unittest.TestCase):
    def test_generated_scenes_are_lawful_and_deterministic(self):
        for difficulty in (None, "easy", "medium", "hard"):
            for sample_index in range(12):
                first = GEN.generate(37, sample_index, difficulty=difficulty)
                second = GEN.generate(37, sample_index, difficulty=difficulty)
                self.assertEqual(first, second)
                self.assertEqual([], GEN.self_check(first))
                self.assertEqual(first, copy.deepcopy(first))

    def test_every_declared_override_extreme_is_realized(self):
        cases = (
            {"grid_h": 7},
            {"grid_h": 12},
            {"grid_w": 10},
            {"grid_w": 16},
            {"n": 2},
            {"n": 4},
            {"grid_h": 7, "grid_w": 10, "n": 4},
            {"grid_h": 12, "grid_w": 16, "n": 2},
        )
        for index, overrides in enumerate(cases):
            grid = GEN.generate(91, index, difficulty="hard", **overrides)
            observed = GEN.observe_overrides(grid)
            for axis, expected in overrides.items():
                self.assertEqual(expected, observed[axis])

    def test_unknown_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(1, 0, typo_axis=3)

    def test_self_check_rejects_minimal_impostors(self):
        impostors = (
            [[0] * 10 for _ in range(7)],
            [[1] * 10 for _ in range(7)],
            [[0] * 10 for _ in range(6)] + [[8] * 10],
        )
        for grid in impostors:
            self.assertTrue(GEN.self_check(grid))

    def test_four_profile_lesson_kills_declared_competitors(self):
        demos = []
        for sample_index in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(123, sample_index)
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(123, GEN.EXAMPLES_NEEDED)
        self.assertEqual(
            [],
            GEN.lesson_identifiable(
                demos,
                {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
            ),
        )

    def test_footprint_rank_shortcut_is_constructively_refuted(self):
        grids = [GEN.generate(223, index) for index in range(GEN.EXAMPLES_NEEDED)]
        self.assertIn("footprint_then_area", GEN.SEMANTIC_RIVALS)
        conflicts = [
            grid
            for grid in grids
            if GEN.semantic_observables(grid).get("footprint_order_conflict")
        ]
        self.assertTrue(conflicts, "the fixed lesson must include an area/footprint reversal")
        for grid in conflicts:
            observables = GEN.semantic_observables(grid)
            self.assertNotEqual(
                observables["sorted_sizes"], observables["footprint_sorted_sizes"]
            )
            self.assertNotEqual(
                GEN.rule_mirror(grid), GEN.SEMANTIC_RIVALS["footprint_then_area"](grid)
            )

        demos = [
            {"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids
        ]
        query_grid = GEN.generate(223, GEN.EXAMPLES_NEEDED)
        self.assertEqual(
            [],
            GEN.lesson_identifiable(
                demos,
                {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
            ),
        )

    def test_named_witnesses_fire_over_one_schedule_cycle(self):
        grids = [GEN.generate(222, index) for index in range(4)]
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            self.assertTrue(any(witness(grid) for grid in grids), name)


if __name__ == "__main__":
    unittest.main()
