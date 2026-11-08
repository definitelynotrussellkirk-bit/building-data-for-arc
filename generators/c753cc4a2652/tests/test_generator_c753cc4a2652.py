from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "c753cc4a2652"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/e57147319d67/H30__c753cc4a2652.json"


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def public_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_public_pairs_exact(self):
        pairs = public_pairs()
        self.assertEqual(len(pairs), 5)
        for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
            grid = MODULE.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MODULE.rule_mirror(grid), pair["output"])
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
            analyses = {profile: MODULE._analysis(MODULE.generate(seed, seed, scene_profile=profile)) for profile in MODULE.GENERAL_PROFILES}
            solid = analyses["solid_rectangle"]["target"]
            self.assertEqual(solid["size"], solid["bbox_area"])
            concave = analyses["concave_target"]["target"]
            self.assertLess(concave["size"], concave["bbox_area"])
            self.assertFalse(MODULE._has_hole(concave))
            self.assertTrue(MODULE._has_hole(analyses["holed_target"]["target"]))
            thin = analyses["thin_target"]["target"]
            self.assertTrue(thin["height"] == 1 or thin["width"] == 1)
            edge = analyses["edge_target"]
            self.assertTrue(any(r in (0, len(edge["output"]) - 1) or c in (0, len(edge["output"][0]) - 1) for r, c in edge["target"]["cells"]))
            self.assertGreater(len(analyses["distractor_objects"]["nonred_objects"]), 1)
            same = analyses["same_color_distractor"]["nonred_objects"]
            self.assertLess(len({obj["color"] for obj in same}), len(same))
            self.assertGreater(len(analyses["multiple_touching_candidates"]["touching"]), 1)
            self.assertGreater(len(analyses["marker_decoys"]["markers"]), 1)
            self.assertGreaterEqual(len(analyses["large_interior"]["interior"]), 6)

    def test_first_marker_and_first_touching_object_selection(self):
        grid = [[0 for _ in range(12)] for _ in range(12)]
        first = {(2, c) for c in range(3, 7)} | {(3, c) for c in range(3, 7)}
        second = {(5, c) for c in range(3, 7)} | {(6, c) for c in range(3, 7)}
        for row, col in first:
            grid[row][col] = 8
        for row, col in second:
            grid[row][col] = 4
        grid[4][4] = 2
        analysis = MODULE._analysis(grid)
        self.assertEqual(analysis["active_marker"], (4, 4))
        self.assertEqual(len(analysis["touching"]), 2)
        self.assertEqual(analysis["target"]["color"], 8)
        self.assertEqual({(r, c) for r, row in enumerate(analysis["output"]) for c, value in enumerate(row) if value == 2}, MODULE._perimeter(first))

        grid[0][0] = 2
        third = {(0, c) for c in range(1, 4)}
        for row, col in third:
            grid[row][col] = 3
        analysis = MODULE._analysis(grid)
        self.assertEqual(analysis["active_marker"], (0, 0))
        self.assertEqual(analysis["target"]["color"], 3)

    def test_output_is_exact_perimeter_on_blank_canvas(self):
        for profile in MODULE.GENERAL_PROFILES:
            for seed in range(80):
                grid = MODULE.generate(seed, seed * 7, scene_profile=profile)
                analysis = MODULE._analysis(grid)
                actual = {(r, c) for r, row in enumerate(analysis["output"]) for c, value in enumerate(row) if value == 2}
                self.assertEqual(actual, analysis["perimeter"])
                self.assertTrue(all(value in (0, 2) for row in analysis["output"] for value in row))
                self.assertTrue(analysis["interior"].isdisjoint(actual))

    def test_distribution(self):
        profiles = Counter()
        inputs = set()
        outputs = set()
        canvas_shapes = set()
        target_sizes = set()
        target_shapes = set()
        marker_counts = set()
        object_counts = set()
        colors = set()
        interior_counts = set()
        touching_counts = set()
        for seed in range(2500):
            grid = MODULE.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            canvas_shapes.add((len(grid), len(grid[0])))
            target_sizes.add(analysis["target"]["size"])
            target_shapes.add((analysis["target"]["height"], analysis["target"]["width"]))
            marker_counts.add(len(analysis["markers"]))
            object_counts.add(len(analysis["nonred_objects"]))
            colors.update(value for row in grid for value in row)
            interior_counts.add(len(analysis["interior"]))
            touching_counts.add(len(analysis["touching"]))
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 1950)
        self.assertGreater(len(outputs), 1800)
        self.assertGreater(len(canvas_shapes), 115)
        self.assertTrue({3, 4, 6, 7, 9, 12, 16, 42}.issubset(target_sizes))
        self.assertTrue({(1, 3), (3, 1), (3, 4), (4, 4), (5, 5), (6, 7)}.issubset(target_shapes))
        self.assertEqual(marker_counts, {1, 2})
        self.assertEqual(object_counts, {1, 2, 3})
        self.assertEqual(colors, set(range(10)))
        self.assertTrue({0, 1, 2, 4, 6, 12, 20}.issubset(interior_counts))
        self.assertEqual(touching_counts, {1, 2})

    def test_malformed_inputs_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)], [[1], [1, 2]]]
        marker_only = [[0] * 8 for _ in range(8)]
        marker_only[1][1] = 2
        cases.append(marker_only)
        singleton = [[0] * 8 for _ in range(8)]
        singleton[2][2] = 2
        singleton[2][3] = 6
        cases.append(singleton)
        red_line = [[0] * 8 for _ in range(8)]
        red_line[2][2:4] = [2, 2]
        red_line[3][2:5] = [6, 6, 6]
        cases.append(red_line)
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MODULE.rule_mirror([])

    def test_determinism_freshness_and_unknowns(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"palette_size": 3}):
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
