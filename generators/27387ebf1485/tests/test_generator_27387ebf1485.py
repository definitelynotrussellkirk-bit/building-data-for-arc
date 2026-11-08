"""Focused semantic regressions for generator 27387ebf1485."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "27387ebf1485"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator27387ebf1485Tests(unittest.TestCase):
    def test_all_five_canonical_pairs_and_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], row["test"]]
        self.assertEqual(len(pairs), 5)
        profiles = []
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            profile = MODULE.canonical_profile_signature(source)
            self.assertIn(profile, MODULE.PUBLIC_PROFILES)
            profiles.append(profile)
            info = MODULE._analysis(source)
            self.assertEqual(info["bbox"][2] - info["bbox"][0] + 1, 3)
            self.assertEqual(info["bbox"][3] - info["bbox"][1] + 1, 3)
        self.assertEqual(profiles, list(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_preserve_complete_linked_masks(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(40):
                grid = MODULE.generate(seed, seed * 13 + 1, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                seen.add(tuple(map(tuple, grid)))
            self.assertGreater(len(seen), 30)

    def test_forced_profiles_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed + 700, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(
                        MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}),
                        [],
                    )

    def test_target_topology_and_bbox_boundaries(self):
        expectations = {
            "singleton_target": lambda info: len(info["target_cells"]) == 1,
            "horizontal_line": lambda info: info["bbox"][0] == info["bbox"][2],
            "vertical_line": lambda info: info["bbox"][1] == info["bbox"][3],
            "target_multicomponent": lambda info: info["component_count"] == 2,
            "wide_bbox_sparse": lambda info: info["component_count"] == 2 and info["target_density"] <= 0.22,
            "target_at_edge": lambda info: info["touches_edge"],
        }
        for profile, predicate in expectations.items():
            info = MODULE._analysis(MODULE.generate(101, 203, difficulty="hard", scene_profile=profile))
            self.assertTrue(predicate(info), (profile, info))

    def test_literal_crop_preserves_foreign_and_origin_cells(self):
        foreign_grid = MODULE.generate(211, 307, scene_profile="foreign_inside_crop")
        origin_grid = MODULE.generate(223, 311, scene_profile="origin_inside_crop")
        foreign = MODULE._analysis(foreign_grid)
        origin = MODULE._analysis(origin_grid)
        self.assertTrue(foreign["foreign_inside"])
        self.assertTrue(any(
            value not in (0, foreign["marker"])
            for row in foreign["crop"] for value in row
        ))
        self.assertTrue(origin["origin_inside"])
        self.assertEqual(origin["crop"][0][0], origin["marker"])
        self.assertNotIn((0, 0), origin["target_cells"])
        self.assertEqual(MODULE.rule_mirror(foreign_grid), foreign["crop"])
        self.assertEqual(MODULE.rule_mirror(origin_grid), origin["crop"])

    def test_color_count_boundaries(self):
        two = MODULE._analysis(MODULE.generate(313, 419, scene_profile="two_colors"))
        five = MODULE._analysis(MODULE.generate(317, 421, scene_profile="five_colors"))
        self.assertEqual(len(two["colors"]), 2)
        self.assertEqual(len(five["colors"]), 5)
        self.assertEqual(two["marker"], two["colors"][0])
        self.assertEqual(five["marker"], five["colors"][0])

    def test_default_prior_coverage_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            strict = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict, 180)
            self.assertLess(strict, 310)
            self.assertGreater(len(inputs), 780)
            self.assertGreater(len(outputs), 450)

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(401, 503, scene_profile="varied_poly")
        all_background = [[0 for _ in row] for row in base]
        marker_only = [[0] * 5 for _ in range(5)]
        marker_only[0][0] = 3
        one_color = [[0] * 5 for _ in range(5)]
        one_color[0][0] = one_color[2][2] = one_color[2][3] = 3
        four_colors = copy.deepcopy(base)
        used = {value for row in base for value in row}
        new_color = next(value for value in range(1, 10) if value not in used)
        four_colors[-1][-1] = new_color
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 10
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (all_background, marker_only, one_color, four_colors, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "target_at_edge"}}))

    def test_override_and_determinism_contract(self):
        for overrides in ({"scene_profile": "unknown"}, {"palette_size": 3}, {"texture": "no_marker"}):
            with self.subTest(overrides=overrides):
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

    def test_rule_authorities_and_pin_are_synchronized(self):
        row = _canonical_row()
        canonical = row["program_solution"]
        base = json.loads((
            ROOT / "data/base/solutions/banks/dc02f6f7c147/E103__27387ebf1485.json"
        ).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "ea5b14ea2c9d")


if __name__ == "__main__":
    unittest.main()
