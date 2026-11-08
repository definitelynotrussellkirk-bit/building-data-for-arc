"""Focused regression tests for generator 23ef3502f576.

Run with:
    python3 -m unittest tests.test_generator_23ef3502f576
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "23ef3502f576"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _pairs(row):
    pairs = list(row["train"])
    test = row["test"]
    pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def _normalized_hash(text):
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


class Generator23ef3502f576Tests(unittest.TestCase):
    def test_rule_hash_and_source_sync(self):
        row = _canonical_row()
        candidates = (
            ROOT / "data/base/solutions/banks/0938460c498b/S19_E4__23ef3502f576.json",
            ROOT / "shared/data/base/solutions/banks/0938460c498b/S19_E4__23ef3502f576.json",
        )
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        self.assertIsNotNone(path, "missing selected base solution")
        base = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(_normalized_hash(row["program_solution"]), GEN.RULE_HASH)
        self.assertEqual(_normalized_hash(base["racket_target"]["target_code"]), GEN.RULE_HASH)
        self.assertFalse(base["racket_target"]["needs_conversion"])

    def test_all_public_pairs_are_exact_rule_witnesses(self):
        row = _canonical_row()
        names = GEN.PUBLIC_PROFILES
        for name, pair in zip(names, _pairs(row), strict=True):
            grid = copy.deepcopy(pair["input"])
            before = copy.deepcopy(grid)
            self.assertEqual(GEN._PUBLIC_INPUTS[name], pair["input"])
            self.assertEqual(GEN.canonical_profile_signature(grid), name)
            self.assertEqual(GEN.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before, "Python mirror mutated a canonical input")
            self.assertEqual(GEN.self_check(grid), [])

    def test_every_declared_profile_is_exactly_observable_in_every_band(self):
        for band in (None, "easy", "medium", "hard"):
            for profile in GEN.SCENE_PROFILES:
                for seed in range(12):
                    grid = GEN.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(GEN.self_check(grid, difficulty=band), [])
                    self.assertEqual(GEN.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(GEN.scene_profile_signature(grid), profile)
                    output = GEN.rule_mirror(grid)
                    self.assertNotEqual(grid, output)
                    signature = GEN.semantic_signature(grid)
                    self.assertEqual(len(output), signature["panel_height"])
                    self.assertEqual(len(output[0]), signature["panel_width"])

    def test_semantic_profiles_break_common_shortcuts(self):
        equal = GEN.semantic_signature(
            GEN.generate(11, 7, difficulty="medium", scene_profile="equal_cell_counts")
        )
        self.assertEqual(len(set(equal["counts"])), 1)
        self.assertEqual(len(set(equal["shapes"])), 3)

        duplicate = GEN.semantic_signature(
            GEN.generate(12, 7, difficulty="medium", scene_profile="duplicate_shape_decoys")
        )
        self.assertEqual(duplicate["shapes"][0], duplicate["shapes"][1])
        self.assertNotEqual(duplicate["shapes"][1], duplicate["shapes"][2])

        scattered = GEN.semantic_signature(
            GEN.generate(13, 7, difficulty="medium", scene_profile="scattered_header")
        )
        self.assertFalse(scattered["header_contiguous"])
        self.assertIn(scattered["choice"], (2, 3))

        varied = GEN.semantic_signature(
            GEN.generate(14, 7, difficulty="medium", scene_profile="varied_palette")
        )
        self.assertNotEqual(varied["palette"], (7, (2, 3, 4)))

        for choice in (1, 2, 3):
            signature = GEN.semantic_signature(
                GEN.generate(20 + choice, 5, difficulty="hard", scene_profile=f"choice_{choice}_general")
            )
            self.assertEqual(signature["choice"], choice)
            self.assertEqual(len(set(signature["counts"])), 3)
            self.assertEqual(len(set(signature["shapes"])), 3)

    def test_default_linked_coverage_and_stability(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            choices = Counter()
            for seed in range(160):
                grid = GEN.generate(seed, seed * 29 + 11, difficulty=band)
                signature = GEN.semantic_signature(grid)
                profiles[signature["scene_profile"]] += 1
                choices[signature["choice"]] += 1
                inputs.add(json.dumps(grid, separators=(",", ":")))
                outputs.add(json.dumps(GEN.rule_mirror(grid), separators=(",", ":")))
            self.assertTrue(set(GEN.SCENE_PROFILES) <= set(profiles), (band, profiles))
            self.assertGreaterEqual(sum(profiles[name] for name in GEN.PUBLIC_PROFILES), 8)
            self.assertEqual(set(choices), {1, 2, 3})
            self.assertGreaterEqual(len(inputs), 115)
            self.assertGreaterEqual(len(outputs), 95)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(8675309)
        before_state = random.getstate()
        first = GEN.generate(101, 9, difficulty="hard", scene_profile="choice_2_general")
        after_state = random.getstate()
        second = GEN.generate(101, 9, difficulty="hard", scene_profile="choice_2_general")
        self.assertEqual(before_state, after_state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(
            second,
            GEN.generate(101, 9, difficulty="hard", scene_profile="choice_2_general"),
        )

        public_a = GEN.generate(1, 1, scene_profile="public_train_1")
        public_b = GEN.generate(1, 1, scene_profile="public_train_1")
        public_a[0][0] = 0
        self.assertEqual(public_b, GEN._PUBLIC_INPUTS["public_train_1"])

    def test_unknown_controls_reject_loudly(self):
        with self.assertRaisesRegex(ValueError, "unknown difficulty"):
            GEN.generate(1, 1, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(1, 1, texture="warm")
        with self.assertRaises(ValueError):
            GEN.generate(1, 1, scene_profile="not_a_profile")

    def test_targeted_mutations_are_rejected(self):
        base = GEN.generate(0, 0, scene_profile="public_train_1")
        mutants = {}

        mutants["broken_divider"] = copy.deepcopy(base)
        mutants["broken_divider"][1][0] = 0

        mutants["header_count_four"] = copy.deepcopy(base)
        mutants["header_count_four"][0] = [7, 7, 7, 7]

        mutants["second_candidate_color"] = copy.deepcopy(base)
        mutants["second_candidate_color"][2][1] = 3

        mutants["disconnected_candidate"] = copy.deepcopy(base)
        mutants["disconnected_candidate"][4][1] = 0
        mutants["disconnected_candidate"][5][3] = 2

        mutants["duplicate_candidate_color"] = copy.deepcopy(base)
        mutants["duplicate_candidate_color"] = [
            [3 if value == 4 else value for value in row]
            for row in mutants["duplicate_candidate_color"]
        ]

        for name, mutant in mutants.items():
            with self.subTest(name=name):
                self.assertTrue(GEN.self_check(mutant), name)
                self.assertIsNone(GEN.scene_profile_signature(mutant))

    def test_negative_public_recombination_is_not_whitelisted(self):
        train = GEN.generate(0, 0, scene_profile="public_train_1")
        test = GEN.generate(0, 0, scene_profile="public_test_1")
        recombined = copy.deepcopy(train)
        recombined[0] = test[0][:]
        self.assertIsNone(GEN.canonical_profile_signature(recombined))
        self.assertIsNone(GEN.scene_profile_signature(recombined))
        self.assertTrue(GEN.self_check(recombined))
        # The broad oracle still has a defined answer; rejection is a calibrated
        # teaching-distribution decision, not a claim that Racket cannot run it.
        self.assertEqual(len(GEN.rule_mirror(recombined)), 4)


if __name__ == "__main__":
    unittest.main()
