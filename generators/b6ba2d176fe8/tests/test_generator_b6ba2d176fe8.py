"""Focused regressions for generator b6ba2d176fe8."""
from __future__ import annotations

import importlib
import json
import random
import unittest
from collections import Counter


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.b6ba2d176fe8.generator"
)


def signature(grid):
    rectangles = generator._ordered_rectangles(grid)
    assert rectangles is not None
    return (
        (len(grid), len(grid[0])),
        tuple(
            (
                rectangle["bbox"][2] - rectangle["bbox"][0] + 1,
                rectangle["bbox"][3] - rectangle["bbox"][1] + 1,
            )
            for rectangle in rectangles
        ),
        tuple(rectangle["bbox"][1] for rectangle in rectangles),
        all(rectangle["bbox"][2] == len(grid) - 1 for rectangle in rectangles),
    )


CANONICAL_SIGNATURES = {
    ((10, 10), ((4, 3), (2, 2), (2, 3)), (0, 4, 7), True),
    ((10, 10), ((3, 2), (2, 2), (2, 2), (4, 1)), (0, 3, 6, 9), True),
    ((10, 10), ((2, 4), (5, 1), (3, 3)), (0, 5, 7), True),
    ((10, 10), ((4, 1), (3, 2), (3, 1), (2, 2)), (0, 2, 5, 7), True),
}


def blank(height=12, width=20):
    return [[0] * width for _ in range(height)]


def rect(grid, row, col, height, width, color):
    for rr in range(row, row + height):
        for cc in range(col, col + width):
            grid[rr][cc] = color


class GeneratorB6ba2d176fe8Tests(unittest.TestCase):
    def test_rule_metadata_and_empirical_prior(self):
        self.assertEqual(generator.VERSION, "3.0.0")
        self.assertEqual(generator.RULE_HASH, "6e7e6d4cfafc")
        for band_index, band in enumerate(("easy", "medium", "hard")):
            counts = Counter()
            distinct = set()
            for offset in range(300):
                seed = 20_000 * band_index + offset
                grid = generator.generate(seed, seed * 31 + 7, difficulty=band)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                self.assertEqual(observed["canonical_prior"], signature(grid) in CANONICAL_SIGNATURES)
                if observed["canonical_prior"]:
                    counts[signature(grid)] += 1
                distinct.add(json.dumps(grid, separators=(",", ":")))
            self.assertEqual(set(counts), CANONICAL_SIGNATURES)
            self.assertGreaterEqual(sum(counts.values()), 65)
            self.assertLessEqual(sum(counts.values()), 115)
            self.assertGreaterEqual(len(distinct), 295)

    def test_exact_overrides_are_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for n_objects in (2, 6):
                for row_layout in generator.ROW_LAYOUTS:
                    for column_layout in generator.COLUMN_LAYOUTS:
                        grid = generator.generate(
                            77,
                            91,
                            difficulty=band,
                            canonical_prior=False,
                            n_objects=n_objects,
                            row_layout=row_layout,
                            column_layout=column_layout,
                        )
                        expected = {
                            "canonical_prior": False,
                            "n_objects": n_objects,
                            "row_layout": row_layout,
                            "column_layout": column_layout,
                        }
                        self.assertEqual(generator.observe_overrides(grid), expected)
                        self.assertEqual(
                            generator.self_check(grid, meta={"overrides": expected}),
                            [],
                        )

    def test_canonical_prior_and_incompatible_combinations_are_loud(self):
        for seed in range(24):
            grid = generator.generate(
                seed,
                seed * 17 + 3,
                canonical_prior=True,
            )
            observed = generator.observe_overrides(grid)
            self.assertTrue(observed["canonical_prior"])
            self.assertIn(signature(grid), CANONICAL_SIGNATURES)
            self.assertEqual(observed["row_layout"], "bottom")
            self.assertEqual(observed["column_layout"], "compact")
        for kwargs in (
            {"canonical_prior": True, "n_objects": 2},
            {"canonical_prior": True, "n_objects": 6},
            {"canonical_prior": True, "row_layout": "mixed"},
            {"canonical_prior": True, "column_layout": "spread"},
        ):
            with self.assertRaises(ValueError):
                generator.generate(3, 5, **kwargs)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=True)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_targeted_rule_hiding_mutations_are_rejected(self):
        mutations = []

        grid = blank()
        rect(grid, 8, 0, 2, 2, 1)
        rect(grid, 8, 3, 2, 2, 2)
        rect(grid, 8, 6, 2, 2, 3)
        mutations.append(grid)

        grid = blank(12, 24)
        for index, color in enumerate(range(1, 8)):
            rect(grid, 9, index * 3, 1, 2, color)
        mutations.append(grid)

        grid = blank()
        grid[8][0] = 1
        grid[8][2] = 2
        mutations.append(grid)

        grid = blank()
        rect(grid, 8, 0, 2, 2, 1)
        rect(grid, 8, 2, 3, 2, 2)
        rect(grid, 8, 5, 2, 3, 3)
        mutations.append(grid)

        grid = blank()
        rect(grid, 8, 0, 2, 2, 1)
        rect(grid, 8, 3, 2, 3, 2)
        rect(grid, 8, 7, 3, 2, 3)
        grid[8][7] = 0
        mutations.append(grid)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)
            self.assertEqual(generator.observe_overrides(mutation), {})

    def test_replay_freshness_and_process_rng_state(self):
        random.seed(918273)
        state_before = random.getstate()
        first = generator.generate(1234, 5678, difficulty="hard")
        state_after = random.getstate()
        second = generator.generate(1234, 5678, difficulty="hard")
        self.assertEqual(state_before, state_after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
