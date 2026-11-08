from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "b705ef68a501"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/0f1ff2289d6f/M75__b705ef68a501.json"


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def decode(grid):
    return [[int(value) for value in row] if isinstance(row, str) else list(row) for row in grid]


def canonical_pairs():
    row = canonical_rows()[0]
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_public_profiles(self):
        self.assertEqual(len(canonical_rows()), 1)
        self.assertEqual(len(canonical_pairs()), 5)
        for profile, pair in zip(MODULE.PUBLIC_PROFILES, canonical_pairs()):
            grid, expected = decode(pair["input"]), decode(pair["output"])
            self.assertEqual(MODULE.rule_mirror(grid), expected)
            self.assertEqual(MODULE.self_check(grid), [])
            self.assertEqual(MODULE.generate(1, 2, scene_profile=profile), grid)
            self.assertEqual(MODULE.canonical_profile_signature(grid), profile)

    def test_every_general_profile_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(35):
                    grid = MODULE.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])
                    self.assertTrue(any(value == 0 for row in analysis["output"] for value in row))
                    self.assertEqual(analysis["selected_key"], sorted(c["key"] for c in analysis["candidates"])[analysis["rank"] - 1])

    def test_rank_profiles_select_requested_position(self):
        expected = {"rank_smallest": 0, "rank_largest": -1}
        for profile, index in expected.items():
            for seed in range(80):
                analysis = MODULE._analysis(MODULE.generate(seed, seed, scene_profile=profile))
                self.assertEqual(analysis["selected"], analysis["candidates"][index])
        for seed in range(80):
            analysis = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="rank_middle"))
            self.assertTrue(0 < analysis["selected_index"] < analysis["candidate_count"] - 1)

    def test_reachable_tie_break_profiles(self):
        for profile, dimension in (("tie_by_row", "row"), ("tie_by_column", "column"), ("tie_by_height", "height")):
            for seed in range(80):
                analysis = MODULE._analysis(MODULE.generate(seed, seed * 3, scene_profile=profile))
                self.assertEqual(analysis["tie_dimension"], dimension)
                tied = [candidate for candidate in analysis["candidates"] if analysis["candidate_sizes"].count(candidate["size"]) > 1]
                self.assertEqual(len(tied), 2)
                self.assertIn(analysis["selected"], tied)

    def test_candidate_filters_are_exercised(self):
        for seed in range(80):
            color_nine = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="filter_color_nine"))
            self.assertGreaterEqual(color_nine["excluded_color_nine"], 1)
            self.assertEqual(color_nine["excluded_row_zero"], 0)
            row_zero = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="filter_row_zero"))
            self.assertEqual(row_zero["excluded_color_nine"], 0)
            self.assertEqual(row_zero["excluded_row_zero"], 1)
            self.assertTrue(all(candidate["color"] != 9 and candidate["r1"] > 0 for candidate in row_zero["candidates"]))

    def test_crop_contains_only_selected_component(self):
        for profile in MODULE.GENERAL_PROFILES:
            for seed in range(60):
                grid = MODULE.generate(seed, seed * 5, difficulty="hard", scene_profile=profile)
                analysis = MODULE._analysis(grid)
                selected = analysis["selected"]
                expected = []
                for row in range(selected["r1"], selected["r2"] + 1):
                    expected.append([
                        grid[row][col] if (row, col) in selected["cells"] else 0
                        for col in range(selected["c1"], selected["c2"] + 1)
                    ])
                self.assertEqual(analysis["output"], expected)

    def test_distribution_and_diversity(self):
        profiles = Counter()
        inputs, outputs, input_shapes, output_shapes = set(), set(), set(), set()
        colors, ranks, candidate_counts, ties = set(), set(), set(), set()
        for seed in range(2400):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MODULE.generate(seed, seed * 29, difficulty=band)
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [], (seed, analysis))
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            input_shapes.add((len(grid), len(grid[0])))
            output_shapes.add((len(analysis["output"]), len(analysis["output"][0])))
            colors.update(value for row in grid for value in row)
            ranks.add(analysis["rank"])
            candidate_counts.add(analysis["candidate_count"])
            ties.add(analysis["tie_dimension"])
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2000)
        self.assertGreater(len(outputs), 1000)
        self.assertGreater(len(input_shapes), 100)
        self.assertGreater(len(output_shapes), 12)
        self.assertEqual(colors, set(range(10)))
        self.assertEqual(ranks, {1, 2, 3, 4, 5})
        self.assertEqual(candidate_counts, {3, 4, 5})
        self.assertEqual(ties, {None, "row", "column", "height"})

    def test_malformed_and_uncalibrated_inputs_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)]]
        ragged = MODULE.generate(3, 4, scene_profile="rank_middle")
        ragged[0].pop()
        cases.append(ragged)
        no_header = MODULE.generate(4, 5, scene_profile="rank_middle")
        no_header[0] = [0] * len(no_header[0])
        cases.append(no_header)
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)

    def test_determinism_fresh_returns_hash_and_source_sync(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "x"}, {"n_objs": 4}):
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
        source = canonical_rows()[0]["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, digest)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
