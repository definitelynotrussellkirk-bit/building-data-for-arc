from __future__ import annotations

import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.e84a374b51f2 import generator


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
                value = row.get(split)
                pairs = value if isinstance(value, list) else [value]
                for pair in pairs:
                    if pair:
                        yield as_grid(pair["input"]), as_grid(pair["output"])


class E84a374b51f2GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_profiles(self):
        self.assertEqual(len(self.pairs), 4)
        profiles = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            profiles.add(generator.canonical_profile_signature(grid))
        self.assertEqual(profiles, generator._CANONICAL_WIDTHS)

    def test_each_band_covers_every_public_width_on_two_ranges(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                widths = Counter()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    widths[len(grid[0])] += 1
                self.assertEqual(
                    set(widths),
                    set(generator._BAND_WIDTHS[band]),
                )
                self.assertTrue(
                    generator._CANONICAL_WIDTHS <= set(widths)
                )
                self.assertGreaterEqual(
                    sum(widths[n] for n in generator._CANONICAL_WIDTHS),
                    150,
                )

    def test_all_lawful_widths_execute_exact_formula(self):
        outputs = set()
        for n in generator._ODD_WIDTHS:
            grid = generator.generate(
                n,
                n * 11,
                difficulty="easy",
                grid_n=n,
            )
            self.assertEqual(generator.observe_overrides(grid), {"grid_n": n})
            output = generator.rule_mirror(grid)
            self.assertEqual((len(output), len(output[0])), (n, n))
            self.assertEqual(output[0][n // 2], 2)
            outputs.add(tuple(map(tuple, output)))
        self.assertEqual(len(outputs), generator.EXPECTED_OUTPUT_CODOMAIN)

    def test_v_and_stripe_geometry(self):
        for n in generator._ODD_WIDTHS:
            output = generator.rule_mirror(
                generator.generate(1, n, grid_n=n)
            )
            mid = n // 2
            for r, row in enumerate(output):
                for c, value in enumerate(row):
                    on_v = (
                        r <= mid
                        and c in (mid - r, mid + r)
                    )
                    on_stripe = (
                        r >= 3
                        and c % 4 == (r + mid) % 4
                        and (
                            r > mid
                            or mid - r < c < mid + r
                        )
                    )
                    expected = 2 if on_v else 1 if on_stripe else 0
                    self.assertEqual(value, expected)

    def test_boundaries_and_strict_controls(self):
        for n in (5, 29):
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(
                    17,
                    23,
                    difficulty=band,
                    grid_n=n,
                )
                self.assertEqual(generator.observe_overrides(grid), {"grid_n": n})

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"texture": "empty_row"},
            {"grid_n": "5"},
            {"grid_n": 5.0},
            {"grid_n": True},
            {"grid_n": 3},
            {"grid_n": 6},
            {"grid_n": 30},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_default_and_forced_paths_record_exact_provenance(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(120):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 23 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                self.assertEqual(
                    captured[-1]._drawn,
                    generator.observe_overrides(grid),
                )

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            forced = generator.generate(9, 11, grid_n=29)
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(captured[-1]._drawn, {"grid_n": 29})
        self.assertEqual(captured[-1]._override_used, {"grid_n": 29})
        self.assertEqual(generator.observe_overrides(forced), {"grid_n": 29})

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(1, 2, grid_n=13)
        mutations = []

        two_rows = [valid[0][:], valid[0][:]]
        mutations.append(two_rows)

        even = [[0] * 6]
        even[0][3] = 2
        mutations.append(even)

        off_center = [valid[0][:]]
        off_center[0][6] = 0
        off_center[0][5] = 2
        mutations.append(off_center)

        extra = [valid[0][:]]
        extra[0][0] = 2
        mutations.append(extra)

        decoy = [valid[0][:]]
        decoy[0][0] = 7
        mutations.append(decoy)

        bad_color = [valid[0][:]]
        bad_color[0][0] = 10
        mutations.append(bad_color)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_nearest_nonpublic_profile_is_lawful_but_not_canonical(self):
        grid = generator.generate(5, 7, grid_n=9)
        self.assertEqual(generator.self_check(grid), [])
        self.assertIsNone(generator.canonical_profile_signature(grid))
        self.assertFalse(generator.is_canonical_profile(grid))
        self.assertEqual(len(generator.rule_mirror(grid)), 9)

    def test_bands_are_ordered_and_each_support_eight_outputs(self):
        means = {}
        for band in ("easy", "medium", "hard"):
            widths = [
                len(
                    generator.generate(
                        seed,
                        seed * 31 + 3,
                        difficulty=band,
                    )[0]
                )
                for seed in range(600)
            ]
            means[band] = sum(widths) / len(widths)
            self.assertGreaterEqual(len(set(widths)), 8)
        self.assertLess(means["easy"], means["medium"])
        self.assertLess(means["medium"], means["hard"])

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
