"""Focused semantic regressions for generator 3696e3c9d426."""

from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "3696e3c9d426"
    / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_3696e3c9d426",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "3696e3c9d426":
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [*row["train"], *tests]
    raise AssertionError("canonical task 3696e3c9d426 is missing")


class ColumnGravityGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_all_canonical_pairs_are_exact_and_linked(self):
        pairs = canonical_pairs()
        self.assertEqual(3, len(pairs))
        self.assertEqual(
            {"public_profile_1", "public_profile_2", "public_profile_3"},
            {
                self.generator.canonical_profile_signature(pair["input"])
                for pair in pairs
            },
        )
        for pair in pairs:
            self.assertEqual([], self.generator.self_check(pair["input"]))
            self.assertEqual(
                pair["output"],
                self.generator.rule_mirror(pair["input"]),
            )

    def test_every_generated_scene_is_active_and_order_preserving(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(180):
                grid = self.generator.generate(seed, seed * 17, difficulty=band)
                analysis = self.generator._analyze(grid)
                self.assertEqual([], analysis["errors"])
                self.assertNotEqual(grid, analysis["facts"]["output"])
                if tuple(map(tuple, grid)) not in self.generator._PUBLIC_INPUTS:
                    self.assertTrue(
                        analysis["facts"]["sorting_counterexample"]
                    )
                for col in range(len(grid[0])):
                    before = [
                        row[col] for row in grid if row[col] != 0
                    ]
                    after = [
                        row[col]
                        for row in analysis["facts"]["output"]
                        if row[col] != 0
                    ]
                    self.assertEqual(before, after)

    def test_linked_branch_reaches_every_public_profile(self):
        for band in ("easy", "medium", "hard"):
            profiles = {
                self.generator.canonical_profile_signature(
                    self.generator.generate(
                        10_000 + seed,
                        seed,
                        difficulty=band,
                        scene_family="linked",
                    )
                )
                for seed in range(360)
            }
            with self.subTest(band=band):
                self.assertEqual(
                    {
                        "public_profile_1",
                        "public_profile_2",
                        "public_profile_3",
                    },
                    profiles,
                )

    def test_generalized_branch_has_band_visible_sizes(self):
        for band, height in {"easy": 6, "medium": 7, "hard": 8}.items():
            for seed in range(100):
                grid = self.generator.generate(
                    30_000 + seed,
                    seed,
                    difficulty=band,
                    scene_family="generalized",
                )
                analysis = self.generator._analyze(grid)
                self.assertEqual([], analysis["errors"])
                self.assertEqual(height, len(grid))
                self.assertEqual("generalized", analysis["facts"]["scene_family"])

    def test_structural_checker_rejects_targeted_impostors(self):
        impostors = [
            [[0] * 6 for _ in range(6)],
            [[1]],
            [[1, 1], [1, 1]],
            [[1, 2, 3, 4, 5, 6]],
            [
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [1, 0, 2, 0, 3, 0],
                [4, 0, 5, 0, 6, 0],
            ],
        ]
        for index, grid in enumerate(impostors):
            with self.subTest(index=index):
                self.assertTrue(self.generator.self_check(grid))

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        state = random.getstate()
        first = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertEqual(
            second,
            self.generator.generate(111, 222, difficulty="hard"),
        )

    def test_bad_calls_fail_loudly(self):
        with self.assertRaises(ValueError):
            self.generator.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            self.generator.generate(1, 2, fake_axis=True)


if __name__ == "__main__":
    unittest.main()
