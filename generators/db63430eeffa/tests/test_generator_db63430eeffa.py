from __future__ import annotations

import unittest

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    "db63430eeffa", root=ROOT
)
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


    def test_unknown_override_names_reject_even_when_none(self):
        for value in (1, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "unknown override"):
                    generator.generate(
                        0,
                        0,
                        __override_contract_unknown_axis__=value,
                    )

    def test_sample_index_requires_exact_nonnegative_integer(self):
        for value in (True, False, 1.0, 1.75, "1", -1):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    (TypeError, ValueError),
                    "sample_index",
                ):
                    generator.generate(0, value)

    def test_integer_overrides_require_exact_integers(self):
        valid = {
            "grid_h": 11,
            "grid_w": 14,
            "row_gap": 2,
            "col_gap": 10,
        }
        for axis, good in valid.items():
            for bad in (True, False, float(good), good + 0.75, str(good)):
                with self.subTest(axis=axis, value=bad):
                    kwargs = dict(valid)
                    kwargs[axis] = bad
                    with self.assertRaisesRegex(
                        (TypeError, ValueError),
                        axis,
                    ):
                        generator.generate(0, 0, **kwargs)

    def test_categorical_overrides_require_strings_or_none(self):
        for axis in ("orientation", "texture"):
            for bad in (0, 0.0, 1.0, True, False):
                with self.subTest(axis=axis, value=bad):
                    with self.assertRaisesRegex((TypeError, ValueError), axis):
                        generator.generate(0, 0, **{axis: bad})


    def test_seed_requires_an_exact_integer(self):
        for value in (True, False, 1.0, 1.75, "1"):
            with self.subTest(value=value):
                with self.assertRaisesRegex((TypeError, ValueError), "seed"):
                    generator.generate(value, 0)

    def test_difficulty_requires_a_declared_string_or_none(self):
        for value in (True, False, 0, 1.0, "__invalid_difficulty__"):
            with self.subTest(value=value):
                with self.assertRaisesRegex((TypeError, ValueError), "difficulty"):
                    generator.generate(0, 0, difficulty=value)
        for value in (None, "easy", "medium", "hard"):
            with self.subTest(valid=value):
                generator.generate(0, 0, difficulty=value)

    def test_square_diagonal_is_explicitly_lawful_degenerate(self):
        self.assertIn(
            "square_diagonal",
            generator.LAWFUL_DEGENERATE_TEXTURES,
        )


if __name__ == "__main__":
    unittest.main()
