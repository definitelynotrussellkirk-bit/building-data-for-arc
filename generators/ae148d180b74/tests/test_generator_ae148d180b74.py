from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "ae148d180b74"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/3cb9777539c7/H141__ae148d180b74.json"


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def pairs():
    row = canonical_row()
    return row["train"] + [row["test"]]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_exact_public_profiles(self):
        self.assertEqual(len(pairs()), 5)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs()):
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.self_check(pair["input"]), [])
            generated = MOD.generate(1, 2, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertEqual(MOD.canonical_profile_signature(generated), profile)

    def test_every_topology_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(40):
                    grid = MOD.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_shortest_union_semantics_and_purity(self):
        for profile in MOD.GENERAL_PROFILES:
            for seed in range(30):
                grid = MOD.generate(seed, seed * 23, scene_profile=profile)
                before = copy.deepcopy(grid)
                analysis = MOD._analysis(grid)
                output = MOD.rule_mirror(grid)
                self.assertEqual(grid, before)
                for row in range(len(grid)):
                    for col in range(len(grid[0])):
                        expected = 8 if (row, col) in analysis["marked_cells"] else grid[row][col]
                        self.assertEqual(output[row][col], expected)
                self.assertTrue(all(output[r][c] == 0 for r, c in analysis["decoy_cells"] if grid[r][c] == 0))

    def test_profile_feature_partition(self):
        expected = {
            "unique_straight": (1, False, False, 0),
            "unique_one_turn": (1, False, False, 1),
            "unique_winding": (1, True, False, None),
            "unique_with_decoys": (1, True, True, None),
            "multi_open": (2, False, False, None),
            "multi_with_decoys": (2, False, True, None),
            "multi_detour": (2, True, False, None),
            "multi_detour_decoys": (2, True, True, None),
        }
        for profile, (paths, detour, decoys, turns) in expected.items():
            analysis = MOD._analysis(MOD.generate(31, 37, scene_profile=profile))
            self.assertEqual(analysis["path_count_class"], paths)
            self.assertEqual(analysis["distance"] > analysis["manhattan"], detour)
            self.assertEqual(bool(analysis["decoy_cells"]), decoys)
            if turns is not None:
                self.assertEqual(analysis["turns"], turns)

    def test_broad_disconnected_returns_fresh_copy(self):
        grid = [[5] * 7 for _ in range(7)]
        grid[1][1] = 2
        grid[5][5] = 3
        before = copy.deepcopy(grid)
        output = MOD.rule_mirror(grid)
        self.assertEqual(output, before)
        self.assertIsNot(output, grid)
        self.assertTrue(MOD.self_check(grid))

    def test_distribution_and_branch_coverage(self):
        profiles = Counter()
        inputs, outputs, shapes, distances, marked, decoys = set(), set(), set(), set(), set(), set()
        for seed in range(3000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 29, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            distances.add(analysis["distance"])
            marked.add(len(analysis["marked_cells"]))
            decoys.add(len(analysis["decoy_cells"]))
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2350)
        self.assertGreater(len(outputs), 2350)
        self.assertGreater(len(shapes), 150)
        self.assertGreater(len(distances), 20)
        self.assertGreater(len(marked), 35)
        self.assertGreater(len(decoys), 5)

    def test_malformed_inputs(self):
        cases = [[], [[]], [[True]], [[10]], [[5] * 6 for _ in range(6)]]
        ragged = MOD.generate(3, 5, scene_profile="multi_open"); ragged[0].pop(); cases.append(ragged)
        extra_start = MOD.generate(7, 9, scene_profile="unique_one_turn"); extra_start[0][0] = 2; cases.append(extra_start)
        extra_color = MOD.generate(11, 13, scene_profile="multi_detour"); extra_color[0][0] = 4; cases.append(extra_color)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)

    def test_override_errors_determinism_fresh_returns_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "maze"}, {"grid_h": 12}):
            with self.assertRaises(ValueError): MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError): MOD.generate(1, 2, difficulty="extreme")
        random.seed(47); state = random.getstate(); first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state); second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second); self.assertIsNot(first, second)

    def test_rule_hash_and_base_source_are_synced(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__": unittest.main()
