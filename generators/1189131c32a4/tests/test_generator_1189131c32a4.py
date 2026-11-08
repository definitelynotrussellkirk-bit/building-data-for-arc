from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_path, find_root

TASK = "1189131c32a4"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASE_RELATIVE = "data/base/solutions/training/5587a8d0__1189131c32a4.json"


def base_path():
    for prefix in ("", "shared/"):
        candidate = ROOT / f"{prefix}{BASE_RELATIVE}"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(BASE_RELATIVE)


def canonical_rows():
    return [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id") == TASK]


def pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_exact_public_profiles_and_all_canonical_pairs(self):
        rows = canonical_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"], "training")
        self.assertEqual(len(pairs(rows[0])), 4)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs(rows[0])):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_canonical_count_and_rank_sequences_are_exact(self):
        expected_counts = ({4: 4, 6: 3}, {8: 5, 5: 4, 1: 8}, {8: 8, 3: 2, 9: 1, 0: 4}, {9: 2, 2: 5, 5: 4, 8: 1, 0: 6, 1: 9})
        expected_ranked = ([4, 6], [1, 8, 5], [8, 0, 3, 9], [1, 0, 2, 5, 9, 8])
        for profile, counts, ranked in zip(MOD.PUBLIC_PROFILES, expected_counts, expected_ranked):
            facts = MOD._analysis(MOD.generate(3, 5, scene_profile=profile))["facts"]
            self.assertEqual(facts["counts"], counts)
            self.assertEqual(facts["ranked"], ranked)

    def test_every_general_profile_in_every_difficulty_band(self):
        for band in (None, "easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(60):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_output_size_and_ring_order_follow_frequency_rank(self):
        for profile in MOD.GENERAL_PROFILES:
            facts = MOD._analysis(MOD.generate(17, 23, scene_profile=profile))["facts"]
            ranked = facts["ranked"]
            output = facts["output"]
            self.assertEqual(len(output), 2 * len(ranked) - 1)
            self.assertTrue(all(len(row) == len(output) for row in output))
            center = len(ranked) - 1
            for distance, color in enumerate(ranked):
                self.assertEqual(output[distance][distance], color)
            self.assertEqual(output[center][center], ranked[-1])

    def test_distinct_counts_rank_descending(self):
        for profile in ("two_connected", "three_connected", "four_connected", "five_connected", "six_connected", "zero_ranked", "scattered_components", "mixed_components"):
            facts = MOD._analysis(MOD.generate(31, 37, scene_profile=profile))["facts"]
            ranked_counts = [facts["counts"][color] for color in facts["ranked"]]
            self.assertEqual(ranked_counts, sorted(ranked_counts, reverse=True))

    def test_ties_use_descending_numeric_color_order(self):
        for profile, tie_size in (("tie_two_way", 2), ("tie_three_way", 3)):
            for seed in range(40):
                facts = MOD._analysis(MOD.generate(seed, 41, scene_profile=profile))["facts"]
                tied_count = next(count for count, frequency in Counter(facts["counts"].values()).items() if frequency == tie_size)
                tied_colors = [color for color in facts["colors"] if facts["counts"][color] == tied_count]
                ranked_tied = [color for color in facts["ranked"] if facts["counts"][color] == tied_count]
                self.assertEqual(ranked_tied, sorted(tied_colors, reverse=True))

    def test_zero_is_ranked_as_foreground(self):
        facts = MOD._analysis(MOD.generate(43, 47, scene_profile="zero_ranked"))["facts"]
        self.assertIn(0, facts["colors"])
        self.assertIn(0, facts["ranked"])
        self.assertIn(0, {value for row in facts["output"] for value in row})

    def test_geometry_profiles_prove_components_are_irrelevant(self):
        scattered = MOD._analysis(MOD.generate(53, 59, scene_profile="scattered_components"))["facts"]
        mixed = MOD._analysis(MOD.generate(61, 67, scene_profile="mixed_components"))["facts"]
        self.assertTrue(all(value >= 2 for value in scattered["components"].values()))
        self.assertTrue(any(value == 1 for value in mixed["components"].values()))
        self.assertTrue(any(value >= 2 for value in mixed["components"].values()))

    def test_malformed_and_undeclared_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[7] * 5 for _ in range(5)], [[1] * 5 for _ in range(5)]]
        equal_unclassified = [[7] * 9 for _ in range(9)]
        for index, color in enumerate((1, 2, 3, 4, 5)):
            equal_unclassified[index * 2][0] = color
        cases.append(equal_unclassified)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "equal_counts"}, {"bg_color": 7}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(71)
        state = random.getstate()
        first = MOD.generate(73, 79, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(73, 79, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_rule_hash_grounded_and_base_sources_are_synced(self):
        source = canonical_rows()[0]["program_solution"]
        self.assertEqual(MOD.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        from solvers.grounded_rules import GROUNDED_RULES
        self.assertEqual(GROUNDED_RULES[TASK], source)
        base = json.loads(base_path().read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(base["primitive_metadata"]["primitive_chain"], ["rows", "cols", "unique", "flatmap", "map", "at", "range", "filter", "sort-by", "find-color", "build-grid", "nth"])


if __name__ == "__main__":
    unittest.main()
