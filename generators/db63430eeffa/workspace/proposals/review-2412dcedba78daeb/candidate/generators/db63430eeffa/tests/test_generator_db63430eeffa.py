from __future__ import annotations

import unittest

from puzzle_generators.per_puzzle.db63430eeffa import generator
from reviewer_support import canonical_pairs as load_canonical_pairs, find_root


ROOT = find_root(__file__)
OFFICIAL_PROFILES = {
    (12, 14, 7, 9, "right_to_left"),
    (13, 13, 9, 6, "left_to_right"),
    (11, 14, 2, 10, "right_to_left"),
    (13, 14, 11, 7, "left_to_right"),
}


def canonical_pairs():
    for pair in load_canonical_pairs(
        generator.TASK_ID,
        root=ROOT,
        labeled_only=True,
    ):
        yield pair["input"], pair["output"]


def endpoint_grid(first, second, *, height=9, width=9):
    grid = [[0] * width for _ in range(height)]
    grid[first[0]][first[1]] = 8
    grid[second[0]][second[1]] = 8
    return grid


class Db63430eeffaGeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_match_mirror_and_linked_profiles(self):
        pairs = list(canonical_pairs())
        self.assertEqual(len(pairs), 8)
        profiles = set()
        for grid, expected in pairs:
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            profiles.add(generator.profile_signature(grid))
        self.assertEqual(profiles, OFFICIAL_PROFILES)

    def test_linked_prior_is_stable_in_every_band(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                with self.subTest(seed_start=seed_start, band=band):
                    exact = 0
                    witnessed = set()
                    for offset in range(400):
                        seed = seed_start + offset
                        grid = generator.generate(
                            seed,
                            seed,
                            difficulty=band,
                        )
                        self.assertEqual(
                            generator.self_check(grid, difficulty=band),
                            [],
                        )
                        signature = generator.profile_signature(grid)
                        if signature in OFFICIAL_PROFILES:
                            exact += 1
                            witnessed.add(signature)
                    self.assertEqual(witnessed, OFFICIAL_PROFILES)
                    self.assertGreaterEqual(exact, 60)
                    self.assertLessEqual(exact, 150)

    def test_adjacent_or_axis_aligned_endpoints_reject(self):
        malformed = {
            "row_gap_0": endpoint_grid((2, 2), (2, 5)),
            "row_gap_1": endpoint_grid((2, 2), (3, 5)),
            "col_gap_0": endpoint_grid((2, 2), (5, 2)),
            "col_gap_1": endpoint_grid((2, 2), (5, 3)),
        }
        for name, grid in malformed.items():
            with self.subTest(name=name):
                self.assertTrue(generator.self_check(grid))
        self.assertEqual(
            generator.self_check(endpoint_grid((2, 2), (4, 4))),
            [],
        )

    def test_explicit_none_is_identical_and_unknown_modes_reject(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                omitted = generator.generate(seed, seed, difficulty=band)
                explicit = generator.generate(
                    seed,
                    seed,
                    difficulty=band,
                    texture="none",
                )
                self.assertEqual(omitted, explicit)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(0, 0, texture="bogus")
        with self.assertRaisesRegex(ValueError, "unknown orientation"):
            generator.generate(0, 0, orientation="bogus")

    def test_generate_rejects_malformed_scalar_requests(self):
        for bad_seed in (True, False, 1.0, 1.75, "1", None):
            with self.subTest(field="seed", value=bad_seed):
                with self.assertRaisesRegex((TypeError, ValueError), "seed"):
                    generator.generate(bad_seed, 0)

        for bad_index in (True, False, 1.0, 1.75, "1", -1, None):
            with self.subTest(field="sample_index", value=bad_index):
                with self.assertRaisesRegex(
                    (TypeError, ValueError),
                    "sample_index",
                ):
                    generator.generate(0, bad_index)

        for bad_difficulty in (True, False, 0, 1.0, "bogus"):
            with self.subTest(field="difficulty", value=bad_difficulty):
                with self.assertRaisesRegex(
                    (TypeError, ValueError),
                    "difficulty",
                ):
                    generator.generate(0, 0, difficulty=bad_difficulty)

    def test_generate_rejects_unknown_and_non_literal_overrides(self):
        for value in (1, None):
            with self.subTest(field="unknown_axis", value=value):
                with self.assertRaisesRegex(ValueError, "unknown override"):
                    generator.generate(0, 0, unknown_axis=value)

        for axis in ("grid_h", "grid_w", "row_gap", "col_gap"):
            for value in (True, False, 7.0, "7"):
                with self.subTest(field=axis, value=value):
                    with self.assertRaisesRegex(TypeError, axis):
                        generator.generate(0, 0, **{axis: value})

    def test_square_diagonal_is_explicitly_lawful_degenerate(self):
        self.assertEqual(
            generator.LAWFUL_DEGENERATE_TEXTURES,
            generator.DEGENERATE_TEXTURES,
        )
        self.assertIn("square_diagonal", generator.LAWFUL_DEGENERATE_TEXTURES)

    def test_square_diagonal_control_is_lawful_and_mirror_is_pure(self):
        grid = generator.generate(
            23,
            23,
            difficulty="medium",
            texture="square_diagonal",
        )
        before = [row[:] for row in grid]
        output = generator.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual(generator.self_check(grid), [])
        self.assertEqual(
            generator.observe_overrides(grid)["row_gap"],
            generator.observe_overrides(grid)["col_gap"],
        )
        self.assertEqual(
            sum(value == 8 for row in output for value in row),
            2,
        )
        self.assertGreater(
            sum(value == 3 for row in output for value in row),
            0,
        )


if __name__ == "__main__":
    unittest.main()
