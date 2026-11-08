from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

TASK = "21d822423cfc"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = "data/base/solutions/banks/385e738e9e70/M94__21d822423cfc.json"


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_exact_public_profiles(self):
        row = canonical_row()
        self.assertEqual(row["source"], "bank:385e738e9e70")
        self.assertEqual(len(pairs(row)), 5)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs(row)):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_canonical_chamber_states_and_changed_counts_are_exact(self):
        expected = (
            (4, ["unique", "unique", "unique", "unique"], 42),
            (4, ["ambiguous", "unique", "unique", "blank"], 26),
            (6, ["unique", "unique", "blank", "unique", "blank", "unique"], 32),
            (4, ["ambiguous", "unique", "unique", "blank"], 20),
            (4, ["unique", "unique", "unique", "unique"], 64),
        )
        for profile, result in zip(MOD.PUBLIC_PROFILES, expected):
            facts = MOD._analysis(MOD.generate(3, 5, scene_profile=profile))["facts"]
            self.assertEqual((facts["chamber_count"], facts["states"], facts["changed"]), result)

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

    def test_unique_seed_fills_only_zero_cells(self):
        facts = MOD._analysis(MOD.generate(31, 37, scene_profile="nonseed_decoys"))["facts"]
        grid = MOD.generate(31, 37, scene_profile="nonseed_decoys")
        output = facts["output"]
        for chamber in facts["chambers"]:
            if chamber["state"] != "unique":
                continue
            seed = chamber["seed_colors"][0]
            for row, col in chamber["cells"]:
                if grid[row][col] == 0:
                    self.assertEqual(output[row][col], seed)
                else:
                    self.assertEqual(output[row][col], grid[row][col])

    def test_blank_and_ambiguous_chambers_stay_unchanged(self):
        grid = MOD.generate(41, 43, scene_profile="four_seed_ambiguous")
        facts = MOD._analysis(grid)["facts"]
        self.assertIn("blank", facts["states"])
        self.assertIn("ambiguous", facts["states"])
        for chamber in facts["chambers"]:
            if chamber["state"] in {"blank", "ambiguous"}:
                for row, col in chamber["cells"]:
                    self.assertEqual(facts["output"][row][col], grid[row][col])

    def test_multiple_same_seed_cells_still_select_one_color(self):
        facts = MOD._analysis(MOD.generate(47, 53, scene_profile="multiple_same_seed"))["facts"]
        repeated = [chamber for chamber in facts["chambers"] if chamber["state"] == "unique" and chamber["seed_cells"] >= 2]
        self.assertEqual(len(repeated), 1)
        self.assertEqual(len(repeated[0]["seed_colors"]), 1)
        self.assertGreater(repeated[0]["changed"], 0)

    def test_nonseed_decoys_are_traversable_and_preserved(self):
        grid = MOD.generate(59, 61, scene_profile="nonseed_decoys")
        facts = MOD._analysis(grid)["facts"]
        decoy_chambers = [chamber for chamber in facts["chambers"] if chamber["decoy_cells"]]
        self.assertEqual(len(decoy_chambers), 1)
        for row, col in decoy_chambers[0]["cells"]:
            if grid[row][col] in {4, 6, 7, 8, 9}:
                self.assertEqual(facts["output"][row][col], grid[row][col])

    def test_gray_walls_are_preserved_and_block_connectivity(self):
        grid = MOD.generate(67, 71, scene_profile="six_mixed")
        facts = MOD._analysis(grid)["facts"]
        self.assertEqual(facts["chamber_count"], 6)
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == 5:
                    self.assertEqual(facts["output"][row][col], 5)

    def test_open_edge_and_t_junction_geometry_are_lawful(self):
        opened = MOD._analysis(MOD.generate(73, 79, scene_profile="open_edge_chambers"))["facts"]
        junction = MOD._analysis(MOD.generate(83, 89, scene_profile="t_junction_chambers"))["facts"]
        self.assertFalse(opened["outer_border"])
        self.assertGreaterEqual(opened["chamber_count"], 3)
        self.assertTrue(junction["outer_border"])
        self.assertGreater(junction["partial_wall_cells"], 0)

    def test_malformed_and_undeclared_impostors_fail_closed(self):
        cases = [[], [[]], [[True] * 7 for _ in range(7)], [[10] * 7 for _ in range(7)], [[1], [1, 2]], [[5] * 7 for _ in range(7)], [[0] * 7 for _ in range(7)]]
        no_unique = MOD.generate(97, 101, scene_profile="four_seed_ambiguous")
        for chamber in MOD._components(no_unique):
            for row, col in chamber:
                if no_unique[row][col] in {1, 2, 3}:
                    no_unique[row][col] = 0
        cases.append(no_unique)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "no_seed"}, {"n_chambers": 4}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(103)
        state = random.getstate()
        first = MOD.generate(107, 109, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(107, 109, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_rule_hash_and_base_sources_are_synced(self):
        source = canonical_row()["program_solution"]
        self.assertEqual(MOD.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        base = json.loads((ROOT / BASE_PATH).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
