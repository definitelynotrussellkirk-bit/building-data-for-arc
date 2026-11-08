"""Focused regressions for the keyed frame-ray generator 7d09ccad28c8."""
from __future__ import annotations

import copy
import importlib
import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.7d09ccad28c8.generator"
)


def _canonical_row():
    pairs = canonical_pairs(GENERATOR.TASK_ID, root=ROOT, labeled_only=True)
    train = [pair for pair in pairs if pair["split"] == "train"]
    test = [pair for pair in pairs if pair["split"] == "test"]
    return {"train": train, "test": test}


def _scenes(grid):
    return [
        GENERATOR._frame_scene(grid, box)
        for box in GENERATOR._frame_boxes(grid)
    ]


class Generator7d09ccad28c8Tests(unittest.TestCase):
    def test_version_rule_hash_and_axis_contract(self):
        self.assertEqual("3.0.0", GENERATOR.VERSION)
        self.assertEqual("850aa5ef55c4", GENERATOR.RULE_HASH)
        self.assertEqual(
            {"grid_h", "grid_w", "n_frames", "frame_size", "n_blocked_rays"},
            set(GENERATOR.AXES),
        )

    def test_self_check_accepts_every_canonical_input(self):
        row = _canonical_row()
        pairs = row["train"] + row["test"]
        self.assertEqual(5, len(pairs))
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            self.assertEqual([], GENERATOR.self_check(grid))
            self.assertEqual(grid, pair["input"], "self_check mutated canonical input")

    def test_four_sample_schedule_covers_semantic_branches(self):
        all_keys = set()
        blocked_counts = []
        wall_rays = 0
        positive_blocked = 0
        zero_length_blocked = 0
        for sample_index in range(4):
            grid = GENERATOR.generate(41, sample_index, difficulty="medium")
            self.assertEqual([], GENERATOR.self_check(grid))
            scenes = _scenes(grid)
            self.assertEqual(2, len(scenes))
            blocked_counts.append(sum(scene["blocked"] for scene in scenes))
            all_keys.update(scene["key"][2] for scene in scenes)
            for scene in scenes:
                if scene["blocked"]:
                    if scene["paint_path"]:
                        positive_blocked += 1
                    else:
                        zero_length_blocked += 1
                else:
                    wall_rays += 1
                self.assertGreater(
                    sum(len(item["paint_path"]) for item in scenes),
                    0,
                    "ordinary grid must not be an identity",
                )
        self.assertEqual({1, 2, 3, 4}, all_keys)
        self.assertEqual([2, 1, 0, 2], blocked_counts)
        self.assertGreater(wall_rays, 0)
        self.assertGreater(positive_blocked, 0)
        self.assertGreater(zero_length_blocked, 0)

    def test_single_axis_boundaries_are_exact_and_observable(self):
        cases = (
            {"grid_h": 13},
            {"grid_h": 18},
            {"grid_w": 15},
            {"grid_w": 22},
            {"n_frames": 1},
            {"n_frames": 2},
            {"frame_size": 6},
            {"frame_size": 8},
            {"n_blocked_rays": 0},
            {"n_blocked_rays": 2},
        )
        for band in ("easy", "medium", "hard"):
            for index, case in enumerate(cases):
                grid = GENERATOR.generate(
                    9000 + index,
                    7000 + index,
                    difficulty=band,
                    **case,
                )
                observed = GENERATOR.observe_overrides(grid)
                self.assertEqual([], GENERATOR.self_check(grid))
                for key, expected in case.items():
                    self.assertEqual(expected, observed[key], (band, case, observed))

    def test_incompatible_exact_axes_reject_loudly(self):
        with self.assertRaisesRegex(ValueError, "exceeds n_frames"):
            GENERATOR.generate(
                1,
                2,
                difficulty="hard",
                n_frames=1,
                n_blocked_rays=2,
            )
        with self.assertRaisesRegex(ValueError, "no feasible"):
            GENERATOR.generate(
                1,
                2,
                difficulty="hard",
                grid_h=13,
                grid_w=15,
                frame_size=8,
                n_frames=2,
            )

    def test_declared_mutation_fixtures_are_rejected(self):
        fixtures = list(GENERATOR.mutation_fixtures())
        self.assertGreaterEqual(len(fixtures), 4)
        for name, grid in fixtures:
            self.assertTrue(GENERATOR.self_check(grid), name)

    def test_degenerate_textures_are_distinct_and_rejected(self):
        baseline = GENERATOR.generate(5, 6, difficulty="medium")
        seen = set()
        for texture in GENERATOR.DEGENERATE_TEXTURES:
            grid = GENERATOR.generate(5, 6, difficulty="medium", texture=texture)
            self.assertNotEqual(baseline, grid)
            self.assertTrue(GENERATOR.self_check(grid), texture)
            seen.add(tuple(map(tuple, grid)))
        self.assertEqual(len(GENERATOR.DEGENERATE_TEXTURES), len(seen))

    def test_generation_is_deterministic_fresh_and_global_rng_pure(self):
        random.seed(78123)
        state = random.getstate()
        first = GENERATOR.generate(77, 31, difficulty="hard")
        pristine = copy.deepcopy(first)
        second = GENERATOR.generate(77, 31, difficulty="hard")
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = 9
        self.assertEqual(pristine, GENERATOR.generate(77, 31, difficulty="hard"))

    def test_unknown_override_rejects(self):
        with self.assertRaisesRegex(ValueError, "unsupported override"):
            GENERATOR.generate(0, 0, invented_axis=True)


if __name__ == "__main__":
    unittest.main()
