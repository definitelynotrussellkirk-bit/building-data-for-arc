"""Regression tests for the linked area-rank frame profiles."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "e2051b3f4045"
    / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_e2051b3f4045",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs() -> list[list[list[int]]]:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "e2051b3f4045":
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [
                pair["input"]
                for pair in [*row["train"], *tests]
            ]
    raise AssertionError("canonical task e2051b3f4045 is missing")


class LinkedAreaRankProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_all_canonical_inputs_match_the_extracted_signature_set(self):
        signatures = {
            self.generator.canonical_profile_signature(grid)
            for grid in canonical_inputs()
        }

        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)

    def test_default_prior_reaches_every_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {
                signature: 0
                for signature in self.generator._CANONICAL_SIGNATURES
            }
            for seed in range(800):
                grid = self.generator.generate(
                    seed,
                    seed * 17 + 1,
                    difficulty=band,
                )
                self.assertEqual(
                    [],
                    self.generator.self_check(grid, difficulty=band),
                )
                signature = self.generator.canonical_profile_signature(grid)
                if signature in counts:
                    counts[signature] += 1

            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(sum(counts.values()), 180)
                self.assertTrue(all(count > 0 for count in counts.values()))

    def test_cross_profile_recombination_is_not_official(self):
        grid = [row[:] for row in canonical_inputs()[0]]

        # Replace the 12x14 profile's L triomino with the 13x15 profile's
        # S tetromino while leaving the canvas and all three frames intact.
        for r, c in ((7, 9), (8, 9), (8, 10)):
            grid[r][c] = 0
        for r, c in ((6, 9), (7, 9), (7, 10), (8, 10)):
            grid[r][c] = 3

        signature = self.generator.canonical_profile_signature(grid)

        self.assertEqual([], self.generator.self_check(grid))
        self.assertIsNotNone(signature)
        self.assertNotIn(signature, self.generator._CANONICAL_SIGNATURES)


if __name__ == "__main__":
    unittest.main()
