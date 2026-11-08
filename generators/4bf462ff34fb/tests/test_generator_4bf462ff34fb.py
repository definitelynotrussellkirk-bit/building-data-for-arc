"""Regression coverage for the top-only blue-component generator."""
from __future__ import annotations

import importlib.util
import random
import sys
import time
import unittest
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


TASK_ID = "4bf462ff34fb"
ROOT = find_root(__file__)
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"


def load_generator():
    name = "generator_4bf462ff34fb"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_inputs() -> list[list[list[int]]]:
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT)]


class TopOnlyComponentGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_all_canonical_inputs_are_accepted_and_linked(self):
        signatures = set()
        for grid in canonical_inputs():
            self.assertEqual([], self.generator.self_check(grid))
            signature = self.generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            signatures.add(signature)
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)

    def test_default_prior_reaches_every_linked_profile_per_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {
                signature: 0
                for signature in self.generator._CANONICAL_SIGNATURES
            }
            for seed in range(800):
                grid = self.generator.generate(
                    seed,
                    seed * 17 + 3,
                    difficulty=band,
                )
                self.assertEqual([], self.generator.self_check(grid))
                signature = self.generator.canonical_profile_signature(grid)
                if signature in counts:
                    counts[signature] += 1
            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(sum(counts.values()), 160)
                self.assertTrue(all(count > 0 for count in counts.values()))

    def test_recombined_component_morphology_is_not_an_official_profile(self):
        grid = [row[:] for row in canonical_inputs()[0]]
        grid[8][0] = 1  # extend the left-border blue singleton to a domino
        self.assertEqual([], self.generator.self_check(grid))
        self.assertIsNone(self.generator.canonical_profile_signature(grid))

    def test_dimension_boundaries_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for height in (8, 18):
                for width in (8, 18):
                    grid = self.generator.generate(
                        19,
                        23,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                    )
                    self.assertEqual((height, width), (len(grid), len(grid[0])))
                    self.assertEqual([], self.generator.self_check(grid))
                    self.assertEqual(
                        {"grid_h": height, "grid_w": width},
                        self.generator.observe_overrides(grid),
                    )

    def test_every_semantic_witness_names_a_rival_disagreement(self):
        self.assertEqual(
            set(self.generator.WITNESS_RIVALS),
            set(self.generator.SEMANTIC_WITNESSES),
        )

    def test_semantic_contract_refutes_declared_shortcuts(self):
        witness_hits = {
            name: 0 for name in self.generator.WITNESS_RIVALS
        }
        for sample_index in range(120):
            grid = self.generator.generate(
                10_000 + sample_index,
                sample_index,
                difficulty="hard",
            )
            expected = self.generator.rule_mirror(grid)
            for witness, rivals in self.generator.WITNESS_RIVALS.items():
                if self.generator.SEMANTIC_WITNESSES[witness](grid):
                    witness_hits[witness] += 1
                    self.assertTrue(
                        any(
                            self.generator.SEMANTIC_RIVALS[name](grid) != expected
                            for name in rivals
                        )
                    )
        self.assertTrue(all(count > 0 for count in witness_hits.values()))

    def test_every_rotation_of_known_four_pair_window_is_identifiable(self):
        pairs = []
        for sample_index in range(5, 9):
            grid = self.generator.generate(
                0,
                sample_index,
                difficulty="easy",
            )
            pairs.append(
                {
                    "input": grid,
                    "output": self.generator.rule_mirror(grid),
                }
            )

        for held_out in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            with self.subTest(held_out=held_out):
                self.assertEqual(
                    [],
                    self.generator.lesson_identifiable(demos, pairs[held_out]),
                )

    def test_fallback_scene_contains_every_anti_shortcut_witness(self):
        grid = self.generator._place_specs(
            8,
            8,
            self.generator._fallback_specs(),
            random.Random(0),
        )
        self.assertIsNotNone(grid)
        for witness in self.generator.WITNESS_RIVALS:
            with self.subTest(witness=witness):
                self.assertTrue(self.generator.SEMANTIC_WITNESSES[witness](grid))

    def test_known_override_matrix_hotspots_finish_promptly(self):
        cases = (
            ("hard", 1, 20, {"grid_h": 9, "grid_w": 14}),
            ("hard", 2, 37, {"grid_h": 16, "grid_w": 17}),
            ("medium", 1, 20, {"grid_h": 11, "grid_w": 13}),
            ("hard", 1, 20, {"grid_h": 14, "grid_w": 17}),
            ("hard", 1, 20, {"grid_w": 17}),
            ("hard", 1, 20, {"grid_h": 17, "grid_w": 15}),
            ("hard", 2, 37, {"grid_h": 12, "grid_w": 14}),
        )
        started = time.perf_counter()
        for band, seed, sample_index, overrides in cases:
            grid = self.generator.generate(
                seed,
                sample_index,
                difficulty=band,
                **overrides,
            )
            self.assertEqual([], self.generator.self_check(grid))
        elapsed = time.perf_counter() - started
        self.assertLess(
            elapsed,
            0.20,
            f"known exact-axis hotspots took {elapsed:.3f}s",
        )

    def test_three_demo_lessons_are_identifiable(self):
        for start in range(24):
            episode = []
            for sample_index in range(
                start,
                start + self.generator.EXAMPLES_NEEDED + 1,
            ):
                grid = self.generator.generate(
                    20_000 + sample_index,
                    sample_index,
                    difficulty="medium",
                )
                episode.append(
                    {
                        "input": grid,
                        "output": self.generator.rule_mirror(grid),
                    }
                )
            self.assertEqual(
                [],
                self.generator.lesson_identifiable(
                    episode[: self.generator.EXAMPLES_NEEDED],
                    episode[-1],
                ),
            )


if __name__ == "__main__":
    unittest.main()
