from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path
from reviewer_support import find_root, canonical_path, load_selected_generator

TASK = "df92ae881dc8"
ROOT = find_root(__file__)
DATA = canonical_path(ROOT).parent.parent
MOD, _, _ = load_selected_generator(TASK, root=ROOT)
BASES = (
    "data/base/solutions/training/f8c80d96__df92ae881dc8.json",
    "data/base/solutions/augmented/f8c80d96__312b01516f3d.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def row_pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_and_public_profiles_exact(self):
        rows = canonical_rows()
        self.assertEqual({row["source"] for row in rows}, {"training", "augmented"})
        pairs = [pair for row in rows for pair in row_pairs(row)]
        self.assertEqual(len(pairs), 8)
        self.assertEqual(len({tuple(map(tuple, pair["input"])) for pair in pairs}), 4)
        seen = set()
        for pair in pairs:
            profile = MOD.canonical_profile_signature(pair["input"])
            self.assertIn(profile, MOD.PUBLIC_PROFILES)
            seen.add(profile)
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
        self.assertEqual(seen, set(MOD.PUBLIC_PROFILES))

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

    def test_profiles_exercise_period_branch_direction_and_winner(self):
        observed_periods = set()
        observed_winners = set()
        for seed in range(100):
            for profile in MOD.GENERAL_PROFILES:
                facts = MOD._analysis(MOD.generate(seed, seed * 7, scene_profile=profile))["facts"]
                observed_periods.add(facts["period"])
                if profile.startswith("full_"):
                    expected_direction = 1 if profile.endswith("_right") else -1
                    self.assertEqual(facts["branch"], "full_columns")
                    self.assertEqual(facts["directions"], [expected_direction])
                    self.assertEqual(len(facts["full_cols"]), 1)
                else:
                    parts = profile.split("_")
                    expected = (-1 if parts[2] == "up" else 1, -1 if parts[3] == "left" else 1)
                    self.assertEqual(facts["branch"], "nested_l")
                    self.assertEqual(facts["winner"], expected)
                    self.assertGreaterEqual(facts["chosen_run"][3], 3)
                    observed_winners.add(facts["winner"])
        self.assertEqual(observed_periods, {2, 3, 4})
        self.assertEqual(observed_winners, {(-1, -1), (-1, 1), (1, -1), (1, 1)})

    def test_exact_tie_key_completion_and_original_cell_preservation(self):
        grid = [[0] * 12 for _ in range(10)]
        for col in range(1, 5):
            grid[2][col] = 7
        for col in range(6, 10):
            grid[7][col] = 7
        facts = MOD._rule_facts(grid)
        self.assertEqual(facts["period"], 2)
        self.assertEqual(facts["chosen_run"], (7, 6, 9, 4))
        self.assertEqual(facts["winner"], (-1, -1))
        output = MOD.rule_mirror(grid)
        for row, col in facts["foreground_cells"]:
            self.assertEqual(output[row][col], 7)
        for row in range(10):
            for col in range(12):
                self.assertEqual(output[row][col], 7 if (row, col) in facts["complete_cells"] else 5)

    def test_distribution_covers_declared_semantics_and_varies_materially(self):
        profiles = Counter()
        inputs, outputs, shapes, fact_signatures = set(), set(), set(), set()
        colors = set()
        branches, periods, winners, full_directions = set(), set(), set(), set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            facts = analysis["facts"]
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            fact_signatures.add((facts["period"], facts["branch"], facts["winner"], tuple(facts["directions"]), facts["foreground"]))
            colors.update(value for row in grid for value in row)
            branches.add(facts["branch"])
            periods.add(facts["period"])
            if facts["winner"] is not None:
                winners.add(facts["winner"])
            full_directions.update(facts["directions"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2400)
        self.assertGreater(len(outputs), 2400)
        self.assertGreater(len(shapes), 80)
        self.assertGreaterEqual(len(fact_signatures), 70)
        self.assertEqual(colors, {0, 1, 2, 3, 4, 6, 7, 8, 9})
        self.assertEqual(branches, {"full_columns", "nested_l"})
        self.assertEqual(periods, {2, 3, 4})
        self.assertEqual(winners, {(-1, -1), (-1, 1), (1, -1), (1, 1)})
        self.assertEqual(full_directions, {-1, 1})

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [
            [],
            [[]],
            [[True]],
            [[10]],
            [[1], [1, 2]],
            [[0] * 8 for _ in range(8)],
            [[3] * 8 for _ in range(8)],
        ]
        two_colors = [[0] * 10 for _ in range(8)]
        for col in range(5):
            two_colors[2][col] = 4
        two_colors[5][5] = 6
        cases.append(two_colors)
        sparse = [[0] * 10 for _ in range(8)]
        for row, col in ((1, 1), (1, 3), (2, 5), (4, 2), (5, 7), (6, 4)):
            sparse[row][col] = 8
        cases.append(sparse)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "spiral"}, {"period": 3}):
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

    def test_rule_hash_and_both_base_sources_are_exactly_synced(self):
        rows = canonical_rows()
        sources = {row["program_solution"] for row in rows}
        self.assertEqual(len(sources), 1)
        source = sources.pop()
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        for path in BASES:
            base = json.loads((DATA / path.removeprefix("data/")).read_text())
            self.assertEqual(base["racket_target"]["raw_code"], source)
            self.assertEqual(base["racket_target"]["target_code"], source)
            self.assertEqual(base["racket_target"]["canonicalization_status"], "preserved_executable_source")


if __name__ == "__main__":
    unittest.main()
