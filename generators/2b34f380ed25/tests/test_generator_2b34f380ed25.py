from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "2b34f380ed25"
ROOT = find_root(__file__)
MOD, _, _ = load_selected_generator(TASK, root=ROOT)
BASE = "base/solutions/training/4e7e0eb9__2b34f380ed25.json"


def canonical_row():
    return next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id") == TASK)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_public_profiles_exact(self):
        pairs = canonical_pairs(TASK, root=ROOT, variant=0)
        self.assertEqual(len(pairs), 6)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_every_general_profile_in_every_band(self):
        for band in (None, "easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(80):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_exact_run_three_and_macro_band_decoding(self):
        self.assertTrue(MOD._has_run_three([0, 2, 2, 2, 0]))
        self.assertTrue(MOD._has_run_three([5, 5, 5, 0, 7, 7, 7, 7]))
        self.assertFalse(MOD._has_run_three([0, 2, 2, 0]))
        self.assertFalse(MOD._has_run_three([0, 2, 2, 2, 2, 0]))
        grid = MOD.generate(7, 13, scene_profile="vertical_swap_four")
        facts = MOD._extract_facts(grid)
        self.assertEqual(len(facts["col_bands"]), 4)
        self.assertTrue(all(end - start + 1 == 3 for start, end in facts["row_bands"] + facts["col_bands"]))
        self.assertEqual(facts["row_cuts"], [])
        self.assertEqual(facts["col_cuts"], [])

    def test_profiles_witness_fill_swap_separators_and_unbalanced_marks(self):
        expected = {
            "fill_uniform_panel": ["fill"],
            "multicolor_preserve_plus_fill": ["preserve", "fill"],
            "vertical_swap_two": ["v_bal"],
            "vertical_swap_four": ["v_bal"],
            "horizontal_swap_two": ["h_bal"],
            "horizontal_swap_four": ["h_bal"],
            "unbalanced_vertical_plus_fill": ["v_unbal", "fill"],
            "unbalanced_horizontal_plus_fill": ["h_unbal", "fill"],
            "row_split_mixed": ["v_bal", "fill"],
            "four_panel_mixed": ["fill", "v_bal", "h_bal", "preserve"],
        }
        for seed in range(100):
            for profile, signature in expected.items():
                grid = MOD.generate(seed, seed * 7, scene_profile=profile)
                facts = MOD._analysis(grid)["facts"]
                self.assertEqual([entry[2] for entry in MOD._panel_signature(facts)], signature)
                if "unbalanced" in profile:
                    marked = facts["panel_facts"][0]
                    balance = marked["balanced_vertical"] or marked["balanced_horizontal"]
                    self.assertEqual(balance, [False])

    def test_unbalanced_mark_is_noop_locally_while_other_panel_fills(self):
        grid = MOD.generate(17, 23, scene_profile="unbalanced_vertical_plus_fill")
        facts = MOD._analysis(grid)["facts"]
        left = facts["panel_facts"][0]
        right = facts["panel_facts"][1]
        self.assertEqual(left["balanced_vertical"], [False])
        self.assertEqual(right["action"], "fill")
        rg, cg = left["row_group"], left["col_group"]
        for row in range(rg[0], rg[1] + 1):
            for col in range(cg[0], cg[1] + 1):
                self.assertEqual(facts["new_macro"][row][col], facts["macro"][row][col])
        self.assertGreater(facts["changed"], 0)

    def test_distribution_covers_all_profiles_and_varies_materially(self):
        profiles = Counter()
        inputs, outputs, general_inputs, general_outputs, shapes, macro_shapes, colors = set(), set(), set(), set(), set(), set(), set()
        actions, row_group_counts, col_group_counts = set(), set(), set()
        balanced = unbalanced = False
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
            macro_shapes.add((len(facts["row_bands"]), len(facts["col_bands"])))
            colors.update(value for line in grid for value in line)
            row_group_counts.add(len(facts["row_groups"]))
            col_group_counts.add(len(facts["col_groups"]))
            for panel in facts["panel_facts"]:
                actions.add(panel["action"])
                balanced |= any(panel["balanced_vertical"] + panel["balanced_horizontal"])
                unbalanced |= any(not value for value in panel["balanced_vertical"] + panel["balanced_horizontal"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        general_count = sum(profiles[profile] for profile in MOD.GENERAL_PROFILES)
        self.assertGreater(len(inputs), 3400)
        self.assertGreater(len(outputs), 3400)
        self.assertGreater(len(general_inputs) / general_count, 0.98)
        self.assertGreater(len(general_outputs) / general_count, 0.98)
        self.assertGreater(len(shapes), 40)
        self.assertGreater(len(macro_shapes), 15)
        self.assertEqual(colors, set(range(10)))
        self.assertEqual(actions, {"fill", "marked", "preserve"})
        self.assertEqual(row_group_counts, {1, 2, 3})
        self.assertEqual(col_group_counts, {1, 2, 3})
        self.assertTrue(balanced and unbalanced)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 9 for _ in range(9)], [[1] * 9 for _ in range(9)]]
        thin = [[0] * 9 for _ in range(9)]
        for row in (1, 2):
            for col in (1, 2, 3):
                thin[row][col] = 2
        cases.append(thin)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"fill_color": 2}):
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

    def test_rule_hash_grounded_rule_and_base_source_are_synced(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        from solvers.grounded_rules import GROUNDED_RULES
        self.assertEqual(GROUNDED_RULES[TASK], source)
        base = json.loads((canonical_path(ROOT).parent.parent / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
