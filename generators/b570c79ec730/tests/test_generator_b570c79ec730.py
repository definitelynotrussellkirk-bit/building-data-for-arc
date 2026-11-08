from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "b570c79ec730"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/training/4347f46a__b570c79ec730.json"


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def canonical_pairs():
    rows = canonical_rows()
    return rows[0]["train"] + rows[0]["test"]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_public_profiles(self):
        self.assertEqual(len(canonical_rows()), 1)
        self.assertEqual(len(canonical_pairs()), 4)
        self.assertEqual(len({tuple(map(tuple, pair["input"])) for pair in canonical_pairs()}), 4)
        for profile, pair in zip(MODULE.PUBLIC_PROFILES, canonical_pairs()):
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MODULE.self_check(pair["input"]), [])
            self.assertEqual(MODULE.generate(1, 2, scene_profile=profile), pair["input"])
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), profile)

    def test_every_general_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(40):
                    grid = MODULE.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertGreater(analysis["erased_cells"], 0)
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])

    def test_strict_bbox_interior_semantics(self):
        grid = [[0] * 10 for _ in range(8)]
        for row in range(1, 5):
            for col in range(1, 6):
                grid[row][col] = 4
        grid[1][3] = 0
        for col in range(2, 8):
            grid[7][col] = 7
        output = MODULE.rule_mirror(grid)
        self.assertEqual(output[1][3], 0)
        self.assertEqual(output[1][2], 4)
        self.assertEqual(output[2][2], 0)
        self.assertEqual(output[7][4], 7)
        analysis = MODULE._analysis(grid)
        self.assertEqual(analysis["scene_profile"], "mixed_components")
        self.assertEqual(analysis["transformed_components"], 1)
        self.assertEqual(analysis["unchanged_components"], 1)

    def test_component_identity_is_color_specific_and_four_connected(self):
        grid = [[0] * 12 for _ in range(8)]
        for top, left in ((1, 1), (1, 7)):
            for row in range(top, top + 4):
                for col in range(left, left + 4):
                    grid[row][col] = 6
        analysis = MODULE._analysis(grid)
        self.assertEqual(analysis["component_count"], 2)
        self.assertEqual(analysis["scene_profile"], "same_color_separate")
        self.assertEqual(analysis["erased_cells"], 8)

    def test_distribution_and_diversity(self):
        profiles = Counter()
        inputs, outputs, shapes, erased = set(), set(), set(), set()
        colors = set()
        component_counts = set()
        for seed in range(2400):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MODULE.generate(seed, seed * 29, difficulty=band)
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [], (seed, analysis))
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            colors.update(value for row in grid for value in row)
            component_counts.add(analysis["component_count"])
            erased.add(analysis["erased_cells"])
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2000)
        self.assertGreater(len(outputs), 1900)
        self.assertGreater(len(shapes), 70)
        self.assertEqual(colors, set(range(10)))
        self.assertEqual(component_counts, {1, 2, 3, 4, 5})
        self.assertGreater(len(erased), 40)

    def test_malformed_and_uncalibrated_inputs_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)]]
        ragged = MODULE.generate(3, 4, scene_profile="single_rectangle")
        ragged[0].pop()
        cases.append(ragged)
        thin_only = [[0] * 7 for _ in range(7)]
        thin_only[3][1:6] = [2] * 5
        cases.append(thin_only)
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)

    def test_determinism_fresh_returns_and_override_rejection(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "x"}, {"grid_h": 12}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="extreme")
        random.seed(9)
        state = random.getstate()
        first = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_rule_hash_and_base_source_sync(self):
        source = canonical_rows()[0]["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, digest)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
