"""Focused regression tests for generator 1314f4ccf5cc."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import re
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "1314f4ccf5cc"
GEN, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row():
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _pairs(row):
    return list(row["train"]) + list(row["test"])


def _normalized_hash(text):
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


class Generator1314f4ccf5ccTests(unittest.TestCase):
    def test_rule_hash_and_all_authorities_are_exactly_synced(self):
        row = _canonical_row()
        program = row["program_solution"]
        base = json.loads(
            (ROOT / "shared/data/base/solutions/training/14754a24__1314f4ccf5cc.json").read_text()
        )
        grounded = (ROOT / "shared/runtime/solvers/grounded_rules.py").read_text()
        match = re.search(
            r'"1314f4ccf5cc"\s*:\s*"""(.*?)""",', grounded, re.DOTALL
        )
        self.assertIsNotNone(match)
        self.assertEqual(_normalized_hash(program), GEN.RULE_HASH)
        self.assertEqual(program, base["racket_target"]["raw_code"])
        self.assertEqual(program, base["racket_target"]["target_code"])
        self.assertEqual(program, match.group(1))

    def test_all_official_pairs_are_exact_linked_profiles(self):
        row = _canonical_row()
        for profile, pair in zip(GEN.PUBLIC_PROFILES, _pairs(row), strict=True):
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(GEN.self_check(source), [], profile)
            self.assertEqual(GEN.canonical_profile_signature(source), profile)
            self.assertEqual(GEN.scene_profile_signature(source), profile)
            self.assertEqual(GEN.rule_mirror(source), pair["output"])
            self.assertEqual(source, before, "rule mirror mutated an official input")

    def test_every_scene_profile_is_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in GEN.SCENE_PROFILES:
                for seed in range(8):
                    grid = GEN.generate(
                        seed,
                        seed * 31 + 7,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(GEN.self_check(grid, difficulty=band), [])
                    self.assertEqual(
                        GEN.observe_overrides(grid), {"scene_profile": profile}
                    )
                    self.assertNotEqual(grid, GEN.rule_mirror(grid))

    def test_general_profiles_exercise_missing_center_edge_and_density_branches(self):
        sparse = GEN._analysis(
            GEN.generate(2, 9, difficulty="medium", scene_profile="general_sparse")
        )
        dense = GEN._analysis(
            GEN.generate(2, 9, difficulty="medium", scene_profile="general_dense")
        )
        edge = GEN._analysis(
            GEN.generate(2, 9, difficulty="medium", scene_profile="general_edge")
        )
        center = GEN._analysis(
            GEN.generate(2, 9, difficulty="medium", scene_profile="general_center_missing")
        )
        single = GEN._analysis(
            GEN.generate(2, 9, difficulty="medium", scene_profile="general_single_missing")
        )
        self.assertLess(sparse["gray_fraction"], 0.32)
        self.assertGreater(dense["gray_fraction"], 0.60)
        self.assertGreaterEqual(edge["edge_target_count"], 1)
        self.assertEqual(center["center_missing_count"], center["target_count"])
        self.assertTrue(
            all(len(target["missing"]) == 1 for target in single["targets"])
        )

    def test_default_linked_coverage_stability_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            missing_counts = Counter()
            for seed in range(220):
                grid = GEN.generate(seed, seed * 37 + 11, difficulty=band)
                profile = GEN.scene_profile_signature(grid)
                profiles[profile] += 1
                inputs.add(json.dumps(grid, separators=(",", ":")))
                outputs.add(json.dumps(GEN.rule_mirror(grid), separators=(",", ":")))
                for target in GEN._analysis(grid)["targets"]:
                    missing_counts[len(target["missing"])] += 1
            self.assertEqual(set(profiles), set(GEN.SCENE_PROFILES), (band, profiles))
            public = sum(profiles[p] for p in GEN.PUBLIC_PROFILES)
            self.assertGreaterEqual(public, 70, (band, profiles))
            self.assertGreaterEqual(len(inputs), 210)
            self.assertGreaterEqual(len(outputs), 210)
            self.assertTrue({1, 2, 3} <= set(missing_counts))

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(8675309)
        before_state = random.getstate()
        first = GEN.generate(
            101, 9, difficulty="hard", scene_profile="general_center_missing"
        )
        after_state = random.getstate()
        second = GEN.generate(
            101, 9, difficulty="hard", scene_profile="general_center_missing"
        )
        self.assertEqual(before_state, after_state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(
            second,
            GEN.generate(
                101, 9, difficulty="hard", scene_profile="general_center_missing"
            ),
        )

    def test_minimal_impostors_and_unknown_controls_reject(self):
        impostors = {
            "all_background": [[0] * 8 for _ in range(8)],
            "full_one_color": [[5] * 8 for _ in range(8)],
            "singleton": [[4 if (r, c) == (3, 3) else 0 for c in range(8)] for r in range(8)],
            "solid_2x2": [[4 if 3 <= r <= 4 and 3 <= c <= 4 else 0 for c in range(8)] for r in range(8)],
            "short_line": [[4 if r == 3 and 2 <= c <= 5 else 0 for c in range(8)] for r in range(8)],
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(GEN.self_check(grid))
                with self.assertRaises(ValueError):
                    GEN.observe_overrides(grid)
        with self.assertRaisesRegex(ValueError, "unknown difficulty"):
            GEN.generate(1, 1, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(1, 1, texture="dense")
        with self.assertRaises(ValueError):
            GEN.generate(1, 1, scene_profile="not_a_profile")

    def test_self_check_rejects_malformed_cells_without_raising(self):
        # Harvested from the parallel reviewer's v2.0.1 line: a validator must
        # fail closed on heterogeneous/unhashable cells, never raise.
        malformed_values = ("not-a-color", None, True, 1.5, [4], {})
        for value in malformed_values:
            grid = [[0] * 13 for _ in range(13)]
            grid[0][0] = value
            before = [row[:] for row in grid]
            with self.subTest(value=repr(value)):
                errors = GEN.self_check(grid)
                self.assertTrue(errors)
                self.assertEqual(before, grid)
                self.assertTrue(
                    any("integer ARC colors" in error for error in errors),
                    errors,
                )

    def test_plausible_profile_recombination_is_not_public(self):
        # Keep dimensions and color counts from public_train_1, but recombine one
        # demonstrated target's center-missing morphology into a different valid
        # three-yellow fragment.  The broad task remains lawful while the linked
        # official signature must reject it.
        for seed in range(30):
            grid = GEN.generate(seed, 5, scene_profile="public_train_1")
            info = GEN._analysis(grid)
            target = next(
                (
                    target
                    for target in info["targets"]
                    if target["edge"] == "interior"
                    and (0, 0) not in target["yellow_rel"]
                    and len(target["yellow_rel"]) == 3
                ),
                None,
            )
            if target is None:
                continue
            center = target["center"]
            old_rel = (0, -1) if (0, -1) in target["yellow_rel"] else (0, 1)
            old = (center[0] + old_rel[0], center[1] + old_rel[1])
            grid[old[0]][old[1]] = 5
            grid[center[0]][center[1]] = 4
            if not GEN.self_check(grid):
                self.assertIsNone(GEN.canonical_profile_signature(grid))
                self.assertIn(GEN.scene_profile_signature(grid), GEN.GENERAL_PROFILES)
                return
        self.fail("could not construct a valid linked-profile recombination witness")


if __name__ == "__main__":
    unittest.main()
