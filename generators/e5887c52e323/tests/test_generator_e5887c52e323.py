from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.e5887c52e323 import generator


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


class E5887c52e323GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        target_counts = set()
        modes = set()
        target_orientations = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            scene = generator._analyze_scene(grid)
            profiles.add(generator.canonical_profile_signature(grid))
            target_counts.add(len(scene["targets"]))
            modes.add(scene["distractor_mode"])
            target_orientations.update(
                component["shape"] for component in scene["targets"]
            )
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 5)
        self.assertEqual(target_counts, {2, 3})
        self.assertEqual(modes, {"color_only", "mixed"})
        self.assertEqual(
            target_orientations,
            set(generator._L_ORIENTATIONS),
        )

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
                self.assertLessEqual(matches, 90)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 545)
                self.assertGreaterEqual(len(outputs), 545)

    def test_general_path_witnesses_targets_modes_and_skip_shapes(self):
        target_counts = set()
        modes = set()
        orientations = set()
        red_shapes = set()
        color_shapes = set()
        decoy_colors = set()
        for mode in generator._DISTRACTOR_MODES:
            for n_targets in range(1, 7):
                for seed in range(100):
                    grid = generator.generate(
                        seed,
                        seed * 29 + n_targets,
                        difficulty="hard",
                        grid_h=18,
                        grid_w=19,
                        n_l_shapes=n_targets,
                        distractor_mode=mode,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    scene = generator._analyze_scene(grid)
                    target_counts.add(len(scene["targets"]))
                    modes.add(scene["distractor_mode"])
                    orientations.update(
                        component["shape"]
                        for component in scene["targets"]
                    )
                    red_shapes.update(
                        component["rotation_key"]
                        for component in scene["red_distractors"]
                    )
                    color_shapes.update(
                        component["rotation_key"]
                        for component in scene["color_distractors"]
                    )
                    decoy_colors.update(
                        component["color"]
                        for component in scene["color_distractors"]
                    )
        self.assertEqual(target_counts, {1, 2, 3, 4, 5, 6})
        self.assertEqual(modes, set(generator._DISTRACTOR_MODES))
        self.assertEqual(orientations, set(generator._L_ORIENTATIONS))
        self.assertEqual(red_shapes, generator._RED_DISTRACTOR_KEYS)
        self.assertEqual(color_shapes, generator._NONRED_KEYS)
        self.assertEqual(decoy_colors, set(generator._DECOY_COLORS))

    def test_rule_changes_only_target_elbows(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(100):
                grid = generator.generate(
                    seed,
                    seed * 37 + 5,
                    difficulty=band,
                )
                scene = generator._analyze_scene(grid)
                elbows = {
                    generator._elbow(component["cells"])
                    for component in scene["targets"]
                }
                output = generator.rule_mirror(grid)
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        expected = 4 if (r, c) in elbows else value
                        self.assertEqual(output[r][c], expected)
                for component in (
                    *scene["red_distractors"],
                    *scene["color_distractors"],
                ):
                    for r, c in component["cells"]:
                        self.assertEqual(output[r][c], grid[r][c])

    def test_small_canvas_never_sheds_targets_or_mode(self):
        for mode in generator._DISTRACTOR_MODES:
            for n_targets in range(1, 7):
                for seed in range(100):
                    grid = generator.generate(
                        seed,
                        seed * 41 + n_targets,
                        difficulty="hard",
                        grid_h=7,
                        grid_w=8,
                        n_l_shapes=n_targets,
                        distractor_mode=mode,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(observed["n_l_shapes"], n_targets)
                    self.assertEqual(observed["distractor_mode"], mode)

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 7},
            {"grid_h": 20},
            {"grid_w": 8},
            {"grid_w": 20},
            {"n_l_shapes": 1},
            {"n_l_shapes": 6},
            {"distractor_mode": "none"},
            {"distractor_mode": "red_only"},
            {"distractor_mode": "color_only"},
            {"distractor_mode": "mixed"},
            {
                "grid_h": 7,
                "grid_w": 8,
                "n_l_shapes": 6,
                "distractor_mode": "mixed",
            },
            {
                "grid_h": 20,
                "grid_w": 20,
                "n_l_shapes": 1,
                "distractor_mode": "none",
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
            {"grid_h": "7"},
            {"grid_w": 8.0},
            {"n_l_shapes": True},
            {"distractor_mode": 1},
            {"grid_h": 6},
            {"grid_h": 21},
            {"grid_w": 7},
            {"grid_w": 21},
            {"n_l_shapes": 0},
            {"n_l_shapes": 7},
            {"distractor_mode": "all"},
            {"texture": "no_l"},
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
                grid_h=7,
                grid_w=20,
                n_l_shapes=6,
                distractor_mode="mixed",
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]

        bad_color = [row[:] for row in original]
        bad_color[6][7] = 4
        self.assertTrue(
            any(
                "color 4 reserved" in error
                for error in generator.self_check(bad_color)
            )
        )

        blank = [[0] * 8 for _ in range(7)]
        self.assertTrue(
            any(
                "1..6 red" in error
                for error in generator.self_check(blank)
            )
        )

        unsupported_red = generator._paint_components(
            12,
            12,
            (
                (2, generator._L_ORIENTATIONS[0]),
                (2, ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))),
            ),
            ((0, 0, 1, 1), (4, 0, 4, 4)),
        )
        self.assertTrue(
            any(
                "recognized non-L" in error
                for error in generator.self_check(unsupported_red)
            )
        )

        unsupported_decoy = generator._paint_components(
            10,
            10,
            (
                (2, generator._L_ORIENTATIONS[0]),
                (5, ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))),
            ),
            ((0, 0, 1, 1), (4, 0, 4, 4)),
        )
        self.assertTrue(
            any(
                "recognized colors and shapes" in error
                for error in generator.self_check(unsupported_decoy)
            )
        )

        too_many_red = generator._paint_components(
            12,
            12,
            (
                (2, generator._L_ORIENTATIONS[0]),
                (2, generator._SINGLE),
                (2, generator._DOMINO),
                (2, generator._LINE3),
            ),
            (
                (0, 0, 1, 1),
                (0, 4, 0, 4),
                (4, 0, 4, 1),
                (4, 4, 4, 6),
            ),
        )
        self.assertTrue(
            any(
                "at most two red" in error
                for error in generator.self_check(too_many_red)
            )
        )

    def test_lawful_cross_profile_recombination_is_rejected(self):
        profile = generator._PROFILE_SPECS[0]
        components = [
            (2, generator._L_ORIENTATIONS[0]),
            (2, generator._L_ORIENTATIONS[1]),
            (2, generator._DOMINO),
            (6, generator._DOMINO),
        ]
        hybrid = generator._draw_components(
            profile[0],
            profile[1],
            components,
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
