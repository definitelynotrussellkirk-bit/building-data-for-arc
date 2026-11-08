"""Focused regressions for the c0aac14eef4d semantic generator repair."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from scripts.canonical_profile_gate import canonical_pairs


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "c0aac14eef4d" / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_c0aac14eef4d", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TriangularFillGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.canonical = canonical_pairs("c0aac14eef4d")

    def test_public_signatures_are_derived_from_all_train_and_test_inputs(self):
        signatures = {
            self.generator.canonical_profile_signature(pair["input"])
            for pair in self.canonical
        }
        self.assertEqual(self.generator._PUBLIC_SIGNATURES, signatures)
        for pair in self.canonical:
            self.assertEqual([], self.generator.self_check(pair["input"]))
            self.assertEqual([], self.generator.strict_canonical_like(pair["input"]))
            self.assertEqual(pair["output"], self.generator.rule_mirror(pair["input"]))

    def test_every_declared_profile_and_color_override_is_exactly_observable(self):
        for band in ("easy", "medium", "hard"):
            for index, profile in enumerate(self.generator.SCENE_PROFILES):
                color = 1 + index % 9
                grid = self.generator.generate(
                    991,
                    index,
                    difficulty=band,
                    scene_profile=profile,
                    color=color,
                )
                self.assertEqual([], self.generator.self_check(grid))
                self.assertEqual(
                    {"scene_profile": profile, "color": color},
                    self.generator.observe_overrides(grid),
                )

    def test_default_and_stability_censuses_keep_canonical_support_in_each_band(self):
        for seed_start in (0, 10000):
            for band in ("easy", "medium", "hard"):
                strict = 0
                seen_profiles = set()
                for offset in range(200):
                    seed = seed_start + offset
                    grid = self.generator.generate(seed, offset * 17 + 3, difficulty=band)
                    self.assertEqual([], self.generator.self_check(grid))
                    seen_profiles.add(self.generator.observe_overrides(grid)["scene_profile"])
                    strict += not self.generator.strict_canonical_like(grid)
                with self.subTest(seed_start=seed_start, band=band):
                    self.assertGreaterEqual(strict, 10)
                    self.assertTrue(set(self.generator.PUBLIC_PROFILES) & seen_profiles)
                    self.assertTrue(set(self.generator.GENERAL_PROFILES) & seen_profiles)

    def test_self_check_rejects_nearest_malformed_mutations(self):
        valid = self.generator.generate(7, 11, scene_profile="public_w8_n1", color=2)
        cases = [
            [],
            [valid[0], valid[0]],
            [valid[0] + [0]],
            [[0] * 8],
            [[2, 3, 0, 0, 0, 0, 0, 0]],
            [[2, True, 0, 0, 0, 0, 0, 0]],
            [[2, 10, 0, 0, 0, 0, 0, 0]],
        ]
        for grid in cases:
            with self.subTest(grid=grid):
                self.assertTrue(self.generator.self_check(grid))

    def test_negative_recombination_is_valid_but_not_public_like(self):
        canonical = self.canonical[0]["input"]
        color = next(value for value in canonical[0] if value)
        count = sum(value != 0 for value in canonical[0])
        width = len(canonical[0])
        recombined = [[0] * width]
        for column in range(width - count, width):
            recombined[0][column] = color
        self.assertEqual([], self.generator.self_check(recombined))
        self.assertTrue(self.generator.strict_canonical_like(recombined))
        self.assertEqual("right_block", self.generator.observe_overrides(recombined)["scene_profile"])

    def test_generated_non_left_witness_refutes_every_canonical_layout_shortcut(self):
        grid = self.generator.generate(
            42,
            5,
            scene_profile="scattered",
            color=6,
            difficulty="medium",
        )
        authoritative = self.generator.rule_mirror(grid)
        self.assertTrue(self.generator.SEMANTIC_WITNESSES["non_left_layout"](grid))
        for name in self.generator.WITNESS_RIVALS["non_left_layout"]:
            with self.subTest(rival=name):
                self.assertNotEqual(authoritative, self.generator.SEMANTIC_RIVALS[name](grid))

    def test_determinism_and_fresh_return_objects(self):
        first = self.generator.generate(123, 456, difficulty="hard")
        second = self.generator.generate(123, 456, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertEqual(second, self.generator.generate(123, 456, difficulty="hard"))


if __name__ == "__main__":
    unittest.main()
