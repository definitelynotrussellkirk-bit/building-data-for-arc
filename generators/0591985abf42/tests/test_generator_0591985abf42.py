from __future__ import annotations

import copy
import hashlib
from importlib import import_module
import json
from pathlib import Path
import random
import unittest

from solvers.grounded_rules import GROUNDED_RULES


generator = import_module(
    "puzzle_generators.per_puzzle.0591985abf42.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = (
    ROOT
    / "data/base/solutions/training/"
    "ad3b40cf__0591985abf42.json"
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


class Generator0591985abf42Tests(unittest.TestCase):
    def test_all_public_pairs_are_positive_controls(self):
        pairs = unique_public_pairs()
        self.assertEqual(len(pairs), 4)
        observed = []
        for index, pair in enumerate(pairs):
            grid = pair["input"]
            self.assertEqual(generator.self_check(grid), [])
            observed.append(
                generator.observe_overrides(
                    grid
                )["scene_profile"]
            )
            self.assertEqual(
                generator.canonical_profile_index(grid),
                index,
            )
            self.assertEqual(
                generator.exact_public_profile_index(grid),
                index,
            )
            before = copy.deepcopy(grid)
            self.assertEqual(
                generator.rule_mirror(grid),
                pair["output"],
            )
            self.assertEqual(grid, before)
        self.assertEqual(
            observed,
            list(generator.SCENE_PROFILES[:4]),
        )

    def test_every_profile_is_constructive_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.SCENE_PROFILES:
                for seed in range(30):
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
                    analysis = generator._analyze_scene(grid)
                    output = generator.rule_mirror(grid)
                    self.assertNotEqual(output, grid)
                    self.assertEqual(
                        sum(
                            left != right
                            for input_row, output_row in zip(
                                grid,
                                output,
                            )
                            for left, right in zip(
                                input_row,
                                output_row,
                            )
                        ),
                        analysis["rare_count"],
                    )

    def test_exact_profiles_preserve_linked_morphology(self):
        for profile_index, profile in enumerate(
            generator.SCENE_PROFILES[:4]
        ):
            spec = generator._PROFILE_SPECS[profile]
            expected_rare = generator._component_signature(
                spec["rare_shapes"]
            )
            expected_decoy = generator._component_signature(
                spec["decoy_shapes"]
            )
            seen_grids = set()
            for seed in range(80):
                grid = generator.generate(
                    2000 + seed,
                    seed * 43,
                    difficulty=(
                        "easy",
                        "medium",
                        "hard",
                    )[seed % 3],
                    scene_profile=profile,
                )
                analysis = generator._analyze_scene(grid)
                self.assertEqual(
                    generator.canonical_profile_index(grid),
                    profile_index,
                )
                self.assertEqual(
                    generator._component_signature(
                        analysis["rare_components"]
                    ),
                    expected_rare,
                )
                self.assertEqual(
                    generator._component_signature(
                        analysis["decoy_components"]
                    ),
                    expected_decoy,
                )
                self.assertEqual(
                    (
                        analysis["size"],
                        analysis["kind"],
                        analysis["param"],
                        analysis["rare_color"],
                        analysis["decoy_color"],
                    ),
                    (
                        spec["size"],
                        spec["kind"],
                        spec["param"],
                        spec["rare_color"],
                        spec["decoy_color"],
                    ),
                )
                seen_grids.add(
                    tuple(tuple(row) for row in grid)
                )
            self.assertGreaterEqual(len(seen_grids), 65)

    def test_default_distribution_covers_profiles_guides_and_sizes(self):
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            profiles = {
                profile: 0
                for profile in generator.SCENE_PROFILES
            }
            guides = {
                kind: 0
                for kind in generator.LINE_KINDS
            }
            sizes = set()
            for seed in range(600):
                grid = generator.generate(
                    3000 + seed,
                    seed * 47 + band_index,
                    difficulty=band,
                )
                analysis = generator._analyze_scene(grid)
                profiles[analysis["scene_profile"]] += 1
                guides[analysis["kind"]] += 1
                sizes.add(analysis["size"])
            self.assertTrue(
                all(value >= 30 for value in profiles.values()),
                profiles,
            )
            self.assertTrue(
                all(value >= 30 for value in guides.values()),
                guides,
            )
            self.assertGreaterEqual(len(sizes), 5)
            self.assertGreater(
                profiles["generalized"],
                profiles["anti_16_r7_d14"],
            )

    def test_literal_public_prior_is_bounded(self):
        literal = 0
        total = 0
        for profile in generator.SCENE_PROFILES[:4]:
            for seed in range(300):
                grid = generator.generate(
                    5000 + seed,
                    seed * 53,
                    difficulty=(
                        "easy",
                        "medium",
                        "hard",
                    )[seed % 3],
                    scene_profile=profile,
                )
                total += 1
                literal += (
                    generator.exact_public_profile_index(grid)
                    is not None
                )
        self.assertEqual(total, 1200)
        self.assertGreaterEqual(literal, 10)
        self.assertLessEqual(literal, 60)

    def test_task_specific_mutations_are_rejected(self):
        source = copy.deepcopy(
            unique_public_pairs()[0]["input"]
        )
        mutations = []

        broken_guide = copy.deepcopy(source)
        broken_guide[0][4] = 8
        mutations.append(broken_guide)

        wrong_guide_color = copy.deepcopy(source)
        for row in range(len(wrong_guide_color)):
            wrong_guide_color[row][4] = 3
        mutations.append(wrong_guide_color)

        tied_counts = copy.deepcopy(source)
        tied_counts[0][6] = 5
        mutations.append(tied_counts)

        both_sides = copy.deepcopy(source)
        both_sides[4][6] = 8
        both_sides[4][2] = 2
        mutations.append(both_sides)

        blocked_reflection = copy.deepcopy(source)
        blocked_reflection[1][2] = 2
        mutations.append(blocked_reflection)

        wrong_background = [
            [
                0 if value == 8 else value
                for value in row
            ]
            for row in source
        ]
        mutations.append(wrong_background)

        mutations.append([row[:-1] for row in source])
        mutations.append([[True]])
        mutations.append([[10]])
        mutations.append([[8], [8, 8]])

        for grid in mutations:
            self.assertTrue(
                generator.self_check(grid),
                msg="mutation unexpectedly passed",
            )
            self.assertEqual(
                generator.observe_overrides(grid),
                {},
            )

    def test_broad_oracle_priority_clipping_and_input_purity(self):
        clipping = [[8 for _col in range(5)] for _row in range(5)]
        clipping[1] = [1, 1, 1, 1, 1]
        clipping[0][0] = 2
        clipping[4][4] = 2
        clipping[0][2] = 3
        clipping[0][3] = 3
        clipping[4][0] = 3
        before = copy.deepcopy(clipping)
        output = generator.rule_mirror(clipping)
        self.assertEqual(clipping, before)
        self.assertEqual(output[2][0], 2)
        self.assertEqual(output[4][4], 2)
        self.assertEqual(
            sum(
                left != right
                for input_row, output_row in zip(clipping, output)
                for left, right in zip(input_row, output_row)
            ),
            1,
        )

        priority = [[8 for _col in range(7)] for _row in range(7)]
        for index in range(7):
            priority[3][index] = 1
            priority[index][3] = 1
        priority[1][0] = 2
        priority[1][1] = 2
        priority[5][4] = 3
        priority[5][5] = 3
        priority[5][6] = 3
        output = generator.rule_mirror(priority)
        self.assertEqual(output[5][0], 2)
        self.assertEqual(output[5][1], 2)
        self.assertEqual(output[1][5], 8)

    def test_invalid_calls_are_loud(self):
        with self.assertRaises(ValueError):
            generator.generate(
                1,
                2,
                difficulty="extreme",
            )
        with self.assertRaises(ValueError):
            generator.generate(
                1,
                2,
                unknown_axis="x",
            )
        with self.assertRaises(ValueError):
            generator.generate(
                1,
                2,
                scene_profile="unknown",
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
        first[0][0] = 0
        self.assertNotEqual(first, second)

    def test_rule_hash_and_all_sources_are_synchronized(self):
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
        self.assertEqual(generator.RULE_HASH, normalized_hash)
        self.assertEqual(
            GROUNDED_RULES[generator.TASK_ID],
            source,
        )
        record = json.loads(BASE_PATH.read_text())
        for field in ("raw_code", "target_code"):
            self.assertEqual(
                record["racket_target"][field],
                source,
            )
        self.assertIn(
            "count-if",
            record["primitive_metadata"]["primitive_chain"],
        )
        self.assertTrue(
            record["primitive_metadata"]["family_chain"]
        )


if __name__ == "__main__":
    unittest.main()
