from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "f34cf63540e2"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = "data/base/solutions/banks/868e1a8cbe17/H124__f34cf63540e2.json"


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in line] for line in value]
    return value


def canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    pairs = row["train"] + ([test] if isinstance(test, dict) else test)
    return [{"input": _grid(pair["input"]), "output": _grid(pair["output"])} for pair in pairs]


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
                for seed in range(80):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_transform_mapping_sequence_order_and_identity(self):
        patch = [[1, 2, 0], [0, 3, 4]]
        self.assertEqual(MOD._apply_commands(patch, (2,)), [[0, 1], [3, 2], [4, 0]])
        self.assertEqual(MOD._apply_commands(patch, (3,)), [[4, 3, 0], [0, 2, 1]])
        self.assertEqual(MOD._apply_commands(patch, (4,)), [[1, 0], [2, 3], [0, 4]])
        self.assertEqual(MOD._apply_commands(patch, (5,)), [[0, 2, 1], [4, 3, 0]])
        self.assertEqual(MOD._apply_commands(patch, (6,)), [[0, 3, 4], [1, 2, 0]])
        self.assertNotEqual(MOD._apply_commands(patch, (2, 5)), MOD._apply_commands(patch, (5, 2)))
        self.assertEqual(MOD._apply_commands(patch, (5, 4, 2)), patch)

    def test_profiles_witness_palette_order_region_selection_and_crop_semantics(self):
        for seed in range(100):
            for profile in MOD.GENERAL_PROFILES:
                grid = MOD.generate(seed, seed * 7, scene_profile=profile)
                facts = MOD._analysis(grid)["facts"]
                self.assertEqual(facts["commands"], MOD._COMMANDS[profile])
                if profile == "triple_disjoint_palette":
                    self.assertFalse(set(facts["commands"]) & facts["source_colors"])
                elif profile == "composed_identity":
                    self.assertTrue(facts["identity"])
                elif profile == "first_region_with_decoy":
                    self.assertGreaterEqual(len(facts["lower_regions"]), 2)
                    self.assertTrue(facts["outside_lower_regions"])
                    self.assertFalse(facts["enclosed_extras"])
                elif profile == "embedded_bbox_decoy":
                    self.assertGreaterEqual(len(facts["lower_regions"]), 2)
                    self.assertTrue(facts["enclosed_extras"])
                    top, left, _, _ = facts["chosen_bounds"]
                    for row, col in facts["enclosed_extras"]:
                        self.assertEqual(facts["source_crop"][row - top][col - left], grid[row][col])
                else:
                    self.assertFalse(facts["identity"])
                    self.assertTrue(set(facts["commands"]) & facts["source_colors"])

    def test_first_lower_region_is_selected_and_external_decoy_is_ignored(self):
        grid = [[0] * 11 for _ in range(9)]
        grid[0][1] = 3
        for row, col, value in ((3, 2, 1), (3, 3, 2), (4, 2, 3), (4, 3, 4)):
            grid[row][col] = value
        grid[6][8] = 9
        facts = MOD._rule_facts(grid)
        self.assertEqual(facts["chosen_bounds"], (3, 2, 2, 2))
        self.assertEqual(facts["source_crop"], [[1, 2], [3, 4]])
        self.assertEqual(facts["output"], [[4, 3], [2, 1]])
        self.assertTrue(facts["outside_lower_regions"])

    def test_distribution_covers_all_profiles_and_varies_materially(self):
        profiles = Counter()
        inputs, outputs, general_inputs, general_outputs, canvas_shapes, crop_shapes, colors = set(), set(), set(), set(), set(), set(), set()
        command_counts, commands = set(), set()
        identity = external = embedded = disjoint = False
        for seed in range(4000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 31, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            facts = analysis["facts"]
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, facts["output"])))
            if analysis["scene_profile"] in MOD.GENERAL_PROFILES:
                general_inputs.add(tuple(map(tuple, grid)))
                general_outputs.add(tuple(map(tuple, facts["output"])))
            canvas_shapes.add((len(grid), len(grid[0])))
            crop_shapes.add((len(facts["source_crop"]), len(facts["source_crop"][0])))
            colors.update(value for line in grid for value in line)
            command_counts.add(len(facts["commands"]))
            commands.update(facts["commands"])
            identity |= facts["identity"]
            external |= bool(facts["outside_lower_regions"])
            embedded |= bool(facts["enclosed_extras"])
            disjoint |= not bool(set(facts["commands"]) & facts["source_colors"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        general_count = sum(profiles[profile] for profile in MOD.GENERAL_PROFILES)
        self.assertGreater(len(inputs), 3500)
        self.assertGreater(len(outputs), 3500)
        self.assertGreater(len(general_inputs) / general_count, 0.99)
        self.assertGreater(len(general_outputs) / general_count, 0.99)
        self.assertGreater(len(canvas_shapes), 90)
        self.assertGreater(len(crop_shapes), 20)
        self.assertEqual(colors, set(range(10)))
        self.assertEqual(command_counts, {1, 2, 3})
        self.assertEqual(commands, {2, 3, 4, 5, 6})
        self.assertTrue(identity and external and embedded and disjoint)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 10 for _ in range(8)]]
        bad_command = [[0] * 10 for _ in range(8)]
        bad_command[0][1] = 7
        bad_command[3][2:4] = [1, 2]
        bad_command[4][2:4] = [3, 4]
        cases.append(bad_command)
        row_one = [[0] * 10 for _ in range(8)]
        row_one[0][1] = 2
        row_one[1][8] = 1
        row_one[3][2:4] = [2, 3]
        row_one[4][2:4] = [4, 5]
        cases.append(row_one)
        mono = [[0] * 10 for _ in range(8)]
        mono[0][1] = 2
        mono[3][2:4] = [1, 1]
        mono[4][2:4] = [1, 1]
        cases.append(mono)
        undeclared = [[0] * 10 for _ in range(8)]
        undeclared[0][1], undeclared[0][4] = 2, 3
        undeclared[3][2:4] = [2, 1]
        undeclared[4][2:4] = [3, 4]
        cases.append(undeclared)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"n_cmds": 2}):
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
