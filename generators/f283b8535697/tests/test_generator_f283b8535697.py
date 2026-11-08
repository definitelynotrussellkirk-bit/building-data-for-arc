from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f283b8535697 import generator


ROOT = Path(__file__).resolve().parents[1]


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return value


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                pairs = row.get(split) or []
                pairs = [pairs] if isinstance(pairs, dict) else pairs
                for pair in pairs:
                    yield _grid(pair["input"]), _grid(pair["output"])


class F283b8535697GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())
        cls.unique_inputs = {
            tuple(tuple(row) for row in grid): grid
            for grid, _ in cls.pairs
        }
        cls.official_profiles = {
            generator.canonical_profile_signature(grid)
            for grid in cls.unique_inputs.values()
        }

    def test_all_canonical_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 8)
        self.assertEqual(len(self.unique_inputs), 4)
        self.assertEqual(
            self.official_profiles,
            {
                (24, 24, 3, 0, 196, 99, "band_h", (6,), 4),
                (24, 24, 2, 2, 190, 252, "corner", (3,), 6),
                (24, 24, 2, 0, 246, 83, "band_v", (5,), 14),
                (24, 24, 3, 3, 176, 61, "band_v", (8,), 8),
            },
        )
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)

    def test_explicit_none_is_identical_and_unknown_texture_rejects(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                omitted = generator.generate(seed, seed, difficulty=band)
                explicit = generator.generate(
                    seed,
                    seed,
                    difficulty=band,
                    texture="none",
                )
                self.assertEqual(omitted, explicit)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(0, 0, texture="bogus")

    def test_dense_texture_records_truthful_exact_axis_provenance(self):
        for seed in range(40):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(
                    seed,
                    seed,
                    texture="dense_field",
                )
            finally:
                base.set_ctx_observer(None)
            drawn = captured[-1]._drawn
            observed = generator.observe_overrides(grid)
            self.assertEqual(drawn["grid_h"], len(grid))
            self.assertEqual(drawn["grid_w"], len(grid[0]))
            self.assertEqual(
                drawn["n_distinct_colors"],
                observed["n_distinct_colors"],
            )
            self.assertEqual(generator.self_check(grid), [])

    def test_minimum_canvas_preserves_requested_palette(self):
        historical_seeds = (1, 4, 7, 14, 26)
        for band in ("easy", "medium", "hard"):
            for seed in historical_seeds:
                grid = generator.generate(
                    seed,
                    seed,
                    difficulty=band,
                    grid_h=10,
                    grid_w=10,
                    n_distinct_colors=2,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid)["n_distinct_colors"],
                    2,
                )

    def test_archetype_prior_is_answer_bearing_and_stable(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                families = set()
                for offset in range(160):
                    seed = seed_start + offset
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                    )
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        families.add(generator._marker_family(grid))
                self.assertGreaterEqual(matches, 35)
                self.assertLessEqual(matches, 90)
                self.assertEqual(
                    families,
                    {"corner", "band_v", "band_h"},
                )

    def test_broad_input_profile_with_multicolor_answer_is_rejected(self):
        grid = [row[:] for row in next(iter(self.unique_inputs.values()))]
        original_output = generator.rule_mirror(grid)
        output_color = next(
            value for row in original_output for value in row if value != 0
        )
        alternate = next(
            value
            for row in grid
            for value in row
            if value not in (0, 1, output_color)
        )
        marker = generator._marker_cells(grid)
        r0 = min(r for r, _ in marker)
        c0 = min(c for _, c in marker)
        target = next(
            (r, c)
            for r in range(r0, r0 + 5)
            for c in range(c0, c0 + 5)
            if generator.rule_mirror(grid)[r - r0][c - c0] == output_color
        )
        h, w = len(grid), len(grid[0])
        orbit = {
            target,
            (target[0], w - 1 - target[1]),
            (h - 1 - target[0], target[1]),
            (h - 1 - target[0], w - 1 - target[1]),
        }
        for r, c in orbit:
            if grid[r][c] != 1:
                grid[r][c] = alternate
        self.assertEqual(generator.self_check(grid), [])
        signature = generator.canonical_profile_signature(grid)
        self.assertEqual(len(signature[7]), 2)
        self.assertFalse(generator.is_canonical_profile(grid))

    def test_self_check_rejects_structural_mutations(self):
        control = [row[:] for row in next(iter(self.unique_inputs.values()))]
        self.assertEqual(generator.self_check(control), [])

        no_marker = [
            [0 if value == 1 else value for value in row]
            for row in control
        ]
        self.assertTrue(generator.self_check(no_marker))

        marker_hole = [row[:] for row in control]
        marker_cell = generator._marker_cells(marker_hole)[0]
        marker_hole[marker_cell[0]][marker_cell[1]] = 0
        self.assertTrue(generator.self_check(marker_hole))

        asymmetric = [row[:] for row in control]
        changed = next(
            (r, c)
            for r, row in enumerate(asymmetric)
            for c, value in enumerate(row)
            if value == 0
            and asymmetric[r][len(row) - 1 - c] == 0
            and asymmetric[len(asymmetric) - 1 - r][c] == 0
        )
        asymmetric[changed[0]][changed[1]] = 2
        self.assertTrue(generator.self_check(asymmetric))

        odd_side = [row[:] for row in control[:-1]]
        self.assertTrue(generator.self_check(odd_side))

    def test_default_provenance_determinism_and_fresh_returns(self):
        state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    first = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                second = generator.generate(seed, seed, difficulty=band)
                self.assertEqual(first, second)
                self.assertEqual(captured[-1]._drawn["grid_h"], len(first))
                self.assertEqual(captured[-1]._drawn["grid_w"], len(first[0]))
                self.assertEqual(
                    captured[-1]._drawn["n_distinct_colors"],
                    generator.observe_overrides(first)["n_distinct_colors"],
                )
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                expected = second[0][0]
                first[0][0] = (first[0][0] + 1) % 10
                replay = generator.generate(seed, seed, difficulty=band)
                self.assertEqual(replay[0][0], expected)
        self.assertEqual(random.getstate(), state)


if __name__ == "__main__":
    unittest.main()
