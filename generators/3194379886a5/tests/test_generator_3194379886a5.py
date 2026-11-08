"""Focused semantic regressions for generator 3194379886a5."""

from __future__ import annotations

import random
import unittest
from collections import Counter

from reviewer_support import canonical_pairs as load_canonical_pairs
from reviewer_support import find_root, load_selected_generator


TASK_ID = "3194379886a5"
ROOT = find_root(__file__)


def load_generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def canonical_pairs():
    return load_canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def projection_signature(cells):
    rows = tuple(sorted(Counter(row for row, _ in cells).values()))
    cols = tuple(sorted(Counter(col for _, col in cells).values()))
    return tuple(sorted((rows, cols)))


class PrototypeDihedralGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_all_canonical_pairs_are_exact_and_classified(self):
        pairs = canonical_pairs()
        self.assertEqual(3, len(pairs))
        self.assertEqual(
            {"public_1", "public_2", "public_3"},
            {
                self.generator.canonical_profile_signature(pair["input"])
                for pair in pairs
            },
        )
        for pair in pairs:
            with self.subTest(signature=pair["output"]):
                self.assertEqual([], self.generator.self_check(pair["input"]))
                self.assertEqual(
                    pair["output"],
                    self.generator.rule_mirror(pair["input"]),
                )

    def test_linked_defaults_reach_all_matching_branches_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            match_indexes = set()
            distinct_inputs = set()
            exact_public = 0
            for seed in range(300):
                grid = self.generator.generate(
                    seed,
                    seed * 31 + 7,
                    difficulty=band,
                    scene_family="linked",
                )
                analysis = self.generator._analyze(grid)
                self.assertEqual([], analysis["errors"])
                self.assertEqual("linked", analysis["facts"]["scene_family"])
                match_indexes.add(analysis["facts"]["match_index"])
                distinct_inputs.add(tuple(map(tuple, grid)))
                exact_public += analysis["facts"]["canonical_profile"] is not None
            with self.subTest(band=band):
                self.assertEqual({0, 1, 2}, match_indexes)
                self.assertGreaterEqual(len(distinct_inputs), 250)
                self.assertGreater(exact_public, 0)
                self.assertLess(exact_public, 60)

    def test_generalized_branch_varies_size_and_stays_outside_linked_bank(self):
        expected_sizes = {"easy": 4, "medium": 5, "hard": 6}
        for band, expected_size in expected_sizes.items():
            matches = set()
            for seed in range(120):
                grid = self.generator.generate(
                    10_000 + seed,
                    seed,
                    difficulty=band,
                    scene_family="generalized",
                )
                analysis = self.generator._analyze(grid)
                self.assertEqual([], analysis["errors"])
                self.assertEqual(
                    "generalized",
                    analysis["facts"]["scene_family"],
                )
                self.assertEqual(expected_size, analysis["facts"]["panel_size"])
                matches.add(analysis["facts"]["match_index"])
            with self.subTest(band=band):
                self.assertEqual({0, 1, 2}, matches)

    def test_generalized_scenes_force_true_d4_reasoning(self):
        for band in ("easy", "medium", "hard"):
            shortcut_failures = 0
            for seed in range(60):
                grid = self.generator.generate(
                    20_000 + seed,
                    seed * 13 + 5,
                    difficulty=band,
                    scene_family="generalized",
                )
                facts = self.generator._analyze(grid)["facts"]
                query_signature = projection_signature(facts["query_cells"])
                signature_matches = [
                    index
                    for index, cells in enumerate(facts["prototype_cells"])
                    if projection_signature(cells) == query_signature
                ]
                self.assertGreaterEqual(len(signature_matches), 2)
                shortcut_failures += signature_matches[0] != facts["match_index"]
            self.assertGreaterEqual(shortcut_failures, 30, band)

    def test_structural_checker_rejects_targeted_impostors(self):
        base = self.generator.generate(
            71,
            9,
            difficulty="medium",
            scene_family="linked",
        )
        mutations = []

        missing_separator = [row[:] for row in base]
        missing_separator[0][4] = 0
        mutations.append(missing_separator)

        mixed_panel = [row[:] for row in base]
        mixed_panel[0][0] = next(
            color
            for color in range(1, 10)
            if color not in (5, mixed_panel[0][0])
        )
        mutations.append(mixed_panel)

        same_query_color = [row[:] for row in base]
        prototype_color = next(
            value
            for row in same_query_color
            for value in row[:4]
            if value != 0
        )
        query_color = next(
            value
            for row in same_query_color
            for value in row[15:]
            if value != 0
        )
        for row in same_query_color:
            for col in range(15, 19):
                if row[col] == query_color:
                    row[col] = prototype_color
        mutations.append(same_query_color)

        ambiguous = [row[:] for row in base]
        for row in range(4):
            for col in range(4):
                ambiguous[row][5 + col] = ambiguous[row][col]
        mutations.append(ambiguous)

        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self.assertTrue(self.generator.self_check(mutation))

    def test_recombined_public_library_is_lawful_but_not_linked(self):
        grid = [row[:] for row in canonical_pairs()[0]["input"]]
        for row in range(4):
            first = grid[row][0:4]
            second = grid[row][5:9]
            grid[row][0:4] = second
            grid[row][5:9] = first

        analysis = self.generator._analyze(grid)

        self.assertEqual([], analysis["errors"])
        self.assertEqual("generalized", analysis["facts"]["scene_family"])
        self.assertTrue(
            self.generator.canonical_profile_signature(grid).startswith(
                "generalized:"
            )
        )

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        state = random.getstate()
        first = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

        first[0][0] = 9 if first[0][0] != 9 else 8
        third = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(second, third)

    def test_bad_calls_fail_loudly(self):
        with self.assertRaises(ValueError):
            self.generator.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            self.generator.generate(1, 2, unknown_axis=True)


if __name__ == "__main__":
    unittest.main()
