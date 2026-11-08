from __future__ import annotations

import json
import random
import unittest
from collections import Counter

from puzzle_generators import base
from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
generator, _, _ = load_selected_generator(
    "33c7c507a8ef", root=ROOT
)


def canonical_pairs():
    for pair in load_canonical_pairs(generator.TASK_ID, root=ROOT):
        yield pair["input"], pair["output"]


def copied(grid):
    return [row[:] for row in grid]


class Generator33c7c507a8efTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_canonical_pairs_are_structural_profiles_and_match_rule(self):
        self.assertEqual(len(self.pairs), 3)
        for grid, expected in self.pairs:
            original = copied(grid)
            self.assertEqual(generator.self_check(grid), [])
            self.assertIsNotNone(generator.canonical_profile_signature(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, original)

    def test_complete_canonical_prior_has_every_linked_public_profile(self):
        for band in ("easy", "medium", "hard"):
            counts = Counter()
            matches = 0
            for seed in range(600):
                grid = generator.generate(seed, seed * 17 + 3, difficulty=band)
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    matches += 1
                    counts[signature[3]] += 1
            self.assertGreaterEqual(matches, 90)
            self.assertLessEqual(matches, 180)
            self.assertEqual(set(counts), {2, 3, 4})
            self.assertGreaterEqual(min(counts.values()), 20)

    def test_every_code_has_a_distinct_rotation_witness(self):
        outputs = []
        for code in (1, 2, 3, 4):
            grid = generator.generate(
                91,
                7,
                difficulty="hard",
                scene_family="generalized",
                code=code,
                interior_h=3,
                interior_w=5,
                frame_top=4,
                frame_left=5,
                n_content_colors=4,
                include_frame_color=True,
            )
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.observe_overrides(grid)["code"], code)
            outputs.append(generator.rule_mirror(grid))
        self.assertEqual(len({json.dumps(out) for out in outputs}), 4)

    def test_exact_axis_boundaries_are_observed_and_invalid_mix_rejects(self):
        cases = (
            {
                "scene_family": "generalized",
                "code": 1,
                "interior_h": 2,
                "interior_w": 2,
                "frame_top": 1,
                "frame_left": 1,
                "n_content_colors": 2,
                "include_frame_color": False,
            },
            {
                "scene_family": "generalized",
                "code": 4,
                "interior_h": 6,
                "interior_w": 7,
                "frame_top": 4,
                "frame_left": 5,
                "n_content_colors": 4,
                "include_frame_color": True,
            },
            {
                "scene_family": "canonical",
                "code": 3,
                "interior_h": 2,
                "interior_w": 3,
                "frame_top": 1,
                "frame_left": 1,
                "n_content_colors": 2,
                "include_frame_color": True,
            },
        )
        for seed, case in enumerate(cases):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(seed, 29, difficulty="hard", **case)
            finally:
                base.set_ctx_observer(None)
            self.assertEqual(generator.self_check(grid), [])
            observed = generator.observe_overrides(grid)
            self.assertEqual({name: observed[name] for name in case}, case)
            self.assertTrue(captured)
            for name, value in case.items():
                self.assertEqual(captured[-1].recorded_draws()[name], value)

        with self.assertRaisesRegex(ValueError, "at least five cells"):
            generator.generate(
                0,
                0,
                scene_family="generalized",
                interior_h=2,
                interior_w=2,
                n_content_colors=4,
            )
        with self.assertRaisesRegex(ValueError, "conflicts"):
            generator.generate(
                0,
                0,
                scene_family="canonical",
                code=2,
                include_frame_color=True,
            )

    def test_self_check_rejects_targeted_structural_impostors(self):
        grid = copied(self.pairs[0][0])
        analysis = generator._analyze(grid)
        top, left, bottom, right = analysis["facts"]["frame_bbox"]

        mutations = {}
        broken = copied(grid)
        broken[top][left + 1] = 0
        mutations["broken frame"] = broken

        outside = copied(grid)
        outside[0][-1] = 7
        mutations["outside distractor"] = outside

        empty = copied(grid)
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                empty[row][col] = 0
        mutations["empty interior"] = empty

        symmetric = copied(empty)
        symmetric[top + 1][left + 1] = 2
        symmetric[bottom - 1][right - 1] = 2
        mutations["rotation ambiguity"] = symmetric

        stray_gray = copied(grid)
        stray_gray[0][-1] = 5
        mutations["stray frame color"] = stray_gray

        missing_code = copied(grid)
        missing_code[0][0] = 0
        mutations["missing code"] = missing_code

        for label, impostor in mutations.items():
            with self.subTest(label=label):
                self.assertTrue(generator.self_check(impostor))

    def test_negative_canonical_recombination_is_loud_but_oracle_executable(self):
        # Replace the test code 3 with code 2. Color 2 is absent everywhere else,
        # so this is a clean cue recombination rather than an accidental echo.
        test_grid = copied(self.pairs[-1][0])
        self.assertNotIn(2, [value for row in test_grid for value in row])
        test_grid[0][0] = 2
        self.assertEqual(generator.self_check(test_grid), [])
        self.assertIsNone(generator.canonical_profile_signature(test_grid))
        self.assertEqual(generator.rule_mirror(test_grid), generator._rotate_cw(
            generator._analyze(test_grid)["facts"]["interior"]
        ))
        with self.assertRaisesRegex(ValueError, "conflicts"):
            generator.generate(
                3,
                3,
                scene_family="canonical",
                code=2,
                include_frame_color=True,
            )

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(7123)
        state = random.getstate()
        first = generator.generate(17, 29, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(17, 29, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9
        self.assertNotEqual(first, second)
        self.assertEqual(random.getstate(), state)


if __name__ == "__main__":
    unittest.main()
