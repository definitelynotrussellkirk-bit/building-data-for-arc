from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f4a707214fb5 import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                for pair in row.get(split) or []:
                    yield pair["input"], pair["output"]


class F4a707214fb5GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_have_complete_profiles_and_match_rule(self):
        self.assertEqual(len(self.pairs), 4)
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)

    def test_full_pair_prior_is_substantive_and_stable(self):
        expected_dims = {(25, 25), (23, 25), (22, 22), (24, 25)}
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                dims = set()
                for offset in range(400):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        dims.add((len(grid), len(grid[0])))
                self.assertGreaterEqual(matches, 80)
                self.assertLessEqual(matches, 180)
                self.assertEqual(dims, expected_dims)

    def test_profile_path_records_every_exact_axis_truthfully(self):
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
                if not generator.is_canonical_profile(grid):
                    continue
                observed = generator.observe_overrides(grid)
                ctx = captured[-1]
                self.assertEqual(ctx._drawn["grid_h"], len(grid))
                self.assertEqual(ctx._drawn["grid_w"], len(grid[0]))
                for label in (
                    "figure_height",
                    "figure_width",
                    "n_diff_rows",
                    "n_colors",
                ):
                    self.assertEqual(ctx._drawn[label], observed[label])
                checked += 1
            self.assertGreaterEqual(checked, 50)

    def test_explicit_none_is_omission_and_invalid_controls_reject(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                self.assertEqual(
                    generator.generate(seed, seed, difficulty=band),
                    generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        texture="none",
                    ),
                )
        bad_calls = (
            {"difficulty": "expert"},
            {"texture": "garbage"},
            {"bogus": 1},
            {"grid_h": "20"},
            {"grid_w": 20.0},
            {"figure_height": True},
            {"n_diff_rows": "2"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_named_textures_remain_generalized_and_lawful(self):
        for texture in generator.DEGENERATE_TEXTURES:
            for band in ("easy", "medium", "hard"):
                for seed in range(40):
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        texture=texture,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertFalse(generator.is_canonical_profile(grid))
                    self.assertTrue(generator.rule_mirror(grid))

    def test_min_diff_records_its_forced_axis_and_checker_caps_row_marks(self):
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                7,
                11,
                texture="min_diff",
                n_diff_rows=1,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(captured[-1]._drawn["n_diff_rows"], 1)
        self.assertEqual(captured[-1]._override_used["n_diff_rows"], 1)
        self.assertEqual(generator.observe_overrides(grid)["n_diff_rows"], 1)
        with self.assertRaisesRegex(ValueError, "n_diff_rows"):
            generator.generate(
                7,
                11,
                texture="min_diff",
                n_diff_rows=2,
            )

        impostor = [[0] * 21 for _ in range(20)]
        for r in range(1, 7):
            for c in range(10):
                impostor[r][c] = 1 + r % 2
            for c in range(11, 21):
                impostor[r][c] = 1 + r % 2
        for c in range(12, 20):
            impostor[3][c] = 0
        self.assertTrue(
            any("7-mark maximum" in err
                for err in generator.self_check(impostor))
        )

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(7123)
        state = random.getstate()
        first = generator.generate(17, 29, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(17, 29, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 99
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
