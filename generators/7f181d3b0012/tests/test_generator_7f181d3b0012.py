"""Regression tests for the binary mirror-family census."""

from __future__ import annotations

import unittest
from reviewer_support import canonical_pairs as read_canonical_pairs
from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)


def load_generator():
    return load_selected_generator("7f181d3b0012", root=ROOT)[0]


def canonical_pairs() -> list[dict]:
    return read_canonical_pairs("7f181d3b0012", root=ROOT, variant=0)


def is_strict_canonical_profile(generator, grid) -> bool:
    return (
        len(grid) == 3
        and len(grid[0]) == 3
        and {value for row in grid for value in row} == {0, 1}
        and sum(value == 1 for row in grid for value in row) in {2, 4, 5}
        and not generator._is_ud_sym(grid)
        and not generator._is_lr_sym(grid)
    )


class BinaryMirrorFamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_all_official_one_counts_define_the_strict_set(self):
        pairs = canonical_pairs()

        self.assertEqual(4, len(pairs))
        self.assertEqual(
            {2, 4, 5},
            {
                sum(value == 1 for row in pair["input"] for value in row)
                for pair in pairs
            },
        )
        self.assertTrue(
            all(
                is_strict_canonical_profile(self.generator, pair["input"])
                for pair in pairs
            )
        )

    def test_python_mirror_matches_every_canonical_output(self):
        for pair in canonical_pairs():
            grid = pair["input"]
            self.assertEqual([*grid, *reversed(grid)], pair["output"])

    def test_strict_profile_is_reached_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            matches = 0
            for seed in range(600):
                grid = self.generator.generate(
                    seed,
                    seed,
                    difficulty=band,
                )
                self.assertEqual([], self.generator.self_check(grid))
                matches += is_strict_canonical_profile(
                    self.generator,
                    grid,
                )

            with self.subTest(band=band, matches=matches):
                self.assertGreaterEqual(matches, 150)

    def test_unknown_override_is_rejected_before_drawing(self):
        for value in (123, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "unknown.*override"):
                    self.generator.generate(23, 9, __override_contract_unknown_axis__=value)

    def test_canonical_family_only_uses_demonstrated_one_counts(self):
        # Use keyed generator streams, without coupling this regression to
        # how often the default mixture selects its canonical branch.
        from puzzle_generators.base import stable_rng
        for seed in range(80):
            grid = self.generator._canonical_family(stable_rng(seed, "family-regression"))
            with self.subTest(seed=seed, grid=grid):
                self.assertTrue(is_strict_canonical_profile(self.generator, grid))

    def test_ambiguous_degenerate_lesson_is_rejected_in_automatic_mode(self):
        from arcpuzzles.worker import lesson_check
        symmetric = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
        asymmetric = [[0, 0, 0], [1, 0, 1], [1, 1, 0]]
        pair = lambda grid: {"input": grid, "output": [*grid, *reversed(grid)]}
        episode = {"train": [pair(symmetric)], "test": [pair(asymmetric)]}
        fixed = {"demonstration_policy": {"automatic": False, "declared_minimum": None}}
        verdict = lesson_check(self.generator, episode, fixed)
        self.assertEqual("diagnostic_unsupported", verdict["status"])
        self.assertEqual("ambiguous", verdict["rivals"]["LESSON_COMPETITORS:duplicate_vertical"])
        self.assertEqual("ambiguous", verdict["rivals"]["LESSON_COMPETITORS:rotate180_bottom"])
        automatic = {"demonstration_policy": {"automatic": True, "declared_minimum": None}}
        with self.assertRaisesRegex(ValueError, "Automatic lesson unsupported"):
            lesson_check(self.generator, episode, automatic)

    def test_asymmetric_demo_refutes_declared_rivals_without_mutation(self):
        from copy import deepcopy
        from arcpuzzles.worker import lesson_check
        grid = [[0, 0, 0], [1, 0, 1], [1, 1, 0]]
        pair = {"input": grid, "output": [*grid, *reversed(grid)]}
        episode = {"train": [pair], "test": [pair]}
        original = deepcopy(episode)
        policy = {"demonstration_policy": {"automatic": True, "declared_minimum": None}}
        verdict = lesson_check(self.generator, episode, policy)
        self.assertEqual("passed_declared_rivals", verdict["status"])
        self.assertEqual({"refuted"}, set(verdict["rivals"].values()))
        self.assertEqual(original, episode)

    def test_lawful_three_cell_pattern_is_not_strict(self):
        grid = [
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]

        self.assertEqual([], self.generator.self_check(grid))
        self.assertFalse(
            is_strict_canonical_profile(self.generator, grid),
        )


if __name__ == "__main__":
    unittest.main()
