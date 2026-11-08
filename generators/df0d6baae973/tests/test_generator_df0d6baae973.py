from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "df0d6baae973"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/868e1a8cbe17/M123__df0d6baae973.json"


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def decode(grid):
    return [[int(value) for value in row] for row in grid] if grid and isinstance(grid[0], str) else grid


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    pairs = row["train"] + ([test] if isinstance(test, dict) else test)
    return [{"input": decode(pair["input"]), "output": decode(pair["output"])} for pair in pairs]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_public_profiles_exact(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 5)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_every_general_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(60):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_profiles_isolate_count_order_tie_and_topology_rivals(self):
        for seed in range(100):
            analyses = {profile: MOD._analysis(MOD.generate(seed, seed * 7, scene_profile=profile)) for profile in MOD.GENERAL_PROFILES}
            self.assertEqual(len(analyses["two_objects_unequal"]["components"]), 2)
            self.assertEqual(len(analyses["four_objects_mixed"]["components"]), 4)
            self.assertEqual(len(analyses["five_objects_mixed"]["components"]), 5)
            increasing = analyses["three_sizes_increasing"]["sizes"]
            decreasing = analyses["three_sizes_decreasing"]["sizes"]
            self.assertEqual(increasing, sorted(increasing))
            self.assertEqual(decreasing, sorted(decreasing, reverse=True))
            low_tie = sorted(analyses["tie_for_smaller"]["sizes"])
            high_tie = sorted(analyses["tie_for_larger"]["sizes"])
            self.assertEqual(low_tie[0], low_tie[1])
            self.assertLess(low_tie[1], low_tie[2])
            self.assertLess(high_tie[0], high_tie[1])
            self.assertEqual(high_tie[1], high_tie[2])
            largest_middle = analyses["largest_middle_color"]["sizes"]
            smallest_middle = analyses["smallest_middle_color"]["sizes"]
            self.assertEqual(largest_middle[1], max(largest_middle))
            self.assertEqual(smallest_middle[1], min(smallest_middle))
            self.assertIn(1, analyses["singleton_component"]["sizes"])
            self.assertTrue(any(MOD._has_two_by_two(fact["cells"]) for fact in analyses["branched_polyominoes"]["components"]))

    def test_exact_matrix_ties_symmetry_and_shape_invariance(self):
        first = [[0] * 14 for _ in range(10)]
        for row, col in ((1, 1), (1, 2), (2, 2)):
            first[row][col] = 2
        for row, col in ((1, 8), (2, 8), (3, 8)):
            first[row][col] = 5
        for row, col in ((6, 3), (6, 4), (6, 5), (7, 5), (7, 6)):
            first[row][col] = 8
        second = [[0] * 14 for _ in range(10)]
        for row, col in ((1, 1), (2, 1), (3, 1)):
            second[row][col] = 2
        for row, col in ((1, 8), (1, 9), (1, 10)):
            second[row][col] = 5
        for row, col in ((6, 3), (7, 3), (8, 3), (8, 4), (8, 5)):
            second[row][col] = 8
        expected = [[0, 0, 8], [0, 0, 8], [8, 8, 0]]
        self.assertEqual(MOD.rule_mirror(first), expected)
        self.assertEqual(MOD.rule_mirror(second), expected)
        self.assertEqual(expected, [list(row) for row in zip(*expected)])

    def test_distribution_respects_intrinsic_matrix_codomain(self):
        profiles = Counter()
        inputs, outputs, input_shapes, output_shapes, signatures = set(), set(), set(), set(), set()
        colors = set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            input_shapes.add((len(grid), len(grid[0])))
            output_shapes.add((len(analysis["output"]), len(analysis["output"][0])))
            signatures.add(tuple(analysis["sizes"]))
            colors.update(value for row in grid for value in row)
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2550)
        self.assertGreater(len(outputs), 550)
        self.assertGreater(len(input_shapes), 45)
        self.assertEqual(output_shapes, {(2, 2), (3, 3), (4, 4), (5, 5)})
        self.assertGreater(len(signatures), 500)
        self.assertEqual(colors, set(range(10)))

    def test_malformed_and_impostors_fail_closed_but_ties_are_valid(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 8 for _ in range(8)], [[3] * 8 for _ in range(8)]]
        duplicate_color = [[0] * 10 for _ in range(8)]
        duplicate_color[1][1] = duplicate_color[1][7] = 4
        duplicate_color[5][4] = 6
        cases.append(duplicate_color)
        six = [[0] * 15 for _ in range(10)]
        for index, color in enumerate(range(1, 7)):
            six[1 + (index // 3) * 5][1 + (index % 3) * 5] = color
        cases.append(six)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        tied = MOD.generate(3, 7, scene_profile="tie_for_smaller")
        self.assertEqual(MOD.self_check(tied), [])
        output = MOD.rule_mirror(tied)
        self.assertTrue(any(output[row][col] == 0 for row in range(3) for col in range(3) if row != col))
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "equal_sizes"}, {"n_blobs": 3}):
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

    def test_rule_hash_and_base_sync(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
