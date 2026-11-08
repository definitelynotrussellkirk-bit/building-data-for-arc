"""Focused semantic tests for generator 33275a4aae3e."""

from __future__ import annotations

import copy
import json
import random
import unittest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "33275a4aae3e"


class Generator33275a4aae3eTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_selected_generator(TASK_ID, root=ROOT)[0]
        cls.public_pairs = canonical_pairs(TASK_ID, root=ROOT, variant=0)
        cls.public_inputs = [pair["input"] for pair in cls.public_pairs]

    def test_metadata_and_single_exact_axis(self) -> None:
        self.assertEqual(self.module.VERSION, "2.1.0")
        self.assertEqual(self.module.RULE_HASH, "a7f4d11b444d")
        self.assertEqual(set(self.module.AXES), {"scene_profile"})
        declared = set(self.module.AXES["scene_profile"]["valid"].split("|"))
        self.assertEqual(declared, set(self.module.SCENE_PROFILES))

    def test_all_public_pairs_are_positive_controls(self) -> None:
        for index, pair in enumerate(self.public_pairs):
            with self.subTest(index=index):
                self.assertEqual(self.module.self_check(pair["input"]), [])
                source = copy.deepcopy(pair["input"])
                actual = self.module.solve_python(source)
                self.assertEqual(actual, pair["output"])
                self.assertEqual(source, pair["input"])

    def test_public_inputs_map_to_four_distinct_profiles(self) -> None:
        observed = [
            self.module.canonical_profile_index(grid)
            for grid in self.public_inputs
        ]
        self.assertEqual(observed, [0, 1, 2, 3])

    def test_every_scene_profile_is_exactly_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for profile in self.module.SCENE_PROFILES:
                for seed in range(5):
                    with self.subTest(band=band, profile=profile, seed=seed):
                        grid = self.module.generate(
                            seed,
                            seed + 17,
                            difficulty=band,
                            scene_profile=profile,
                        )
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {"scene_profile": profile},
                        )

    def test_profile_topology_matches_its_declared_signature(self) -> None:
        for profile, spec in self.module.SCENE_SPECS.items():
            grid = self.module.generate(91, 12, scene_profile=profile)
            analysis = self.module._analyze(grid)
            self.assertEqual(analysis["height"], spec.height)
            self.assertEqual(analysis["width"], spec.width)
            self.assertEqual(analysis["enclosed_regions"], spec.rooms)
            self.assertEqual(
                analysis["horizontal_runs"], spec.horizontal_runs
            )
            self.assertEqual(analysis["vertical_runs"], spec.vertical_runs)
            self.assertEqual(analysis["boundary_sides"], spec.boundary_sides)
            self.assertEqual(analysis["degree3"], int(spec.t_junction))
            self.assertEqual(
                self.module._signature(analysis),
                self.module._expected_signature(spec),
            )

    def test_defaults_are_deterministic_fresh_and_nonidentity(self) -> None:
        for band in ("easy", "medium", "hard"):
            for seed in range(30):
                first = self.module.generate(seed, 4, difficulty=band)
                second = self.module.generate(seed, 4, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                output = self.module.solve_python(first)
                self.assertNotEqual(first, output)
                self.assertIsNot(first, output)
                self.assertEqual(self.module.self_check(first), [])

    def test_generation_does_not_touch_global_random_state(self) -> None:
        random.seed(20260719)
        before = random.getstate()
        self.module.generate(1234, 8, difficulty="hard")
        self.assertEqual(random.getstate(), before)

    def test_unknown_override_fails_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, obsolete_texture="frame")

    def test_literal_public_inputs_are_not_replayed(self) -> None:
        encoded_public = {
            json.dumps(grid, separators=(",", ":"))
            for grid in self.public_inputs
        }
        for profile in self.module.SCENE_PROFILES:
            for seed in range(20):
                generated = self.module.generate(
                    seed, seed, scene_profile=profile
                )
                self.assertNotIn(
                    json.dumps(generated, separators=(",", ":")),
                    encoded_public,
                )

    def test_self_check_rejects_minimal_impostors(self) -> None:
        impostors = []
        impostors.append([[0 for _ in range(22)] for _ in range(22)])

        singleton = [[0 for _ in range(22)] for _ in range(22)]
        singleton[10][10] = 1
        impostors.append(singleton)

        short_line = [[0 for _ in range(22)] for _ in range(22)]
        short_line[10][8:14] = [1] * 6
        impostors.append(short_line)

        rectangle = [[0 for _ in range(22)] for _ in range(22)]
        for col in range(5, 17):
            rectangle[5][col] = 1
            rectangle[16][col] = 1
        for row in range(5, 17):
            rectangle[row][5] = 1
            rectangle[row][16] = 1
        impostors.append(rectangle)

        two_colors = self.module.generate(17, 3)
        two_colors[0][0] = 9 if two_colors[0][0] != 9 else 6
        impostors.append(two_colors)

        for index, grid in enumerate(impostors):
            with self.subTest(index=index):
                self.assertTrue(self.module.self_check(grid))

    def test_self_check_rejects_output_only_network_color(self) -> None:
        grid = self.module.generate(77, 9)
        network_color = next(
            value for row in grid for value in row if value != 0
        )
        recolored = [
            [2 if value == network_color else value for value in row]
            for row in grid
        ]
        self.assertTrue(self.module.self_check(recolored))

    def test_broad_oracle_handles_a_simple_frame(self) -> None:
        grid = [[0 for _ in range(7)] for _ in range(7)]
        for col in range(1, 6):
            grid[1][col] = 8
            grid[5][col] = 8
        for row in range(1, 6):
            grid[row][1] = 8
            grid[row][5] = 8
        output = self.module.solve_python(grid)
        for row in range(7):
            for col in range(7):
                if grid[row][col] == 8:
                    self.assertEqual(output[row][col], 8)
                elif 1 < row < 5 and 1 < col < 5:
                    self.assertEqual(output[row][col], 2)
                else:
                    self.assertEqual(output[row][col], 3)

    def test_solve_python_returns_fresh_rows(self) -> None:
        grid = self.module.generate(812, 4)
        output = self.module.solve_python(grid)
        self.assertIsNot(grid, output)
        self.assertTrue(all(a is not b for a, b in zip(grid, output)))
        original = copy.deepcopy(grid)
        output[0][0] = (output[0][0] + 1) % 10
        self.assertEqual(grid, original)


if __name__ == "__main__":
    unittest.main()
