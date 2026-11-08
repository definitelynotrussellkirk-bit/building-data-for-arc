"""Focused semantic regressions for generator 14042d4b8317."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "14042d4b8317"
from reviewer_support import canonical_path, find_root
import importlib.util
SPEC=importlib.util.spec_from_file_location("fourth_corner_generator",Path(__file__).parents[1]/"generator.py")
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ROOT=find_root(__file__)


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source):
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else row
        for row in value
    ]


class Generator14042d4b8317Tests(unittest.TestCase):
    def test_all_five_canonical_pairs_and_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 5)
        profiles = set()
        changed_counts = []
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            observed = MODULE.observe_overrides(source)["scene_profile"]
            self.assertIn(observed, MODULE.PUBLIC_PROFILES)
            profiles.add(observed)
            changed_counts.append(sum(
                source[row][col] != expected[row][col]
                for row in range(len(source))
                for col in range(len(source[0]))
            ))
        self.assertEqual(profiles, set(MODULE.PUBLIC_PROFILES))
        self.assertEqual(changed_counts, [1, 2, 1, 2, 2])

    def test_every_public_profile_retains_all_d4_orientations(self):
        for profile in MODULE.PUBLIC_PROFILES:
            literal = MODULE._public_literal(profile)
            signatures = {
                MODULE.canonical_profile_signature(
                    MODULE._transform(literal, transform)
                )
                for transform in MODULE._TRANSFORMS
            }
            self.assertEqual(len(signatures), 8)
            for signature in signatures:
                self.assertEqual(
                    MODULE._PUBLIC_SIGNATURE_LOOKUP[signature],
                    profile,
                )

    def test_forced_scene_profiles_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(30):
                    grid = MODULE.generate(
                        seed,
                        seed * 19 + 7,
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

    def test_default_whole_profile_prior_and_general_coverage(self):
        for band in ("easy", "medium", "hard"):
            main = Counter()
            disjoint = Counter()
            for seed in range(1000):
                main[MODULE.observe_overrides(MODULE.generate(
                    seed,
                    seed * 11 + 1,
                    difficulty=band,
                ))["scene_profile"]] += 1
                disjoint[MODULE.observe_overrides(MODULE.generate(
                    seed + 50_000,
                    seed * 17 + 3,
                    difficulty=band,
                ))["scene_profile"]] += 1
            self.assertEqual(set(main), set(MODULE.SCENE_PROFILES))
            self.assertEqual(set(disjoint), set(MODULE.SCENE_PROFILES))
            for counts in (main, disjoint):
                strict = sum(counts[name] for name in MODULE.PUBLIC_PROFILES)
                self.assertGreater(strict, 220)
                self.assertLess(strict, 400)
                self.assertTrue(all(counts[name] > 25 for name in MODULE.PUBLIC_PROFILES))

    def test_general_profiles_have_the_claimed_geometry(self):
        for profile in MODULE.GENERAL_PROFILES:
            grid = MODULE.generate(41, 73, difficulty="medium", scene_profile=profile)
            info = MODULE._analysis(grid)
            rectangles = info["rectangles"]
            self.assertEqual(info["errors"], [])
            if profile == "single_general":
                self.assertEqual(len(rectangles), 1)
            elif profile == "thin_general":
                self.assertEqual(len(rectangles), 1)
                box = rectangles[0]["box"]
                self.assertIn(2, (box[2] - box[0] + 1, box[3] - box[1] + 1))
            elif profile == "edge_general":
                box = rectangles[0]["box"]
                self.assertTrue(
                    box[0] == 0 or box[1] == 0
                    or box[2] == len(grid) - 1
                    or box[3] == len(grid[0]) - 1
                )
            elif profile == "multi_disjoint":
                self.assertGreaterEqual(len(rectangles), 2)
                self.assertFalse(any(
                    MODULE._boxes_overlap(rectangles[left]["box"], rectangles[right]["box"])
                    for left in range(len(rectangles))
                    for right in range(left + 1, len(rectangles))
                ))
            elif profile == "multi_overlap":
                self.assertEqual(len(rectangles), 2)
                self.assertTrue(MODULE._boxes_overlap(
                    rectangles[0]["box"], rectangles[1]["box"]
                ))

    def test_python_oracle_changes_exactly_one_corner_per_color(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(150):
                source = MODULE.generate(seed + 8000, seed, difficulty=band)
                before = copy.deepcopy(source)
                output = MODULE.rule_mirror(source)
                info = MODULE._analysis(source)
                self.assertEqual(source, before)
                self.assertIsNot(output, source)
                changed = []
                for row in range(len(source)):
                    self.assertIsNot(output[row], source[row])
                    for col in range(len(source[0])):
                        if source[row][col] != output[row][col]:
                            changed.append((row, col, output[row][col]))
                expected = sorted(
                    (*item["missing_point"], item["color"])
                    for item in info["rectangles"]
                )
                self.assertEqual(sorted(changed), expected)

    def test_self_check_rejects_nearest_impostors(self):
        grid = MODULE.generate(
            313,
            991,
            difficulty="hard",
            scene_profile="multi_overlap",
        )
        info = MODULE._analysis(grid)
        color = info["rectangles"][0]["color"]
        cell = next(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        )

        two_corners = copy.deepcopy(grid)
        two_corners[cell[0]][cell[1]] = 0
        all_four = copy.deepcopy(grid)
        missing = info["rectangles"][0]["missing_point"]
        all_four[missing[0]][missing[1]] = color
        invalid_value = copy.deepcopy(grid)
        invalid_value[0][0] = 10
        boolean_value = copy.deepcopy(grid)
        boolean_value[0][0] = True
        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        collinear = [[0] * 8 for _ in range(6)]
        collinear[2][1] = collinear[2][3] = collinear[2][6] = 4
        all_background = [[0] * 8 for _ in range(6)]
        for mutation in (
            two_corners,
            all_four,
            invalid_value,
            boolean_value,
            ragged,
            collinear,
            all_background,
        ):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_invalid_override_fails_closed(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"texture": "only_2_corners"},
            {"grid_h": 9},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    MODULE.generate(1, 2, **overrides)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(20260721)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        for left, right in zip(first, second):
            self.assertIsNot(left, right)
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)

    def test_rule_authorities_and_pin_are_synchronized(self):
        row = _canonical_row()
        base = json.loads((
            canonical_path(ROOT).parents[1] / "base/solutions/banks/fd166f81148e/E145__14042d4b8317.json"
        ).read_text())
        canonical = row["program_solution"]
        raw = base["racket_target"]["raw_code"]
        target = base["racket_target"]["target_code"]
        self.assertEqual(raw, canonical)
        self.assertEqual(target, canonical)
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "af34f04ae393")


if __name__ == "__main__":
    unittest.main()
