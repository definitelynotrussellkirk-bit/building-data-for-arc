from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "a85f5274d2ae"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/training/18286ef8__a85f5274d2ae.json"


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def pairs():
    row = canonical_row()
    return row["train"] + row["test"]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_exact_public_profiles(self):
        self.assertEqual(len(pairs()), 4)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs()):
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.self_check(pair["input"]), [])
            generated = MOD.generate(1, 2, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertEqual(MOD.canonical_profile_signature(generated), profile)
            self.assertIsNot(generated, MOD._PUBLIC_INPUTS[profile])

    def test_every_direction_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(50):
                    grid = MOD.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(analysis["direction"], MOD._PROFILE_DIRECTION[profile])
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_coarse_step_recolor_semantics(self):
        for profile in MOD.GENERAL_PROFILES:
            for seed in range(40):
                grid = MOD.generate(seed, seed * 23, scene_profile=profile)
                before = copy.deepcopy(grid)
                analysis = MOD._analysis(grid)
                marker, target = analysis["marker"], analysis["target"]
                step = MOD._coarse_step(marker, target)
                next_cell = marker[0] + step[0], marker[1] + step[1]
                expected = copy.deepcopy(grid)
                expected[marker[0]][marker[1]] = 5
                expected[next_cell[0]][next_cell[1]] = 9
                expected[target[0]][target[1]] = 9
                self.assertEqual(MOD.rule_mirror(grid), expected)
                self.assertEqual(grid, before)

    def test_separator_ring_and_noise_visual_grammar(self):
        for profile in MOD.GENERAL_PROFILES:
            grid = MOD.generate(31, 37, scene_profile=profile)
            analysis = MOD._analysis(grid)
            self.assertEqual(len(analysis["separator_rows"]), 2)
            self.assertEqual(len(analysis["separator_cols"]), 2)
            self.assertTrue(all(all(value == 0 for value in grid[row]) for row in analysis["separator_rows"]))
            self.assertTrue(all(all(grid[row][col] == 0 for row in range(len(grid))) for col in analysis["separator_cols"]))
            marker, target = analysis["marker"], analysis["target"]
            for row in range(marker[0] - 1, marker[0] + 2):
                for col in range(marker[1] - 1, marker[1] + 2):
                    expected = 9 if (row, col) == marker else 6 if (row, col) == target else 5
                    self.assertEqual(grid[row][col], expected)
            self.assertGreaterEqual(analysis["noise_cells"], 3)

    def test_adjacent_target_uses_no_movement_step(self):
        for seed in range(50):
            grid = MOD.generate(seed, seed, scene_profile="near_no_step")
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["direction"], (0, 0))
            output = analysis["output"]
            self.assertEqual(output[analysis["marker"][0]][analysis["marker"][1]], 9)
            self.assertEqual(output[analysis["target"][0]][analysis["target"][1]], 9)

    def test_broad_missing_marker_returns_input(self):
        grid = MOD.generate(13, 17, scene_profile="target_lr")
        target = MOD._analysis(grid)["target"]
        grid[target[0]][target[1]] = 7
        before = copy.deepcopy(grid)
        self.assertTrue(MOD.self_check(grid))
        self.assertEqual(MOD.rule_mirror(grid), before)

    def test_broad_multiple_markers_use_first_row_major(self):
        grid = MOD.generate(19, 23, scene_profile="target_lr")
        analysis = MOD._analysis(grid)
        grid[0][0] = 9
        grid[0][1] = 6
        self.assertTrue(MOD.self_check(grid))
        expected = copy.deepcopy(grid)
        expected[0][0] = 9
        expected[0][1] = 9
        self.assertEqual(MOD.rule_mirror(grid), expected)
        self.assertEqual(analysis["marker"], MOD._positions(grid, 9)[1])

    def test_distribution_and_branch_coverage(self):
        profiles = Counter()
        inputs, outputs, shapes, separators, directions, colors = set(), set(), set(), set(), set(), set()
        for seed in range(3000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 29, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            separators.add((analysis["separator_rows"], analysis["separator_cols"]))
            directions.add(analysis["direction"])
            colors.update(value for row in grid for value in row)
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2500)
        self.assertGreater(len(outputs), 2500)
        self.assertGreater(len(shapes), 150)
        self.assertGreater(len(separators), 500)
        self.assertEqual(directions, set(MOD._DIRECTION_PROFILES))
        self.assertEqual(colors, set(range(10)))

    def test_malformed_and_uncalibrated_inputs(self):
        cases = [[], [[]], [[True]], [[10]], [[7] * 8 for _ in range(8)]]
        ragged = MOD.generate(3, 5, scene_profile="target_up")
        ragged[0].pop()
        cases.append(ragged)
        broken_separator = MOD.generate(7, 9, scene_profile="target_left")
        row = MOD._analysis(broken_separator)["separator_rows"][0]
        broken_separator[row][0] = 7
        cases.append(broken_separator)
        broken_ring = MOD.generate(11, 13, scene_profile="target_down")
        marker = MOD._analysis(broken_ring)["marker"]
        broken_ring[marker[0] - 1][marker[1]] = 7
        cases.append(broken_ring)
        extra_nine = MOD.generate(17, 19, scene_profile="target_ur")
        extra_nine[0][0] = 9
        cases.append(extra_nine)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)

    def test_override_errors_determinism_fresh_returns_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "rect_outline"}, {"grid_h": 12}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_rule_hash_and_base_source_are_synced(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
