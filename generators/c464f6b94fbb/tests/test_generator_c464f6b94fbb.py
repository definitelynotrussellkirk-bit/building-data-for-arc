from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "c464f6b94fbb"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/e06827914c5c/H8__c464f6b94fbb.json"


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def public_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def numeric_grid(grid):
    return [[int(value) for value in row] if isinstance(row, str) else row for row in grid]


class GeneratorTests(unittest.TestCase):
    def test_all_public_pairs_exact(self):
        pairs = public_pairs()
        self.assertEqual(len(pairs), 3)
        for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
            grid = MODULE.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, numeric_grid(pair["input"]))
            self.assertEqual(MODULE.rule_mirror(grid), numeric_grid(pair["output"]))
            self.assertEqual(MODULE.self_check(grid), [])
            self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
            self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})

    def test_every_general_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(50):
                    grid = MODULE.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])

    def test_profiles_exercise_declared_semantics(self):
        for seed in range(100):
            row_tie = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="tie_by_row"))
            col_tie = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="tie_by_column"))
            row_group = [obj for obj in row_tie["components"] if obj["size"] == 4]
            col_group = [obj for obj in col_tie["components"] if obj["size"] == 4]
            self.assertEqual([obj["r1"] for obj in sorted(row_group, key=lambda obj: obj["r1"])], sorted(obj["r1"] for obj in row_group))
            self.assertEqual(len({obj["r1"] for obj in row_group}), 2)
            self.assertEqual(len({obj["r1"] for obj in col_group}), 1)
            self.assertEqual(len({obj["c1"] for obj in col_group}), 2)

            two = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="two_objects"))
            five = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="five_objects"))
            same = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="same_color_objects"))
            holes = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="internal_holes"))
            heights = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="varied_heights"))
            single = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="single_cell_member"))
            self.assertEqual(len(two["components"]), 2)
            self.assertEqual(len(five["components"]), 5)
            self.assertLess(len({obj["color"] for obj in same["components"]}), len(same["components"]))
            self.assertTrue(any(obj["bbox_area"] > obj["size"] for obj in holes["components"]))
            self.assertEqual(len({obj["height"] for obj in heights["components"]}), len(heights["components"]))
            self.assertIn(1, {obj["size"] for obj in single["components"]})

    def test_exact_sort_key_raw_crops_and_layout(self):
        grid = [
            [0, 2, 2, 0, 3, 3, 0, 0, 0],
            [0, 2, 0, 0, 0, 0, 0, 5, 5],
            [0, 2, 2, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 4, 4, 0, 0, 0],
        ]
        analysis = MODULE._analysis(grid)
        self.assertEqual(analysis["errors"], [])
        self.assertEqual(
            [(obj["color"], obj["size"], obj["r1"], obj["c1"]) for obj in analysis["ordered"]],
            [(2, 5, 0, 1), (3, 2, 0, 4), (5, 2, 1, 7), (4, 2, 3, 4)],
        )
        self.assertEqual(
            analysis["output"],
            [
                [2, 2, 0, 3, 3, 0, 5, 5, 0, 4, 4],
                [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            ],
        )
        left = 0
        for index, obj in enumerate(analysis["ordered"]):
            actual = [row[left:left + obj["width"]] for row in analysis["output"][:obj["height"]]]
            self.assertEqual(actual, obj["crop"])
            left += obj["width"]
            if index + 1 < len(analysis["ordered"]):
                self.assertTrue(all(row[left] == 0 for row in analysis["output"]))
                left += 1

    def test_distribution(self):
        profiles = Counter()
        inputs = set()
        outputs = set()
        canvas_shapes = set()
        object_counts = set()
        sizes = set()
        colors = set()
        bbox_shapes = set()
        for seed in range(2400):
            grid = MODULE.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            canvas_shapes.add((len(grid), len(grid[0])))
            object_counts.add(len(analysis["components"]))
            sizes.update(obj["size"] for obj in analysis["components"])
            colors.update(obj["color"] for obj in analysis["components"])
            bbox_shapes.update((obj["height"], obj["width"]) for obj in analysis["components"])
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 1900)
        self.assertGreater(len(outputs), 500)
        self.assertGreater(len(canvas_shapes), 120)
        self.assertEqual(object_counts, {2, 3, 5})
        self.assertTrue({1, 2, 3, 4, 5, 6, 8}.issubset(sizes))
        self.assertEqual(colors, set(range(1, 10)))
        self.assertTrue({(1, 1), (1, 4), (2, 2), (2, 3), (3, 2), (3, 3), (4, 2), (5, 1)}.issubset(bbox_shapes))

    def test_malformed_inputs_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)], [[1], [1, 2]]]
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MODULE.rule_mirror([])

    def test_determinism_freshness_and_unknowns(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"n_objects": 4}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="extreme")
        random.seed(83)
        state = random.getstate()
        first = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_source_hash_and_base_sync(self):
        source = canonical_row()["program_solution"]
        expected_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, expected_hash)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
