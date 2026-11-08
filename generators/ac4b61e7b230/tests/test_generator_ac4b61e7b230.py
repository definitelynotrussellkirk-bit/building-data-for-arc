from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "ac4b61e7b230"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASE = "data/base/solutions/training/05f2a901__ac4b61e7b230.json"


def canonical_row():
    return next(
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def pairs():
    return canonical_pairs(TASK, root=ROOT, labeled_only=True)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_exact_public_profiles(self):
        self.assertEqual(len(pairs()), 4)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs()):
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.self_check(pair["input"]), [])
            generated = MOD.generate(1, 2, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertEqual(MOD.canonical_profile_signature(generated), profile)
            self.assertIsNot(generated, MOD._PUBLIC_INPUTS[profile])

    def test_every_relation_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(50):
                    grid = MOD.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(analysis["relation"], MOD._PROFILE_RELATION[profile])
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_translation_semantics_shape_preservation_and_purity(self):
        for profile in MOD.GENERAL_PROFILES:
            for seed in range(40):
                grid = MOD.generate(seed, seed * 23, scene_profile=profile)
                before = copy.deepcopy(grid)
                analysis = MOD._analysis(grid)
                output = MOD.rule_mirror(grid)
                self.assertEqual(grid, before)
                self.assertEqual(
                    {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 2},
                    analysis["shifted_red"],
                )
                self.assertEqual(
                    {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 8},
                    analysis["cyan"],
                )
                self.assertEqual(len(analysis["red"]), len(analysis["shifted_red"]))
                moved_bbox = MOD._bbox(analysis["shifted_red"])
                cyan_bbox = analysis["cyan_bbox"]
                rel = analysis["relation"]
                if rel[0] < 0:
                    self.assertEqual(moved_bbox[2] + 1, cyan_bbox[0])
                elif rel[0] > 0:
                    self.assertEqual(cyan_bbox[2] + 1, moved_bbox[0])
                if rel[1] < 0:
                    self.assertEqual(moved_bbox[3] + 1, cyan_bbox[1])
                elif rel[1] > 0:
                    self.assertEqual(cyan_bbox[3] + 1, moved_bbox[1])

    def test_distribution_and_branch_coverage(self):
        profiles = Counter()
        inputs, outputs, shapes, translations, red_shapes, cyan_shapes = set(), set(), set(), set(), set(), set()
        for seed in range(3000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 29, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            translations.add(analysis["translation"])
            red_shapes.add(tuple(sorted((r - analysis["red_bbox"][0], c - analysis["red_bbox"][1]) for r, c in analysis["red"])))
            cyan_shapes.add(tuple(sorted((r - analysis["cyan_bbox"][0], c - analysis["cyan_bbox"][1]) for r, c in analysis["cyan"])))
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2500)
        self.assertGreater(len(outputs), 2200)
        self.assertGreater(len(shapes), 150)
        self.assertGreater(len(translations), 120)
        declared_shapes = {tuple(sorted(shape)) for shape in MOD._SHAPES.values()}
        self.assertTrue(declared_shapes <= red_shapes)
        self.assertTrue(declared_shapes <= cyan_shapes)

    def test_malformed_and_uncalibrated_inputs(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)]]
        ragged = MOD.generate(3, 5, scene_profile="red_above")
        ragged[0].pop()
        cases.append(ragged)
        extra_color = MOD.generate(7, 9, scene_profile="red_left")
        extra_color[0][0] = 4
        cases.append(extra_color)
        split_red = MOD.generate(11, 13, scene_profile="red_below")
        split_red[0][0] = 2
        cases.append(split_red)
        overlapping_boxes = [[0] * 5 for _ in range(5)]
        overlapping_boxes[1][1] = overlapping_boxes[1][2] = overlapping_boxes[2][1] = 2
        overlapping_boxes[2][2] = overlapping_boxes[2][3] = overlapping_boxes[3][2] = 8
        cases.append(overlapping_boxes)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)

    def test_override_errors_determinism_fresh_returns_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "spread"}, {"grid_h": 12}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_rule_hash_and_base_source_are_normalized_equivalent(self):
        source = canonical_row()["program_solution"]
        normalized = " ".join(source.split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), normalized)
        self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), normalized)


if __name__ == "__main__":
    unittest.main()
