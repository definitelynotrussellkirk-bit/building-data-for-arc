"""Focused semantic regressions for generator 19c5f15066d3."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest

from reviewer_support import canonical_path, find_root


TASK_ID = "19c5f15066d3"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = find_root(__file__)


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator19c5f15066d3Tests(unittest.TestCase):
    def test_all_four_canonical_pairs_rules_and_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 4)
        profiles = set()
        object_counts = []
        for pair in pairs:
            source, expected = pair["input"], pair["output"]
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            profile = MODULE.canonical_profile_signature(source)
            self.assertIn(profile, MODULE.PUBLIC_PROFILES)
            profiles.add(profile)
            object_counts.append(len(MODULE._analysis(source)["red_objects"]))
        self.assertEqual(profiles, set(MODULE.PUBLIC_PROFILES))
        self.assertEqual(object_counts, [5, 6, 6, 10])

    def test_public_profiles_relayout_complete_linked_features(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(40):
                grid = MODULE.generate(
                    seed,
                    seed * 23 + 5,
                    scene_profile=profile,
                )
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                self.assertEqual(MODULE.self_check(grid), [])
                seen.add(tuple(map(tuple, grid)))
            self.assertGreater(len(seen), 35)

    def test_every_d4_public_orientation_is_recognized(self):
        for profile in MODULE.PUBLIC_PROFILES:
            literal = MODULE._public_literal(profile)
            for transform in MODULE._TRANSFORMS:
                grid = MODULE._transform(literal, transform)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.rule_mirror(grid), MODULE._transform(
                    MODULE.rule_mirror(literal), transform
                ))

    def test_forced_scene_profiles_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(
                        seed + 700,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(
                        MODULE.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertEqual(
                        MODULE.self_check(
                            grid,
                            meta={"overrides": {"scene_profile": profile}},
                        ),
                        [],
                    )

    def test_general_profiles_have_claimed_line_and_object_roles(self):
        for profile in MODULE.GENERAL_PROFILES:
            grid = MODULE.generate(
                811,
                923,
                difficulty="medium",
                scene_profile=profile,
            )
            info = MODULE._analysis(grid)
            self.assertEqual(info["errors"], [])
            self.assertIsNone(MODULE.canonical_profile_signature(grid))
            self.assertTrue(any(item["touched"] for item in info["red_objects"]))
            self.assertTrue(any(not item["touched"] for item in info["red_objects"]))
            if profile == "vertical_only":
                self.assertTrue(info["vcols"])
                self.assertFalse(info["hrows"])
            elif profile == "horizontal_only":
                self.assertFalse(info["vcols"])
                self.assertTrue(info["hrows"])
            elif profile == "cross":
                self.assertEqual((len(info["vcols"]), len(info["hrows"])), (1, 1))
            elif profile == "multi_lines":
                self.assertGreaterEqual(len(info["vcols"]) + len(info["hrows"]), 3)
            elif profile == "adjacent_touch":
                self.assertTrue(any(item["adjacent_only"] for item in info["red_objects"]))
            elif profile == "edge_objects":
                self.assertTrue(any(
                    MODULE._edge_mask(item["box"], info["height"], info["width"])
                    for item in info["red_objects"]
                ))

    def test_default_prior_coverage_and_uniqueness(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            for seed in range(600):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            strict = sum(profiles[name] for name in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict, 130)
            self.assertLess(strict, 250)
            self.assertGreater(len(inputs), 590)
            self.assertGreater(len(outputs), 590)

    def test_python_oracle_draws_lines_and_selectively_recolors(self):
        for profile in MODULE.GENERAL_PROFILES:
            source = MODULE.generate(101, 203, difficulty="hard", scene_profile=profile)
            before = copy.deepcopy(source)
            output = MODULE.rule_mirror(source)
            info = MODULE._analysis(source)
            self.assertEqual(source, before)
            for row in info["hrows"]:
                self.assertEqual(set(output[row]), {1})
            for col in info["vcols"]:
                self.assertTrue(all(output[row][col] == 1 for row in range(info["height"])))
            for item in info["red_objects"]:
                values = {output[row][col] for row, col in item["cells"]}
                self.assertEqual(values, {1} if item["touched"] else {2})

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(
            331,
            557,
            difficulty="medium",
            scene_profile="cross",
        )
        info = MODULE._analysis(base)
        col = info["vcols"][0]

        unpaired = copy.deepcopy(base)
        unpaired[-1][col] = 0
        interior_blue = copy.deepcopy(base)
        interior_blue[1][1] = 1
        corner_blue = copy.deepcopy(base)
        corner_blue[0][0] = 1
        invalid = copy.deepcopy(base)
        invalid[1][1] = 9
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        no_markers = copy.deepcopy(base)
        for row in range(len(no_markers)):
            for cell in range(len(no_markers[0])):
                if no_markers[row][cell] == 1:
                    no_markers[row][cell] = 0
        nonsolid = copy.deepcopy(base)
        target = next(item for item in info["red_objects"] if not item["touched"])
        center = target["cells"][len(target["cells"]) // 2]
        nonsolid[center[0]][center[1]] = 0
        for mutation in (
            unpaired,
            interior_blue,
            corner_blue,
            invalid,
            ragged,
            no_markers,
            nonsolid,
        ):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_invalid_override_and_determinism_contract(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"grid_h": 20},
            {"texture": "no_marks"},
        ):
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

    def test_all_rule_authorities_and_pin_are_exactly_synchronized(self):
        from solvers.grounded_rules import GROUNDED_RULES

        row = _canonical_row()
        base = json.loads((
            ROOT / "data/base/solutions/training/0d87d2a6__19c5f15066d3.json"
        ).read_text())
        canonical = row["program_solution"]
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(GROUNDED_RULES[TASK_ID], canonical)
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "1ffa1234962c")


if __name__ == "__main__":
    unittest.main()
