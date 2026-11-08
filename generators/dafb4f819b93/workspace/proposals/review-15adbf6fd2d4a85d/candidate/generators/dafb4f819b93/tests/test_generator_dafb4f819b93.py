from __future__ import annotations

import random
import unittest

from puzzle_generators import base
from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    find_root,
    load_selected_generator,
)


TASK_ID = "dafb4f819b93"
ROOT = find_root(__file__)
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    for pair in load_canonical_pairs(
        generator.TASK_ID, root=ROOT, labeled_only=True
    ):
        yield as_grid(pair["input"]), as_grid(pair["output"])


class Dafb4f819b93GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 4)
        profiles = set()
        relations = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            profiles.add(generator.canonical_profile_signature(grid))
            relations.add(generator.observe_overrides(grid)["border_relation"])
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(relations, {"matched", "different"})

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                inputs = set()
                outputs = set()
                for offset in range(500):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    inputs.add(tuple(map(tuple, grid)))
                    outputs.add(
                        tuple(map(tuple, generator.rule_mirror(grid)))
                    )
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 20)
                self.assertLessEqual(matches, 65)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 430)
                self.assertGreaterEqual(len(outputs), 430)

    def test_general_path_witnesses_every_axis_and_relation(self):
        sizes = set()
        color_counts = set()
        relations = set()
        run_pairs = set()
        for n in (8, 14):
            for n_colors in (4, 6):
                for relation in ("matched", "different"):
                    for seed in range(10):
                        grid = generator.generate(
                            seed,
                            seed * 31 + n + n_colors,
                            difficulty="hard",
                            grid_n=n,
                            n_colors=n_colors,
                            border_relation=relation,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        observed = generator.observe_overrides(grid)
                        self.assertEqual(observed["grid_n"], n)
                        self.assertEqual(observed["n_colors"], n_colors)
                        self.assertEqual(
                            observed["border_relation"],
                            relation,
                        )
                        scene = generator._analyze_scene(grid)
                        sizes.add(scene["n"])
                        color_counts.add(scene["n_colors"])
                        relations.add(scene["border_relation"])
                        run_pairs.add(
                            (
                                scene["right_lengths"],
                                scene["bottom_lengths"],
                            )
                        )
        self.assertEqual(sizes, {8, 14})
        self.assertEqual(color_counts, {4, 6})
        self.assertEqual(relations, {"matched", "different"})
        self.assertGreater(len(run_pairs), 30)

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_n": 8},
            {"grid_n": 14},
            {"n_colors": 4},
            {"n_colors": 6},
            {"border_relation": "matched"},
            {"border_relation": "different"},
            {
                "grid_n": 8,
                "n_colors": 6,
                "border_relation": "different",
            },
            {
                "grid_n": 14,
                "n_colors": 4,
                "border_relation": "matched",
            },
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
            {"grid_n": "10"},
            {"grid_n": True},
            {"n_colors": 4.0},
            {"border_relation": 1},
            {"grid_n": 7},
            {"grid_n": 15},
            {"n_colors": 3},
            {"n_colors": 7},
            {"border_relation": "independent"},
            {"texture": "all_zero"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_profile_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
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
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx.axis_value(key), observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 30)

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]

        interior = [row[:] for row in original]
        interior[0][0] = 5
        self.assertTrue(
            any(
                "background zero" in error
                for error in generator.self_check(interior)
            )
        )

        zero_border = [row[:] for row in original]
        zero_border[0][-1] = 0
        self.assertTrue(
            any(
                "entirely nonzero" in error
                for error in generator.self_check(zero_border)
            )
        )

        wrong_order = [row[:] for row in original]
        wrong_order[-1][0] = 2
        self.assertTrue(
            any(
                "same ordered" in error
                for error in generator.self_check(wrong_order)
            )
        )

        repeated_color = [row[:] for row in original]
        repeated_color[-1][3] = 5
        self.assertTrue(
            any(
                "contiguous run" in error
                for error in generator.self_check(repeated_color)
            )
        )

        non_square = [row[:-1] for row in original]
        self.assertTrue(generator.self_check(non_square))

        invalid_color = [row[:] for row in original]
        invalid_color[0][-1] = 10
        self.assertTrue(
            any(
                "ARC colors" in error
                for error in generator.self_check(invalid_color)
            )
        )

    def test_swapped_asymmetric_borders_are_lawful_but_not_canonical(self):
        grid, _ = self.pairs[2]
        scene = generator._analyze_scene(grid)
        swapped = generator._paint_scene(scene["bottom"], scene["right"])
        self.assertEqual(generator.self_check(swapped), [])
        self.assertNotEqual(
            generator.rule_mirror(swapped),
            generator.rule_mirror(grid),
        )
        self.assertFalse(generator.is_canonical_profile(swapped))

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
