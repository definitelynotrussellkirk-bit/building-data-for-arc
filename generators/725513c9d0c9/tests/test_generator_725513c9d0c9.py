"""Focused regression tests for the key-adjacent-component repair."""
from __future__ import annotations

import importlib
import random
import unittest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "725513c9d0c9"


def load_generator():
    return importlib.import_module(
        "puzzle_generators.per_puzzle.725513c9d0c9.generator"
    )


class KeyAdjacentComponentGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.canonical = canonical_pairs(TASK_ID)

    def test_every_canonical_input_is_accepted_and_signatures_are_pinned(self):
        signatures = set()
        for index, pair in enumerate(self.canonical):
            with self.subTest(index=index):
                self.assertEqual([], self.generator.self_check(pair["input"]))
                self.assertEqual(
                    pair["output"], self.generator.rule_mirror(pair["input"])
                )
                signatures.add(
                    self.generator.canonical_profile_signature(pair["input"])
                )
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)

    def test_diagonal_distractor_is_lawful_but_not_selected(self):
        # Official train[1] is the decisive counterexample: a distractor is
        # diagonal to the marker while only the target is cardinally adjacent.
        pair = self.canonical[1]
        grid = pair["input"]
        obs = self.generator.semantic_observables(grid)
        self.assertTrue(obs["diagonal_decoy"])
        self.assertNotEqual(
            pair["output"], self.generator._rival_diagonal_preferred(grid)
        )

    def test_all_declared_overrides_are_exact_and_observable(self):
        for axis, spec in self.generator.AXES.items():
            values = str(spec["valid"]).split("|")
            for value in (values[0], values[-1]):
                with self.subTest(axis=axis, value=value):
                    grid = self.generator.generate(
                        9001, 17, difficulty="hard", **{axis: value}
                    )
                    self.assertEqual([], self.generator.self_check(grid))
                    self.assertEqual(
                        value, self.generator.observe_overrides(grid)[axis]
                    )
        with self.assertRaisesRegex(ValueError, "unknown override axis"):
            self.generator.generate(0, 0, misspelled_axis="x")

    def test_bbox_intruders_are_excluded_from_the_answer(self):
        grid = self.generator.generate(30, 30, difficulty="easy")
        obs = self.generator.semantic_observables(grid)
        self.assertTrue(obs["bbox_intruder"])
        answer = self.generator.rule_mirror(grid)
        self.assertNotIn(8, {value for row in answer for value in row})
        self.assertNotEqual(
            answer, self.generator._rival_raw_bbox_crop(grid)
        )

    def test_negative_mutations_are_rejected(self):
        for name in ("no_key", "key_isolated", "key_adj_multiple", "solid_target"):
            with self.subTest(name=name):
                self.assertTrue(
                    self.generator.self_check(
                        self.generator._draw_from_degenerate(name)
                    )
                )

    def test_every_four_example_window_identifies_the_rule(self):
        for band in ("easy", "medium", "hard"):
            for start in range(12):
                pairs = []
                for sample_index in range(start, start + 5):
                    grid = self.generator.generate(
                        7000 + start, sample_index, difficulty=band
                    )
                    pairs.append(
                        {"input": grid, "output": self.generator.rule_mirror(grid)}
                    )
                with self.subTest(band=band, start=start):
                    self.assertEqual(
                        [], self.generator.lesson_identifiable(pairs[:4], pairs[4])
                    )

    def test_profiles_and_canonical_support_recur_in_every_band(self):
        pooled_counts = {name: 0 for name in self.generator.PROFILE_NAMES}
        for band in ("easy", "medium", "hard"):
            profile_counts = {name: 0 for name in self.generator.PROFILE_NAMES}
            canonical_count = 0
            for seed in range(280):
                grid = self.generator.generate(seed, seed, difficulty=band)
                obs = self.generator.observe_overrides(grid)
                profile_counts[obs["scene_profile"]] += 1
                pooled_counts[obs["scene_profile"]] += 1
                canonical_count += not self.generator.strict_canonical_like(grid)
            with self.subTest(band=band, counts=profile_counts):
                self.assertTrue(
                    all(
                        profile_counts[name] > 0
                        for name in self.generator.CANONICAL_PROFILE_NAMES
                    )
                )
                self.assertGreaterEqual(canonical_count, 120)
        self.assertTrue(all(count > 0 for count in pooled_counts.values()))

    def test_canvas_dimensions_do_not_label_one_target_shape(self):
        for band in ("easy", "medium", "hard"):
            shapes_by_dims = {}
            for index, profile in enumerate(self.generator.PROFILE_NAMES):
                grid = self.generator.generate(8200 + index, 3, difficulty=band, scene_profile=profile)
                obs = self.generator.semantic_observables(grid)
                self.assertEqual(profile, obs["scene_profile"])
                dims = (len(grid), len(grid[0]))
                shapes_by_dims.setdefault(dims, set()).add(obs["target_shape"])
            with self.subTest(band=band, shapes_by_dims=shapes_by_dims):
                self.assertTrue(
                    any(len(shapes) > 1 for shapes in shapes_by_dims.values()),
                    "at least one canvas size must host multiple target morphologies",
                )

    def test_dimension_shape_shortcut_is_part_of_the_semantic_contract(self):
        rival = "dimension_shape_lookup"
        witness = "target_not_dimension_shape_selected"
        self.assertIn(rival, self.generator.SEMANTIC_RIVALS)
        self.assertIn(witness, self.generator.SEMANTIC_WITNESSES)
        self.assertIn(rival, self.generator.WITNESS_RIVALS[witness])

    def test_palette_rank_shortcut_is_part_of_the_semantic_contract(self):
        rival = "palette_rank_selector"
        witness = "target_not_palette_rank_selected"
        self.assertIn(rival, self.generator.SEMANTIC_RIVALS)
        self.assertIn(witness, self.generator.SEMANTIC_WITNESSES)
        self.assertIn(rival, self.generator.WITNESS_RIVALS[witness])

    def test_every_four_example_window_breaks_palette_rank_selection(self):
        def palette_rank_shortcut_index(grid):
            analysis = self.generator._analyze(grid)
            components = analysis["components"]
            return min(
                range(len(components)),
                key=lambda index: (
                    min(grid[r][c] for r, c in components[index]),
                    -len({grid[r][c] for r, c in components[index]}),
                    min(components[index]),
                ),
            )

        for band in ("easy", "medium", "hard"):
            for start in range(12):
                disagreements = 0
                for sample_index in range(start, start + 4):
                    grid = self.generator.generate(8100 + start, sample_index, difficulty=band)
                    analysis = self.generator._analyze(grid)
                    disagreements += (
                        palette_rank_shortcut_index(grid) != analysis["target_index"]
                    )
                with self.subTest(band=band, start=start):
                    self.assertGreater(
                        disagreements,
                        0,
                        "every lesson window must refute selecting the component "
                        "with the smallest color, breaking ties by color count",
                    )

    def test_deterministic_fresh_returns_and_global_rng_purity(self):
        random.seed(123456)
        state = random.getstate()
        first = self.generator.generate(44, 8, difficulty="medium")
        self.assertEqual(state, random.getstate())
        second = self.generator.generate(44, 8, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        second[0][0] = 9 if second[0][0] != 9 else 1
        third = self.generator.generate(44, 8, difficulty="medium")
        self.assertEqual(first, third)


if __name__ == "__main__":
    unittest.main()
