"""Focused semantic regressions for generator 1b7cbdffd485."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest

from reviewer_support import canonical_path, find_root


TASK_ID = "1b7cbdffd485"
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


class Generator1b7cbdffd485Tests(unittest.TestCase):
    def test_all_four_canonical_pairs_rules_and_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 4)
        seen = set()
        orientations = []
        for pair in pairs:
            source, expected = pair["input"], pair["output"]
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            profile = MODULE.canonical_profile_signature(source)
            self.assertIn(profile, MODULE.PUBLIC_PROFILES)
            seen.add(profile)
            orientations.append(MODULE._analysis(source)["output_orientation"])
        self.assertEqual(seen, set(MODULE.PUBLIC_PROFILES))
        self.assertEqual(orientations, ["column", "row", "column", "row"])

    def test_public_profiles_preserve_complete_linked_geometry(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(40):
                grid = MODULE.generate(seed, seed * 23 + 5, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(
                    MODULE.observe_overrides(grid), {"scene_profile": profile}
                )
                self.assertEqual(MODULE.self_check(grid), [])
                seen.add(tuple(map(tuple, grid)))
            self.assertGreater(len(seen), 35)

    def test_every_d4_public_orientation_is_recognized_and_solved(self):
        for profile in MODULE.PUBLIC_PROFILES:
            literal = MODULE._public_literal(profile)
            for transform in MODULE._TRANSFORMS:
                grid = MODULE._transform(literal, transform)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                expected = MODULE.rule_mirror(grid)
                info = MODULE._analysis(grid)
                self.assertEqual(
                    (len(expected), len(expected[0])),
                    (len(info["order"]), 1)
                    if info["row_span"] >= info["col_span"]
                    else (1, len(info["order"])),
                )

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
                        MODULE.observe_overrides(grid), {"scene_profile": profile}
                    )
                    self.assertEqual(
                        MODULE.self_check(
                            grid, meta={"overrides": {"scene_profile": profile}}
                        ),
                        [],
                    )

    def test_general_profiles_cover_band_counts_and_orientation_branches(self):
        for profile in MODULE.GENERAL_PROFILES:
            grid = MODULE.generate(
                811, 923, difficulty="medium", scene_profile=profile
            )
            info = MODULE._analysis(grid)
            self.assertEqual(info["errors"], [])
            self.assertIsNone(MODULE.canonical_profile_signature(grid))
            self.assertTrue(all(
                MODULE._component_is_connected(grid, color)
                for color in info["order"]
            ))
            if profile.startswith("horizontal_"):
                self.assertEqual(info["output_orientation"], "column")
                self.assertTrue(all(
                    extent[2:4] == (0, info["width"] - 1)
                    for extent in info["color_extents"].values()
                ))
            elif profile.startswith("vertical_"):
                self.assertEqual(info["output_orientation"], "row")
                self.assertTrue(all(
                    extent[:2] == (0, info["height"] - 1)
                    for extent in info["color_extents"].values()
                ))
            elif profile == "tie_column":
                self.assertEqual(info["row_span"], info["col_span"])
                self.assertEqual(info["output_orientation"], "column")
            elif profile == "row_margin_column":
                self.assertEqual(info["row_span"], info["col_span"] + 1)
                self.assertEqual(info["output_orientation"], "column")
            else:
                self.assertEqual(info["col_span"], info["row_span"] + 1)
                self.assertEqual(info["output_orientation"], "row")

    def test_default_prior_coverage_and_uniqueness(self):
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
            strict = sum(profiles[name] for name in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict, 180)
            self.assertLess(strict, 310)
            self.assertGreater(len(inputs), 790)
            self.assertGreater(len(outputs), 650)

    def test_python_oracle_uses_first_appearance_not_frequency_or_last_cell(self):
        grid = [
            [4, 4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4, 4],
            [4, 4, 2, 2, 2, 2],
            [4, 4, 2, 2, 2, 2],
            [4, 4, 2, 8, 8, 8],
            [4, 4, 2, 8, 8, 8],
        ]
        before = copy.deepcopy(grid)
        # First cells are (0,0), (2,2), (4,3): row span 4 > col span 3.
        self.assertEqual(MODULE.rule_mirror(grid), [[4], [2], [8]])
        self.assertEqual(grid, before)

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(
            331, 557, difficulty="medium", scene_profile="tie_column"
        )
        disconnected = copy.deepcopy(base)
        second = MODULE._analysis(base)["order"][1]
        disconnected[0][-1] = second
        with_zero = copy.deepcopy(base)
        with_zero[0][0] = 0
        singleton = copy.deepcopy(base)
        singleton[0][0] = next(
            color for color in range(1, 10) if color not in MODULE._analysis(base)["order"]
        )
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 10
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        wrong_margin = [[1] * 8 for _ in range(8)]
        for row in range(5, 8):
            for col in range(2, 8):
                wrong_margin[row][col] = 2
        for mutation in (
            disconnected,
            with_zero,
            singleton,
            ragged,
            invalid,
            boolean,
            wrong_margin,
        ):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_invalid_override_and_determinism_contract(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"grid_h": 20},
            {"texture": "no_bands"},
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

    def test_all_rule_authorities_and_pin_are_synchronized(self):
        from solvers.grounded_rules import GROUNDED_RULES

        row = _canonical_row()
        candidates = (
            ROOT / "data/base/solutions/training/4be741c5__1b7cbdffd485.json",
            ROOT / "shared/data/base/solutions/training/4be741c5__1b7cbdffd485.json",
        )
        base_path = next((path for path in candidates if path.is_file()), None)
        self.assertIsNotNone(base_path, "missing portable base-solution authority")
        base = json.loads(base_path.read_text())
        canonical = row["program_solution"]
        self.assertEqual(_normalized_hash(base["racket_target"]["raw_code"]), MODULE.RULE_HASH)
        self.assertEqual(_normalized_hash(base["racket_target"]["target_code"]), MODULE.RULE_HASH)
        self.assertEqual(_normalized_hash(GROUNDED_RULES[TASK_ID]), "db42b0b2c380")
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "db42b0b2c380")


if __name__ == "__main__":
    unittest.main()
