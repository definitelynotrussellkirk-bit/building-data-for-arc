"""Focused semantic regressions for generator 5295bc5ff1cb."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root


TASK_ID = "5295bc5ff1cb"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]


def _rows():
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if len(rows) != 2:
        raise AssertionError(f"expected two canonical rows, found {len(rows)}")
    return rows


def _hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator5295bc5ff1cbTests(unittest.TestCase):
    def test_all_eight_canonical_occurrences_and_four_unique_inputs(self):
        occurrences, unique = 0, set()
        for row in _rows():
            for split in ("train", "test"):
                for pair in row.get(split, []):
                    occurrences += 1
                    unique.add(tuple(map(tuple, pair["input"])))
                    self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
                    self.assertIn(MODULE.canonical_profile_signature(pair["input"]), MODULE.PUBLIC_PROFILES)
        self.assertEqual(occurrences, 8)
        self.assertEqual(len(unique), 4)

    def test_public_profiles_are_exact_linked_inputs(self):
        expected = []
        for row in _rows():
            for split in ("train", "test"):
                for pair in row.get(split, []):
                    if pair["input"] not in expected:
                        expected.append(pair["input"])
        actual = [MODULE.generate(1, 2, scene_profile=profile) for profile in MODULE.PUBLIC_PROFILES]
        self.assertEqual(actual, expected)

    def test_every_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertNotEqual(MODULE.rule_mirror(grid), grid)

    def test_all_eight_fundamental_period_lessons(self):
        for profile in MODULE.PERIOD_PROFILES:
            row_period, col_period = map(int, profile.removeprefix("period_").split("x"))
            for seed in range(30):
                info = MODULE._analysis(MODULE.generate(seed, seed + 71, scene_profile=profile))
                self.assertEqual((info["row_period"], info["col_period"]), (row_period, col_period))
                self.assertEqual(info["bottom_cover_rows"], 2)
                self.assertEqual(info["right_cover_cols"], 2)

    def test_cover_extent_lessons_are_distinct(self):
        for seed in range(30):
            bottom = MODULE._analysis(MODULE.generate(seed, seed + 101, scene_profile="thin_bottom_cover"))
            right = MODULE._analysis(MODULE.generate(seed, seed + 103, scene_profile="thin_right_cover"))
            minimal = MODULE._analysis(MODULE.generate(seed, seed + 107, scene_profile="minimal_cover"))
            large = MODULE._analysis(MODULE.generate(seed, seed + 109, scene_profile="large_cover"))
            self.assertEqual(bottom["bottom_cover_rows"], 1)
            self.assertGreaterEqual(bottom["right_cover_cols"], 2)
            self.assertEqual(right["right_cover_cols"], 1)
            self.assertGreaterEqual(right["bottom_cover_rows"], 2)
            self.assertEqual((minimal["bottom_cover_rows"], minimal["right_cover_cols"]), (1, 1))
            self.assertGreaterEqual(large["bottom_cover_rows"], len(large["output"]) // 2)
            self.assertGreaterEqual(large["right_cover_cols"], len(large["output"][0]) // 2)

    def test_output_uses_smallest_period_shift_and_erases_cover(self):
        for profile in MODULE.GENERAL_PROFILES:
            grid = MODULE.generate(211, 307, scene_profile=profile)
            info = MODULE._analysis(grid)
            output = MODULE.rule_mirror(grid)
            for row in range(len(grid)):
                for col in range(len(grid[0])):
                    expected = grid[row % info["row_period"]][(col + 1) % info["col_period"]]
                    self.assertEqual(output[row][col], expected)
            self.assertNotIn(info["cover"], {value for row in output for value in row})

    def test_prefix_can_end_mid_cycle_and_still_finds_period(self):
        grid = MODULE.generate(223, 311, scene_profile="period_2x3")
        info = MODULE._analysis(grid)
        self.assertEqual(info["col_period"], 3)
        prefix = grid[0][:info["prefix_width"]]
        self.assertTrue(all(value == prefix[index % 3] for index, value in enumerate(prefix)))

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, pairs = Counter(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profile = MODULE.observe_overrides(grid)["scene_profile"]
                profiles[profile] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
                if profile in MODULE.GENERAL_PROFILES:
                    height, width = len(grid), len(grid[0])
                    bounds = {"easy": (6, 8), "medium": (9, 13), "hard": (14, 18)}[band]
                    self.assertTrue(bounds[0] <= height <= bounds[1])
                    self.assertTrue(bounds[0] <= width <= bounds[1])
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            public = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreater(public, 150)
            self.assertLess(public, 260)
            self.assertGreater(len(pairs), 550)

    def test_self_check_rejects_malformed_and_semantic_impostors(self):
        base = MODULE.generate(401, 503, scene_profile="period_2x3")
        cover = base[-1][-1]
        full_cover = [[cover for _ in row] for row in base]
        no_bottom = copy.deepcopy(base); no_bottom[-1][0] = base[0][0]
        leaked = copy.deepcopy(base); leaked[1][1] = cover
        stray = copy.deepcopy(base); stray[-1][-1] = base[0][0]
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        boolean = copy.deepcopy(base); boolean[0][0] = True
        for mutation in (full_cover, no_bottom, leaked, stray, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "period_3x2"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 8}, {"pattern_kind": "checker"}, {"texture": "full_cover"}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        random.seed(20260721)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_both_rule_authorities_and_pin(self):
        rows = _rows()
        canonical = rows[0]["program_solution"]
        self.assertEqual(rows[1]["program_solution"], canonical)
        paths = (
            DATA_ROOT / "base/solutions/training/caa06a1f__5295bc5ff1cb.json",
            DATA_ROOT / "base/solutions/augmented/caa06a1f__78fdceec0784.json",
        )
        normalized = " ".join(canonical.split())
        for path in paths:
            base = json.loads(path.read_text())
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), normalized)
            self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), normalized)
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "e3633abbbdea")


if __name__ == "__main__":
    unittest.main()
