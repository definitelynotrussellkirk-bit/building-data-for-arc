from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs as load_canonical_pairs, canonical_path, find_root

TASK = "f13d23b71bd4"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASE = "data/base/solutions/training/6ca952ad__f13d23b71bd4.json"


def canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        return next(row for line in handle if (row := json.loads(line)).get("task_id") == TASK)


def canonical_pairs():
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in load_canonical_pairs(TASK, root=ROOT)
    ]


def base_path():
    for relative in (BASE, "shared/" + BASE):
        candidate = ROOT / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No base solution for {TASK} under {ROOT}")


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_public_profiles_exact(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 4)
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

    def test_profiles_isolate_threshold_connectivity_shapes_and_collisions(self):
        for seed in range(100):
            for profile in MOD.GENERAL_PROFILES:
                facts = MOD._analysis(MOD.generate(seed, seed * 7, scene_profile=profile))["facts"]
                objects = facts["objects"]
                sizes = sorted(obj["size"] for obj in objects)
                if profile == "threshold_3_vs_4":
                    self.assertEqual(sizes, [3, 4])
                    self.assertEqual(len({obj["color"] for obj in objects}), 2)
                elif profile == "same_color_thresholds":
                    self.assertEqual(sizes, [3, 4])
                    self.assertEqual(len({obj["color"] for obj in objects}), 1)
                elif profile == "mixed_sizes_1_to_6":
                    self.assertEqual(sizes, [1, 2, 3, 4, 5, 6])
                elif profile == "different_colors_touch":
                    self.assertTrue(facts["different_color_touching"])
                elif profile == "diagonal_same_color":
                    self.assertTrue(facts["diagonal_same_color"])
                elif profile == "wide_fall":
                    self.assertIn("wide", {obj["shape_kind"] for obj in objects})
                elif profile == "tall_fall":
                    self.assertIn("tall", {obj["shape_kind"] for obj in objects})
                elif profile == "irregular_fall":
                    self.assertIn("irregular", {obj["shape_kind"] for obj in objects})
                elif profile == "already_bottom_big":
                    self.assertTrue(any(obj["size"] >= 4 and obj["drop"] == 0 for obj in objects))
                    self.assertTrue(any(obj["size"] >= 4 and obj["drop"] > 0 for obj in objects))
                elif profile == "landing_overlap_small_wins":
                    self.assertTrue(facts["collision_pairs"])
                    self.assertTrue(any(objects[index]["size"] < 4 for pair in facts["collision_pairs"] for index in pair))
                elif profile == "landing_overlap_later_big_wins":
                    self.assertTrue(facts["collision_pairs"])
                    self.assertTrue(all(objects[index]["size"] >= 4 for pair in facts["collision_pairs"] for index in pair))
                elif profile == "many_colors":
                    self.assertEqual(len(objects), 5)
                    self.assertEqual(len({obj["color"] for obj in objects}), 5)

    def test_exact_threshold_translation_fresh_canvas_and_later_winner(self):
        grid = [[7] * 9 for _ in range(9)]
        for row, col in ((1, 1), (2, 1), (2, 2)):
            grid[row][col] = 3
        for row, col in ((1, 5), (1, 6), (2, 5), (2, 6)):
            grid[row][col] = 4
        output = MOD.rule_mirror(grid)
        self.assertEqual({(row, col) for row in range(9) for col in range(9) if output[row][col] == 3}, {(1, 1), (2, 1), (2, 2)})
        self.assertEqual({(row, col) for row in range(9) for col in range(9) if output[row][col] == 4}, {(7, 5), (7, 6), (8, 5), (8, 6)})
        for profile in ("landing_overlap_small_wins", "landing_overlap_later_big_wins"):
            scene = MOD.generate(17, 23, scene_profile=profile)
            facts = MOD._analysis(scene)["facts"]
            for cell, owners in facts["collisions"].items():
                self.assertEqual(facts["output"][cell[0]][cell[1]], facts["objects"][owners[-1]]["color"])

    def test_distribution_covers_declared_semantics_and_varies_materially(self):
        profiles = Counter()
        inputs, outputs, shapes, colors = set(), set(), set(), set()
        sizes, counts, drops, palette_counts = set(), set(), set(), set()
        collision = different_touch = diagonal = False
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
            counts.add(len(facts["objects"]))
            palette_counts.add(len({obj["color"] for obj in facts["objects"]}))
            for obj in facts["objects"]:
                sizes.add(obj["size"])
                drops.add(obj["drop"])
            collision = collision or bool(facts["collisions"])
            different_touch = different_touch or bool(facts["different_color_touching"])
            diagonal = diagonal or bool(facts["diagonal_same_color"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2550)
        self.assertGreater(len(outputs), 2500)
        self.assertGreater(len(shapes), 100)
        self.assertEqual(colors, set(range(10)))
        self.assertTrue(set(range(1, 11)).issubset(sizes))
        self.assertEqual(counts, {2, 3, 5, 6})
        self.assertIn(1, palette_counts)
        self.assertIn(5, palette_counts)
        self.assertIn(0, drops)
        self.assertTrue(any(drop > 0 for drop in drops))
        self.assertTrue(collision and different_touch and diagonal)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[7] * 8 for _ in range(8)], [[1] * 8 for _ in range(8)]]
        one_object = [[7] * 9 for _ in range(9)]
        for row in range(4):
            one_object[row][2] = 3
        cases.append(one_object)
        only_small = [[7] * 9 for _ in range(9)]
        only_small[1][1] = 2
        only_small[3][3] = 4
        cases.append(only_small)
        no_fall = [[7] * 9 for _ in range(9)]
        for row, col in ((7, 1), (7, 2), (8, 1), (8, 2)):
            no_fall[row][col] = 3
        no_fall[2][6] = 4
        cases.append(no_fall)
        too_large = [[7] * 12 for _ in range(12)]
        for col in range(11):
            too_large[1][col] = 3
        too_large[4][10] = 5
        cases.append(too_large)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "balanced"}, {"n_big_blobs": 2}):
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
        base = json.loads(base_path().read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
