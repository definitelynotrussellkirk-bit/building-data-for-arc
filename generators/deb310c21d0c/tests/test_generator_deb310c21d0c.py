from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.per_puzzle.deb310c21d0c import generator


ROOT = Path(__file__).resolve().parents[1]
BASE_PATHS = (
    ROOT
    / "data/base/solutions/augmented/"
    "b74ca5d1__8f22e02e4bdd.json",
    ROOT
    / "data/base/solutions/training/"
    "b74ca5d1__deb310c21d0c.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in (
            ROOT / "data/canonical/puzzles.jsonl"
        ).read_text().splitlines()
        if json.loads(line).get("task_id")
        == generator.TASK_ID
    ]


def unique_public_pairs():
    pairs = []
    seen = set()
    for row in canonical_rows():
        for split in ("train", "test"):
            value = row.get(split)
            candidates = (
                [value]
                if isinstance(value, dict)
                else value or []
            )
            for pair in candidates:
                frozen = tuple(
                    tuple(grid_row)
                    for grid_row in pair["input"]
                )
                if frozen not in seen:
                    seen.add(frozen)
                    pairs.append(pair)
    return pairs


def rotate_180(grid):
    return [
        list(reversed(row))
        for row in reversed(grid)
    ]


class GeneratorDeb310c21d0cTests(unittest.TestCase):
    def test_all_public_pairs_are_positive_controls(self):
        pairs = unique_public_pairs()
        self.assertEqual(len(pairs), 5)
        observed = set()
        for index, pair in enumerate(pairs):
            grid = pair["input"]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(
                generator.exact_public_profile_index(grid),
                index,
            )
            profile = generator.observe_overrides(
                grid
            )["scene_profile"]
            observed.add(profile)
            self.assertEqual(
                generator.rule_mirror(grid),
                pair["output"],
            )
        self.assertEqual(
            observed,
            set(generator.SCENE_PROFILES),
        )

    def test_every_axis_value_is_constructive_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.SCENE_PROFILES:
                for seed in range(12):
                    grid = generator.generate(
                        1000 + seed,
                        seed * 41,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(
                        generator.self_check(
                            grid,
                            difficulty=band,
                            meta={
                                "overrides": {
                                    "scene_profile": profile,
                                },
                            },
                        ),
                        [],
                    )
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertNotEqual(
                        generator.rule_mirror(grid),
                        grid,
                    )

    def test_default_distribution_covers_profiles_and_difficulty(self):
        counts = {}
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            band_counts = {
                profile: 0
                for profile in generator.SCENE_PROFILES
            }
            for seed in range(600):
                grid = generator.generate(
                    3000 + seed,
                    seed * 43 + band_index,
                    difficulty=band,
                )
                profile = generator.observe_overrides(
                    grid
                )["scene_profile"]
                band_counts[profile] += 1
            self.assertTrue(
                all(value >= 35 for value in band_counts.values())
            )
            counts[band] = band_counts
        self.assertGreater(
            counts["easy"][
                "four_centered_hole_two_markers"
            ],
            counts["easy"][
                "five_twin_three_markers"
            ],
        )
        self.assertGreater(
            counts["hard"][
                "five_twin_three_markers"
            ],
            counts["hard"][
                "five_mixed_two_markers"
            ],
        )

    def test_palette_and_literal_prior_are_bounded(self):
        backgrounds = set()
        colors = set()
        exact = 0
        for seed in range(1200):
            grid = generator.generate(
                5000 + seed,
                seed * 47,
                difficulty=(
                    "easy",
                    "medium",
                    "hard",
                )[seed % 3],
            )
            analysis = generator._analyze_scene(grid)
            self.assertIsNotNone(analysis)
            backgrounds.add(analysis["background"])
            colors.update(
                value
                for row in grid
                for value in row
            )
            exact += (
                generator.exact_public_profile_index(grid)
                is not None
            )
        self.assertEqual(backgrounds, set(range(10)))
        self.assertEqual(colors, set(range(10)))
        self.assertGreaterEqual(exact, 35)
        self.assertLessEqual(exact, 85)

    def test_negative_recombinations_are_rejected(self):
        source = copy.deepcopy(
            unique_public_pairs()[0]["input"]
        )
        mutations = []

        missing_marker = copy.deepcopy(source)
        missing_marker[0][0] = 2
        mutations.append(missing_marker)

        wrong_marker = copy.deepcopy(source)
        wrong_marker[0][0] = 4
        mutations.append(wrong_marker)

        third_motif_color = copy.deepcopy(source)
        third_motif_color[3][15] = 7
        mutations.append(third_motif_color)

        extra_stray = copy.deepcopy(source)
        extra_stray[15][2] = 7
        mutations.append(extra_stray)

        mutations.append([row[:-1] for row in source])
        mutations.append([[True]])
        mutations.append([[10]])
        mutations.append([[0], [0, 0]])

        for grid in mutations:
            self.assertTrue(
                generator.self_check(grid),
                msg="mutation unexpectedly passed",
            )
            self.assertEqual(
                generator.observe_overrides(grid),
                {},
            )

    def test_recolor_and_rotation_metamorphisms(self):
        source = generator.generate(
            7001,
            83,
            difficulty="hard",
            scene_profile="five_twin_three_markers",
        )
        expected = generator.rule_mirror(source)

        mapping = {
            value: (value * 3 + 1) % 10
            for value in range(10)
        }
        recolored = [
            [mapping[value] for value in row]
            for row in source
        ]
        recolored_expected = [
            [mapping[value] for value in row]
            for row in expected
        ]
        self.assertEqual(
            generator.rule_mirror(recolored),
            recolored_expected,
        )

        rotated = rotate_180(source)
        self.assertEqual(
            generator.rule_mirror(rotated),
            rotate_180(expected),
        )
        self.assertEqual(
            generator.observe_overrides(rotated),
            generator.observe_overrides(source),
        )

    def test_determinism_fresh_returns_and_global_rng(self):
        before = random.getstate()
        first = generator.generate(
            8111,
            97,
            difficulty="medium",
        )
        middle = random.getstate()
        second = generator.generate(
            8111,
            97,
            difficulty="medium",
        )
        after = random.getstate()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertNotEqual(first, second)

    def test_rule_hash_and_base_sources_are_synchronized(self):
        rows = canonical_rows()
        sources = {
            row["program_solution"]
            for row in rows
        }
        self.assertEqual(len(sources), 1)
        source = next(iter(sources))
        normalized_hash = hashlib.sha256(
            " ".join(source.split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(
            generator.RULE_HASH,
            normalized_hash,
        )
        for path in BASE_PATHS:
            record = json.loads(path.read_text())
            for field in ("raw_code", "target_code"):
                self.assertEqual(
                    record["racket_target"][field],
                    source,
                )
            self.assertTrue(
                record["primitive_metadata"][
                    "primitive_chain"
                ]
            )
            self.assertTrue(
                record["primitive_metadata"][
                    "family_chain"
                ]
            )


if __name__ == "__main__":
    unittest.main()
