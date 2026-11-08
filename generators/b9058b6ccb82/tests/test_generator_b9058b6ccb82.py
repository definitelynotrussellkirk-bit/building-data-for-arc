"""Regression tests for the b9058b6ccb82 generator repair."""
from __future__ import annotations

import importlib.util
import unittest

from reviewer_support import canonical_pairs as read_canonical_pairs, find_root

TASK_ID = "b9058b6ccb82"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path
    for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    if path.is_file()
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_b9058b6ccb82_test", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return read_canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


class DihedralColoredOddOneOutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_rule_hash_is_pinned(self):
        self.assertEqual("7fc0dbf623b9", self.generator.RULE_HASH)

    def test_canonical_pairs_are_accepted_and_solved_exactly(self):
        for pair in canonical_pairs():
            with self.subTest(split=pair["split"], pair_index=pair["pair_index"]):
                self.assertEqual([], self.generator.self_check(pair["input"]))
                self.assertEqual(pair["output"], self.generator.rule_mirror(pair["input"]))
                self.assertEqual([], self.generator.strict_canonical_like(pair["input"]))

    def test_output_preserves_outlier_color_and_observed_pose(self):
        grid = [
            [1, 1, 0, 0, 2, 0, 0, 0],
            [1, 0, 0, 0, 2, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [3, 0, 0, 0, 4, 4, 4, 0],
            [3, 3, 0, 0, 0, 0, 0, 0],
        ]
        self.assertEqual([], self.generator.self_check(grid))
        self.assertEqual([[4, 4, 4]], self.generator.rule_mirror(grid))

    def test_three_profile_schedule_teaches_declared_shortcuts(self):
        for band in ("easy", "medium", "hard"):
            demos = []
            witness_hits = {name: 0 for name in self.generator.SEMANTIC_WITNESSES}
            for sample_index in range(self.generator.EXAMPLES_NEEDED):
                grid = self.generator.generate(17, sample_index, difficulty=band)
                answer = self.generator.rule_mirror(grid)
                self.assertIsNotNone(answer)
                demos.append({"input": grid, "output": answer})
                for name, witness in self.generator.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += int(witness(grid))
            query_grid = self.generator.generate(
                17, self.generator.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": self.generator.rule_mirror(query_grid)}
            with self.subTest(band=band, witness_hits=witness_hits):
                self.assertTrue(all(count > 0 for count in witness_hits.values()))
                self.assertEqual([], self.generator.lesson_identifiable(demos, query))
                for name, competitor in self.generator.LESSON_COMPETITORS.items():
                    self.assertTrue(
                        any(competitor(pair["input"]) != pair["output"] for pair in demos),
                        name,
                    )

    def test_every_cyclic_start_and_query_rotation_is_identifiable(self):
        for band in ("easy", "medium", "hard"):
            for seed in (7, 19):
                for start in range(len(self.generator.SCHEDULE_PROFILES)):
                    pairs = []
                    for offset in range(self.generator.EXAMPLES_NEEDED + 1):
                        grid = self.generator.generate(
                            seed, start + offset, difficulty=band
                        )
                        pairs.append(
                            {"input": grid, "output": self.generator.rule_mirror(grid)}
                        )
                    for query_index, query in enumerate(pairs):
                        demos = [
                            pair for index, pair in enumerate(pairs)
                            if index != query_index
                        ]
                        with self.subTest(
                            band=band, seed=seed, start=start, query_index=query_index
                        ):
                            self.assertEqual(
                                [], self.generator.lesson_identifiable(demos, query)
                            )

    def test_exact_axis_overrides_work_in_every_band_and_are_observable(self):
        cases = (
            {"grid_h": 9, "grid_w": 10, "n_siblings": 2},
            {"grid_h": 9, "grid_w": 10, "n_siblings": 3},
            {"grid_h": 18, "grid_w": 20, "n_siblings": 2},
            {"grid_h": 18, "grid_w": 20, "n_siblings": 3},
        )
        for band in ("easy", "medium", "hard"):
            for index, overrides in enumerate(cases):
                grid = self.generator.generate(31, index, difficulty=band, **overrides)
                observed = self.generator.observe_overrides(grid)
                with self.subTest(band=band, overrides=overrides, observed=observed):
                    self.assertEqual([], self.generator.self_check(grid))
                    for key, value in overrides.items():
                        self.assertEqual(value, observed[key])

    def test_invalid_public_inputs_are_rejected_strictly(self):
        invalid_sample_indices = (True, False, 1.0, "1", -1)
        invalid_sibling_counts = (True, False, 1.0, "1", -1)
        for value in invalid_sample_indices:
            with self.subTest(sample_index=value):
                with self.assertRaises((TypeError, ValueError)):
                    self.generator.generate(1, value)
        for value in invalid_sibling_counts:
            with self.subTest(n_siblings=value):
                with self.assertRaises((TypeError, ValueError)):
                    self.generator.generate(1, 0, n_siblings=value)
        with self.assertRaises(TypeError):
            self.generator.generate(1, 0, typo_axis=3)
        with self.assertRaises(ValueError):
            self.generator.generate(1, 0, difficulty="extreme")

    def test_every_band_hits_both_canonical_profiles(self):
        expected = {(9, 10, 5), (10, 11, 5)}
        for band in ("easy", "medium", "hard"):
            seen = set()
            for sample_index in range(20):
                grid = self.generator.generate(0, sample_index, difficulty=band)
                palette_size = len({value for row in grid for value in row})
                seen.add((len(grid), len(grid[0]), palette_size))
            with self.subTest(band=band, seen=seen):
                self.assertTrue(expected <= seen)

    def test_schedule_restores_shape_and_size_diversity(self):
        common_classes = set()
        outlier_classes = set()
        size_relations = set()
        object_sizes = set()
        for sample_index in range(36):
            grid = self.generator.generate(73, sample_index, difficulty="medium")
            analysis = self.generator._analysis(grid)
            self.assertEqual([], analysis["errors"])
            common_classes.add(analysis["common"]["canonical"])
            outlier_classes.add(analysis["outlier"]["canonical"])
            common_size = analysis["common"]["size"]
            outlier_size = analysis["outlier"]["size"]
            size_relations.add("same" if common_size == outlier_size else "different")
            object_sizes.update(record["size"] for record in analysis["components"])
        self.assertGreaterEqual(len(common_classes), 4)
        self.assertGreaterEqual(len(outlier_classes), 6)
        self.assertEqual({"same", "different"}, size_relations)
        self.assertTrue({3, 4, 5} <= object_sizes)

    def test_mutation_fixtures_are_rejected(self):
        fixtures = self.generator.mutation_fixtures()
        self.assertGreaterEqual(len(fixtures), 6)
        for name, grid in fixtures:
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))

    def test_deterministic_and_lawful_over_a_seed_sweep(self):
        for band in ("easy", "medium", "hard"):
            for sample_index in range(30):
                first = self.generator.generate(101, sample_index, difficulty=band)
                second = self.generator.generate(101, sample_index, difficulty=band)
                with self.subTest(band=band, sample_index=sample_index):
                    self.assertEqual(first, second)
                    self.assertEqual([], self.generator.self_check(first))
                    self.assertIsNotNone(self.generator.rule_mirror(first))


if __name__ == "__main__":
    unittest.main()
