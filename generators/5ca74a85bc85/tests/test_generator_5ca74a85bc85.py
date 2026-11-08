"""Focused semantic regressions for generator 5ca74a85bc85."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "5ca74a85bc85"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)


def canonical_row():
    return next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
                if json.loads(line).get("task_id") == TASK_ID)


class Generator5ca74a85bc85Tests(unittest.TestCase):
    def test_all_five_canonical_pairs(self):
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        self.assertEqual(len(pairs), 5)
        for index, pair in enumerate(pairs):
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), MODULE.PUBLIC_PROFILES[index])

    def test_public_profiles_are_exact(self):
        expected = [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT)]
        self.assertEqual([MODULE.generate(1, 2, scene_profile=p) for p in MODULE.PUBLIC_PROFILES], expected)

    def test_every_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(25):
                    grid = MODULE.generate(seed, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertNotEqual(MODULE.rule_mirror(grid), grid)

    def test_exact_reflection_preserves_source_and_color(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            info = MODULE._analysis(grid)
            output = MODULE.rule_mirror(grid)
            for r, c, value in info["source_cells"]:
                self.assertEqual(output[r][c], value)
                self.assertEqual(output[r][2 * info["divider"] - c], value)
            self.assertTrue(all(output[r][info["divider"]] == 9 for r in range(len(grid))))

    def test_side_and_shape_profiles(self):
        infos = {profile: MODULE._analysis(MODULE.generate(211, 307, scene_profile=profile)) for profile in (
            "left_rectangle", "right_rectangle", "left_single_cell", "right_single_cell",
            "left_horizontal_bar", "right_vertical_bar", "multiple_objects_left",
        )}
        self.assertEqual(infos["left_rectangle"]["source_side"], "left")
        self.assertEqual(infos["right_rectangle"]["source_side"], "right")
        self.assertEqual(infos["left_single_cell"]["source_count"], 1)
        self.assertEqual(infos["right_single_cell"]["source_count"], 1)
        self.assertEqual(len({r for r, _, _ in infos["left_horizontal_bar"]["source_cells"]}), 1)
        self.assertEqual(len({c for _, c, _ in infos["right_vertical_bar"]["source_cells"]}), 1)
        self.assertGreaterEqual(len(infos["multiple_objects_left"]["source_components"]), 2)

    def test_color_boundary_and_distance_profiles(self):
        for profile, side in (("multicolor_left", "left"), ("multicolor_right", "right")):
            info = MODULE._analysis(MODULE.generate(223, 311, scene_profile=profile))
            self.assertEqual(info["source_side"], side)
            self.assertGreaterEqual(len(info["source_colors"]), 2)
        boundary = MODULE._analysis(MODULE.generate(227, 313, scene_profile="boundary_mirror"))
        self.assertTrue(any(2 * boundary["divider"] - c in (0, boundary["width"] - 1)
                            for _, c, _ in boundary["source_cells"]))
        near = MODULE._analysis(MODULE.generate(229, 317, scene_profile="near_divider"))
        self.assertTrue(all(abs(c - near["divider"]) == 1 for _, c, _ in near["source_cells"]))

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, pairs = Counter(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            self.assertTrue(90 < sum(profiles[p] for p in MODULE.PUBLIC_PROFILES) < 220)
            self.assertGreater(len(pairs), 520)

    def test_minimal_and_malformed_inputs_rejected(self):
        base = MODULE.generate(401, 503, scene_profile="left_rectangle")
        h, w = len(base), len(base[0])
        empty = [[0] * w for _ in range(h)]
        divider_only = copy.deepcopy(empty)
        for r in range(h): divider_only[r][w // 2] = 9
        both_sides = copy.deepcopy(divider_only); both_sides[1][1] = 4; both_sides[1][w - 2] = 4
        collision = copy.deepcopy(divider_only); collision[2][1] = 4; collision[2][w - 2] = 5
        two_dividers = copy.deepcopy(divider_only)
        for r in range(h): two_dividers[r][w // 2 - 1] = 9
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        boolean = copy.deepcopy(base); boolean[0][0] = True
        for mutation in (empty, divider_only, both_sides, collision, two_dividers, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_determinism_freshness_rng_and_unknown_axes(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 8}, {"texture": "warm"}, {"n_cells": 4}):
            with self.assertRaises(ValueError): MODULE.generate(1, 2, **overrides)
        random.seed(20260721); state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second); self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_source_sync_and_rule_pin(self):
        source = canonical_row()["program_solution"]
        base = json.loads((canonical_path(ROOT).parents[1] / "base/solutions/banks/3b7f019624a4/E49__5ca74a85bc85.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(MODULE.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        self.assertEqual(MODULE.RULE_HASH, "f57d1e04d7d6")


if __name__ == "__main__":
    unittest.main()
