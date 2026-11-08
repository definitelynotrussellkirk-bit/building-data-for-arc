from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_path, find_root

TASK = "0281fbec1cf2"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASE_PATHS = (
    "shared/data/base/solutions/training/9def23fe__0281fbec1cf2.json",
    "shared/data/base/solutions/augmented/9def23fe__6e62720322fd.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def normalized_pairs(row):
    pairs = []
    for split in ("train", "test"):
        value = row[split]
        pairs.extend(value if isinstance(value, list) else [value])
    return pairs


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_and_public_profiles_exact(self):
        rows = canonical_rows()
        self.assertEqual({row["source"] for row in rows}, {"training", "augmented"})
        self.assertEqual(sum(len(normalized_pairs(row)) for row in rows), 8)
        training = next(row for row in rows if row["source"] == "training")
        public_pairs = normalized_pairs(training)
        self.assertEqual(len(public_pairs), 4)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, public_pairs):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
        expected = {(tuple(map(tuple, pair["input"])), tuple(map(tuple, pair["output"]))) for pair in public_pairs}
        augmented = next(row for row in rows if row["source"] == "augmented")
        actual = {(tuple(map(tuple, pair["input"])), tuple(map(tuple, pair["output"]))) for pair in normalized_pairs(augmented)}
        self.assertEqual(actual, expected)

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

    def test_directional_blocking_is_side_specific(self):
        grid = MOD.generate(17, 23, scene_profile="up_only")
        facts = MOD._analysis(grid)["facts"]
        top, _, bottom, _ = facts["bbox"]
        col = facts["above_cols"][0]
        self.assertNotIn(col, facts["below_cols"])
        self.assertTrue(any(grid[row][col] == 0 for row in range(top)))
        self.assertTrue(any(facts["output"][row][col] == 0 for row in range(top)))
        self.assertTrue(all(facts["output"][row][col] == 2 for row in range(bottom + 1, len(grid))))

        both = MOD.generate(17, 23, scene_profile="same_col_opposites")
        both_facts = MOD._analysis(both)["facts"]
        self.assertEqual(both_facts["above_cols"], both_facts["below_cols"])
        both_col = both_facts["above_cols"][0]
        top, _, bottom, _ = both_facts["bbox"]
        self.assertTrue(any(both_facts["output"][row][both_col] == 0 for row in range(top)))
        self.assertTrue(any(both_facts["output"][row][both_col] == 0 for row in range(bottom + 1, len(both))))

    def test_profile_blocker_signatures_are_exact(self):
        expected = {
            "open_with_decoys": (False, False, False, False, True),
            "up_only": (True, False, False, False, False),
            "down_only": (False, True, False, False, False),
            "left_only": (False, False, True, False, False),
            "right_only": (False, False, False, True, False),
            "same_col_opposites": (True, True, False, False, False),
            "split_col_opposites": (True, True, False, False, False),
            "same_row_opposites": (False, False, True, True, False),
            "split_row_opposites": (False, False, True, True, False),
            "mixed_colors_four_sides": (True, True, True, True, False),
            "aligned_with_decoys": (True, True, True, True, True),
            "dense_four_sides": (True, True, True, True, False),
        }
        for seed in range(100):
            for profile, signature in expected.items():
                facts = MOD._analysis(MOD.generate(seed, seed * 7, scene_profile=profile))["facts"]
                actual = tuple(bool(facts[key]) for key in ("above_cols", "below_cols", "left_rows", "right_rows", "decoys"))
                self.assertEqual(actual, signature)
                if profile == "mixed_colors_four_sides":
                    self.assertGreaterEqual(len(facts["marker_colors"]), 2)
                if profile == "dense_four_sides":
                    rows, cols = facts["rectangle_shape"]
                    self.assertEqual(tuple(map(len, (facts["above_cols"], facts["below_cols"], facts["left_rows"], facts["right_rows"]))), (cols - 1, cols - 1, rows - 1, rows - 1))

    def test_misaligned_decoys_are_inert_and_preserved(self):
        for profile in ("open_with_decoys", "aligned_with_decoys"):
            grid = MOD.generate(31, 47, scene_profile=profile)
            facts = MOD._analysis(grid)["facts"]
            self.assertTrue(facts["decoys"])
            for row, col, value in facts["decoys"]:
                self.assertEqual(facts["output"][row][col], value)
            if profile == "open_with_decoys":
                self.assertFalse(any(facts[key] for key in ("above_cols", "below_cols", "left_rows", "right_rows")))

    def test_distribution_is_broad_non_degenerate_and_complete(self):
        profiles = Counter()
        inputs, outputs, general_inputs, general_outputs = set(), set(), set(), set()
        shapes, rectangle_shapes, marker_colors = set(), set(), set()
        for seed in range(4000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 31, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            facts = analysis["facts"]
            profile = analysis["scene_profile"]
            profiles[profile] += 1
            key_in = tuple(map(tuple, grid))
            key_out = tuple(map(tuple, facts["output"]))
            inputs.add(key_in)
            outputs.add(key_out)
            if profile in MOD.GENERAL_PROFILES:
                general_inputs.add(key_in)
                general_outputs.add(key_out)
            shapes.add((len(grid), len(grid[0])))
            rectangle_shapes.add(facts["rectangle_shape"])
            marker_colors.update(facts["marker_colors"])
        general_count = sum(profiles[profile] for profile in MOD.GENERAL_PROFILES)
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 3600)
        self.assertGreater(len(outputs), 3600)
        self.assertGreater(len(general_inputs) / general_count, 0.99)
        self.assertGreater(len(general_outputs) / general_count, 0.99)
        self.assertGreater(len(shapes), 100)
        self.assertGreater(len(rectangle_shapes), 40)
        self.assertEqual(marker_colors, {1, 3, 4, 5, 6, 7, 8, 9})

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 9 for _ in range(9)]]
        border = [[0] * 9 for _ in range(9)]
        border[0][2:5] = [2, 2, 2]
        border[1][2:5] = [2, 2, 2]
        border[8][8] = 3
        cases.append(border)
        broken = [[0] * 9 for _ in range(9)]
        broken[3][3] = broken[3][4] = broken[4][3] = 2
        broken[0][0] = 3
        cases.append(broken)
        markerless = [[0] * 9 for _ in range(9)]
        for row in range(3, 6):
            for col in range(3, 6):
                markerless[row][col] = 2
        cases.append(markerless)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "plain"}, {"grid_h": 20}):
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
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        from solvers.grounded_rules import GROUNDED_RULES
        self.assertEqual(GROUNDED_RULES[TASK], source)
        for path in BASE_PATHS:
            base = json.loads((ROOT / path).read_text())
            self.assertEqual(base["racket_target"]["raw_code"], source)
            self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
