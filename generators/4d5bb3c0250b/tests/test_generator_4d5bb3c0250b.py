"""Focused regression tests for the unique-pure-block generator repair."""
from __future__ import annotations

import importlib.util
import json
import os
import random
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GENERATOR = (
    ROOT / "puzzle_generators" / "per_puzzle" / "4d5bb3c0250b" / "generator.py"
)
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_4d5bb3c0250b_under_test", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == "4d5bb3c0250b":
                test = row["test"]
                tests = [test] if isinstance(test, dict) else test
                return [pair["input"] for pair in [*row["train"], *tests]]
    raise AssertionError("canonical task missing")


class UniquePureBlockGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_canonical_inputs_are_accepted_and_strictly_profiled(self):
        signatures = []
        for grid in canonical_inputs():
            self.assertEqual([], self.generator.self_check(grid))
            signature = self.generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            signatures.append(signature[0])
        self.assertEqual(
            {
                "canonical_23_5x4",
                "canonical_29_5x5",
                "canonical_23_3x6",
            },
            set(signatures),
        )

    def test_default_prior_has_stable_strict_support_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            matches = 0
            profile_counts = Counter()
            for seed in range(300):
                grid = self.generator.generate(seed, seed * 17 + 3, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                signature = self.generator.canonical_profile_signature(grid)
                if signature is not None:
                    matches += 1
                    profile_counts[signature[0]] += 1
            with self.subTest(band=band, counts=profile_counts):
                self.assertGreaterEqual(matches, 75)
                self.assertTrue(all(profile_counts[name] > 0 for name in self.generator._CANONICAL_PROFILES))

    def test_every_exact_axis_is_observed_from_the_returned_grid(self):
        cases = (
            {
                "profile": "canonical_23_3x6",
                "separator_color": 1,
                "target_color": 9,
                "target_at_border": True,
                "target_cells": 4,
                "distractor_colors": 2,
            },
            {
                "profile": "generalized_29_4x6",
                "separator_color": 9,
                "target_color": 1,
                "target_at_border": False,
                "target_cells": 8,
                "distractor_colors": 4,
            },
        )
        for i, case in enumerate(cases):
            grid = self.generator.generate(100 + i, 500 + i, difficulty="hard", **case)
            self.assertEqual([], self.generator.self_check(grid))
            self.assertEqual(case, self.generator.observe_overrides(grid))

    def test_recombined_two_pure_blocks_is_rejected(self):
        grid = self.generator.generate(
            19,
            23,
            profile="canonical_23_5x4",
            target_at_border=False,
            target_cells=6,
            distractor_colors=2,
        )
        data = self.generator._analyze(grid)
        target = data["pure"][0]
        other = next(block for block in data["blocks"] if block is not target)
        changed = [row[:] for row in grid]
        # Reduce one distractor to a second pure block while preserving its span.
        r0, r1 = data["row_spans"][other["ri"]]
        c0, c1 = data["col_spans"][other["ci"]]
        kept = next(iter(other["colors"]))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if changed[r][c] != 0:
                    changed[r][c] = kept
        self.assertTrue(any("exactly one" in p for p in self.generator.self_check(changed)))
        self.assertIsNone(self.generator.canonical_profile_signature(changed))

    def test_fresh_returns_and_process_global_rng_preservation(self):
        random.seed(9127)
        state = random.getstate()
        first = self.generator.generate(4, 9, difficulty="medium")
        self.assertEqual(state, random.getstate())
        snapshot = [row[:] for row in first]
        second = self.generator.generate(5, 10, difficulty="medium")
        self.assertEqual(snapshot, first)
        first[0][0] = (first[0][0] + 1) % 10
        replay = self.generator.generate(4, 9, difficulty="medium")
        self.assertEqual(snapshot, replay)
        self.assertNotEqual(first, replay)
        self.assertIsNot(first, second)


if __name__ == "__main__":
    unittest.main()
