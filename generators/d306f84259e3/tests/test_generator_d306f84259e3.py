from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "d306f84259e3"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/training/a5f85a15__d306f84259e3.json"


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def decode(grid):
    return [[int(value) for value in row] for row in grid] if grid and isinstance(grid[0], str) else grid


def public_pairs():
    row = canonical_row()
    test = row["test"]
    pairs = row["train"] + ([test] if isinstance(test, dict) else test)
    return [{"input": decode(pair["input"]), "output": decode(pair["output"])} for pair in pairs]


class GeneratorTests(unittest.TestCase):
    def test_all_public_pairs_exact(self):
        pairs = public_pairs()
        self.assertEqual(len(pairs), 4)
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
                    self.assertGreaterEqual(analysis["changed"] / (len(grid) * len(grid[0])), 0.01)

    def test_profiles_isolate_ordering_rivals(self):
        for seed in range(100):
            grids = {profile: MOD.generate(seed, seed * 7, scene_profile=profile) for profile in MOD.GENERAL_PROFILES}
            analyses = {profile: MOD._analysis(grid) for profile, grid in grids.items()}
            self.assertEqual(len(analyses["contiguous_single_diagonal"]["effectful_diagonals"]), 1)
            gapped = analyses["gapped_single_diagonal"]["effectful_diagonals"][0]
            self.assertTrue(any(b[0] - a[0] > 1 for a, b in zip(gapped, gapped[1:])))
            self.assertEqual(len(analyses["two_diagonals_reset"]["effectful_diagonals"]), 2)
            self.assertGreaterEqual(len(analyses["many_diagonals"]["effectful_diagonals"]), 4)
            self.assertGreater(len({value for row in grids["multicolor_diagonal"] for value in row if value}), 1)
            self.assertTrue(any(value == 4 for row in grids["existing_yellow"] for value in row))
            self.assertGreaterEqual(sum(len(group) == 1 for group in analyses["singleton_decoys"]["diagonals"].values()), 3)
            for profile, axis in (("same_row_different_parity", 0), ("same_column_different_parity", 1)):
                analysis = analyses[profile]
                buckets = {}
                for (row, col), parity in analysis["parity"].items():
                    buckets.setdefault((row, col)[axis], set()).add(parity)
                self.assertTrue(any(values == {0, 1} for values in buckets.values()))
            edge = grids["edge_diagonals"]
            self.assertTrue(all(edge[r][c] != 0 for r, c in ((0, 0), (0, len(edge[0]) - 1), (len(edge) - 1, 0), (len(edge) - 1, len(edge[0]) - 1))))
            self.assertGreaterEqual(max(map(len, analyses["long_diagonal"]["effectful_diagonals"])), 10)
            self.assertGreaterEqual(len({len(group) for group in analyses["mixed_lengths"]["effectful_diagonals"]}), 3)

    def test_exact_multicolor_gap_existing_yellow_and_diagonal_reset(self):
        grid = [[0] * 8 for _ in range(8)]
        cells = {
            (0, 0): 2, (2, 2): 7, (5, 5): 3, (7, 7): 9,
            (0, 2): 4, (1, 3): 6, (4, 6): 8,
            (6, 0): 5,
        }
        for (row, col), value in cells.items():
            grid[row][col] = value
        before = [row[:] for row in grid]
        output = MOD.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual([output[i][i] for i in (0, 2, 5, 7)], [2, 4, 3, 4])
        self.assertEqual([output[r][c] for r, c in ((0, 2), (1, 3), (4, 6))], [4, 4, 8])
        self.assertEqual(output[6][0], 5)
        self.assertTrue(all(output[r][c] == 0 for r in range(8) for c in range(8) if (r, c) not in cells))

    def test_distribution(self):
        profiles = Counter()
        inputs, outputs, shapes, diagonal_counts, nonzero_counts = set(), set(), set(), set(), set()
        colors = set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            diagonal_counts.add(len(analysis["diagonals"]))
            nonzero_counts.add(sum(len(group) for group in analysis["diagonals"].values()))
            colors.update(value for row in grid for value in row)
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2300)
        self.assertGreater(len(outputs), 2300)
        self.assertGreater(len(shapes), 65)
        self.assertEqual(colors, set(range(10)))
        self.assertGreaterEqual(len(diagonal_counts), 4)
        self.assertGreater(len(nonzero_counts), 10)

    def test_malformed_and_impostors_fail_closed(self):
        cases = [
            [], [[]], [[True]], [[10]], [[1], [1, 2]],
            [[0] * 8 for _ in range(8)],
            [[3, 3], [3, 3]],
            [[7] * 6 for _ in range(6)],
        ]
        singleton = [[0] * 8 for _ in range(8)]
        singleton[2][2] = 3
        cases.append(singleton)
        wrong_diags = [[0] * 8 for _ in range(8)]
        wrong_diags[0][0] = wrong_diags[0][2] = wrong_diags[0][4] = 3
        cases.append(wrong_diags)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "noise"}, {"grid_h": 10}):
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
