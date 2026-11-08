from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

TASK = "196d5de2ea8c"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE_PATHS = (
    "data/base/solutions/training/996ec1f3__196d5de2ea8c.json",
    "data/base/solutions/augmented/996ec1f3__21a5c55b126a.json",
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

    def test_canonical_dividers_and_modes_are_exact(self):
        expected = ((11, 8, 3, [1, 9, 8, 2]), (6, 6, 8, [3, 4, 2, 1]), (10, 10, 0, [1, 8, 2, 4]), (7, 10, 1, [2, 4, 0, 8]))
        for profile, (row, col, divider, modes) in zip(MOD.PUBLIC_PROFILES, expected):
            facts = MOD._analysis(MOD.generate(3, 5, scene_profile=profile))["facts"]
            self.assertEqual((facts["div_row"], facts["div_col"], facts["divider"], facts["modes"]), (row, col, divider, modes))
            self.assertEqual(facts["uniform_rows"], [row])
            self.assertEqual(facts["uniform_cols"], [col])

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

    def test_output_corners_and_cross_are_exact(self):
        for profile in MOD.GENERAL_PROFILES:
            facts = MOD._analysis(MOD.generate(17, 23, scene_profile=profile))["facts"]
            out, modes, divider = facts["output"], facts["modes"], facts["divider"]
            self.assertEqual([out[0][0], out[0][2], out[2][0], out[2][2]], modes)
            self.assertEqual([out[0][1], out[1][0], out[1][1], out[1][2], out[2][1]], [divider] * 5)

    def test_zero_is_lawful_as_divider_or_one_region_mode(self):
        divider = MOD._analysis(MOD.generate(31, 37, scene_profile="zero_divider"))["facts"]
        region = MOD._analysis(MOD.generate(41, 43, scene_profile="zero_quadrant"))["facts"]
        self.assertEqual(divider["divider"], 0)
        self.assertNotIn(0, divider["modes"])
        self.assertNotEqual(region["divider"], 0)
        self.assertEqual(region["modes"].count(0), 1)

    def test_repeated_and_divider_reused_modes_are_distinct_lessons(self):
        repeated = MOD._analysis(MOD.generate(47, 53, scene_profile="repeated_modes"))["facts"]
        reused = MOD._analysis(MOD.generate(59, 61, scene_profile="divider_reused_mode"))["facts"]
        self.assertEqual(len(set(repeated["modes"])), 3)
        self.assertNotIn(repeated["divider"], repeated["modes"])
        self.assertEqual(len(set(reused["modes"])), 4)
        self.assertEqual(reused["modes"].count(reused["divider"]), 1)

    def test_close_runner_and_heavy_noise_still_have_unique_modes(self):
        runner = MOD._analysis(MOD.generate(67, 71, scene_profile="close_runner_up"))["facts"]
        heavy = MOD._analysis(MOD.generate(73, 79, scene_profile="heavy_noise"))["facts"]
        self.assertLessEqual(min(runner["margins"]), 2)
        self.assertTrue(all(margin > 0 for margin in runner["margins"]))
        self.assertLessEqual(max(heavy["fractions"]), 0.48)
        self.assertTrue(all(margin > 0 for margin in heavy["margins"]))

    def test_row_zero_and_column_zero_are_ignored_by_region_modes(self):
        grid = MOD.generate(83, 89, scene_profile="centered_distinct")
        expected = MOD.rule_mirror(grid)
        changed = [row[:] for row in grid]
        facts = MOD._extract_facts(changed)
        divider = facts["divider"]
        for col in range(len(changed[0])):
            if col != facts["div_col"]:
                changed[0][col] = (col * 3 + 2) % 10
                if changed[0][col] == divider:
                    changed[0][col] = (divider + 1) % 10
        for row in range(1, len(changed)):
            if row != facts["div_row"]:
                changed[row][0] = (row * 7 + 1) % 10
                if changed[row][0] == divider:
                    changed[row][0] = (divider + 1) % 10
        self.assertEqual(MOD.rule_mirror(changed), expected)

    def test_outer_border_decoys_do_not_change_region_decision(self):
        facts = MOD._analysis(MOD.generate(97, 101, scene_profile="outer_border_decoys"))["facts"]
        self.assertGreaterEqual(len(facts["ignored_border_colors"]), 8)
        self.assertEqual(len(set(facts["modes"])), 4)

    def test_malformed_and_ambiguous_impostors_fail_closed(self):
        cases = [[], [[]], [[True] * 7 for _ in range(7)], [[10] * 7 for _ in range(7)], [[1], [1, 2]], [[0] * 7 for _ in range(7)]]
        no_cross = [[(row + col) % 3 for col in range(9)] for row in range(9)]
        cases.append(no_cross)
        multiple_rows = MOD.generate(103, 107, scene_profile="centered_distinct")
        multiple_rows[1] = multiple_rows[MOD._extract_facts(multiple_rows)["div_row"]][:]
        cases.append(multiple_rows)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "no_divider"}, {"divider": 4}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(109)
        state = random.getstate()
        first = MOD.generate(113, 127, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(113, 127, difficulty="hard")
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
