"""Focused regression tests for the 004ca3500787 generator repair."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from reviewer_support import canonical_pairs as read_canonical_pairs, find_root

ROOT = find_root(__file__)
GENERATOR_PATH = next(path for path in (
    ROOT / "generators" / "004ca3500787" / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / "004ca3500787" / "generator.py",
) if path.is_file())


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_004ca3500787_test", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return read_canonical_pairs("004ca3500787", root=ROOT, labeled_only=True)


class DihedralOddOneOutGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_rule_hash_and_shape_bank_are_pinned(self):
        self.assertEqual("18bdd6911037", self.generator.RULE_HASH)
        self.assertEqual(
            len(self.generator._SHAPES),
            len({
                self.generator._d4_canonical(cells)
                for cells in self.generator._SHAPES.values()
            }),
        )

    def test_all_canonical_pairs_match_python_mirror_and_profiles(self):
        signatures = set()
        for pair in canonical_pairs():
            self.assertEqual([], self.generator.self_check(pair["input"]))
            self.assertEqual(pair["output"], self.generator.rule_mirror(pair["input"]))
            self.assertEqual([], self.generator.strict_canonical_like(pair["input"]))
            signatures.add(self.generator.canonical_profile_signature(pair["input"]))
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)

    def test_four_profile_schedule_teaches_every_named_shortcut(self):
        for band in ("easy", "medium", "hard"):
            demos = []
            witness_hits = {name: 0 for name in self.generator.SEMANTIC_WITNESSES}
            for sample_index in range(4):
                grid = self.generator.generate(7, sample_index, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                demos.append({"input": grid, "output": self.generator.rule_mirror(grid)})
                for name, witness in self.generator.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += int(witness(grid))
            query_grid = self.generator.generate(7, 4, difficulty=band)
            query = {"input": query_grid, "output": self.generator.rule_mirror(query_grid)}
            with self.subTest(band=band, witness_hits=witness_hits):
                self.assertTrue(all(count > 0 for count in witness_hits.values()))
                self.assertEqual([], self.generator.lesson_identifiable(demos, query))
                for name, competitor in self.generator.LESSON_COMPETITORS.items():
                    self.assertTrue(
                        any(competitor(pair["input"]) != pair["output"] for pair in demos),
                        name,
                    )

    def test_single_axis_overrides_are_consumed_and_observable(self):
        cases = [
            {"grid_h": 9},
            {"grid_h": 18},
            {"grid_w": 12},
            {"grid_w": 22},
            {"num_components": 3},
            {"num_components": 5},
            {"common_shape": "O4"},
            {"outlier_shape": "Z5"},
            {"size_relation": "same"},
            {"size_relation": "different"},
        ]
        for index, overrides in enumerate(cases):
            grid = self.generator.generate(31, index, difficulty="medium", **overrides)
            observed = self.generator.observe_overrides(grid)
            with self.subTest(overrides=overrides, observed=observed):
                self.assertEqual([], self.generator.self_check(grid))
                for key, value in overrides.items():
                    self.assertEqual(value, observed[key])

    def test_explicit_compatible_and_incompatible_shape_tuples(self):
        legal = self.generator.generate(
            5,
            0,
            common_shape="L3",
            outlier_shape="T4",
            size_relation="different",
        )
        self.assertEqual(
            {
                "common_shape": "L3",
                "outlier_shape": "T4",
                "size_relation": "different",
            },
            {
                key: self.generator.observe_overrides(legal)[key]
                for key in ("common_shape", "outlier_shape", "size_relation")
            },
        )
        with self.assertRaises(ValueError):
            self.generator.generate(
                5,
                0,
                common_shape="L3",
                outlier_shape="L3",
            )
        with self.assertRaises(ValueError):
            self.generator.generate(
                5,
                0,
                common_shape="L3",
                outlier_shape="T4",
                size_relation="same",
            )
        with self.assertRaises(TypeError):
            self.generator.generate(5, 0, typo_axis=1)

    def test_mutation_fixtures_are_all_rejected(self):
        fixtures = self.generator.mutation_fixtures()
        self.assertGreaterEqual(len(fixtures), 5)
        for name, grid in fixtures:
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))

    def test_determinism_and_schedule_coverage(self):
        for band in ("easy", "medium", "hard"):
            seen = set()
            strict = 0
            for sample_index in range(40):
                first = self.generator.generate(101, sample_index, difficulty=band)
                second = self.generator.generate(101, sample_index, difficulty=band)
                self.assertEqual(first, second)
                seen.add(self.generator.schedule_profile(101, sample_index, band))
                strict += int(not self.generator.strict_canonical_like(first))
            self.assertEqual(set(self.generator.SCHEDULE_PROFILES), seen)
            self.assertGreaterEqual(strict, 20)


if __name__ == "__main__":
    unittest.main()
