"""Focused semantic tests for generator 453e406712ce."""

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
TASK_ID = "453e406712ce"


def canonical_row() -> dict:
    path = ROOT / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def periodic_grid(
    tile: list[list[int]],
    size: int,
    hole: tuple[int, int, int, int],
) -> list[list[int]]:
    period = len(tile)
    grid = [
        [tile[row % period][col % period] for col in range(size)]
        for row in range(size)
    ]
    r1, c1, height, width = hole
    for row in range(r1, r1 + height):
        for col in range(c1, c1 + width):
            grid[row][col] = 0
    return grid


class Generator453e406712ceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generator_module(TASK_ID)
        cls.row = canonical_row()
        cls.public_pairs = cls.row["train"] + cls.row["test"]
        cls.public_inputs = [pair["input"] for pair in cls.public_pairs]

    def test_metadata_and_single_exact_axis(self) -> None:
        self.assertEqual(self.module.VERSION, "2.0.0")
        self.assertEqual(self.module.RULE_HASH, "6dd0a63a27c0")
        self.assertEqual(set(self.module.AXES), {"scene_profile"})
        declared = set(
            self.module.AXES["scene_profile"]["valid"].split("|")
        )
        self.assertEqual(declared, set(self.module.SCENE_PROFILES))

    def test_all_public_pairs_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.public_pairs), 4)
        for index, pair in enumerate(self.public_pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                self.assertEqual(
                    self.module.canonical_profile_index(source), index
                )
                self.assertEqual(
                    self.module.solve_python(source), pair["output"]
                )
                self.assertEqual(source, pair["input"])

    def test_public_profiles_preserve_linked_morphology(self) -> None:
        for profile in self.module.PUBLIC_PROFILES:
            expected_tile = self.module._PUBLIC_TILE_CLASSES[profile]
            expected_output = self.module._PUBLIC_OUTPUT_CLASSES[profile]
            for seed in range(48):
                with self.subTest(profile=profile, seed=seed):
                    grid = self.module.generate(
                        10_000 + seed,
                        seed * 17,
                        difficulty="hard",
                        scene_profile=profile,
                    )
                    analysis = self.module._analyze(grid)
                    self.assertEqual(analysis["tile_class"], expected_tile)
                    if expected_output is not None:
                        self.assertEqual(
                            self.module._tile_class(analysis["output"]),
                            expected_output,
                        )
                    self.assertNotEqual(
                        frozenset(analysis["colors"]),
                        self.module._PUBLIC_PALETTES[profile],
                    )

    def test_every_profile_is_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for profile, spec in self.module.SCENE_SPECS.items():
                for seed in range(12):
                    with self.subTest(
                        band=band, profile=profile, seed=seed
                    ):
                        grid = self.module.generate(
                            seed,
                            seed * 31 + 9,
                            difficulty=band,
                            scene_profile=profile,
                        )
                        analysis = self.module._analyze(grid)
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(analysis["profile"], profile)
                        self.assertEqual(analysis["height"], spec.size)
                        self.assertEqual(analysis["width"], spec.size)
                        self.assertEqual(analysis["period"], spec.period)
                        self.assertEqual(
                            analysis["hole_size"], spec.hole_size
                        )
                        self.assertEqual(
                            len(analysis["boundary_sides"]),
                            spec.touched_sides,
                        )
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {"scene_profile": profile},
                        )

    def test_default_distribution_covers_every_profile(self) -> None:
        linked_floors = {"easy": 80, "medium": 80, "hard": 60}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            colors = set()
            linked = 0
            distinct = set()
            for index in range(360):
                grid = self.module.generate(
                    20_000 + band_index,
                    index,
                    difficulty=band,
                )
                analysis = self.module._analyze(grid)
                profiles[analysis["profile"]] += 1
                colors.update(analysis["colors"])
                linked += analysis["profile"] in self.module.PUBLIC_PROFILES
                distinct.add(tuple(tuple(row) for row in grid))
            self.assertEqual(set(profiles), set(self.module.SCENE_PROFILES))
            self.assertGreaterEqual(min(profiles.values()), 8)
            self.assertEqual(colors, set(range(1, 10)))
            self.assertGreaterEqual(linked, linked_floors[band])
            self.assertGreaterEqual(len(distinct), 320)

    def test_defaults_are_deterministic_fresh_and_rng_isolated(self) -> None:
        random.seed(20260719)
        global_state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(24):
                first = self.module.generate(seed, 4, difficulty=band)
                second = self.module.generate(seed, 4, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                self.assertEqual(self.module.self_check(first), [])
                self.assertNotEqual(first, self.module.solve_python(first))
        self.assertEqual(random.getstate(), global_state)

    def test_literal_public_inputs_are_not_replayed(self) -> None:
        public = {
            json.dumps(grid, separators=(",", ":"))
            for grid in self.public_inputs
        }
        for profile in self.module.SCENE_PROFILES:
            for seed in range(100):
                grid = self.module.generate(
                    seed,
                    50_000 + seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                self.assertNotIn(
                    json.dumps(grid, separators=(",", ":")), public
                )

    def test_broad_oracle_handles_rectangles_and_period_four(self) -> None:
        cases = [
            (
                [[1, 2], [2, 1]],
                8,
                (5, 6, 2, 2),
            ),
            (
                [
                    [1, 1, 1, 2],
                    [1, 1, 2, 1],
                    [1, 2, 1, 1],
                    [2, 1, 1, 1],
                ],
                9,
                (6, 6, 2, 3),
            ),
        ]
        for tile, size, hole in cases:
            with self.subTest(period=len(tile), hole=hole):
                grid = periodic_grid(tile, size, hole)
                before = copy.deepcopy(grid)
                output = self.module.solve_python(grid)
                r1, c1, height, width = hole
                expected = [
                    [
                        tile[(r1 + row) % len(tile)][
                            (c1 + col) % len(tile)
                        ]
                        for col in range(width)
                    ]
                    for row in range(height)
                ]
                self.assertEqual(output, expected)
                self.assertEqual(grid, before)

    def test_self_check_rejects_semantic_impostors(self) -> None:
        no_hole = self.module.generate(
            1, 1, scene_profile="p2_n4_h1_edge"
        )
        recovered = self.module.solve_python(no_hole)[0][0]
        for row in range(len(no_hole)):
            for col in range(len(no_hole[0])):
                if no_hole[row][col] == 0:
                    no_hole[row][col] = recovered

        rectangle = periodic_grid(
            [[1, 2], [2, 1]], 5, (3, 0, 2, 1)
        )
        interior = periodic_grid(
            [[1, 2], [2, 1]], 5, (2, 2, 2, 2)
        )
        third_color = self.module.generate(
            2, 2, scene_profile="p3_n7_h2_edge"
        )
        for row in range(len(third_color)):
            for col in range(len(third_color[0])):
                if third_color[row][col] != 0:
                    third_color[row][col] = 9
                    break
            else:
                continue
            break
        wrong_public_tile = periodic_grid(
            [[1, 2], [2, 1]], 5, (3, 0, 2, 2)
        )
        solid_output = periodic_grid(
            [[1, 2, 1], [1, 1, 1], [2, 1, 2]],
            7,
            (0, 5, 2, 2),
        )
        erased_reference = periodic_grid(
            [[1, 2], [2, 1]], 4, (0, 0, 1, 1)
        )

        impostors = {
            "no_hole": no_hole,
            "rectangular_hole": rectangle,
            "interior_hole": interior,
            "third_color": third_color,
            "wrong_public_tile": wrong_public_tile,
            "solid_output": solid_output,
            "erased_reference": erased_reference,
        }
        for label, grid in impostors.items():
            with self.subTest(label=label):
                self.assertTrue(self.module.self_check(grid))
                self.assertEqual(self.module.observe_overrides(grid), {})

    def test_unknown_controls_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, obsolete_texture="no_period")
        with self.assertRaisesRegex(ValueError, "invalid difficulty"):
            self.module.generate(0, 0, difficulty="expert")
        with self.assertRaises(ValueError):
            self.module.generate(0, 0, scene_profile="missing")

    def test_rule_hash_and_base_sources_match_canonical(self) -> None:
        program = self.row["program_solution"]
        digest = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()
        self.assertEqual(self.module.RULE_HASH, digest[:12])
        path = (
            ROOT
            / "data/base/solutions/training"
            / "f9012d9b__453e406712ce.json"
        )
        record = json.loads(path.read_text())
        self.assertEqual(record["racket_target"]["raw_code"], program)
        self.assertEqual(record["racket_target"]["target_code"], program)


if __name__ == "__main__":
    unittest.main()
