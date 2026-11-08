from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "edb55a59dc46"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/fd166f81148e/E141__edb55a59dc46.json"


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def decode(grid):
    return [[int(value) for value in line] for line in grid] if grid and isinstance(grid[0], str) else grid


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

    def test_profiles_isolate_order_boundary_occupancy_and_selection(self):
        for seed in range(100):
            for profile in MOD.GENERAL_PROFILES:
                grid = MOD.generate(seed, seed * 7, scene_profile=profile)
                facts = MOD._analysis(grid)["facts"]
                header = facts["header_cells"]
                seed_row, seed_col = facts["seed"]
                if profile == "baseline_interior":
                    self.assertEqual(header[1][1] - header[0][1], 1)
                    self.assertFalse(facts["header_on_ray"])
                elif profile == "separated_header":
                    self.assertGreater(header[1][1] - header[0][1], 1)
                elif profile == "header_on_ray":
                    self.assertTrue(facts["header_on_ray"])
                elif profile == "seed_near_top":
                    self.assertEqual(seed_row, 1)
                elif profile == "seed_on_edge":
                    self.assertTrue(seed_row in (0, len(grid) - 1) or seed_col in (0, len(grid[0]) - 1))
                elif profile == "seed_in_corner":
                    self.assertIn(seed_row, (0, len(grid) - 1))
                    self.assertIn(seed_col, (0, len(grid[0]) - 1))
                elif profile == "occupied_ray_steps":
                    self.assertEqual(facts["ray_obstacles"], facts["obstacle_cells"])
                    self.assertEqual(len(facts["obstacle_cells"]), 2)
                elif profile == "third_header_ignored":
                    self.assertEqual(len(header), 3)
                    self.assertEqual(sum(value == header[2][2] for line in facts["output"] for value in line), 1)
                elif profile == "off_ray_distractors":
                    self.assertEqual(facts["off_ray_obstacles"], facts["obstacle_cells"])
                elif profile == "multiple_seeds_first":
                    self.assertEqual(len(facts["seed_cells"]), 2)
                    self.assertEqual(facts["seed"], min(facts["seed_cells"]))

    def test_phase_advances_through_occupied_cells_and_preserves_them(self):
        grid = [[0] * 10 for _ in range(8)]
        grid[0][1], grid[0][2] = 3, 5
        grid[3][4] = 9
        grid[4][4] = 6
        grid[3][6] = 7
        output = MOD.rule_mirror(grid)
        self.assertEqual(output[4][4], 6)
        self.assertEqual(output[5][4], 5)
        self.assertEqual(output[6][4], 3)
        self.assertEqual(output[3][5], 3)
        self.assertEqual(output[3][6], 7)
        self.assertEqual(output[3][7], 3)
        self.assertEqual(output[2][4], 3)
        self.assertEqual(output[1][4], 5)

    def test_distribution_covers_declared_semantics_and_varies_materially(self):
        profiles = Counter()
        inputs, outputs, shapes, colors = set(), set(), set(), set()
        seed_counts, header_counts, zero_extents = set(), set(), set()
        ray_obstacles = off_ray_obstacles = False
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            facts = analysis["facts"]
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, facts["output"])))
            shapes.add((len(grid), len(grid[0])))
            colors.update(value for line in grid for value in line)
            seed_counts.add(len(facts["seed_cells"]))
            header_counts.add(len(facts["header_cells"]))
            zero_extents.add(any(extent == 0 for extent in facts["extents"]))
            ray_obstacles = ray_obstacles or bool(facts["ray_obstacles"])
            off_ray_obstacles = off_ray_obstacles or bool(facts["off_ray_obstacles"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2550)
        self.assertGreater(len(outputs), 2550)
        self.assertGreater(len(shapes), 80)
        self.assertEqual(colors, set(range(10)))
        self.assertEqual(seed_counts, {1, 2})
        self.assertEqual(header_counts, {2, 3})
        self.assertEqual(zero_extents, {False, True})
        self.assertTrue(ray_obstacles)
        self.assertTrue(off_ray_obstacles)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 8 for _ in range(8)], [[3] * 8 for _ in range(8)]]
        one_header = [[0] * 9 for _ in range(8)]
        one_header[0][1] = 3
        one_header[3][4] = 9
        cases.append(one_header)
        same_header = [[0] * 9 for _ in range(8)]
        same_header[0][1] = same_header[0][2] = 3
        same_header[3][4] = 9
        cases.append(same_header)
        too_many_header = [[0] * 10 for _ in range(8)]
        too_many_header[0][1:5] = [1, 2, 3, 4]
        too_many_header[3][5] = 9
        cases.append(too_many_header)
        too_many_seeds = [[0] * 10 for _ in range(8)]
        too_many_seeds[0][1:3] = [1, 2]
        for row, col in ((2, 2), (4, 4), (6, 6)):
            too_many_seeds[row][col] = 9
        cases.append(too_many_seeds)
        mixed_obstacles = [[0] * 10 for _ in range(8)]
        mixed_obstacles[0][1:3] = [1, 2]
        mixed_obstacles[3][4] = 9
        mixed_obstacles[3][5] = 6
        mixed_obstacles[5][7] = 7
        cases.append(mixed_obstacles)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])
        with self.assertRaises(ValueError):
            MOD.rule_mirror(one_header)

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"grid_h": 8}):
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
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
