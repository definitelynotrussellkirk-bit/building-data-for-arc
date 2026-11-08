from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.e250cb77a62e import generator


from reviewer_support import canonical_pairs as portable_pairs, find_root
ROOT = find_root(__file__)


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    for pair in portable_pairs(generator.TASK_ID, root=ROOT):
        yield pair["input"], pair["output"]


class E250cb77a62eGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 3)
        profiles = set()
        frame_positions = set()
        seed_layouts = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            scene = generator._analyze_scene(grid)
            self.assertEqual((scene["frame_h"], scene["frame_w"]), (5, 4))
            self.assertEqual(scene["pattern"], generator._PUBLIC_PATTERN)
            self.assertEqual(len(scene["seeds"]), 2)
            profiles.add(generator.canonical_profile_signature(grid))
            frame_positions.add(scene["frame_bbox"][:2])
            seed_layouts.add(scene["seeds"])
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 3)
        self.assertEqual(len(frame_positions), 3)
        self.assertEqual(len(seed_layouts), 3)

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                inputs = set()
                outputs = set()
                for offset in range(600):
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
                self.assertGreaterEqual(matches, 25)
                self.assertLessEqual(matches, 100)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 550)
                self.assertGreaterEqual(len(outputs), 550)

    def test_general_path_witnesses_frames_patterns_and_seed_counts(self):
        frame_heights = set()
        frame_widths = set()
        pattern_sizes = set()
        patterns = set()
        seed_counts = set()
        for band in ("easy", "medium", "hard"):
            for n_seeds in range(1, 5):
                for seed in range(120):
                    grid = generator.generate(
                        seed,
                        seed * 29 + n_seeds,
                        difficulty=band,
                        grid_h=20,
                        grid_w=21,
                        n_seeds=n_seeds,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    scene = generator._analyze_scene(grid)
                    frame_heights.add(scene["frame_h"])
                    frame_widths.add(scene["frame_w"])
                    pattern_sizes.add(len(scene["pattern"]))
                    patterns.add(scene["pattern"])
                    seed_counts.add(len(scene["seeds"]))
                    self.assertIn((0, 0), scene["pattern"])
                    self.assertIn(
                        (scene["frame_h"] - 3, scene["frame_w"] - 3),
                        scene["pattern"],
                    )
                    self.assertTrue(generator._is_connected(scene["pattern"]))
        self.assertEqual(frame_heights, {4, 5, 6, 7})
        self.assertEqual(frame_widths, {4, 5, 6, 7})
        self.assertEqual(seed_counts, {1, 2, 3, 4})
        self.assertIn(3, pattern_sizes)
        self.assertGreaterEqual(max(pattern_sizes), 10)
        self.assertGreaterEqual(len(patterns), 40)

    def test_rule_stamps_exact_offsets_and_preserves_source(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                grid = generator.generate(
                    seed,
                    seed * 37 + 5,
                    difficulty=band,
                )
                scene = generator._analyze_scene(grid)
                output = generator.rule_mirror(grid)
                targets = {
                    (seed_r + dr, seed_c + dc)
                    for seed_r, seed_c in scene["seeds"]
                    for dr, dc in scene["pattern"]
                }
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        expected = 8 if (r, c) in targets else value
                        self.assertEqual(output[r][c], expected)
                r0, c0, r1, c1 = scene["frame_bbox"]
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        self.assertEqual(output[r][c], grid[r][c])
                self.assertTrue(
                    all(output[r][c] == 8 for r, c in scene["seeds"])
                )

    def test_small_canvas_never_sheds_requested_seeds(self):
        for n_seeds in range(1, 5):
            for seed in range(300):
                grid = generator.generate(
                    seed,
                    seed * 41 + n_seeds,
                    difficulty="hard",
                    grid_h=11,
                    grid_w=11,
                    n_seeds=n_seeds,
                )
                self.assertEqual(generator.self_check(grid), [])
                scene = generator._analyze_scene(grid)
                self.assertEqual(len(scene["seeds"]), n_seeds)
                self.assertEqual(
                    generator.observe_overrides(grid)["n_seeds"],
                    n_seeds,
                )

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 11},
            {"grid_h": 22},
            {"grid_w": 11},
            {"grid_w": 22},
            {"n_seeds": 1},
            {"n_seeds": 4},
            {"grid_h": 11, "grid_w": 11, "n_seeds": 4},
            {"grid_h": 22, "grid_w": 22, "n_seeds": 1},
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
            {"grid_h": "11"},
            {"grid_w": 11.0},
            {"n_seeds": True},
            {"grid_h": 10},
            {"grid_h": 23},
            {"grid_w": 10},
            {"grid_w": 23},
            {"n_seeds": 0},
            {"n_seeds": 5},
            {"texture": "no_frame"},
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

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=11,
                grid_w=22,
                n_seeds=4,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]
        scene = generator._analyze_scene(original)

        bad_color = [row[:] for row in original]
        bad_color[10][10] = 8
        self.assertTrue(
            any(
                "colors 0, 1, 4, or 7" in error
                for error in generator.self_check(bad_color)
            )
        )

        broken_frame = [row[:] for row in original]
        r0, c0, _r1, _c1 = scene["frame_bbox"]
        broken_frame[r0][c0] = 0
        self.assertTrue(generator.self_check(broken_frame))

        yellow_outside = [row[:] for row in original]
        yellow_outside[10][10] = 4
        self.assertTrue(
            any(
                "strictly inside" in error
                for error in generator.self_check(yellow_outside)
            )
        )

        missing_anchor = [row[:] for row in original]
        missing_anchor[r0 + 1][c0 + 1] = 0
        self.assertTrue(
            any(
                "top-left anchor" in error
                for error in generator.self_check(missing_anchor)
            )
        )

        edge_seed = [row[:] for row in original]
        old_seed = scene["seeds"][0]
        edge_seed[old_seed[0]][old_seed[1]] = 0
        edge_seed[10][10] = 7
        self.assertTrue(
            any(
                "fit inside" in error
                for error in generator.self_check(edge_seed)
            )
        )

        no_seeds = [row[:] for row in original]
        for r, c in scene["seeds"]:
            no_seeds[r][c] = 0
        self.assertTrue(
            any(
                "1..4 orange" in error
                for error in generator.self_check(no_seeds)
            )
        )

        overlapping = generator._paint_scene(
            11,
            11,
            (0, 0, 4, 3),
            generator._PUBLIC_PATTERN,
            ((6, 6, 8, 7), (6, 7, 8, 8)),
        )
        self.assertTrue(
            any(
                "pairwise disjoint" in error
                for error in generator.self_check(overlapping)
            )
        )

    def test_lawful_cross_profile_recombination_is_rejected(self):
        alternate = ((0, 0), (1, 0), (2, 0), (2, 1))
        hybrid = generator._draw_scene(
            11,
            11,
            5,
            4,
            alternate,
            2,
            random.Random(72),
        )
        self.assertIsNotNone(hybrid)
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
