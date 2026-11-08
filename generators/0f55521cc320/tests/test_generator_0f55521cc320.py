"""Regression tests for the linked triangle-base generator repair."""

from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / "0f55521cc320" / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_0f55521cc320", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "0f55521cc320":
                continue
            tests = [row["test"]] if isinstance(row["test"], dict) else row["test"]
            return [pair["input"] for pair in [*row["train"], *tests]]
    raise AssertionError("canonical task is missing")


class TriangleBaseGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_all_canonical_inputs_have_the_exact_linked_profiles(self):
        signatures = {
            self.generator.canonical_profile_signature(grid)
            for grid in canonical_inputs()
        }
        self.assertEqual({(3, 1), (5, 1), (5, 3), (7, 3), (9, 3)}, signatures)
        for grid in canonical_inputs():
            self.assertEqual([], self.generator.self_check(grid))

    def test_every_profile_is_reachable_and_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in self.generator.SCENE_PROFILES:
                grid = self.generator.generate(
                    17,
                    23,
                    difficulty=band,
                    scene_profile=profile,
                )
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                self.assertEqual(
                    {"scene_profile": profile},
                    self.generator.observe_overrides(grid),
                )

    def test_default_prior_reaches_official_manifold_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            matches = 0
            for seed in range(240):
                grid = self.generator.generate(seed, seed * 13 + 5, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                matches += self.generator.canonical_profile_signature(grid) is not None
            self.assertGreaterEqual(matches, 80, band)

    def test_recombined_bottom_and_upper_widths_are_rejected(self):
        grid = [row[:] for row in canonical_inputs()[2]]
        grid[-1][1] = grid[-1][3]
        self.assertTrue(self.generator.self_check(grid))
        self.assertIsNone(self.generator.canonical_profile_signature(grid))

    def test_generation_preserves_process_global_rng(self):
        random.seed(12345)
        expected = [random.random() for _ in range(4)]
        random.seed(12345)
        self.generator.generate(9, 11, difficulty="hard")
        observed = [random.random() for _ in range(4)]
        self.assertEqual(expected, observed)


if __name__ == "__main__":
    unittest.main()
