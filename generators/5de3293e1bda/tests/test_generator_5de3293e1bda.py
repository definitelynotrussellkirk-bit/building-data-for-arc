"""Focused semantic regressions for generator 5de3293e1bda."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK_ID = "5de3293e1bda"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
                if json.loads(line).get("task_id") == TASK_ID)


class Generator5de3293e1bdaTests(unittest.TestCase):
    def test_all_five_canonical_pairs(self):
        pairs = canonical_row()["train"] + canonical_row()["test"]
        self.assertEqual(len(pairs), 5)
        for index, pair in enumerate(pairs):
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), MODULE.PUBLIC_PROFILES[index])

    def test_public_profiles_are_exact(self):
        expected = [pair["input"] for pair in canonical_row()["train"] + canonical_row()["test"]]
        self.assertEqual([MODULE.generate(1, 2, scene_profile=p) for p in MODULE.PUBLIC_PROFILES], expected)

    def test_every_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(25):
                    grid = MODULE.generate(seed, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid), [])

    def test_exact_normalize_intersect_and_crop(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            info = MODULE._analysis(grid)
            expected = MODULE._crop(info["blue_shape"] & info["red_shape"])
            self.assertEqual(MODULE.rule_mirror(grid), expected)
            self.assertTrue(all(value in (0, 8) for row in expected for value in row))

    def test_overlap_geometry_profiles(self):
        expectations = {
            "overlap_single_cell": (1, (1, 1)), "overlap_vertical_pair": (2, (2, 1)),
            "overlap_horizontal_pair": (2, (1, 2)), "overlap_l_three": (3, (2, 2)),
            "overlap_t_four": (4, (2, 3)), "overlap_sparse_wide": (3, (2, 4)),
            "overlap_sparse_tall": (3, (4, 2)),
        }
        for profile, (count, dims) in expectations.items():
            info = MODULE._analysis(MODULE.generate(211, 307, scene_profile=profile))
            output = info["output"]
            self.assertEqual(info["intersection_size"], count)
            self.assertEqual((len(output), len(output[0])), dims)

    def test_subset_large_and_placement_profiles(self):
        second = MODULE._analysis(MODULE.generate(223, 311, scene_profile="second_shape_subset"))
        first = MODULE._analysis(MODULE.generate(227, 313, scene_profile="first_shape_subset"))
        large = MODULE._analysis(MODULE.generate(229, 317, scene_profile="large_partial_overlap"))
        same = MODULE._analysis(MODULE.generate(233, 319, scene_profile="same_row_placement"))
        self.assertLess(second["red_shape"], second["blue_shape"])
        self.assertLess(first["blue_shape"], first["red_shape"])
        self.assertGreaterEqual(large["intersection_size"], 5)
        self.assertEqual(same["blue_origin"][0], same["red_origin"][0])

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, inputs, outputs = Counter(), set(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            self.assertTrue(35 < sum(profiles[p] for p in MODULE.PUBLIC_PROFILES) < 145)
            self.assertGreater(len(inputs), 590)
            self.assertGreater(len(outputs), 70)

    def test_minimal_and_malformed_inputs_rejected(self):
        valid = MODULE.generate(401, 503, scene_profile="overlap_l_three")
        h, w = len(valid), len(valid[0])
        empty = [[0] * w for _ in range(h)]
        only_blue = copy.deepcopy(empty); only_blue[1][1] = 1
        disconnected = copy.deepcopy(valid); disconnected[0][w - 1] = 1
        identical = copy.deepcopy(empty)
        for dr, dc in ((0, 0), (0, 1), (1, 0)):
            identical[1 + dr][1 + dc] = 1; identical[4 + dr][6 + dc] = 2
        no_overlap = copy.deepcopy(empty)
        no_overlap[1][1] = no_overlap[2][2] = 1
        no_overlap[4][6] = no_overlap[5][5] = 2
        ragged = copy.deepcopy(valid); ragged[0].pop()
        invalid = copy.deepcopy(valid); invalid[0][0] = 4
        boolean = copy.deepcopy(valid); boolean[0][0] = True
        for mutation in (empty, only_blue, disconnected, identical, no_overlap, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_determinism_freshness_rng_and_unknown_axes(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 8}, {"texture": "default"}, {"blob_size": 4}):
            with self.assertRaises(ValueError): MODULE.generate(1, 2, **overrides)
        random.seed(20260721); state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second); self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_source_sync_and_rule_pin(self):
        source = canonical_row()["program_solution"]
        base = json.loads((ROOT / "data/base/solutions/banks/f4facb1306bd/M117__5de3293e1bda.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(MODULE.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        self.assertEqual(MODULE.RULE_HASH, "7cd0ccb1b858")


if __name__ == "__main__":
    unittest.main()
