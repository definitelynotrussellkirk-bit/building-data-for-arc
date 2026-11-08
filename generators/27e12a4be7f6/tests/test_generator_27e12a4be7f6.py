"""Focused semantic regressions for generator 27e12a4be7f6."""

from __future__ import annotations

import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path


TASK_ID = "27e12a4be7f6"
ROOT = Path(__file__).resolve().parents[1]
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [*row["train"], *tests]
    raise AssertionError(f"canonical task {TASK_ID} is missing")


def copy_grid(grid):
    return [list(row) for row in grid]


class HoleCountScaleGeneratorTests(unittest.TestCase):
    def test_all_canonical_inputs_are_accepted_and_profiles_are_linked(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 5)
        profiles = Counter()
        keys = Counter()
        for pair in pairs:
            analysis = GENERATOR._analysis(pair["input"])
            self.assertEqual(analysis["errors"], [], analysis)
            profiles[analysis["scene_profile"]] += 1
            keys[analysis["key_color"]] += 1
            self.assertEqual(GENERATOR.self_check(pair["input"]), [])
            self.assertEqual(
                GENERATOR.observe_overrides(pair["input"]),
                {
                    "key_color": analysis["key_color"],
                    "scene_profile": analysis["scene_profile"],
                },
            )
        self.assertEqual(
            profiles,
            Counter(
                {
                    "canonical_square": 2,
                    "canonical_plus": 2,
                    "canonical_cup": 1,
                }
            ),
        )
        self.assertEqual(keys, Counter({2: 3, 3: 2}))

    def test_every_exact_override_works_at_both_grid_boundaries(self):
        for height in (14, 22):
            for width in (14, 22):
                for profile in GENERATOR.SCENE_PROFILES:
                    for key_color in (2, 3):
                        for seed in (17, 91):
                            grid = GENERATOR.generate(
                                seed,
                                seed * 19 + 7,
                                difficulty="hard",
                                grid_h=height,
                                grid_w=width,
                                scene_profile=profile,
                                key_color=key_color,
                            )
                            self.assertEqual((len(grid), len(grid[0])), (height, width))
                            self.assertEqual(
                                GENERATOR.observe_overrides(grid),
                                {
                                    "key_color": key_color,
                                    "scene_profile": profile,
                                },
                            )
                            self.assertEqual(
                                GENERATOR.self_check(
                                    grid,
                                    difficulty="hard",
                                    meta={
                                        "overrides": {
                                            "scene_profile": profile,
                                            "key_color": key_color,
                                        }
                                    },
                                ),
                                [],
                            )

    def test_disjoint_default_census_covers_profiles_topology_and_variation(self):
        inputs = set()
        dimensions = set()
        marker_positions = set()
        marker_quadrants = set()
        target_bboxes = set()
        oriented_shapes = set()
        profile_key_pairs = Counter()
        target_size_relations = set()

        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            keys = Counter()
            start = 1000 + 400 * band_index
            for seed in range(start, start + 240):
                grid = GENERATOR.generate(
                    seed,
                    seed * 31 + 11,
                    difficulty=band,
                )
                analysis = GENERATOR._analysis(grid)
                self.assertEqual(analysis["errors"], [], (band, seed, analysis))
                profile = analysis["scene_profile"]
                key_color = analysis["key_color"]
                profiles[profile] += 1
                keys[key_color] += 1
                profile_key_pairs[(profile, key_color)] += 1
                inputs.add(tuple(map(tuple, grid)))
                dimensions.add((len(grid), len(grid[0])))
                marker = analysis["marker"]
                marker_positions.add((len(grid), len(grid[0]), marker))
                marker_quadrants.add(
                    (
                        "bottom" if marker[0] * 2 >= len(grid) else "top",
                        "right" if marker[1] * 2 >= len(grid[0]) else "left",
                    )
                )
                needed = 1 if key_color == 2 else 2
                target = analysis["components_by_holes"][needed]
                target_bboxes.add(GENERATOR._bbox_size(target))
                oriented_shapes.add((needed, tuple(sorted(GENERATOR._normalize(target)))))
                sizes = {
                    holes: len(component)
                    for holes, component in analysis["components_by_holes"].items()
                }
                target_size = sizes[needed]
                less = sum(size < target_size for size in sizes.values())
                greater = sum(size > target_size for size in sizes.values())
                ties = sum(size == target_size for size in sizes.values())
                target_size_relations.add((less, greater, ties))

            with self.subTest(band=band, profiles=profiles, keys=keys):
                self.assertEqual(set(profiles), set(GENERATOR.SCENE_PROFILES))
                self.assertEqual(set(keys), {2, 3})
                self.assertTrue(all(count >= 15 for count in profiles.values()))

        self.assertEqual(set(profile_key_pairs), {
            (profile, key) for profile in GENERATOR.SCENE_PROFILES for key in (2, 3)
        })
        self.assertGreaterEqual(len(inputs), 715)
        self.assertGreaterEqual(len(dimensions), 30)
        self.assertGreaterEqual(len(marker_positions), 250)
        self.assertGreaterEqual(len(marker_quadrants), 3)
        self.assertGreaterEqual(len(target_bboxes), 8)
        self.assertGreaterEqual(len(oriented_shapes), 12)
        self.assertTrue(any(relation[2] == 3 for relation in target_size_relations))
        self.assertTrue(any(relation[1] == 0 and relation[2] == 1 for relation in target_size_relations))
        self.assertTrue(any(relation[1] > 0 for relation in target_size_relations))

    def test_self_check_rejects_targeted_structural_impostors(self):
        canonical = copy_grid(canonical_pairs()[0]["input"])
        mutations = []

        missing_marker = copy_grid(canonical)
        missing_marker[1][1] = 0
        mutations.append(missing_marker)

        duplicate_key = copy_grid(canonical)
        duplicate_key[0][1] = 2
        mutations.append(duplicate_key)

        filled_target_hole = copy_grid(canonical)
        filled_target_hole[9][2] = 4
        mutations.append(filled_target_hole)

        missing_zero_hole_distractor = copy_grid(canonical)
        for row in (4, 5):
            for col in (9, 10):
                missing_zero_hole_distractor[row][col] = 0
        mutations.append(missing_zero_hole_distractor)

        clipped_marker = copy_grid(canonical)
        clipped_marker[1][1] = 0
        clipped_marker[-1][-1] = 8
        mutations.append(clipped_marker)

        for mutation in mutations:
            self.assertTrue(GENERATOR.self_check(mutation), mutation)

    def test_cross_profile_recombination_is_rejected_by_distribution_predicate(self):
        grid = GENERATOR.generate(
            73,
            991,
            difficulty="medium",
            scene_profile="equal_bbox",
            key_color=2,
        )
        analysis = GENERATOR._analysis(grid)
        zero_component = analysis["components_by_holes"][0]
        top = min(row for row, _ in zero_component)
        left = min(col for _, col in zero_component)
        recombined = copy_grid(grid)
        for row, col in zero_component:
            recombined[row][col] = 0
        for row, col in GENERATOR._SQUARE_2:
            recombined[top + row][left + col] = 4

        recombined_analysis = GENERATOR._analysis(recombined)
        self.assertEqual(set(recombined_analysis["components_by_holes"]), {0, 1, 2})
        self.assertIsNone(recombined_analysis["scene_profile"])
        self.assertTrue(
            any("linked component shapes" in error for error in recombined_analysis["errors"]),
            recombined_analysis,
        )
        self.assertTrue(GENERATOR.self_check(recombined))

    def test_determinism_fresh_returns_unknowns_and_global_rng(self):
        before = random.getstate()
        first = GENERATOR.generate(31, 47, difficulty="medium")
        second = GENERATOR.generate(31, 47, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 0
        self.assertNotEqual(first, second)
        self.assertEqual(before, random.getstate())
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, palette_kind="warm")


if __name__ == "__main__":
    unittest.main()
