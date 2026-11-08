from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "e2eab62ba331"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/cc07013acae1/E69__e2eab62ba331.json"


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
        for band in (None, "easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(60):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_profiles_isolate_selector_shape_bbox_and_distractor_rivals(self):
        shape_profiles = {"hollow_ring", "concave_c", "staircase"}
        for seed in range(100):
            for profile in MOD.GENERAL_PROFILES:
                grid = MOD.generate(seed, seed * 7, scene_profile=profile)
                facts = MOD._analysis(grid)["facts"]
                self.assertEqual(len(facts["choices"]), 1)
                self.assertNotIn((0, 0), facts["selected"]["cells"])
                if profile in shape_profiles:
                    self.assertEqual(facts["shape_kind"], profile)
                elif profile == "irregular_polyomino":
                    self.assertIsNone(facts["shape_kind"])
                elif profile == "extended_selector":
                    self.assertGreater(len(facts["anchor"]["cells"]), 1)
                elif profile == "interior_distractor":
                    self.assertTrue(facts["interior_other"])
                elif profile == "target_touches_edge":
                    row0, col0, row1, col1 = facts["bbox"]
                    self.assertTrue(row0 == 0 or col0 == 0 or row1 == len(grid) - 1 or col1 == len(grid[0]) - 1)
                elif profile == "many_distractors":
                    self.assertGreaterEqual(len(facts["other_objects"]), 4)

    def test_exact_subgrid_preserves_interior_other_colors_and_excludes_anchor(self):
        grid = [[0] * 10 for _ in range(9)]
        grid[0][0] = grid[0][1] = grid[1][0] = 6
        for row, col in ((2, 3), (2, 4), (2, 5), (3, 3), (3, 5), (4, 3), (4, 4), (4, 5)):
            grid[row][col] = 6
        grid[3][4] = 9
        grid[7][7] = grid[7][8] = 2
        facts = MOD._rule_facts(grid)
        self.assertEqual(len(facts["anchor"]["cells"]), 3)
        self.assertEqual(facts["bbox"], (2, 3, 4, 5))
        self.assertEqual(facts["interior_other"], {(3, 4)})
        self.assertEqual(MOD.rule_mirror(grid), [[6, 6, 6], [6, 9, 6], [6, 6, 6]])

    def test_distribution_covers_profiles_and_retains_material_variation(self):
        profiles = Counter()
        inputs, outputs, input_shapes, output_shapes = set(), set(), set(), set()
        colors = set()
        selector_sizes, target_sizes = set(), set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            facts = analysis["facts"]
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, facts["output"])))
            input_shapes.add((len(grid), len(grid[0])))
            output_shapes.add((len(facts["output"]), len(facts["output"][0])))
            colors.update(value for row in grid for value in row)
            selector_sizes.add(len(facts["anchor"]["cells"]))
            target_sizes.add(len(facts["selected"]["cells"]))
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2600)
        self.assertGreater(len(outputs), 1000)
        self.assertGreater(len(input_shapes), 80)
        self.assertGreater(len(output_shapes), 25)
        self.assertEqual(colors, set(range(10)))
        self.assertIn(1, selector_sizes)
        self.assertTrue(any(size > 1 for size in selector_sizes))
        self.assertGreater(len(target_sizes), 10)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 8 for _ in range(8)], [[3] * 8 for _ in range(8)]]
        no_match = [[0] * 10 for _ in range(8)]
        no_match[0][0] = 4
        no_match[3][3] = no_match[3][4] = 7
        cases.append(no_match)
        duplicate = [[0] * 10 for _ in range(8)]
        duplicate[0][0] = 4
        duplicate[2][2] = duplicate[2][3] = 4
        duplicate[5][6] = duplicate[5][7] = 4
        duplicate[6][1] = 8
        cases.append(duplicate)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        self.assertEqual(MOD.rule_mirror(no_match), [[0]])
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"n_blobs": 3}):
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

    def test_rule_hash_and_base_source_are_exactly_synced(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
