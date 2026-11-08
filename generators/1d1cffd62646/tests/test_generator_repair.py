"""Focused input-contract regressions for the three-dot square-ring task."""
from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator("1d1cffd62646", root=ROOT)


def dots(grid):
    return [(r, c, value) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value != 0]


def grid_with(points, *, h=16, w=18):
    grid = [[0] * w for _ in range(h)]
    for r, c, value in points:
        grid[r][c] = value
    return grid


class GeneratorRepairTests(unittest.TestCase):
    def test_original_canonical_three_dot_inputs_are_admitted(self):
        pairs = canonical_pairs("1d1cffd62646", root=ROOT, variant=0)
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(len(dots(pair["input"])), 3)
                self.assertEqual(GENERATOR.self_check(pair["input"]), [])


    def test_real_overrides_define_three_symmetric_same_color_dots(self):
        for orientation, delta in [
            ("vertical", (4, 0)), ("horizontal", (0, 4)),
            ("diag_down", (4, 4)), ("diag_up", (4, -4)),
        ]:
            with self.subTest(orientation=orientation):
                kwargs = dict(grid_h=16, grid_w=18, step=4,
                              dot_color=9, orientation=orientation)
                grid = GENERATOR.generate(17, 2, **kwargs)
                self.assertEqual((len(grid), len(grid[0])), (16, 18))
                points = dots(grid)
                self.assertEqual(len(points), 3)
                self.assertEqual({point[2] for point in points}, {9})
                self.assertEqual((points[1][0] - points[0][0], points[1][1] - points[0][1]), delta)
                self.assertEqual((points[2][0] - points[1][0], points[2][1] - points[1][1]), delta)
                self.assertEqual(GENERATOR.self_check(grid), [])
                self.assertEqual(GENERATOR.generate(17, 2, **kwargs), grid)


    def test_explicit_dimensions_cover_full_declared_range_even_on_easy(self):
        for shape in [(10, 30), (30, 10), (23, 28)]:
            with self.subTest(shape=shape):
                grid = GENERATOR.generate(3, 0, difficulty="easy", grid_h=shape[0],
                                          grid_w=shape[1], step=2)
                self.assertEqual((len(grid), len(grid[0])), shape)
                self.assertEqual(GENERATOR.self_check(grid), [])


    def test_step_override_selects_a_feasible_direction(self):
        grid = GENERATOR.generate(19, 0, grid_h=10, grid_w=13, step=6)
        points = dots(grid)
        self.assertEqual(len(points), 3)
        self.assertEqual([point[1] for point in points], [0, 6, 12])
        self.assertEqual(len({point[0] for point in points}), 1)


    def test_impossible_spacing_is_rejected_instead_of_clamped(self):
        for orientation in ["vertical", "horizontal", "diag_down", "diag_up"]:
            with self.subTest(orientation=orientation), self.assertRaises(ValueError):
                GENERATOR.generate(0, 0, grid_h=10, grid_w=10, step=6,
                                   orientation=orientation)


    def test_numeric_override_types_are_exact_integers(self):
        for axis in ["grid_h", "grid_w", "step", "dot_color"]:
            nominal = 16 if axis in ("grid_h", "grid_w") else 3
            for value in [True, float(nominal), str(nominal)]:
                with self.subTest(axis=axis, value=value), self.assertRaises((TypeError, ValueError)):
                    GENERATOR.generate(0, 0, **{axis: value})


    def test_invalid_or_unsupported_controls_fail_visibly(self):
        for overrides in [
    {"grid_h": 9}, {"grid_w": 31}, {"step": 1}, {"step": 7},
    {"dot_color": 0}, {"dot_color": 10}, {"orientation": "diagonal"},
    {"texture": "no_dots"}, {"texture": "single_dot"},
    {"texture": "full_grid"}, {"palette_kind": "warm"},
    {"anchor_corner": True}, {"asymmetry_force": True},
    {"palette_size": 1}, {"position_bias": "rng"}, {"unknown": 1},
        ]:
            with self.subTest(overrides=overrides), self.assertRaises((TypeError, ValueError)):
                GENERATOR.generate(0, 0, **overrides)


    def test_self_check_rejects_malformed_and_out_of_domain_inputs(self):
        for index, grid in enumerate([None, [], [[]], "000", [[0], []],
    grid_with([(2, 4, True), (4, 4, True), (6, 4, True)]),
    grid_with([(2, 4, 2.0), (4, 4, 2.0), (6, 4, 2.0)]),
    grid_with([(2, 4, 10), (4, 4, 10), (6, 4, 10)]),
    grid_with([(2, 4, 2), (4, 4, 2)], h=9),
    grid_with([(2, 4, 2), (4, 4, 2)], h=31),
    grid_with([(2, 4, 2), (4, 4, 2)]),
    grid_with([(2, 4, 2), (4, 4, 2), (6, 4, 3)]),
    grid_with([(2, 4, 2), (4, 4, 2), (7, 4, 2)]),
    grid_with([(2, 4, 2), (4, 5, 2), (6, 4, 2)]),
    grid_with([(2, 4, 2), (3, 4, 2), (4, 4, 2)]),
        ]):
            with self.subTest(case=index):
                self.assertTrue(GENERATOR.self_check(grid))


    def test_metadata_cannot_bypass_the_input_contract(self):
        grid = grid_with([(2, 4, 2), (4, 4, 2)])
        self.assertTrue(GENERATOR.self_check(grid, meta={"texture": "no_dots"}))


    def test_default_draws_cover_both_diagonals_and_axis_aligned_dots(self):
        directions = set()
        for sample_index in range(32):
            grid = GENERATOR.generate(17, sample_index)
            self.assertEqual(GENERATOR.self_check(grid), [])
            points = dots(grid)
            self.assertEqual(len(points), 3)
            dr, dc = points[1][0] - points[0][0], points[1][1] - points[0][1]
            directions.add((0 if dr == 0 else 1, 0 if dc == 0 else (1 if dc > 0 else -1)))
        self.assertEqual(directions, {(1, 0), (0, 1), (1, 1), (1, -1)})


if __name__ == "__main__":
    unittest.main(verbosity=2)
