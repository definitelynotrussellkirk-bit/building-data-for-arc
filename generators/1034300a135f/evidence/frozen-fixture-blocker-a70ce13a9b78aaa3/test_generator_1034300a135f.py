from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

TASK = "1034300a135f"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE_PATHS = (
    "data/base/solutions/training/ac0c2ac3__1034300a135f.json",
    "data/base/solutions/augmented/ac0c2ac3__7feaa5f0e591.json",
)


def canonical_rows():
    return [json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK]


def pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_and_exact_public_profiles(self):
        rows = canonical_rows()
        self.assertEqual({row["source"] for row in rows}, {"training", "augmented"})
        self.assertEqual(sum(len(pairs(row)) for row in rows), 8)
        training = next(row for row in rows if row["source"] == "training")
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs(training)):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
        expected = {(tuple(map(tuple, pair["input"])), tuple(map(tuple, pair["output"]))) for pair in pairs(training)}
        augmented = next(row for row in rows if row["source"] == "augmented")
        self.assertEqual({(tuple(map(tuple, pair["input"])), tuple(map(tuple, pair["output"]))) for pair in pairs(augmented)}, expected)

    def test_canonical_marker_sequences_are_exact(self):
        expected = ([0, 4, 3, 1, 8], [5, 8, 9, 2], [8, 0, 1, 6, 9, 5], [0, 4, 3, 1, 8, 5, 2])
        for profile, sequence in zip(MOD.PUBLIC_PROFILES, expected):
            facts = MOD._analysis(MOD.generate(3, 5, scene_profile=profile))["facts"]
            self.assertEqual(facts["sequence"], sequence)
            self.assertEqual(facts["distances"], list(range(len(sequence))))
            self.assertEqual(len(sequence), facts["capacity"])

    def test_every_general_profile_in_every_band(self):
        for band in (None, "easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(60):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_full_and_partial_ring_coverage(self):
        for profile in ("full_odd_square", "full_even_square", "full_wide_rectangle", "full_tall_rectangle"):
            facts = MOD._analysis(MOD.generate(7, 13, scene_profile=profile))["facts"]
            self.assertEqual(len(facts["sequence"]), facts["capacity"])
            self.assertNotIn(facts["background"], {value for row in facts["output"] for value in row})
        facts = MOD._analysis(MOD.generate(7, 13, scene_profile="partial_center_background"))["facts"]
        center = facts["output"][facts["height"] // 2][facts["width"] // 2]
        self.assertEqual(center, facts["background"])
        self.assertLess(len(facts["sequence"]), facts["capacity"])

    def test_sparse_distances_control_order_not_ring_indices(self):
        facts = MOD._analysis(MOD.generate(17, 23, scene_profile="sparse_distance_jumps"))["facts"]
        self.assertNotEqual(facts["distances"], list(range(len(facts["distances"]))))
        for distance, color in enumerate(facts["sequence"]):
            self.assertEqual(facts["output"][distance][distance], color)

    def test_zero_marker_can_drive_outer_or_inner_ring(self):
        for profile, index in (("zero_outer_ring", 0), ("zero_inner_ring", -1)):
            facts = MOD._analysis(MOD.generate(31, 47, scene_profile=profile))["facts"]
            self.assertNotEqual(facts["background"], 0)
            self.assertEqual(facts["sequence"][index], 0)
            self.assertEqual(sum(marker["color"] == 0 for marker in facts["markers"]), 1)

    def test_equal_distances_use_stable_row_major_order(self):
        facts = MOD._analysis(MOD.generate(37, 41, scene_profile="tied_distance_row_major"))["facts"]
        tied = next(distance for distance in facts["distances"] if facts["distances"].count(distance) == 2)
        tied_markers = [marker for marker in facts["ordered_markers"] if marker["distance"] == tied]
        self.assertEqual([(marker["row"], marker["col"]) for marker in tied_markers], sorted((marker["row"], marker["col"]) for marker in tied_markers))
        start = facts["distances"].index(tied)
        self.assertEqual(facts["sequence"][start:start + 2], [marker["color"] for marker in tied_markers])

    def test_repeated_marker_colors_create_repeated_layers(self):
        facts = MOD._analysis(MOD.generate(43, 53, scene_profile="repeated_color_layers"))["facts"]
        sequence = facts["sequence"]
        self.assertLess(len(set(sequence)), len(sequence))
        self.assertTrue(any(left == right for left, right in zip(sequence, sequence[1:])))

    def test_malformed_impostors_and_zero_background_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 7 for _ in range(7)], [[7] * 7 for _ in range(7)]]
        zero_background = [[0] * 7 for _ in range(7)]
        for index, color in enumerate((1, 2, 3, 4)):
            zero_background[index][index] = color
        cases.append(zero_background)
        short_same_color_line = [[7] * 7 for _ in range(7)]
        for col in range(4):
            short_same_color_line[3][col] = 1
        cases.append(short_same_color_line)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "edge"}, {"bg_color": 7}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_rule_hash_grounded_and_both_base_sources_are_synced(self):
        source = canonical_rows()[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == source for row in canonical_rows()))
        self.assertEqual(MOD.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        from solvers.grounded_rules import GROUNDED_RULES
        self.assertEqual(GROUNDED_RULES[TASK], source)
        for path in BASE_PATHS:
            base = json.loads((ROOT / path).read_text())
            self.assertEqual(base["racket_target"]["raw_code"], source)
            self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
