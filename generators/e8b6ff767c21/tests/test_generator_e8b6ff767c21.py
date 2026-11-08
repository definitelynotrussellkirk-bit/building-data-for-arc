from __future__ import annotations

import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from reviewer_support import canonical_pairs as reviewed_canonical_pairs, find_root
from puzzle_generators.per_puzzle.e8b6ff767c21 import generator


ROOT = find_root(__file__)


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    for pair in reviewed_canonical_pairs(
        generator.TASK_ID,
        root=ROOT,
        labeled_only=True,
    ):
        yield pair["input"], pair["output"]



class E8b6ff767c21GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 6)
        profiles = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            profiles.add(generator.canonical_profile_signature(grid))
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_complete_profile_prior_is_stable_on_two_ranges(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                shapes = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    shapes.add((len(grid), len(grid[0])))
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 45)
                self.assertLessEqual(matches, 120)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(shapes), 95)

    def test_all_lawful_shapes_execute_and_exhaust_codomain(self):
        outputs = set()
        for height in range(5, 29):
            for width in range(5, 29):
                grid = generator.generate(
                    height * 31 + width,
                    width * 37 + height,
                    grid_h=height,
                    grid_w=width,
                )
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"grid_h": height, "grid_w": width},
                )
                output = generator.rule_mirror(grid)
                self.assertEqual(
                    (len(output), len(output[0])),
                    (height, width),
                )
                self.assertEqual(output[0][0], 3)
                outputs.add(tuple(map(tuple, output)))
        self.assertEqual(
            len(outputs),
            generator.EXPECTED_OUTPUT_CODOMAIN,
        )

    def test_spiral_geometry_has_openings_between_successive_turns(self):
        for height, width in ((5, 5), (6, 8), (9, 14), (18, 18), (28, 21)):
            output = generator.rule_mirror(
                generator.generate(
                    1,
                    2,
                    grid_h=height,
                    grid_w=width,
                )
            )
            self.assertTrue(all(value == 3 for value in output[0]))
            self.assertTrue(all(row[-1] == 3 for row in output))
            self.assertTrue(all(value in (0, 3) for row in output for value in row))
            if height >= 6 and width >= 6:
                self.assertEqual(output[1][0], 0)
                self.assertEqual(output[1][-1], 3)
                self.assertEqual(output[2][0], 3)
                self.assertEqual(output[2][1], 3)
                self.assertEqual(output[2][-2], 0)

    def test_lawful_cross_profile_rectangle_is_not_canonical(self):
        grid = generator.generate(1, 2, grid_h=6, grid_w=8)
        self.assertEqual(generator.self_check(grid), [])
        self.assertEqual(generator.observe_overrides(grid), {
            "grid_h": 6,
            "grid_w": 8,
        })
        self.assertIsNone(generator.canonical_profile_signature(grid))
        self.assertFalse(generator.is_canonical_profile(grid))
        self.assertEqual(
            (len(generator.rule_mirror(grid)), len(generator.rule_mirror(grid)[0])),
            (6, 8),
        )

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 5},
            {"grid_h": 28},
            {"grid_w": 5},
            {"grid_w": 28},
            {"grid_h": 5, "grid_w": 5},
            {"grid_h": 5, "grid_w": 28},
            {"grid_h": 28, "grid_w": 5},
            {"grid_h": 28, "grid_w": 28},
        )
        for kwargs in boundary_calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(17, 23, difficulty=band, **kwargs)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                for key, value in kwargs.items():
                    self.assertEqual(observed[key], value)

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "5"},
            {"grid_w": 5.0},
            {"grid_h": True},
            {"grid_h": 4},
            {"grid_h": 29},
            {"grid_w": 4},
            {"grid_w": 29},
            {"grid_n": 6},
            {"texture": "single_cell"},
            {"include_decoy": True},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_profile_default_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 41 + 3,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 50)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=28,
                grid_w=5,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            {"grid_h": 28, "grid_w": 5},
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"grid_h": 28, "grid_w": 5},
        )
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )

    def test_self_check_rejects_content_and_shape_impostors(self):
        valid = generator.generate(1, 2, grid_h=8, grid_w=10)
        mutations = []

        nonblank = [row[:] for row in valid]
        nonblank[3][4] = 3
        mutations.append(nonblank)

        decoy = [row[:] for row in valid]
        decoy[3][4] = 7
        mutations.append(decoy)

        bad_color = [row[:] for row in valid]
        bad_color[3][4] = 10
        mutations.append(bad_color)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        mutations.append([[0] * 4 for _ in range(5)])
        mutations.append([[0] * 5 for _ in range(4)])
        mutations.append([[0] * 29 for _ in range(5)])
        mutations.append([[0] * 5 for _ in range(29)])

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_are_ordered_and_rectangles_are_dominant(self):
        means = {}
        for band in ("easy", "medium", "hard"):
            areas = []
            squares = 0
            shapes = Counter()
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                height = len(grid)
                width = len(grid[0])
                areas.append(height * width)
                squares += height == width
                shapes[(height, width)] += 1
            means[band] = sum(areas) / len(areas)
            self.assertGreaterEqual(len(shapes), 95)
            self.assertLess(squares, 180)
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
