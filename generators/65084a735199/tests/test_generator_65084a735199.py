"""Focused regressions for generator 65084a735199."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK_ID = "65084a735199"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    return next(
        json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def pairs():
    row = canonical_row()
    return row["train"] + row["test"]


class Tests(unittest.TestCase):
    def test_all_canonical_pairs(self):
        self.assertEqual(len(pairs()), 3)
        for pair in pairs():
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])

    def test_exact_public_profiles(self):
        for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs()):
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), profile)
            for band in ("easy", "medium", "hard"):
                self.assertEqual(MODULE.generate(7, 11, difficulty=band, scene_profile=profile), pair["input"])

    def test_every_general_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertNotEqual(grid, MODULE.rule_mirror(grid))

    def test_frame_binding_and_clearing(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            before = copy.deepcopy(grid)
            info = MODULE._analysis(grid)
            output = MODULE.rule_mirror(grid)
            self.assertEqual(grid, before)
            self.assertGreaterEqual(len(info["frames"]), 2)
            for frame in info["frames"]:
                color = frame["marker_color"]
                self.assertTrue(all(output[r][c] == color for r, c in frame["cells"]))
                r, c = frame["marker"]
                self.assertEqual(output[r][c], 0)

    def test_default_diversity_and_coverage(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs, outputs, shapes, colors = set(), set(), set(), set()
            for seed in range(600):
                grid = MODULE.generate(seed, seed * 19 + 1, difficulty=band)
                info = MODULE._analysis(grid)
                profiles[info["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, info["output"])))
                shapes.add((len(grid), len(grid[0])))
                colors.update(info["marker_colors"])
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            self.assertGreater(len(inputs), 480)
            self.assertGreater(len(outputs), 480)
            self.assertGreaterEqual(len(shapes), 8)
            self.assertEqual(colors, {1, 2, 3, 4, 6, 7, 8, 9})

    def test_malformed_and_minimal_impostors(self):
        valid = MODULE.generate(401, 503, scene_profile="paired_mixed")
        candidates = []
        candidates.append([[0 for _ in row] for row in valid])
        ragged = copy.deepcopy(valid); ragged[0].pop(); candidates.append(ragged)
        invalid = copy.deepcopy(valid); invalid[0][0] = 10; candidates.append(invalid)
        boolean = copy.deepcopy(valid); boolean[0][0] = True; candidates.append(boolean)
        open_frame = copy.deepcopy(valid); frame = MODULE._analysis(valid)["frames"][0]; r, c = next(iter(frame["cells"])); open_frame[r][c] = 0; candidates.append(open_frame)
        no_marker = copy.deepcopy(valid); r, c = frame["marker"]; no_marker[r][c] = 0; candidates.append(no_marker)
        one_frame = [[0] * 7 for _ in range(7)]
        for r in range(1, 5):
            for c in range(1, 5):
                if r in (1, 4) or c in (1, 4): one_frame[r][c] = 5
        one_frame[2][2] = 2; candidates.append(one_frame)
        for candidate in candidates:
            self.assertTrue(MODULE.self_check(candidate))

    def test_determinism_fresh_returns_and_rejections(self):
        for overrides in ({"scene_profile": "x"}, {"grid_h": 12}, {"texture": "warm"}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        random.seed(20260721)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_source_sync_and_hash(self):
        row = canonical_row()
        source = row["program_solution"]
        base = json.loads((ROOT / "data/base/solutions/banks/765a70430bc9/M7__65084a735199.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, expected)


if __name__ == "__main__":
    unittest.main()
