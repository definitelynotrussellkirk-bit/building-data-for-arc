"""Regression tests for the linked cross-projection profile repair."""

from __future__ import annotations

import importlib.util
import unittest

from reviewer_support import canonical_pairs as read_canonical_pairs, find_root


TASK_ID = "e937c5b85cdd"
ROOT = find_root(__file__)
# The supported task-test stage mirrors library sources beside the legacy
# runtime. Prefer that authoritative source, with the legacy layout as fallback.
GENERATOR_PATH = next(
    path for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ) if path.is_file()
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_e937c5b85cdd",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return read_canonical_pairs(TASK_ID, root=ROOT)


def chamber(size=11):
    return [
        [6 if r in (0, size - 1) or c in (0, size - 1) else 7
         for c in range(size)]
        for r in range(size)
    ]


def add_cross(grid, color, center, arms):
    r, c = center
    grid[r][c] = color
    for (dr, dc), length in zip(((-1, 0), (1, 0), (0, -1), (0, 1)), arms):
        for step in range(1, length + 1):
            grid[r + dr * step][c + dc * step] = color


class LinkedCrossProjectionProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_all_six_canonical_pairs_match_the_strict_signature(self):
        pairs = canonical_pairs()

        self.assertEqual(6, len(pairs))
        self.assertEqual(
            self.generator._CANONICAL_SIGNATURES,
            {
                self.generator.canonical_profile_signature(pair["input"])
                for pair in pairs
            },
        )

    def test_python_oracle_matches_all_canonical_outputs(self):
        for pair in canonical_pairs():
            self.assertEqual(
                pair["output"],
                self.generator._rule_output(pair["input"]),
            )

    def test_default_prior_reaches_strict_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            matches = 0
            for seed in range(600):
                grid = self.generator.generate(
                    seed,
                    seed * 17 + 1,
                    difficulty=band,
                )
                self.assertEqual(
                    [],
                    self.generator.self_check(grid, difficulty=band),
                )
                if (
                    self.generator.canonical_profile_signature(grid)
                    in self.generator._CANONICAL_SIGNATURES
                ):
                    matches += 1

            with self.subTest(band=band, matches=matches):
                self.assertGreaterEqual(matches, 150)

    def test_lawful_extended_palette_is_not_counted_as_canonical(self):
        grid = [row[:] for row in canonical_pairs()[0]["input"]]
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 2:
                    grid[r][c] = 1

        signature = self.generator.canonical_profile_signature(grid)

        self.assertEqual([], self.generator.self_check(grid))
        self.assertIsNotNone(signature)
        self.assertNotIn(signature, self.generator._CANONICAL_SIGNATURES)

    def test_unknown_override_keys_fail_loudly(self):
        for value in (123, None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.generator.generate(1, 1, typo_cross_count=value)

    def test_integer_axes_reject_coercible_non_integer_values(self):
        valid = {"grid_h": 11, "grid_w": 11,
                 "cross_count": 4, "max_arm_len": 2}
        for axis, value in valid.items():
            for invalid in (float(value), value + 0.9, str(value), True, False):
                with self.subTest(axis=axis, value=invalid):
                    with self.assertRaises(ValueError):
                        self.generator.generate(1, 1, **{axis: invalid})

    def test_malformed_container_inputs_return_diagnostics(self):
        for grid in (None, 0, 7, True, 3.5, {}, {"row": 1}, "777",
                     [None], [[7] * 11, None], ["7" * 11] * 11):
            with self.subTest(grid=grid):
                errors = self.generator.self_check(grid)
                self.assertIsInstance(errors, list)
                self.assertTrue(errors)

    def test_exact_integer_overrides_hold_in_every_band(self):
        corners = ((11, 11, 1, 2), (11, 11, 5, 3), (16, 11, 5, 3),
                   (11, 16, 5, 3), (16, 16, 5, 2))
        for band in ("easy", "medium", "hard"):
            for palette in self.generator.PALETTE_KINDS:
                for index, (h, w, count, arm) in enumerate(corners):
                    with self.subTest(band=band, palette=palette, corner=index):
                        grid = self.generator.generate(
                            1200 + index, 1, difficulty=band, grid_h=h,
                            grid_w=w, cross_count=count, max_arm_len=arm,
                            palette_kind=palette,
                        )
                        self.assertEqual([], self.generator.self_check(grid))
                        self.assertEqual((h, w), (len(grid), len(grid[0])))
                        self.assertEqual(
                            {"cross_count": count, "max_arm_len": arm},
                            self.generator.observe_overrides(grid),
                        )

    def test_each_direction_edits_only_the_facing_and_opposite_frame(self):
        for arms, facing, opposite in (
            ((2, 1, 1, 1), (0, 5), (10, 5)),
            ((1, 2, 1, 1), (10, 5), (0, 5)),
            ((1, 1, 2, 1), (5, 0), (5, 10)),
            ((1, 1, 1, 2), (5, 10), (5, 0)),
        ):
            with self.subTest(arms=arms):
                grid = chamber()
                add_cross(grid, 2, (5, 5), arms)
                expected = [row[:] for row in grid]
                expected[facing[0]][facing[1]] = 0
                expected[opposite[0]][opposite[1]] = 2
                self.assertEqual([], self.generator.self_check(grid))
                self.assertEqual(expected, self.generator._rule_output(grid))

    def test_arm_ties_extra_extended_arms_and_length_four_are_rejected(self):
        for arms in ((1, 1, 1, 1), (2, 2, 1, 1), (1, 1, 2, 3),
                     (1, 1, 1, 4)):
            with self.subTest(arms=arms):
                grid = chamber()
                add_cross(grid, 2, (5, 5), arms)
                self.assertTrue(self.generator.self_check(grid))

    def test_horizontal_and_vertical_projection_collisions_are_rejected(self):
        for first, second, arms in (
            ((5, 4), (5, 11), (1, 1, 1, 2)),
            ((4, 5), (11, 5), (1, 2, 1, 1)),
        ):
            with self.subTest(first=first, second=second):
                grid = chamber(16)
                add_cross(grid, 2, first, arms)
                add_cross(grid, 8, second, arms)
                self.assertTrue(any("collision" in error for error in
                                    self.generator.self_check(grid)))

    def test_duplicate_cross_colors_are_rejected(self):
        grid = chamber(16)
        add_cross(grid, 2, (4, 4), (1, 1, 1, 2))
        add_cross(grid, 2, (9, 9), (1, 1, 1, 2))
        self.assertTrue(any("distinct" in error for error in
                            self.generator.self_check(grid)))

    def test_different_colored_crosses_may_touch_without_overlapping(self):
        grid = chamber()
        add_cross(grid, 2, (4, 4), (1, 1, 1, 2))
        add_cross(grid, 8, (5, 7), (2, 1, 1, 1))
        self.assertEqual([], self.generator.self_check(grid))

    def test_all_declared_diagnostic_textures_remain_lawful(self):
        for texture in self.generator.DEGENERATE_TEXTURES:
            with self.subTest(texture=texture):
                grid = self.generator.generate(3, 9, texture=texture)
                self.assertEqual([], self.generator.self_check(grid))
                self.assertNotEqual(grid, self.generator._rule_output(grid))


if __name__ == "__main__":
    unittest.main()
