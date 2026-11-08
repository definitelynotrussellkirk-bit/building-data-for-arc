"""Regression tests for the seeded-frame generator repair."""

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
    / "a2eace95c1cf"
    / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_a2eace95c1cf",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _norm_grid(grid):
    return [
        [int(value) for value in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def canonical_inputs() -> list[list[list[int]]]:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "a2eace95c1cf":
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [
                _norm_grid(pair["input"])
                for pair in [*row["train"], *tests]
            ]
    raise AssertionError("canonical task a2eace95c1cf is missing")


class SeededFrameGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.canonical = canonical_inputs()

    def test_all_canonical_inputs_are_accepted_and_define_the_profile_bank(self):
        signatures = {
            self.generator.canonical_profile_signature(grid)
            for grid in self.canonical
        }
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)
        for index, grid in enumerate(self.canonical):
            with self.subTest(index=index):
                self.assertEqual([], self.generator.self_check(grid))
                self.assertEqual([], self.generator.strict_canonical_like(grid))

    def test_default_prior_reaches_every_linked_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {
                signature: 0
                for signature in self.generator._CANONICAL_SIGNATURES
            }
            for seed in range(600):
                grid = self.generator.generate(
                    seed,
                    seed * 17 + 1,
                    difficulty=band,
                )
                self.assertEqual([], self.generator.self_check(grid))
                signature = self.generator.canonical_profile_signature(grid)
                if signature in counts:
                    counts[signature] += 1
            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(sum(counts.values()), 300)
                self.assertTrue(all(count > 0 for count in counts.values()))

    def test_exact_axis_boundaries_are_observable(self):
        cases = (
            {"grid_h": 9},
            {"grid_h": 14},
            {"grid_w": 12},
            {"grid_w": 18},
            {"n_frames": 2},
            {"n_frames": 3},
            {"n_seeded_frames": 1},
            {"n_seeded_frames": 3},
            {"frame_spacing": "gapped"},
            {"frame_spacing": "adjacent"},
            {
                "grid_h": 9,
                "grid_w": 12,
                "n_frames": 3,
                "n_seeded_frames": 3,
                "frame_spacing": "gapped",
            },
        )
        for overrides in cases:
            grid = self.generator.generate(17, 3, difficulty="hard", **overrides)
            observed = self.generator.observe_overrides(grid)
            with self.subTest(overrides=overrides, observed=observed):
                self.assertEqual([], self.generator.self_check(grid))
                for key, value in overrides.items():
                    self.assertEqual(value, observed[key])
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            self.generator.generate(17, 3, n_frames=2, n_seeded_frames=3)

    def test_self_check_rejects_targeted_impostors(self):
        base = [row[:] for row in self.canonical[0]]
        mutations = {}

        no_seed = [row[:] for row in base]
        no_seed[2][2] = 0
        mutations["no_seed"] = no_seed

        two_seeds = [row[:] for row in base]
        two_seeds[3][3] = 9
        mutations["two_seeds"] = two_seeds

        broken_frame = [row[:] for row in base]
        broken_frame[1][1] = 0
        mutations["broken_frame"] = broken_frame

        outside_distractor = [row[:] for row in base]
        outside_distractor[8][8] = 9
        mutations["outside_distractor"] = outside_distractor

        own_border_seed = [row[:] for row in base]
        own_border_seed[3][3] = 2
        mutations["own_border_seed"] = own_border_seed

        for name, grid in mutations.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))

    def test_negative_recombination_and_role_reuse_are_distinguished(self):
        valid = self.generator.generate(91, 0, difficulty="medium")
        analysis = self.generator._analysis(valid)
        seeded = next(frame for frame in analysis["frames"] if frame["seed"] is not None)
        occupied = {(seeded["seed"][0], seeded["seed"][1])}
        replacement = next(cell for cell in seeded["interior"] if cell not in occupied)
        absent_color = next(
            color for color in range(1, 10)
            if all(color not in row for row in valid)
        )
        impostor = [row[:] for row in valid]
        impostor[replacement[0]][replacement[1]] = absent_color
        self.assertTrue(self.generator.self_check(impostor))

        role_reuse = self.generator.generate(91, 7, difficulty="medium")
        role_analysis = self.generator._analysis(role_reuse)
        self.assertTrue(
            any(
                color in role_analysis["border_colors"]
                for color in role_analysis["seed_colors"]
            )
        )
        self.assertEqual([], self.generator.self_check(role_reuse))

    def test_first_lesson_block_falsifies_named_rivals(self):
        pairs = []
        for sample_index in range(4):
            grid = self.generator.generate(2026, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": self.generator._fill_local(grid)})
        self.assertEqual(
            [],
            self.generator.lesson_identifiable(pairs[:3], pairs[3]),
        )

    def test_replay_fresh_returns_and_global_rng_purity(self):
        random.seed(123456)
        before = random.getstate()
        first = self.generator.generate(77, 9, difficulty="hard")
        middle = self.generator.generate(88, 10, difficulty="easy")
        replay = self.generator.generate(77, 9, difficulty="hard")
        after = random.getstate()
        self.assertEqual(before, after)
        self.assertEqual(first, replay)
        self.assertIsNot(first, replay)
        self.assertIsNot(first[0], replay[0])
        middle[0][0] = 9
        self.assertEqual(first, self.generator.generate(77, 9, difficulty="hard"))


if __name__ == "__main__":
    unittest.main()
