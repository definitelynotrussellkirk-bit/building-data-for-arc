"""Behavioral regressions for marker-bbox cropping.

Run from the repository with:
    PYTHONPATH=shared/runtime python -m unittest discover \
        -s generators/9c3781759581/tests -v

Pytest also collects these tests.  Canonical labels are authoring data; this
module is not a blind-solve aid.  The small Python crops below are independent
rival probes, not replacements for the unchanged Racket labeling runtime.
"""
from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9c3781759581"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
DIFFICULTIES = (None, "easy", "medium", "hard")


def positions(grid, predicate):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
            if predicate(v)]


def bounds(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def crop(grid, cells):
    top, left, bottom, right = bounds(cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def marker_cells(grid):
    return positions(grid, lambda value: value == 9)


def marker_crop(grid):
    return crop(grid, marker_cells(grid))


def nonzero_crop(grid):
    return crop(grid, positions(grid, lambda value: value != 0))


def first_last_marker_crop(grid):
    markers = marker_cells(grid)
    return crop(grid, [markers[0], markers[-1]])


class CanonicalDomainTests(unittest.TestCase):
    def test_all_canonical_inputs_are_accepted(self):
        self.assertTrue(PAIRS, "canonical coverage must not silently disappear")
        for pair in PAIRS:
            with self.subTest(variant=pair["variant"], split=pair["split"],
                              pair_index=pair["pair_index"]):
                self.assertEqual(GEN.self_check(pair["input"]), [])

    def test_independent_bbox_probe_matches_every_canonical_label(self):
        for pair in PAIRS:
            with self.subTest(variant=pair["variant"], split=pair["split"],
                              pair_index=pair["pair_index"]):
                self.assertEqual(marker_crop(pair["input"]), pair["output"])

    def test_crop_all_nonzero_really_is_a_canonical_fitting_rival(self):
        for pair in PAIRS:
            self.assertEqual(nonzero_crop(pair["input"]), pair["output"])
            self.assertEqual(first_last_marker_crop(pair["input"]), pair["output"])

    def test_reference_lawful_sparse_arrangements_are_accepted(self):
        # Reverse diagonal; the 5 is outside the marker box and must be dropped.
        reverse_diagonal = [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 9, 0],
            [5, 0, 2, 0, 0, 0],
            [0, 9, 0, 3, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        # First/last in row order only see column 3, missing the two side 9s.
        side_extrema = [
            [0, 0, 0, 0, 0, 0, 8],
            [0, 0, 0, 9, 0, 0, 0],
            [0, 9, 4, 0, 0, 9, 0],
            [0, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
        cases = {
            "reverse_diagonal": reverse_diagonal,
            "side_extrema": side_extrema,
            "singleton": [[0, 2, 0], [0, 9, 0], [0, 0, 0]],
            "one_row": [[0, 9, 4, 9, 0]],
            "one_column": [[0], [9], [4], [9], [0]],
            "only_marker": [[9]],
        }
        for name, grid in cases.items():
            with self.subTest(case=name):
                self.assertEqual(GEN.self_check(grid), [])
        self.assertNotEqual(nonzero_crop(reverse_diagonal), marker_crop(reverse_diagonal))
        self.assertNotEqual(first_last_marker_crop(side_extrema), marker_crop(side_extrema))

    def test_malformed_self_check_returns_reasons_without_raising(self):
        cases = {
            "none": None,
            "scalar": 9,
            "empty": [],
            "empty_row": [[]],
            "ragged": [[9, 0], [2]],
            "non_row": [[9, 0], 2],
            "bool_cell": [[9, False], [9, 2]],
            "float_cell": [[9, 1.0], [9, 2]],
            "string_cell": [[9, "1"], [9, 2]],
            "negative_cell": [[9, -1], [9, 2]],
            "large_cell": [[9, 10], [9, 2]],
            "no_marker": [[0, 1], [2, 0]],
            "too_tall": [[9] for _ in range(31)],
            "too_wide": [[9] * 31],
        }
        for name, grid in cases.items():
            with self.subTest(case=name):
                reasons = GEN.self_check(grid)
                self.assertIsInstance(reasons, list)
                self.assertTrue(reasons, "malformed or markerless input needs a reason")
                self.assertTrue(all(isinstance(reason, str) and reason for reason in reasons))


class SampledTeachingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Aggregate requirements belong to unforced samples.  Exact full-canvas
        # boxes are intentionally tested separately and need no outside cells.
        cls.samples = {
            difficulty: [GEN.generate(20261019, index, difficulty=difficulty)
                         for index in range(64)]
            for difficulty in DIFFICULTIES
        }

    def test_samples_are_valid_and_reproducible(self):
        for difficulty, samples in self.samples.items():
            for index, grid in enumerate(samples):
                with self.subTest(difficulty=difficulty, sample_index=index):
                    self.assertEqual(GEN.self_check(grid), [])
                    self.assertEqual(grid, GEN.generate(20261019, index,
                                                       difficulty=difficulty))
                    self.assertTrue(marker_cells(grid))

    def test_each_difficulty_teaches_two_dimensional_cropping(self):
        for difficulty, samples in self.samples.items():
            with self.subTest(difficulty=difficulty):
                self.assertTrue(any(
                    len(marker_crop(grid)) < len(grid)
                    and len(marker_crop(grid)[0]) < len(grid[0])
                    for grid in samples
                ), "a column-only crop must not fit every sampled example")
                shapes = {(len(marker_crop(grid)), len(marker_crop(grid)[0]))
                          for grid in samples}
                self.assertGreaterEqual(len(shapes), 4, "crop sizes must vary")

    def test_each_difficulty_refutes_crop_all_nonzero(self):
        for difficulty, samples in self.samples.items():
            with self.subTest(difficulty=difficulty):
                self.assertTrue(any(nonzero_crop(grid) != marker_crop(grid)
                                    for grid in samples),
                                "outside content must distinguish the marker-defined crop")

    def test_each_difficulty_varies_marker_counts_and_refutes_first_last_pair(self):
        for difficulty, samples in self.samples.items():
            with self.subTest(difficulty=difficulty):
                counts = {len(marker_cells(grid)) for grid in samples}
                self.assertIn(2, counts, "retain the canonical sparse-pair family")
                self.assertTrue(any(count > 2 for count in counts))
                self.assertTrue(any(first_last_marker_crop(grid) != marker_crop(grid)
                                    for grid in samples),
                                "some examples must require all markers, not just a pair")


class ExactOverrideTests(unittest.TestCase):
    def assert_observed(self, grid, requested):
        self.assertEqual(GEN.self_check(grid), [])
        if "height" in requested:
            self.assertEqual(len(grid), requested["height"])
        if "width" in requested:
            self.assertEqual(len(grid[0]), requested["width"])
        if "box_h" in requested:
            self.assertEqual(len(marker_crop(grid)), requested["box_h"])
        if "box_w" in requested:
            self.assertEqual(len(marker_crop(grid)[0]), requested["box_w"])
        if "marker_count" in requested:
            self.assertEqual(len(marker_cells(grid)), requested["marker_count"])
        if "n_distinct_colors" in requested:
            self.assertEqual(len({cell for row in grid for cell in row}),
                             requested["n_distinct_colors"])
        if "texture" in requested:
            markers = set(marker_cells(grid))
            top, left, bottom, right = bounds(markers)
            if requested["texture"] == "canonical_pair":
                self.assertTrue({(top, left), (bottom, right)} <= markers)
            elif requested["texture"] == "anti_diagonal":
                self.assertTrue({(top, right), (bottom, left)} <= markers)
            elif requested["texture"] == "scattered":
                self.assertNotEqual(first_last_marker_crop(grid), marker_crop(grid))

    def test_valid_exact_overrides_are_observed_in_the_grid(self):
        cases = [
            {"height": 12, "width": 15, "box_h": 5, "box_w": 7,
             "marker_count": 2, "n_distinct_colors": 3, "texture": "canonical_pair"},
            {"height": 13, "width": 12, "box_h": 6, "box_w": 5,
             "marker_count": 2, "n_distinct_colors": 7, "texture": "anti_diagonal"},
            {"height": 10, "width": 11, "box_h": 7, "box_w": 5,
             "marker_count": 4, "n_distinct_colors": 10, "texture": "scattered"},
            {"height": 30, "width": 30, "box_h": 28, "box_w": 28,
             "marker_count": 8, "n_distinct_colors": 10, "texture": "scattered"},
            {"height": 6, "width": 6, "box_h": 3, "box_w": 3,
             "marker_count": 2, "n_distinct_colors": 3, "texture": "canonical_pair"},
        ]
        for difficulty in DIFFICULTIES:
            for index, requested in enumerate(cases):
                with self.subTest(difficulty=difficulty, requested=requested):
                    grid = GEN.generate(17, index, difficulty=difficulty, **requested)
                    self.assert_observed(grid, requested)

    def test_single_axis_overrides_adapt_unpinned_choices(self):
        cases = {
            "height": (6, 30), "width": (6, 30),
            "box_h": (3, 28), "box_w": (3, 28),
            "marker_count": (2, 3, 4, 8), "n_distinct_colors": (3, 10),
        }
        for difficulty in DIFFICULTIES:
            for axis, values in cases.items():
                for value in values:
                    with self.subTest(difficulty=difficulty, axis=axis, value=value):
                        requested = {axis: value}
                        grid = GEN.generate(17, 0, difficulty=difficulty, **requested)
                        self.assert_observed(grid, requested)

    def test_exact_full_canvas_box_is_not_silently_shrunk(self):
        requested = {"height": 8, "width": 8, "box_h": 8, "box_w": 8,
                     "marker_count": 2, "n_distinct_colors": 3,
                     "texture": "canonical_pair"}
        grid = GEN.generate(17, 0, **requested)
        self.assert_observed(grid, requested)
        self.assertEqual(marker_crop(grid), grid)

    def test_unknown_and_retired_overrides_fail_visibly(self):
        for requested in ({"not_an_axis": 7}, {"n_panels": 8},
                          {"palette_kind": "warm"}, {"density": "sparse"}):
            with self.subTest(requested=requested):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(17, 0, **requested)

    def test_exact_integer_axes_reject_scalar_coercion(self):
        for axis in ("height", "width", "box_h", "box_w", "marker_count",
                     "n_distinct_colors"):
            for value in (True, False, 6.0, "6"):
                with self.subTest(axis=axis, value=value):
                    with self.assertRaises((TypeError, ValueError)):
                        GEN.generate(17, 0, **{axis: value})

    def test_impossible_overrides_raise_instead_of_clamping_or_ignoring(self):
        cases = [
            {"height": 5}, {"height": 31}, {"width": 5}, {"width": 31},
            {"box_h": 2}, {"box_h": 29}, {"box_w": 2}, {"box_w": 29},
            {"height": 6, "box_h": 7}, {"width": 6, "box_w": 7},
            {"marker_count": 1}, {"marker_count": 9},
            {"n_distinct_colors": 2}, {"n_distinct_colors": 11},
            {"texture": "scattered", "marker_count": 2},
            {"texture": "not_a_texture"},
        ]
        for requested in cases:
            with self.subTest(requested=requested):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(17, 0, **requested)


if __name__ == "__main__":
    unittest.main()
