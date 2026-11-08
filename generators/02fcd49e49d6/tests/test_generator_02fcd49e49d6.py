from __future__ import annotations

import random
import unittest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "02fcd49e49d6"
ROOT = find_root(__file__)


def load_generator():
    module, _source, _sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module


def canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT)]


def independent_signature(grid):
    rows_and_gaps = []
    for row_index, row in enumerate(grid):
        nonzero = [column for column, value in enumerate(row) if value]
        if not nonzero:
            continue
        eights = [column for column, value in enumerate(row) if value == 8]
        if len(eights) != 2 or len(nonzero) != 2:
            return None
        c1, c2 = eights
        if (c1 + c2) % 2:
            return None
        rows_and_gaps.append((row_index, c2 - c1))
    return (len(grid), len(grid[0]), tuple(rows_and_gaps))


class MidpointMarkerGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_canonical_inputs_are_accepted_and_profiles_are_exact(self):
        inputs = canonical_inputs()
        expected = {independent_signature(grid) for grid in inputs}
        self.assertEqual(expected, set(self.generator._CANONICAL_SIGNATURES))
        for grid in inputs:
            self.assertEqual([], self.generator.self_check(grid))

    def test_four_sample_lesson_cycle_covers_every_semantic_branch(self):
        expected = {"none", "odd_pair", "triple_8s", "filled_mid"}
        for band in ("easy", "medium", "hard"):
            for seed in range(20):
                observed = set()
                for sample_index in range(seed * 4, seed * 4 + 4):
                    grid = self.generator.generate(seed, sample_index, difficulty=band)
                    self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                    observed.add(self.generator.observe_overrides(grid)["near_miss"])
                self.assertEqual(expected, observed)

    def test_linked_canonical_prior_is_stable_in_two_disjoint_censuses(self):
        expected = set(self.generator._CANONICAL_SIGNATURES)
        for label, seed_start in (("tuning", 0), ("stability", 10_000)):
            for band in ("easy", "medium", "hard"):
                counts = {signature: 0 for signature in expected}
                for offset in range(200):
                    seed = seed_start + offset
                    grid = self.generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                    )
                    signature = independent_signature(grid)
                    if signature in counts:
                        counts[signature] += 1
                with self.subTest(census=label, band=band, counts=counts):
                    self.assertGreaterEqual(sum(counts.values()), 25)
                    self.assertTrue(all(count > 0 for count in counts.values()))

    def test_exact_overrides_round_trip_and_incompatible_pair_rejects(self):
        cases = (
            {"grid_h": 4, "grid_w": 7, "n_rows": 1, "near_miss": "none"},
            {"grid_h": 10, "grid_w": 14, "n_rows": 5, "near_miss": "filled_mid"},
            {"grid_h": 7, "grid_w": 9, "n_rows": 3, "near_miss": "odd_pair"},
            {"grid_h": 8, "grid_w": 10, "n_rows": 4, "near_miss": "triple_8s"},
        )
        for band in ("easy", "medium", "hard"):
            for index, overrides in enumerate(cases):
                grid = self.generator.generate(index, 99 + index, difficulty=band, **overrides)
                self.assertEqual(overrides, self.generator.observe_overrides(grid))
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
        with self.assertRaisesRegex(ValueError, "requires grid_h"):
            self.generator.generate(
                1,
                1,
                difficulty="easy",
                grid_h=4,
                n_rows=5,
                near_miss="filled_mid",
            )

    def test_self_check_rejects_targeted_impostors(self):
        valid = self.generator.generate(
            7,
            7,
            difficulty="medium",
            grid_h=8,
            grid_w=10,
            n_rows=3,
            near_miss="odd_pair",
        )
        impostors = []

        blank = [[0 for _ in row] for row in valid]
        impostors.append(blank)

        answer_leak = [row[:] for row in valid]
        answer_leak[0][0] = 2
        impostors.append(answer_leak)

        stray_texture = [row[:] for row in valid]
        blank_row = next(index for index, row in enumerate(stray_texture) if not any(row))
        stray_texture[blank_row][0] = 4
        impostors.append(stray_texture)

        duplicate_near_miss = [row[:] for row in valid]
        blank_row = next(index for index, row in enumerate(duplicate_near_miss) if not any(row))
        duplicate_near_miss[blank_row][0] = 8
        duplicate_near_miss[blank_row][1] = 8
        impostors.append(duplicate_near_miss)

        four_eights = [row[:] for row in valid]
        firing_row = next(
            index
            for index, row in enumerate(four_eights)
            if self.generator._classify_row(row)[0] == "firing"
        )
        free = [index for index, value in enumerate(four_eights[firing_row]) if value == 0]
        four_eights[firing_row][free[0]] = 8
        four_eights[firing_row][free[1]] = 8
        impostors.append(four_eights)

        for index, grid in enumerate(impostors):
            with self.subTest(impostor=index):
                self.assertTrue(self.generator.self_check(grid))

    def test_negative_recombination_is_rejected(self):
        grid = [row[:] for row in canonical_inputs()[0]]
        # Add a feature absent from every remaining scene part: a non-midpoint
        # color-3 cell in an otherwise canonical firing row.
        grid[0][0] = 3
        self.assertTrue(self.generator.self_check(grid))

    def test_replay_freshness_and_global_rng_purity(self):
        before = random.getstate()
        first = self.generator.generate(123, 456, difficulty="hard")
        after = random.getstate()
        second = self.generator.generate(123, 456, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
