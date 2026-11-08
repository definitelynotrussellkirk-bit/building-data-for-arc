"""Regression tests for the fill-row-intervals generator repair."""

from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "e4e743fd0a82"
    / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_e4e743fd0a82",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_inputs() -> list[list[list[int]]]:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "e4e743fd0a82":
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [pair["input"] for pair in [*row["train"], *tests]]
    raise AssertionError("canonical task e4e743fd0a82 is missing")


class FillRowIntervalsGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.canonical = canonical_inputs()

    def test_all_canonical_inputs_are_accepted_with_exact_joint_signatures(self):
        signatures = {
            self.generator.canonical_profile_signature(grid)
            for grid in self.canonical
        }
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)
        for grid in self.canonical:
            self.assertEqual([], self.generator.self_check(grid))

    def test_every_exact_override_combination_is_observed_from_returned_grid(self):
        for band in ("easy", "medium", "hard"):
            for layout in self.generator.LAYOUTS:
                for texture in self.generator.TEXTURES:
                    for color_reuse in (False, True):
                        grid = self.generator.generate(
                            91,
                            17,
                            difficulty=band,
                            layout=layout,
                            texture=texture,
                            color_reuse=color_reuse,
                        )
                        self.assertEqual([], self.generator.self_check(grid))
                        self.assertEqual(
                            {
                                "layout": layout,
                                "texture": texture,
                                "color_reuse": color_reuse,
                            },
                            self.generator.observe_overrides(grid),
                        )

    def test_default_prior_reaches_all_branches_and_retains_canonical_profiles(self):
        for band in ("easy", "medium", "hard"):
            layouts = set()
            textures = set()
            reuse_values = set()
            canonical_counts = {
                signature: 0 for signature in self.generator._CANONICAL_SIGNATURES
            }
            draws = 1200
            for seed in range(draws):
                grid = self.generator.generate(seed, seed * 13 + 5, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                observed = self.generator.observe_overrides(grid)
                layouts.add(observed["layout"])
                textures.add(observed["texture"])
                reuse_values.add(observed["color_reuse"])
                signature = self.generator.canonical_profile_signature(grid)
                if signature in canonical_counts:
                    canonical_counts[signature] += 1

            with self.subTest(band=band):
                self.assertEqual(set(self.generator.LAYOUTS), layouts)
                self.assertEqual(set(self.generator.TEXTURES), textures)
                self.assertEqual({False, True}, reuse_values)
                self.assertGreaterEqual(sum(canonical_counts.values()), draws * 0.05)
                self.assertTrue(all(count > 0 for count in canonical_counts.values()))

    def test_minimal_impostors_and_filled_output_are_rejected(self):
        impostors = {
            "all_background": [[0] * 9 for _ in range(6)],
            "full_one_color": [[3] * 9 for _ in range(6)],
            "singleton": [[0] * 9 for _ in range(6)],
            "solid_2x2": [[0] * 9 for _ in range(6)],
            "short_line": [[0] * 9 for _ in range(6)],
        }
        impostors["singleton"][2][4] = 3
        for row in (2, 3):
            for col in (4, 5):
                impostors["solid_2x2"][row][col] = 3
        impostors["short_line"][2][2:5] = [3, 3, 3]

        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))

        output_like = copy.deepcopy(self.canonical[0])
        output_like[1][2:6] = [3, 3, 3, 3]
        self.assertTrue(self.generator.self_check(output_like))

    def test_recombined_span_profile_is_rejected_but_remains_rule_executable_shape(self):
        changed = copy.deepcopy(self.canonical[0])
        # Replace the official right-edge span 6 with span 4.  The grid still
        # contains two lawful pair rows, but the linked 6x9 canonical profile
        # is no longer one of the observed official signatures.
        changed[4][2] = 0
        changed[4][4] = 4

        signature = self.generator.canonical_profile_signature(changed)
        self.assertIsNotNone(signature)
        self.assertNotIn(signature, self.generator._CANONICAL_SIGNATURES)
        self.assertTrue(self.generator.self_check(changed))

    def test_determinism_fresh_returns_and_global_rng_preservation(self):
        random.seed(24680)
        before = random.getstate()
        first = self.generator.generate(99, 7, difficulty="hard")
        middle = random.getstate()
        second = self.generator.generate(99, 7, difficulty="hard")
        after = random.getstate()

        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
