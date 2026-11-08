"""Focused semantic and regression tests for zone last-non-zero compression."""
from __future__ import annotations

import copy
import importlib
import random
import unittest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.9df67b512dad.generator"
)


class ZoneLastNonzeroGeneratorTests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_pairs(self):
        self.assertEqual(gen.RULE_HASH, "574840a0b71b")
        pairs = canonical_pairs(gen.TASK_ID)
        self.assertEqual(len(pairs), 6)
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            self.assertEqual(gen.self_check(pair["input"]), [])
            self.assertEqual(gen.strict_canonical_like(pair["input"]), [])
            self.assertEqual(gen.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(pair["input"], before)

    def test_exact_override_boundaries_are_observable(self):
        for height in (5, 14):
            for width in (7, 16):
                for palette_size in (1, 3):
                    for pattern in gen.SCHEDULE_PROFILES:
                        grid = gen.generate(
                            3127,
                            44,
                            difficulty="hard",
                            grid_h=height,
                            grid_w=width,
                            palette_size=palette_size,
                            zone_pattern=pattern,
                        )
                        self.assertEqual(gen.self_check(grid), [])
                        self.assertEqual(
                            gen.observe_overrides(grid),
                            {
                                "grid_h": height,
                                "grid_w": width,
                                "palette_size": palette_size,
                                "zone_pattern": pattern,
                            },
                        )
        with self.assertRaises(TypeError):
            gen.generate(1, 0, misspelled_axis=7)
        with self.assertRaises(ValueError):
            gen.generate(1, 0, difficulty="expert")
        with self.assertRaises(ValueError):
            gen.generate(1, 0, grid_h=4)

    def test_every_four_demo_window_covers_masks_and_kills_rivals(self):
        for band in ("easy", "medium", "hard"):
            for start in range(20):
                demos = []
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(8801, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    8801, start + gen.EXAMPLES_NEEDED, difficulty=band
                )
                query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
                self.assertEqual(gen.lesson_identifiable(demos, query), [])
                self.assertEqual(
                    {gen.observe_overrides(pair["input"])["zone_pattern"] for pair in demos},
                    set(gen.SCHEDULE_PROFILES),
                )
                for rival in gen.LESSON_COMPETITORS.values():
                    self.assertTrue(
                        any(rival(pair["input"]) != pair["output"] for pair in demos)
                    )

    def test_multicolor_draws_expose_row_major_last_value(self):
        for pattern in gen.SCHEDULE_PROFILES:
            grid = gen.generate(
                773,
                7,
                difficulty="medium",
                palette_size=3,
                zone_pattern=pattern,
            )
            analysis = gen._analyse(grid)
            self.assertEqual(analysis["errors"], [])
            conflicts = [
                values
                for zone_index, values in enumerate(analysis["zone_values"])
                if zone_index not in (0, 2, 6, 8) and values
            ]
            self.assertTrue(conflicts)
            self.assertTrue(all(values[0] != values[-1] for values in conflicts))
            self.assertNotEqual(gen._rival_first_nonzero(grid), gen.rule_mirror(grid))
            self.assertNotEqual(
                gen._rival_occupancy_global_first(grid), gen.rule_mirror(grid)
            )

    def test_structural_impostors_and_negative_recombination_are_rejected(self):
        for name, grid in gen.mutation_fixtures():
            self.assertTrue(gen.self_check(grid), name)

        grid = gen.generate(512, 2, difficulty="medium", palette_size=2)
        used = {value for row in grid for value in row if value}
        replacement = next(value for value in range(1, 10) if value not in used)
        recombined = copy.deepcopy(grid)
        analysis = gen._analyse(grid)
        empty_zones = [
            index for index, values in enumerate(analysis["zone_values"]) if not values
        ]
        self.assertEqual(len(empty_zones), 2)
        for empty_zone in empty_zones:
            row, col = analysis["zones"][empty_zone][0]
            recombined[row][col] = replacement
        self.assertNotIn(replacement, used)
        self.assertTrue(gen.self_check(recombined))
        # The Racket/Python oracle remains total on the malformed curriculum row.
        self.assertEqual(len(gen.rule_mirror(recombined)), 3)

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(20260727)
        before = random.getstate()
        first = gen.generate(99, 17, difficulty="hard")
        middle = random.getstate()
        second = gen.generate(99, 17, difficulty="hard")
        after = random.getstate()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
