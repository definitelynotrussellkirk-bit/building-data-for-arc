"""Focused semantic regressions for generator 33f9169a335e."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from solvers.grounded_rules import GROUNDED_RULES


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "33f9169a335e"
GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.33f9169a335e.generator"
)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


class Generator33f9169a335eTests(unittest.TestCase):
    def test_rule_authorities_and_metadata_are_synchronized(self):
        row = canonical_row()
        self.assertEqual("3.0.0", GENERATOR.VERSION)
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(row["program_solution"]),
        )
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(GROUNDED_RULES[TASK_ID]),
        )
        base = json.loads(
            (
                ROOT
                / "data/base/solutions/training"
                / f"54d82841__{TASK_ID}.json"
            ).read_text()
        )
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(base["racket_target"]["target_code"]),
        )
        self.assertEqual({"scene_family"}, set(GENERATOR.AXES))

    def test_every_canonical_pair_is_structurally_accepted_and_exact(self):
        pairs = canonical_row()["train"] + canonical_row()["test"]
        self.assertEqual(4, len(pairs))
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
                    with self.subTest(band=band, family=family, seed=seed):
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

    def test_distribution_covers_profiles_counts_layouts_and_palettes(self):
        census = {band: Counter() for band in ("easy", "medium", "hard")}
        profiles = set()
        colors = set()
        shapes = set()
        inputs = set()
        outputs = set()
        repeated_color = 0
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
                census[band][f"count_{facts['n_us']}"] += 1
                census[band][f"layout_{facts['layout']}"] += 1
                profiles.add(facts["canonical_profile"])
                colors.update(facts["colors"])
                shapes.add((len(grid), len(grid[0])))
                inputs.add(tuple(map(tuple, grid)))
                output = GENERATOR.rule_mirror(grid)
                outputs.add(tuple(map(tuple, output)))
                self.assertNotEqual(grid, output)
                if facts["n_us"] > len(facts["colors"]):
                    repeated_color += 1
        for counts in census.values():
            self.assertGreaterEqual(counts["linked"], 400)
            self.assertGreaterEqual(counts["generalized"], 400)
            self.assertGreater(counts["layout_row"], 0)
            self.assertGreater(counts["layout_staggered"], 0)
        self.assertEqual(
            {None, "public_1", "public_2", "public_3", "public_4"},
            profiles,
        )
        self.assertEqual(set(GENERATOR.COLORS), colors)
        self.assertGreaterEqual(len(shapes), 40)
        self.assertGreaterEqual(len(inputs), 2_950)
        self.assertEqual(len(inputs), len(outputs))
        self.assertGreater(repeated_color, 300)

    def test_every_detected_gap_and_only_that_gap_is_marked(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                grid = GENERATOR.generate(seed, seed * 29 + 11, difficulty=band)
                analysis = GENERATOR._analyze(grid)
                output = GENERATOR.rule_mirror(grid)
                gaps = set(analysis["facts"]["gap_columns"])
                self.assertEqual(
                    gaps,
                    {col for col, value in enumerate(output[-1]) if value == 4},
                )
                self.assertEqual(grid[:-1], output[:-1])
                self.assertTrue(all(grid[-1][col] == 0 for col in gaps))

    def test_self_check_rejects_semantic_impostors(self):
        valid = GENERATOR.generate(
            41,
            43,
            difficulty="medium",
            scene_family="generalized",
        )
        with_orange = copy.deepcopy(valid)
        with_orange[0][0] = 4
        occupied_bottom = copy.deepcopy(valid)
        occupied_bottom[-1][0] = 2
        stray = copy.deepcopy(valid)
        stray[-2][0] = 3
        impostors = [
            [[0 for _ in row] for row in valid],
            [[1] * 5 for _ in range(5)],
            [[0, 0, 2, 0, 0] for _ in range(5)],
            [[2, 2, 2, 0, 0] for _ in range(5)],
            [[2, 2, 0, 0, 0], [2, 2, 0, 0, 0]] + [[0] * 5 for _ in range(3)],
            [row[:-1] if index == 0 else row for index, row in enumerate(valid)],
            [[True if value else 0 for value in row] for row in valid],
            with_orange,
            occupied_bottom,
            stray,
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
