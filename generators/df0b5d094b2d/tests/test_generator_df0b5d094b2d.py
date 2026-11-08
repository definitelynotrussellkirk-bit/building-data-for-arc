from __future__ import annotations

import random
import unittest

from puzzle_generators import base
from puzzle_generators.per_puzzle.df0b5d094b2d import generator
from reviewer_support import canonical_pairs as load_canonical_pairs, find_root


ROOT = find_root(__file__)


def canonical_pairs():
    for pair in load_canonical_pairs(
        generator.TASK_ID, root=ROOT, labeled_only=True
    ):
        yield pair["input"], pair["output"]


class Df0b5d094b2dGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 8)
        profiles = set()
        unique_inputs = set()
        counts = set()
        corners = set()
        dimensions = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            profiles.add(generator.canonical_profile_signature(grid))
            unique_inputs.add(tuple(map(tuple, grid)))
            scene = generator._analyze_scene(grid)
            counts.add(len(scene["objects"]))
            corners.update(obj["corner"] for obj in scene["objects"])
            dimensions.update(
                (obj["height"], obj["width"])
                for obj in scene["objects"]
            )
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 4)
        self.assertEqual(len(unique_inputs), 4)
        self.assertEqual(counts, {2, 3, 4})
        self.assertEqual(corners, {0, 1, 2, 3})
        self.assertIn((2, 2), dimensions)
        self.assertIn((5, 5), dimensions)

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
                self.assertGreaterEqual(len(inputs), 450)
                self.assertGreaterEqual(len(outputs), 450)

    def test_general_path_witnesses_object_geometry_and_exact_counts(self):
        counts = set()
        corners = set()
        dimensions = set()
        colors = set()
        for count in (2, 3, 4):
            for seed in range(120):
                grid = generator.generate(
                    seed,
                    seed * 31 + count,
                    difficulty="hard",
                    grid_h=20,
                    grid_w=22,
                    shape_count=count,
                )
                self.assertEqual(generator.self_check(grid), [])
                scene = generator._analyze_scene(grid)
                self.assertEqual(len(scene["objects"]), count)
                self.assertEqual(
                    generator.observe_overrides(grid)["shape_count"],
                    count,
                )
                counts.add(count)
                corners.update(obj["corner"] for obj in scene["objects"])
                dimensions.update(
                    (obj["height"], obj["width"])
                    for obj in scene["objects"]
                )
                colors.update(obj["color"] for obj in scene["objects"])
        self.assertEqual(counts, {2, 3, 4})
        self.assertEqual(corners, {0, 1, 2, 3})
        self.assertTrue(
            {(2, 2), (3, 3), (4, 4), (5, 5)} <= dimensions
        )
        self.assertEqual(colors, set(range(10)) - {7, 8})

        for seed in range(300):
            grid = generator.generate(
                seed,
                seed * 37 + 5,
                grid_h=10,
                grid_w=10,
                shape_count=4,
            )
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(
                generator.observe_overrides(grid)["shape_count"],
                4,
            )

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 10},
            {"grid_h": 20},
            {"grid_w": 10},
            {"grid_w": 22},
            {"shape_count": 2},
            {"shape_count": 4},
            {"grid_h": 10, "grid_w": 10, "shape_count": 4},
            {"grid_h": 20, "grid_w": 22, "shape_count": 2},
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
            {"grid_h": "10"},
            {"grid_w": 10.0},
            {"shape_count": True},
            {"grid_h": 9},
            {"grid_h": 21},
            {"grid_w": 9},
            {"grid_w": 23},
            {"shape_count": 1},
            {"shape_count": 5},
            {"texture": "no_rects"},
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
        first = scene["objects"][0]

        no_marker = [row[:] for row in original]
        mr, mc = first["marker"]
        no_marker[mr][mc] = first["color"]
        self.assertTrue(
            any(
                "omit exactly one" in error
                for error in generator.self_check(no_marker)
            )
        )

        interior_hole = [row[:] for row in original]
        interior_hole[mr][mc] = first["color"]
        interior_hole[first["r0"] + 1][first["c0"] + 1] = 8
        self.assertTrue(generator.self_check(interior_hole))

        extra_marker = [row[:] for row in original]
        extra_marker[5][9] = 8
        self.assertTrue(
            any(
                "marker cells" in error
                for error in generator.self_check(extra_marker)
            )
        )

        two_shape, _ = self.pairs[1]
        one_shape = [row[:] for row in two_shape]
        victim = generator._analyze_scene(one_shape)["objects"][0]
        for r in range(victim["r0"], victim["r1"] + 1):
            for c in range(victim["c0"], victim["c1"] + 1):
                one_shape[r][c] = 7
        self.assertTrue(
            any(
                "2..4" in error
                for error in generator.self_check(one_shape)
            )
        )

        clipped = [row[:] for row in original]
        edge = next(
            obj
            for obj in scene["objects"]
            if obj["r0"] == 0 and obj["c0"] == 0
        )
        old_r, old_c = edge["marker"]
        clipped[old_r][old_c] = edge["color"]
        new_r, new_c = generator._corner_cells(
            edge["r0"],
            edge["c0"],
            edge["r1"],
            edge["c1"],
        )[0]
        clipped[new_r][new_c] = 8
        self.assertTrue(
            any(
                "in-bounds" in error
                for error in generator.self_check(clipped)
            )
        )

        invalid_color = [row[:] for row in original]
        invalid_color[0][0] = 10
        self.assertTrue(
            any(
                "ARC colors" in error
                for error in generator.self_check(invalid_color)
            )
        )

    def test_color_swap_is_lawful_but_not_canonical(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        for r, row in enumerate(hybrid):
            for c, value in enumerate(row):
                if value == 1:
                    hybrid[r][c] = 5
                elif value == 5:
                    hybrid[r][c] = 1
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertNotEqual(
            generator.rule_mirror(hybrid),
            generator.rule_mirror(grid),
        )
        self.assertFalse(generator.is_canonical_profile(hybrid))

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
