from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "c739fcbc6cbd"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/training/0a938d79__c739fcbc6cbd.json"


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def public_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + (test if isinstance(test, list) else [test])


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
                for seed in range(45):
                    grid = MODULE.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])

    def test_profiles_exercise_exact_branch_conditions(self):
        for seed in range(100):
            analyses = {profile: MODULE._analysis(MODULE.generate(seed, seed, scene_profile=profile)) for profile in MODULE.GENERAL_PROFILES}
            self.assertTrue(analyses["row_same_column"]["row_bands"])
            self.assertEqual(analyses["row_same_column"]["dc"], 0)
            self.assertTrue(0 < analyses["row_diagonal"]["dr"] < analyses["row_diagonal"]["dc"])
            self.assertFalse(analyses["column_same_row"]["row_bands"])
            self.assertEqual(analyses["column_same_row"]["dr"], 0)
            self.assertGreater(analyses["column_diagonal"]["dr"], analyses["column_diagonal"]["dc"])
            self.assertEqual(analyses["equal_distance_column"]["dr"], analyses["equal_distance_column"]["dc"])
            self.assertFalse(analyses["equal_distance_column"]["row_bands"])
            self.assertGreater(analyses["row_nonzero_prefix"]["prefix"], 0)
            self.assertGreater(analyses["column_nonzero_prefix"]["prefix"], 0)
            self.assertEqual(analyses["adjacent_phases"]["distance"], 1)
            reverse = analyses["spatial_color_reverse"]
            self.assertGreater(reverse["r1"] if reverse["row_bands"] else reverse["c1"], reverse["r2"] if reverse["row_bands"] else reverse["c2"])
            self.assertEqual(analyses["same_color_phases"]["color1"], analyses["same_color_phases"]["color2"])
            self.assertGreater(len(analyses["high_color_decoys"]["ignored"]), 0)

    def test_color_major_then_row_major_selection_and_prefix(self):
        grid = [[0 for _ in range(11)] for _ in range(9)]
        grid[5][4] = 2
        grid[2][4] = 7
        grid[0][9] = 9
        analysis = MODULE._analysis(grid)
        self.assertEqual(analysis["selected"], [(5, 4, 2), (2, 4, 7)])
        self.assertEqual(analysis["ignored"], [(0, 9, 9)])
        self.assertTrue(analysis["row_bands"])
        self.assertEqual(analysis["period"], 6)
        self.assertEqual(analysis["prefix"], 2)
        self.assertTrue(all(value == 0 for row in analysis["output"][:2] for value in row))
        self.assertEqual(analysis["output"][2], [7] * 11)
        self.assertEqual(analysis["output"][5], [2] * 11)
        self.assertEqual(analysis["output"][8], [7] * 11)

        same = [[0 for _ in range(8)] for _ in range(8)]
        same[6][3] = 4
        same[1][5] = 4
        same[0][0] = 8
        selected = MODULE._analysis(same)["selected"]
        self.assertEqual(selected, [(1, 5, 4), (6, 3, 4)])

    def test_output_is_full_lines_and_clears_nonselected_dots(self):
        for profile in MODULE.GENERAL_PROFILES:
            for seed in range(80):
                grid = MODULE.generate(seed, seed * 7, scene_profile=profile)
                analysis = MODULE._analysis(grid)
                output = analysis["output"]
                if analysis["row_bands"]:
                    for row in output:
                        self.assertEqual(len(set(row)), 1)
                else:
                    for col in range(len(output[0])):
                        self.assertEqual(len({row[col] for row in output}), 1)
                for row, col, _ in analysis["ignored"]:
                    expected = output[row][col]
                    self.assertIn(expected, (0, analysis["color1"], analysis["color2"]))

    def test_distribution(self):
        profiles = Counter()
        inputs = set()
        outputs = set()
        canvas_shapes = set()
        dot_counts = set()
        distances = set()
        periods = set()
        prefixes = set()
        colors = set()
        axes = set()
        for seed in range(2600):
            grid = MODULE.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            canvas_shapes.add((len(grid), len(grid[0])))
            dot_counts.add(len(analysis["dots"]))
            distances.add(analysis["distance"])
            periods.add(analysis["period"])
            prefixes.add(analysis["prefix"])
            colors.update(value for row in grid for value in row)
            axes.add(analysis["active_axis"])
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2050)
        self.assertGreater(len(outputs), 1800)
        self.assertGreater(len(canvas_shapes), 115)
        self.assertEqual(dot_counts, {2, 3, 4, 5})
        self.assertTrue(set(range(1, 8)).issubset(distances))
        self.assertTrue(set(range(2, 15, 2)).issubset(periods))
        self.assertTrue({0, 1, 2, 3, 5, 7}.issubset(prefixes))
        self.assertEqual(colors, set(range(10)))
        self.assertEqual(axes, {"row", "column"})

    def test_malformed_inputs_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)], [[1], [1, 2]]]
        one = [[0] * 8 for _ in range(8)]
        one[0][0] = 2
        cases.append(one)
        six = [[0] * 8 for _ in range(8)]
        for index, color in enumerate((1, 2, 3, 4, 5, 6)):
            six[index][index] = color
        cases.append(six)
        same_color_line = [[0] * 8 for _ in range(8)]
        same_color_line[2][2:5] = [4, 4, 4]
        cases.append(same_color_line)
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MODULE.rule_mirror([])

    def test_determinism_freshness_and_unknowns(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "r90"}, {"gap_min": 2}):
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
