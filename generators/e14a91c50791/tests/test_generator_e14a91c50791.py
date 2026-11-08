from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.e14a91c50791 import generator
from reviewer_support import canonical_pairs as load_canonical_pairs, find_root


ROOT = find_root(__file__)


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    for pair in load_canonical_pairs(generator.TASK_ID, root=ROOT, labeled_only=True):
        yield as_grid(pair["input"]), as_grid(pair["output"])



class E14a91c50791GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        canvas_shapes = set()
        class_shapes = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            profiles.add(generator.canonical_profile_signature(grid))
            scene = generator._analyze_scene(grid)
            canvas_shapes.add((scene["h"], scene["w"]))
            self.assertEqual(len(scene["groups"]), 3)
            self.assertEqual(sorted(map(len, scene["groups"].values())), [2, 2, 3])
            self.assertEqual(len(scene["odd_keys"]), 1)
            class_shapes.update(scene["groups"])
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 5)
        self.assertEqual(len(canvas_shapes), 5)
        self.assertIn(2, {len(shape) for shape in class_shapes})
        self.assertIn(5, {len(shape) for shape in class_shapes})

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
                self.assertLessEqual(matches, 70)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 450)
                self.assertGreaterEqual(len(outputs), 450)

    def test_general_path_witnesses_class_counts_and_shape_sizes(self):
        class_counts = set()
        shape_sizes = set()
        odd_counts = set()
        for band in ("easy", "medium", "hard"):
            for count in (2, 3, 4):
                for seed in range(80):
                    grid = generator.generate(
                        seed,
                        seed * 31 + count,
                        difficulty=band,
                        grid_h=20,
                        grid_w=20,
                        n_classes=count,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    scene = generator._analyze_scene(grid)
                    self.assertEqual(len(scene["groups"]), count)
                    self.assertEqual(len(scene["odd_keys"]), 1)
                    class_counts.add(count)
                    shape_sizes.update(len(key) for key in scene["groups"])
                    odd_counts.add(
                        len(scene["groups"][scene["odd_keys"][0]])
                    )
                    for key, values in scene["groups"].items():
                        if key != scene["odd_keys"][0]:
                            self.assertEqual(len(values), 2)
        self.assertEqual(class_counts, {2, 3, 4})
        self.assertEqual(shape_sizes, {2, 3, 4, 5, 6})
        self.assertEqual(odd_counts, {1, 3})

    def test_small_canvas_never_sheds_requested_classes_or_objects(self):
        for seed in range(300):
            grid = generator.generate(
                seed,
                seed * 37 + 5,
                grid_h=13,
                grid_w=13,
                n_classes=4,
            )
            self.assertEqual(generator.self_check(grid), [])
            scene = generator._analyze_scene(grid)
            self.assertEqual(len(scene["groups"]), 4)
            self.assertIn(len(scene["components"]), {7, 9})
            self.assertEqual(
                generator.observe_overrides(grid)["n_classes"],
                4,
            )

    def test_rotation_classes_do_not_collapse_reflections(self):
        left = ((0, 0), (0, 1), (0, 2), (1, 0))
        right = ((0, 0), (0, 1), (0, 2), (1, 2))
        self.assertNotEqual(
            generator._rotation_key(left),
            generator._rotation_key(right),
        )
        grid = generator._draw_scene(
            13,
            13,
            ((left, 3), (right, 2)),
            random.Random(72),
        )
        self.assertEqual(generator.self_check(grid), [])
        scene = generator._analyze_scene(grid)
        self.assertEqual(len(scene["groups"]), 2)
        self.assertEqual(len(scene["odd_keys"]), 1)
        target_key = scene["odd_keys"][0]
        self.assertEqual(len(scene["groups"][target_key]), 3)
        output = generator.rule_mirror(grid)
        for key, objects in scene["groups"].items():
            for cells in objects:
                expected_color = 7 if key == target_key else 2
                for r, c in cells:
                    self.assertEqual(output[r][c], expected_color)

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 13},
            {"grid_h": 26},
            {"grid_w": 13},
            {"grid_w": 26},
            {"n_classes": 2},
            {"n_classes": 4},
            {"grid_h": 13, "grid_w": 13, "n_classes": 4},
            {"grid_h": 26, "grid_w": 26, "n_classes": 2},
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
            {"grid_h": "13"},
            {"grid_w": 13.0},
            {"n_classes": True},
            {"grid_h": 12},
            {"grid_h": 27},
            {"grid_w": 12},
            {"grid_w": 27},
            {"n_classes": 1},
            {"n_classes": 5},
            {"texture": "all_even"},
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
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 30)

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]
        scene = generator._analyze_scene(original)

        bad_color = [row[:] for row in original]
        first_r, first_c = scene["components"][0][0]
        bad_color[first_r][first_c] = 7
        self.assertTrue(
            any(
                "colors 0 or 2" in error
                for error in generator.self_check(bad_color)
            )
        )

        extra_singleton = [row[:] for row in original]
        extra_singleton[12][14] = 2
        self.assertTrue(
            any(
                "2..6 cells" in error
                for error in generator.self_check(extra_singleton)
            )
        )

        second_odd = [row[:] for row in original]
        even_key = next(
            key
            for key, values in scene["groups"].items()
            if len(values) == 2
        )
        victim = scene["groups"][even_key][0]
        for r, c in victim:
            second_odd[r][c] = 0
        self.assertTrue(
            any(
                "exactly one odd" in error
                for error in generator.self_check(second_odd)
            )
        )

        one_class = generator._draw_scene(
            13,
            13,
            ((((0, 0), (0, 1)), 3),),
            random.Random(4),
        )
        self.assertTrue(
            any(
                "2..4 rotation classes" in error
                for error in generator.self_check(one_class)
            )
        )

        all_even = generator._draw_scene(
            13,
            13,
            (
                (((0, 0), (0, 1)), 2),
                (((0, 0), (0, 1), (0, 2)), 2),
            ),
            random.Random(5),
        )
        self.assertTrue(
            any(
                "exactly one odd" in error
                for error in generator.self_check(all_even)
            )
        )

        too_large = [row[:] for row in original]
        for c in range(7):
            too_large[12][c] = 2
        self.assertTrue(generator.self_check(too_large))

        too_short = original[:12]
        self.assertTrue(
            any(
                "height" in error
                for error in generator.self_check(too_short)
            )
        )

    def test_lawful_cross_profile_recombination_is_rejected(self):
        h, w, classes = generator._PROFILE_SPECS[0]
        replacement = generator._PROFILE_SPECS[1][2][0][0]
        hybrid_classes = ((replacement, classes[0][1]), *classes[1:])
        hybrid = generator._draw_scene(
            h,
            w,
            hybrid_classes,
            random.Random(91),
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertFalse(generator.is_canonical_profile(hybrid))
        self.assertNotIn(
            generator.canonical_profile_signature(hybrid),
            generator._CANONICAL_PROFILE_SIGNATURES,
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


if __name__ == "__main__":
    unittest.main()
