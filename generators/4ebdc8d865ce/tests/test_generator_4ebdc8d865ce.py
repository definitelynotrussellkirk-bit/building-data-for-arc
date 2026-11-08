"""Focused semantic regressions for generator 4ebdc8d865ce."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "4ebdc8d865ce"
GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.4ebdc8d865ce.generator"
)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


class Generator4ebdc8d865ceTests(unittest.TestCase):
    def test_rule_authorities_and_metadata_are_synchronized(self):
        row = canonical_row()
        self.assertEqual("3.0.0", GENERATOR.VERSION)
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(row["program_solution"]),
        )
        base_root = next(
            path
            for path in (
                ROOT / "data" / "base" / "solutions",
                ROOT / "shared" / "data" / "base" / "solutions",
            )
            if path.is_dir()
        )
        base_paths = sorted(base_root.rglob(f"*{TASK_ID}*.json"))
        self.assertEqual(1, len(base_paths))
        base = json.loads(base_paths[0].read_text())
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(base["racket_target"]["target_code"]),
        )
        self.assertEqual({"scene_family"}, set(GENERATOR.AXES))

    def test_every_canonical_pair_is_accepted_and_exact(self):
        pairs = canonical_row()["train"] + canonical_row()["test"]
        self.assertEqual(5, len(pairs))
        for index, pair in enumerate(pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                analysis = GENERATOR._analyze(source)
                self.assertEqual([], analysis["errors"])
                self.assertEqual(
                    f"public_{index + 1}",
                    analysis["facts"]["canonical_profile"],
                )
                self.assertEqual(pair["output"], GENERATOR.rule_mirror(source))
                self.assertEqual(pair["input"], source)

    def test_family_override_is_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for family in GENERATOR.SCENE_FAMILIES:
                for seed in range(60):
                    grid = GENERATOR.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_family=family,
                    )
                    self.assertEqual([], GENERATOR.self_check(grid))
                    self.assertEqual(
                        {"scene_family": family},
                        GENERATOR.observe_overrides(grid),
                    )

    def test_defaults_are_deterministic_fresh_and_rng_isolated(self):
        global_state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                first = GENERATOR.generate(seed, seed * 19 + 5, difficulty=band)
                second = GENERATOR.generate(seed, seed * 19 + 5, difficulty=band)
                pristine = copy.deepcopy(first)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(all(a is not b for a, b in zip(first, second)))
                first[0][0] = (first[0][0] + 1) % 10
                self.assertEqual(
                    pristine,
                    GENERATOR.generate(seed, seed * 19 + 5, difficulty=band),
                )
                self.assertEqual(global_state, random.getstate())

    def test_distribution_covers_profiles_components_and_shapes(self):
        census = {band: Counter() for band in ("easy", "medium", "hard")}
        profiles = set()
        shapes = set()
        inputs = set()
        outputs = set()
        for band_index, band in enumerate(census):
            for seed in range(1_000):
                grid = GENERATOR.generate(
                    100_000 * band_index + seed,
                    seed * 23 + 7,
                    difficulty=band,
                )
                analysis = GENERATOR._analyze(grid)
                self.assertEqual([], analysis["errors"])
                facts = analysis["facts"]
                census[band][facts["scene_family"]] += 1
                census[band][f"isolated_{facts['n_isolated']}"] += 1
                census[band][f"groups_{facts['n_groups']}"] += 1
                profiles.add(facts["canonical_profile"])
                shapes.add((len(grid), len(grid[0])))
                inputs.add(tuple(map(tuple, grid)))
                output = GENERATOR.rule_mirror(grid)
                outputs.add(tuple(map(tuple, output)))
                self.assertNotEqual(grid, output)
        for counts in census.values():
            self.assertGreaterEqual(counts["linked"], 400)
            self.assertGreaterEqual(counts["generalized"], 400)
        self.assertEqual(
            {None, "public_1", "public_2", "public_3", "public_4", "public_5"},
            profiles,
        )
        self.assertGreaterEqual(len(shapes), 80)
        self.assertGreaterEqual(len(inputs), 2_600)
        self.assertGreaterEqual(len(outputs), 2_600)
        self.assertLessEqual(len(outputs), len(inputs))
        self.assertGreater(census["hard"]["groups_4"], 0)
        self.assertGreater(census["hard"]["isolated_6"], 0)

    def test_only_isolated_twos_change_to_one(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                grid = GENERATOR.generate(seed, seed * 29 + 11, difficulty=band)
                analysis = GENERATOR._analyze(grid)
                output = GENERATOR.rule_mirror(grid)
                isolated = set(analysis["facts"]["isolated"])
                for row in range(len(grid)):
                    for col in range(len(grid[0])):
                        expected = 1 if (row, col) in isolated else grid[row][col]
                        self.assertEqual(expected, output[row][col])

    def test_self_check_rejects_semantic_impostors(self):
        valid = GENERATOR.generate(
            41,
            43,
            difficulty="medium",
            scene_family="generalized",
        )
        with_one = copy.deepcopy(valid)
        with_one[0][0] = 1
        with_three = copy.deepcopy(valid)
        with_three[0][0] = 3
        impostors = [
            [[0] * 5 for _ in range(4)],
            [[2] * 5 for _ in range(4)],
            [[0, 0, 2, 0, 0]] + [[0] * 5 for _ in range(3)],
            [[2, 2, 2, 0, 0]] + [[0] * 5 for _ in range(3)],
            [row[:-1] if index == 0 else row for index, row in enumerate(valid)],
            [[True if value else 0 for value in row] for row in valid],
            with_one,
            with_three,
        ]
        for index, grid in enumerate(impostors):
            with self.subTest(index=index):
                self.assertTrue(GENERATOR.self_check(grid))

    def test_invalid_calls_fail_loudly(self):
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, mystery_axis=3)
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, scene_family="not-a-family")


if __name__ == "__main__":
    unittest.main()
