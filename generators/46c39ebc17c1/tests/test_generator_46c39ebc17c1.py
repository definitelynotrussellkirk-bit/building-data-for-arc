"""Focused semantic tests for generator 46c39ebc17c1."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.runner import _load_generator_module


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "46c39ebc17c1"


def canonical_rows() -> list[dict]:
    rows = []
    path = ROOT / "data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def noise_grid() -> list[list[int]]:
    palette = (1, 2, 3, 6, 8)
    return [
        [palette[(row * 2 + col * 3) % len(palette)] for col in range(30)]
        for row in range(30)
    ]


class Generator46c39ebc17c1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generator_module(TASK_ID)
        cls.rows = canonical_rows()
        cls.public_pairs = [
            pair
            for row in cls.rows
            for split in ("train", "test")
            for pair in row.get(split, [])
        ]
        cls.unique_public_inputs = {
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in cls.public_pairs
        }

    def test_metadata_and_exact_profile_axis(self) -> None:
        self.assertEqual(self.module.VERSION, "2.0.0")
        self.assertEqual(self.module.RULE_HASH, "e55ddd0b7670")
        self.assertEqual(set(self.module.AXES), {"scene_profile"})
        declared = set(
            self.module.AXES["scene_profile"]["valid"].split("|")
        )
        self.assertEqual(declared, set(self.module.SCENE_PROFILES))

    def test_all_six_canonical_pairs_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.public_pairs), 6)
        self.assertEqual(len(self.unique_public_inputs), 3)
        profiles = set()
        for index, pair in enumerate(self.public_pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                self.assertEqual(
                    self.module.solve_python(source), pair["output"]
                )
                self.assertEqual(source, pair["input"])
                profiles.add(
                    self.module.observe_overrides(source)["scene_profile"]
                )
        self.assertEqual(profiles, set(self.module.PUBLIC_PROFILES))

    def test_every_profile_is_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for profile, spec in self.module.SCENE_SPECS.items():
                expected_shapes = tuple(sorted(spec.shapes))
                for seed in range(8):
                    with self.subTest(
                        band=band, profile=profile, seed=seed
                    ):
                        grid = self.module.generate(
                            seed,
                            seed * 37 + 5,
                            difficulty=band,
                            scene_profile=profile,
                        )
                        analysis = self.module._analyze(grid)
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(analysis["profile"], profile)
                        self.assertEqual(
                            analysis["normalized_shapes"], expected_shapes
                        )
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {"scene_profile": profile},
                        )

    def test_returned_grid_has_dense_canonical_roles_and_halos(self) -> None:
        for profile in self.module.SCENE_PROFILES:
            grid = self.module.generate(
                919, 41, difficulty="hard", scene_profile=profile
            )
            analysis = self.module._analyze(grid)
            self.assertEqual((len(grid), len(grid[0])), (30, 30))
            self.assertEqual(
                {value for row in grid for value in row},
                set(self.module.NOISE_PALETTE),
            )
            self.assertNotIn(0, {value for row in grid for value in row})
            self.assertNotIn(4, {value for row in grid for value in row})
            self.assertGreaterEqual(
                min(analysis["background_counts"].values()), 40
            )
            self.assertGreaterEqual(min(analysis["halo_matches"]), 2)
            colors = {
                rectangle["color"]
                for rectangle in analysis["rectangles"]
            }
            self.assertEqual(len(colors), len(analysis["rectangles"]))

    def test_default_bands_realize_linked_and_extrapolated_profiles(self) -> None:
        expected_counts = {"easy": {2}, "medium": {3}, "hard": {4}}
        expected_profiles = {
            "easy": {
                "two_public_5x9_6x7",
                "two_extreme_4x5_7x10",
            },
            "medium": {
                "three_public_4x5_6x7_7x10",
                "three_mixed_5x5_5x9_6x7",
            },
            "hard": {
                "four_public_5x5_6x6_6x7x2",
                "four_mixed_4x5_5x5_6x6_7x10",
            },
        }
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            counts = set()
            colors = set()
            linked = 0
            distinct = set()
            for index in range(300):
                grid = self.module.generate(
                    20_000 + index,
                    band_index * 10_000 + index,
                    difficulty=band,
                )
                analysis = self.module._analyze(grid)
                profile = analysis["profile"]
                profiles[profile] += 1
                counts.add(len(analysis["rectangles"]))
                colors.update(
                    rectangle["color"]
                    for rectangle in analysis["rectangles"]
                )
                linked += profile in self.module.PUBLIC_PROFILES
                distinct.add(tuple(tuple(row) for row in grid))
            self.assertEqual(set(profiles), expected_profiles[band])
            self.assertEqual(counts, expected_counts[band])
            self.assertEqual(colors, set(self.module.NOISE_PALETTE))
            self.assertGreaterEqual(linked, 100)
            self.assertLessEqual(linked, 200)
            self.assertEqual(len(distinct), 300)

    def test_defaults_are_deterministic_fresh_and_rng_isolated(self) -> None:
        random.seed(20260719)
        state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(20):
                first = self.module.generate(seed, 7, difficulty=band)
                second = self.module.generate(seed, 7, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                before = copy.deepcopy(first)
                output = self.module.solve_python(first)
                self.assertEqual(first, before)
                self.assertNotEqual(output, first)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, output))
                )
        self.assertEqual(random.getstate(), state)

    def test_literal_public_inputs_are_not_replayed(self) -> None:
        for profile in self.module.SCENE_PROFILES:
            for seed in range(30):
                grid = self.module.generate(
                    seed,
                    50_000 + seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                self.assertNotIn(
                    json.dumps(grid, separators=(",", ":")),
                    self.unique_public_inputs,
                )

    def test_oracle_recolors_only_qualifying_rectangles(self) -> None:
        grid = [[(row + col) % 3 + 1 for col in range(18)] for row in range(14)]
        for row in range(2, 7):
            for col in range(3, 10):
                grid[row][col] = 8
        for row in range(8, 12):
            for col in range(12, 16):
                grid[row][col] = 6
        grid[0][0] = 9
        before = copy.deepcopy(grid)
        output = self.module.solve_python(grid)
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                in_first = 2 <= row <= 6 and 3 <= col <= 9
                in_second = 8 <= row <= 11 and 12 <= col <= 15
                self.assertEqual(
                    output[row][col],
                    4 if in_first or in_second else grid[row][col],
                )
        self.assertEqual(grid, before)

    def test_self_check_rejects_semantic_impostors(self) -> None:
        no_rectangles = noise_grid()
        wrong_size = self.module.generate(1, 1)[:-1]
        output_color = self.module.generate(2, 2)
        output_color[0][0] = 4
        same_rectangle_colors = self.module.generate(
            3,
            3,
            scene_profile="two_public_5x9_6x7",
        )
        rectangles = self.module._analyze(
            same_rectangle_colors
        )["rectangles"]
        target_color = rectangles[0]["color"]
        for row, col in rectangles[1]["cells"]:
            same_rectangle_colors[row][col] = target_color
        wrong_profile = noise_grid()
        for row in range(2, 6):
            for col in range(2, 6):
                wrong_profile[row][col] = 1
        for row in range(15, 20):
            for col in range(15, 20):
                wrong_profile[row][col] = 2
        impostors = {
            "no_rectangles": no_rectangles,
            "wrong_size": wrong_size,
            "output_color": output_color,
            "same_rectangle_colors": same_rectangle_colors,
            "wrong_profile": wrong_profile,
        }
        for label, grid in impostors.items():
            with self.subTest(label=label):
                self.assertTrue(self.module.self_check(grid))
                self.assertEqual(self.module.observe_overrides(grid), {})

    def test_unknown_controls_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, obsolete_texture="sparse")
        with self.assertRaisesRegex(ValueError, "invalid difficulty"):
            self.module.generate(0, 0, difficulty="expert")
        with self.assertRaises(ValueError):
            self.module.generate(0, 0, scene_profile="missing")

    def test_rule_hash_and_both_base_sources_match_canonical(self) -> None:
        programs = {row["program_solution"] for row in self.rows}
        self.assertEqual(len(programs), 1)
        program = programs.pop()
        digest = hashlib.sha256(program.encode()).hexdigest()
        self.assertEqual(self.module.RULE_HASH, digest[:12])
        paths = (
            ROOT
            / "data/base/solutions/training"
            / "25094a63__46c39ebc17c1.json",
            ROOT
            / "data/base/solutions/augmented"
            / "25094a63__5e0649bc7f49.json",
        )
        for path in paths:
            record = json.loads(path.read_text())
            self.assertEqual(record["racket_target"]["raw_code"], program)
            self.assertEqual(record["racket_target"]["target_code"], program)
            self.assertEqual(
                record["primitive_metadata"]["primitive_chain"],
                ["rows", "cols", "range", "at", "build-grid"],
            )


if __name__ == "__main__":
    unittest.main()
