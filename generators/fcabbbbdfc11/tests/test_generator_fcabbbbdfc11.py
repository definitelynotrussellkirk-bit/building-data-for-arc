from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.fcabbbbdfc11 import generator


ROOT = Path(__file__).resolve().parents[1]


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                for pair in row.get(split) or []:
                    yield as_grid(pair["input"]), as_grid(pair["output"])


class Fcabbbbdfc11GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_have_linked_profiles_and_match_rule(self):
        self.assertEqual(len(self.pairs), 5)
        seen = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_linked_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            seen.add(generator.linked_profile_signature(grid))
        self.assertEqual(seen, generator._CANONICAL_LINKED_SIGNATURES)

    def test_linked_prior_is_substantive_and_stable(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                for offset in range(400):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    if generator.is_canonical_linked_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.linked_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 75)
                self.assertLessEqual(matches, 170)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_LINKED_SIGNATURES,
                )

    def test_profile_and_degenerate_paths_record_exact_axes(self):
        for band in ("easy", "medium", "hard"):
            checked = 0
            for seed in range(300):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                if not generator.is_canonical_linked_profile(grid):
                    continue
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                self.assertEqual(ctx._drawn["grid_h"], len(grid))
                self.assertEqual(ctx._drawn["grid_w"], len(grid[0]))
                for label, value in observed.items():
                    self.assertEqual(ctx._drawn[label], value)
                self.assertEqual(ctx._drawn["texture"], "none")
                checked += 1
            self.assertGreaterEqual(checked, 50)

        for texture in generator.DEGENERATE_TEXTURES:
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(3, 5, texture=texture)
            finally:
                base.set_ctx_observer(None)
            ctx = captured[-1]
            observed = generator.observe_overrides(grid)
            self.assertEqual(ctx._drawn["texture"], texture)
            self.assertEqual(ctx._drawn["grid_h"], len(grid))
            self.assertEqual(ctx._drawn["grid_w"], len(grid[0]))
            for label, value in observed.items():
                self.assertEqual(ctx._drawn[label], value)

    def test_explicit_none_palette_aliases_and_invalid_controls(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                self.assertEqual(
                    generator.generate(seed, seed, difficulty=band),
                    generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        texture="none",
                    ),
                )
        for kind in generator.PALETTE_KINDS:
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                generator.generate(7, 11, texture=kind)
            finally:
                base.set_ctx_observer(None)
            self.assertEqual(captured[-1]._drawn["texture"], kind)
            self.assertEqual(captured[-1]._drawn["palette_kind"], kind)

        bad_calls = (
            {"difficulty": "expert"},
            {"texture": "garbage"},
            {"palette_kind": "garbage"},
            {"bogus": 1},
            {"grid_h": "5"},
            {"grid_w": 12.0},
            {"n_colors": True},
            {"n_duplicates": "1"},
            {"texture": "warm", "palette_kind": "cool"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_checker_enforces_claimed_order_and_count_bounds(self):
        same_order = generator._draw_from_degenerate(
            "no_extras",
            base.gen_ctx(
                seed=0,
                sample_index=0,
                version=generator.VERSION,
                task_id=generator.TASK_ID,
                overrides={},
            ),
            random.Random(0),
        )
        same_order[0] = [0] * len(same_order[0])
        for column, color in zip((1, 3, 5), (2, 7, 4)):
            same_order[0][column] = color
        self.assertTrue(
            any("matches below reading order" in error
                for error in generator.self_check(same_order))
        )

        too_many_legend = [[0] * 12 for _ in range(5)]
        for index, color in enumerate(range(1, 7)):
            too_many_legend[0][index] = color
            too_many_legend[2 + index // 4][2 * (index % 4)] = color
        self.assertTrue(
            any("outside the declared 1..5" in error
                for error in generator.self_check(too_many_legend))
        )

        too_many_duplicates = [[0] * 12 for _ in range(5)]
        too_many_duplicates[0][1] = 2
        for r, c in ((2, 0), (2, 2), (4, 4), (4, 6)):
            too_many_duplicates[r][c] = 2
        self.assertTrue(
            any("duplicate count" in error
                for error in generator.self_check(too_many_duplicates))
        )

        too_many_distractors = [[0] * 12 for _ in range(5)]
        too_many_distractors[0][1] = 2
        for (r, c), color in zip(
            ((2, 0), (2, 2), (4, 4), (4, 6)),
            (2, 3, 4, 5),
        ):
            too_many_distractors[r][c] = color
        self.assertTrue(
            any("distractor count" in error
                for error in generator.self_check(too_many_distractors))
        )

    def test_duplicate_pieces_are_shape_distinguishable(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                grid = generator.generate(
                    seed,
                    seed,
                    difficulty=band,
                    n_colors=2,
                    n_duplicates=2,
                    n_distractors=0,
                )
                legend = set(value for value in grid[0] if value)
                by_color = {}
                for color, cells in generator._components(grid, 2):
                    if color in legend:
                        by_color.setdefault(color, []).append(
                            generator._normalize_shape(cells)
                        )
                for shapes in by_color.values():
                    if len(shapes) > 1:
                        self.assertEqual(len(shapes), len(set(shapes)))
                self.assertEqual(generator.self_check(grid), [])

    def test_lawful_cross_profile_role_recombination_is_not_canonical(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        for r in range(2, len(hybrid)):
            for c, value in enumerate(hybrid[r]):
                if value == 2:
                    hybrid[r][c] = 4
                elif value == 4:
                    hybrid[r][c] = 2
        hybrid[0] = [0] * len(hybrid[0])
        for column, color in zip((1, 3, 5), (2, 7, 4)):
            hybrid[0][column] = color

        self.assertEqual(generator.self_check(hybrid), [])
        self.assertIsNotNone(generator.rule_mirror(hybrid))
        self.assertFalse(generator.is_canonical_linked_profile(hybrid))
        self.assertNotIn(
            generator.linked_profile_signature(hybrid),
            generator._CANONICAL_LINKED_SIGNATURES,
        )

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 99
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
