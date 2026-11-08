from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "f29af9159005"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/765a70430bc9/H3__f29af9159005.json"


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_public_profiles_exact(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 3)
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

    def test_profiles_isolate_blocking_union_boundaries_and_transparency(self):
        for seed in range(100):
            for profile in MOD.GENERAL_PROFILES:
                grid = MOD.generate(seed, seed * 7, scene_profile=profile)
                facts = MOD._analysis(grid)["facts"]
                anchors = facts["seeds"]
                if profile == "single_clear_cross":
                    self.assertEqual(len(anchors), 1)
                    self.assertEqual(len(facts["blockers"]), 1)
                    self.assertEqual(facts["off_axis_blockers"], facts["blockers"])
                elif profile == "off_axis_decoys":
                    self.assertEqual(facts["off_axis_blockers"], facts["blockers"])
                elif profile == "clip_up_adjacent":
                    self.assertEqual(facts["directional_blockers"][anchors[0]], {"up": 1})
                elif profile == "clip_down_distant":
                    self.assertGreaterEqual(facts["directional_blockers"][anchors[0]]["down"], 2)
                elif profile == "clip_left_right":
                    self.assertEqual(set(facts["directional_blockers"][anchors[0]]), {"left", "right"})
                elif profile == "clip_all_four":
                    self.assertEqual(set(facts["directional_blockers"][anchors[0]]), set(MOD._DIRECTIONS))
                elif profile == "aligned_two_seeds":
                    self.assertEqual(len(anchors), 2)
                    self.assertTrue(anchors[0][0] == anchors[1][0] or anchors[0][1] == anchors[1][1])
                elif profile == "crossing_two_seeds":
                    self.assertEqual(len(anchors), 2)
                    self.assertNotEqual(anchors[0][0], anchors[1][0])
                    self.assertNotEqual(anchors[0][1], anchors[1][1])
                elif profile == "two_seed_rescue":
                    self.assertTrue(facts["rescue_cells"])
                elif profile == "seed_on_edge":
                    row, col = anchors[0]
                    self.assertTrue(row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1))
                elif profile == "seed_in_corner":
                    row, col = anchors[0]
                    self.assertIn(row, (0, len(grid) - 1))
                    self.assertIn(col, (0, len(grid[0]) - 1))
                elif profile == "non_one_transparent":
                    self.assertEqual(len(facts["other_nonzero"]), 1)

    def test_strict_between_blocking_any_seed_rescue_and_non_one_transparency(self):
        grid = [[0] * 9 for _ in range(7)]
        grid[3][4] = 2
        grid[3][6] = 1
        output = MOD.rule_mirror(grid)
        self.assertEqual(output[3][5], 4)
        self.assertEqual(output[3][6], 1)
        self.assertEqual(output[3][7], 0)
        self.assertEqual(output[3][8], 0)
        self.assertEqual(output[0][4], 4)
        transparent = [[0] * 9 for _ in range(7)]
        transparent[3][4] = 2
        transparent[3][2] = 8
        transparent_out = MOD.rule_mirror(transparent)
        self.assertEqual(transparent_out[3][2], 8)
        self.assertEqual(transparent_out[3][1], 4)
        self.assertEqual(transparent_out[3][0], 4)
        rescue = MOD.generate(17, 23, scene_profile="two_seed_rescue")
        rescue_facts = MOD._analysis(rescue)["facts"]
        for row, col in rescue_facts["rescue_cells"]:
            self.assertEqual(rescue_facts["output"][row][col], 4)
            self.assertTrue(rescue_facts["visible_from"][(row, col)])
            self.assertTrue(rescue_facts["blocked_from"][(row, col)])

    def test_distribution_covers_declared_semantics_and_varies_materially(self):
        profiles = Counter()
        inputs, outputs, shapes, colors = set(), set(), set(), set()
        seed_counts, blocker_counts = set(), set()
        blocked_directions, edge_states = set(), set()
        rescue = transparent = False
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
            seed_counts.add(len(facts["seeds"]))
            blocker_counts.add(len(facts["blockers"]))
            for directions in facts["directional_blockers"].values():
                blocked_directions.update(directions)
            edge_states.add(any(row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1) for row, col in facts["seeds"]))
            rescue = rescue or bool(facts["rescue_cells"])
            transparent = transparent or bool(facts["other_nonzero"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2700)
        self.assertGreater(len(outputs), 2700)
        self.assertGreater(len(shapes), 50)
        self.assertEqual(colors, set(range(10)))
        self.assertEqual(seed_counts, {1, 2})
        self.assertIn(0, blocker_counts)
        self.assertIn(10, blocker_counts)
        self.assertEqual(blocked_directions, set(MOD._DIRECTIONS))
        self.assertEqual(edge_states, {False, True})
        self.assertTrue(rescue and transparent)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 8 for _ in range(8)], [[2] * 8 for _ in range(8)]]
        three_seeds = [[0] * 9 for _ in range(7)]
        for row, col in ((1, 1), (3, 4), (5, 7)):
            three_seeds[row][col] = 2
        cases.append(three_seeds)
        too_many_blockers = [[0] * 13 for _ in range(9)]
        too_many_blockers[4][11] = 2
        for row, col in [(0, c) for c in range(11)]:
            too_many_blockers[row][col] = 1
        cases.append(too_many_blockers)
        two_other = [[0] * 9 for _ in range(7)]
        two_other[3][4] = 2
        two_other[2][2] = 5
        two_other[4][6] = 6
        cases.append(two_other)
        undeclared = [[0] * 9 for _ in range(7)]
        undeclared[3][4] = 2
        undeclared[3][1] = 1
        cases.append(undeclared)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"n_seeds": 2}):
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
