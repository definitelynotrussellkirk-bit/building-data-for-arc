from __future__ import annotations

import copy
import hashlib
from importlib import import_module
import json
import random
import unittest

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)
from solvers.grounded_rules import GROUNDED_RULES


ROOT = find_root(__file__)
generator = import_module(
    "puzzle_generators.per_puzzle.d5a059b0f3a6.generator"
)


def canonical_row():
    for line in (
        canonical_path(ROOT)
    ).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if (
            row.get("task_id") == generator.TASK_ID
            and row.get("source") == "training"
        ):
            return row
    raise RuntimeError("canonical row not found")


def canonical_pairs():
    return load_canonical_pairs(generator.TASK_ID, root=ROOT)


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


class GeneratorD5a059b0f3a6Tests(unittest.TestCase):
    def test_compact_public_specs_reconstruct_every_input(self):
        for profile, pair in zip(
            generator.PUBLIC_PROFILES,
            canonical_pairs(),
        ):
            self.assertEqual(generator._PUBLIC_INPUTS[profile], pair["input"])

    def test_all_public_pairs_are_strict_and_exact(self):
        for pair in canonical_pairs():
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.solve_python(grid), pair["output"])

    def test_every_public_d4_variant_remains_exact(self):
        for profile, pair in zip(
            generator.PUBLIC_PROFILES,
            canonical_pairs(),
        ):
            for transform in generator.TRANSFORMS:
                grid = generator._transform(pair["input"], transform)
                expected = generator._transform(pair["output"], transform)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.solve_python(grid), expected)
                self.assertEqual(
                    generator._analyze(grid)["answer_profile"],
                    profile,
                )

    def test_every_profile_and_band_is_exactly_observable(self):
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for index in range(30):
                    grid = generator.generate(
                        10_000 * profile_index
                        + 1_000 * band_index
                        + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertNotEqual(generator.solve_python(grid), grid)

    def test_default_profile_prior_and_complete_coverage(self):
        public = 0
        total = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            seen = set()
            for index in range(2_000):
                grid = generator.generate(
                    500_000 + 10_000 * band_index + index,
                    index,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)["scene_profile"]
                seen.add(observed)
                public += observed in generator.PUBLIC_PROFILES
                total += 1
            self.assertEqual(seen, set(generator.SCENE_PROFILES))
        self.assertGreater(public / total, 0.22)
        self.assertLess(public / total, 0.28)

    def test_public_profiles_never_replay_literals(self):
        literals = {grid_key(pair["input"]) for pair in canonical_pairs()}
        for profile_index, profile in enumerate(generator.PUBLIC_PROFILES):
            shapes = set()
            grids = set()
            outputs = set()
            for index in range(2_000):
                grid = generator.generate(
                    600_000 + 10_000 * profile_index + index,
                    index,
                    scene_profile=profile,
                )
                self.assertNotIn(grid_key(grid), literals)
                shapes.add((len(grid), len(grid[0])))
                grids.add(grid_key(grid))
                outputs.add(grid_key(generator.solve_python(grid)))
            original = generator._PUBLIC_INPUTS[profile]
            self.assertEqual(
                shapes,
                {
                    (len(original), len(original[0])),
                    (len(original[0]), len(original)),
                },
            )
            self.assertGreater(len(grids), 1_900)
            self.assertGreater(len(outputs), 900)

    def test_controls_cover_branch_and_difficulty_structure(self):
        expected_frames = {"easy": 2, "medium": 3, "hard": 4}
        expected_shapes = {
            "easy": {(22, 22), (22, 24), (24, 22)},
            "medium": {(24, 26), (26, 24), (26, 26)},
            "hard": {(28, 28), (28, 30), (30, 28), (30, 30)},
        }
        for profile_index, profile in enumerate(
            generator.EXTRAPOLATION_PROFILES
        ):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                shapes = set()
                for index in range(500):
                    grid = generator.generate(
                        700_000
                        + 10_000 * profile_index
                        + 1_000 * band_index
                        + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = generator._analyze(grid)
                    self.assertEqual(
                        analysis["frame_count"],
                        expected_frames[band],
                    )
                    self.assertGreaterEqual(
                        analysis["distractor_count"],
                        4,
                    )
                    shapes.add((len(grid), len(grid[0])))
                self.assertEqual(shapes, expected_shapes[band])

    def test_mutations_are_rejected_from_final_grid(self):
        base = generator.generate(
            800_000,
            0,
            difficulty="hard",
            scene_profile="mixed_axes",
        )
        analysis = generator._analyze(base)

        ragged = copy.deepcopy(base)
        ragged[0].pop()
        self.assertEqual(generator.self_check(ragged), ["ragged"])

        invalid = copy.deepcopy(base)
        invalid[0][0] = True
        self.assertEqual(
            generator.self_check(invalid),
            ["invalid_arc_value"],
        )

        broken_corner = copy.deepcopy(base)
        row1, col1, _, _ = analysis["frames"][0]
        broken_corner[row1][col1 + 1] = 0
        self.assertIn(
            "invalid_frame_corner",
            generator.self_check(broken_corner),
        )

        second_color = copy.deepcopy(base)
        second_color[row1][col1] = (
            2 if analysis["frame_color"] != 2 else 3
        )
        self.assertIn(
            "frame_color_cardinality",
            generator.self_check(second_color),
        )

        no_distractors = generator.solve_python(base)
        self.assertIn(
            "distractor_count",
            generator.self_check(no_distractors),
        )

        empty_seed = copy.deepcopy(base)
        frame = analysis["frames"][0]
        for row in range(frame[0], frame[2] + 1):
            for col in range(frame[1], frame[3] + 1):
                if empty_seed[row][col] == 1:
                    empty_seed[row][col] = 0
        self.assertIn("empty_frame_seed", generator.self_check(empty_seed))

    def test_cross_profile_seed_recombination_is_rejected(self):
        grid = generator.generate(
            850_000,
            0,
            difficulty="hard",
            scene_profile="mixed_axes",
        )
        frame = generator._analyze(grid)["frames"][0]
        row1, col1, row2, col2 = frame
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                if grid[row][col] == 1:
                    grid[row][col] = 0
        grid[row1 + 2][col1 + 2] = 1
        grid[row2 - 2][col2 - 2] = 1
        self.assertIn(
            "ambiguous_vertical_seed",
            generator.self_check(grid),
        )

    def test_broad_one_frame_oracle_is_exact_but_not_training_grammar(self):
        frame = (2, 2, 10, 10)
        grid = generator._build_scene(
            (20, 20),
            (frame,),
            ((4, 4), (5, 4), (5, 5)),
            7,
        )
        before = copy.deepcopy(grid)
        self.assertTrue(generator.self_check(grid))
        output = generator.solve_python(grid)
        self.assertNotEqual(output, grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[4][8], 1)

    def test_deterministic_fresh_and_global_rng_isolated(self):
        state = random.getstate()
        first = generator.generate(900_000, 17, difficulty="hard")
        second = generator.generate(900_000, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)
        self.assertEqual(random.getstate(), state)

    def test_seed_and_sample_index_both_matter(self):
        base = [generator.generate(1_000_000, index) for index in range(12)]
        different_seed = [
            generator.generate(1_000_001, index) for index in range(12)
        ]
        different_index = [
            generator.generate(1_000_000, index + 1)
            for index in range(12)
        ]
        self.assertNotEqual(base, different_seed)
        self.assertNotEqual(base, different_index)

    def test_invalid_overrides_fail_closed(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 0, scene_profile="invented")
        with self.assertRaises(ValueError):
            generator.generate(1, 0, grid_h=22)

    def test_version_and_rule_hash_are_pinned(self):
        self.assertEqual(generator.VERSION, "3.1.0")
        self.assertEqual(generator.RULE_HASH, "77f0ca66f33e")

    def test_invalid_request_scalars_fail_closed(self):
        for invalid_seed in (True, False, 1.0, 1.75, "1", None):
            with self.subTest(seed=invalid_seed):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(invalid_seed, 0)
        for invalid_index in (True, False, 1.0, 1.75, "1", -1, None):
            with self.subTest(sample_index=invalid_index):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(1, invalid_index)
        for invalid_difficulty in (True, False, 0, 1.0, "invented"):
            with self.subTest(difficulty=invalid_difficulty):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(1, 0, difficulty=invalid_difficulty)
        with self.assertRaises((TypeError, ValueError)):
            generator.generate(1, 0, scene_profile=1)

    def test_schedule_preserves_prior_and_rotated_teaching_coverage(self):
        self.assertEqual(generator.EXAMPLES_NEEDED, 3)
        self.assertEqual(generator.SCHEDULE_PERIOD, 16)
        self.assertEqual(
            set(generator.SCHEDULE_PROFILES),
            set(generator.SCENE_PROFILES),
        )
        counts = {
            profile: generator.DEFAULT_PROFILE_SCHEDULE.count(profile)
            for profile in generator.SCENE_PROFILES
        }
        self.assertEqual(
            counts,
            {
                "public_train_1": 1,
                "public_train_2": 1,
                "public_train_3": 1,
                "public_test_1": 1,
                "horizontal_frames": 4,
                "vertical_frames": 4,
                "mixed_axes": 4,
            },
        )
        mixed_profiles = set(generator.PUBLIC_PROFILES) | {"mixed_axes"}
        for start in range(generator.SCHEDULE_PERIOD):
            four = [
                generator.schedule_profile(109, start + offset, "medium")
                for offset in range(4)
            ]
            self.assertGreaterEqual(
                sum(profile in mixed_profiles for profile in four),
                2,
                (start, four),
            )
            for query_offset in range(4):
                demos = [
                    profile
                    for offset, profile in enumerate(four)
                    if offset != query_offset
                ]
                self.assertTrue(
                    any(profile in mixed_profiles for profile in demos),
                    (start, query_offset, four),
                )

    def test_default_windows_refute_forced_axis_rivals_under_query_rotation(self):
        for band in (None, "easy", "medium", "hard"):
            for start in range(generator.SCHEDULE_PERIOD):
                pairs = []
                for offset in range(4):
                    grid = generator.generate(
                        109,
                        start + offset,
                        difficulty=band,
                    )
                    pairs.append(
                        {
                            "input": grid,
                            "output": generator.solve_python(grid),
                        }
                    )
                for query_offset in range(4):
                    demos = [
                        pair
                        for offset, pair in enumerate(pairs)
                        if offset != query_offset
                    ]
                    query = pairs[query_offset]
                    self.assertEqual(
                        generator.lesson_identifiable(demos, query),
                        [],
                        (band, start, query_offset),
                    )
                    for name in ("horizontal_only", "vertical_only"):
                        rival = generator.LESSON_COMPETITORS[name]
                        self.assertFalse(
                            all(
                                rival(pair["input"]) == pair["output"]
                                for pair in demos
                            ),
                            (band, start, query_offset, name),
                        )

    def test_semantic_witnesses_are_truthful_and_rivals_are_pure(self):
        self.assertEqual(
            set(generator.SEMANTIC_WITNESSES),
            {"mixed_axis_scene", "outside_distractors"},
        )
        self.assertEqual(
            set(generator.SEMANTIC_RIVALS),
            {"horizontal_only", "vertical_only", "keep_distractors"},
        )
        self.assertEqual(
            set(generator.LESSON_COMPETITORS),
            set(generator.SEMANTIC_RIVALS),
        )
        for index, profile in enumerate(
            (*generator.PUBLIC_PROFILES, "mixed_axes")
        ):
            grid = generator.generate(
                1_200_000 + index,
                index,
                difficulty="medium",
                scene_profile=profile,
            )
            before = copy.deepcopy(grid)
            truth = generator.solve_python(grid)
            self.assertTrue(
                generator.SEMANTIC_WITNESSES["mixed_axis_scene"](grid)
            )
            self.assertTrue(
                generator.SEMANTIC_WITNESSES["outside_distractors"](grid)
            )
            for name, rival in generator.SEMANTIC_RIVALS.items():
                prediction = rival(grid)
                self.assertEqual(grid, before, name)
                self.assertNotEqual(prediction, truth, (profile, name))

    def test_lesson_hook_catches_the_retained_horizontal_shortcut_shape(self):
        demos = []
        for index in range(3):
            grid = generator.generate(
                109,
                index,
                difficulty="medium",
                scene_profile="horizontal_frames",
            )
            demos.append(
                {"input": grid, "output": generator.solve_python(grid)}
            )
        query_grid = generator.generate(
            109,
            3,
            difficulty="medium",
            scene_profile="mixed_axes",
        )
        reasons = generator.lesson_identifiable(
            demos,
            {
                "input": query_grid,
                "output": generator.solve_python(query_grid),
            },
        )
        self.assertTrue(
            any("horizontal_only" in reason for reason in reasons),
            reasons,
        )

    def test_every_rule_authority_is_synchronized(self):
        row = canonical_row()
        source = row["program_solution"]
        digest = hashlib.sha256(
            " ".join(source.split()).encode()
        ).hexdigest()
        self.assertEqual(generator.RULE_HASH, digest[:12])
        base_path = (
            ROOT
            / "shared/data/base/solutions/training"
            / "93c31fbe__d5a059b0f3a6.json"
        )
        base = json.loads(base_path.read_text(encoding="utf-8"))
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        grounded_digest = hashlib.sha256(
            " ".join(GROUNDED_RULES[generator.TASK_ID].split()).encode()
        ).hexdigest()
        self.assertEqual(grounded_digest, digest)


if __name__ == "__main__":
    unittest.main()
