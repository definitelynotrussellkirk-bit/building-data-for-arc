"""Focused public-contract tests for the anchor parameter.

Run from the review packet root with::

    python3 review.py run python3 generators/9c5bdbcdcd50/tests/test_parametric.py

These tests validate Python label claims and episode assembly. Protected Racket
qualification separately checks the emitted programs against every label.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


PARAMETRIC = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
ANCHORS = ("frame", "largest")
BOUNDARY_INPUT = [
    [0, 3, 0, 0, 3, 0],
    [0, 3, 0, 0, 3, 0],
    [3, 3, 3, 3, 3, 3],
    [0, 3, 0, 0, 3, 0],
    [3, 3, 3, 3, 3, 3],
    [0, 3, 0, 0, 3, 0],
]
BOUNDARY_LARGEST = [
    [0, 3, 7, 7, 3, 0],
    [0, 3, 7, 7, 3, 0],
    [3, 3, 3, 3, 3, 3],
    [1, 3, 0, 0, 3, 8],
    [3, 3, 3, 3, 3, 3],
    [1, 3, 0, 0, 3, 8],
]
BOUNDARY_FRAME = [
    [2, 3, 0, 0, 3, 4],
    [2, 3, 0, 0, 3, 4],
    [3, 3, 3, 3, 3, 3],
    [0, 3, 7, 7, 3, 0],
    [3, 3, 3, 3, 3, 3],
    [1, 3, 0, 0, 3, 8],
]


def load_local_module(name, path):
    if not path.is_file():
        raise AssertionError(f"missing parametric implementation: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def raw_lattice(row_bands, col_bands):
    """Build invalid grammar fixtures without asking production to accept them."""
    row_axis = [0]
    col_axis = [0]
    for axis, bands in ((row_axis, row_bands), (col_axis, col_bands)):
        axis.clear()
        for index, width in enumerate(bands):
            if index:
                axis.append(3)
            axis.extend([0] * width)
    return [[3 if row == 3 or col == 3 else 0 for col in col_axis] for row in row_axis]


def zero_components(grid):
    """Independent four-neighbor traversal; no divider parser from production."""
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, color in enumerate(values)
        if color == 0
    }
    components = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        component = {first}
        pending = [first]
        while pending:
            row, col = pending.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    pending.append(point)
        components.append(component)
    return components


def bounds(component):
    return (
        min(row for row, _ in component),
        max(row for row, _ in component),
        min(col for _, col in component),
        max(col for _, col in component),
    )


def component_oracle(grid, anchor, pivot=None):
    """Label connected regions from boundary contact or geometric relations."""
    components = zero_components(grid)
    result = [row[:] for row in grid]
    if anchor == "largest":
        pivot = max(components, key=len) if pivot is None else pivot
        pivot_top, pivot_bottom, pivot_left, pivot_right = bounds(pivot)
    for component in components:
        top, bottom, left, right = bounds(component)
        if anchor == "frame":
            north, south = top == 0, bottom == len(grid) - 1
            west, east = left == 0, right == len(grid[0]) - 1
            color = (
                2 if north and west else
                4 if north and east else
                1 if south and west else
                8 if south and east else
                0 if north or south or west or east else 7
            )
        else:
            color = (
                7 if component == pivot else
                2 if bottom < pivot_top and right < pivot_left else
                4 if bottom < pivot_top and left > pivot_right else
                1 if top > pivot_bottom and right < pivot_left else
                8 if top > pivot_bottom and left > pivot_right else 0
            )
        for row, col in component:
            result[row][col] = color
    return result


def wrong_pivot(grid, rival):
    components = zero_components(grid)
    if rival == "first":
        return components[0]
    if rival == "last":
        return components[-1]
    if rival == "smallest":
        return min(components, key=len)
    if rival == "tallest_only":
        return max(components, key=lambda component: bounds(component)[1] - bounds(component)[0])
    if rival == "widest_only":
        return max(components, key=lambda component: bounds(component)[3] - bounds(component)[2])
    if rival in ("central_region", "row_derived_column", "column_derived_row"):
        tops = sorted({bounds(component)[0] for component in components})
        lefts = sorted({bounds(component)[2] for component in components})
        if rival == "row_derived_column":
            tallest = max(components, key=lambda component: bounds(component)[1] - bounds(component)[0])
            row_index = tops.index(bounds(tallest)[0])
            col_index = max(0, len(lefts) - 1 - row_index)
        elif rival == "column_derived_row":
            widest = max(components, key=lambda component: bounds(component)[3] - bounds(component)[2])
            col_index = lefts.index(bounds(widest)[2])
            row_index = max(0, len(tops) - 1 - col_index)
        else:
            row_index, col_index = len(tops) // 2, len(lefts) // 2
        return next(
            component for component in components
            if bounds(component)[0] == tops[row_index]
            and bounds(component)[2] == lefts[col_index]
        )
    raise AssertionError(f"unknown test rival: {rival}")


class ParametricContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load_local_module(
            "anchor_parametric_under_test", PARAMETRIC / "prototype.py"
        )

    def assert_rejected(self, function, *args, **kwargs):
        with self.assertRaises((TypeError, ValueError)):
            function(*args, **kwargs)

    def assert_valid_episode(self, episode, anchor, demos, queries):
        self.assertEqual(len(episode["train"]), demos)
        self.assertEqual(len(episode["test"]), queries)
        self.assertEqual(episode["program_solution"], self.prototype.program({"anchor": anchor}))
        pairs = episode["train"] + episode["test"]
        self.assertEqual(len({frozen(pair["input"]) for pair in pairs}), len(pairs))
        for pair in pairs:
            grid = pair["input"]
            self.assertTrue(6 <= len(grid) <= 30 and 6 <= len(grid[0]) <= 30)
            self.assertTrue(all(len(row) == len(grid[0]) for row in grid))
            self.assertTrue(all(type(value) is int and value in (0, 3) for row in grid for value in row))
            facts = self.prototype.analyze(grid)
            for axis in (facts["row_bands"], facts["col_bands"]):
                self.assertTrue(3 <= len(axis) <= 6)
                self.assertTrue(all(type(width) is int and 1 <= width <= 6 for width in axis))
                self.assertEqual(axis.count(max(axis)), 1)
            self.assertTrue(all(type(value) is int for row in pair["output"] for value in row))
            self.assertEqual(pair["output"], component_oracle(grid, anchor))

    def test_frame_program_is_the_exact_selected_canonical_resource(self):
        self.assertEqual(
            self.prototype.program({"anchor": "frame"}),
            (PARAMETRIC / "canonical.rkt").read_text(),
        )
        self.assertNotEqual(
            self.prototype.program({"anchor": "frame"}),
            self.prototype.program({"anchor": "largest"}),
        )

    def test_lattice_and_analysis_locate_a_boundary_maximum(self):
        self.assertEqual(self.prototype.lattice([2, 1, 1], [1, 2, 1]), BOUNDARY_INPUT)
        facts = self.prototype.analyze(BOUNDARY_INPUT)
        self.assertEqual(facts["row_bands"], [2, 1, 1])
        self.assertEqual(facts["col_bands"], [1, 2, 1])
        self.assertEqual(facts["pivot"], [0, 1])

    def test_largest_anchor_uses_boundary_pivot_and_leaves_its_cross_zero(self):
        self.assertEqual(self.prototype.transform(BOUNDARY_INPUT, "largest"), BOUNDARY_LARGEST)

    def test_frame_anchor_keeps_corners_edges_and_interior_semantics(self):
        self.assertEqual(self.prototype.transform(BOUNDARY_INPUT, "frame"), BOUNDARY_FRAME)

    def test_interior_pivot_labels_all_regions_without_mutating_the_input(self):
        grid = raw_lattice([2, 5, 1, 3], [1, 3, 6, 2, 4])
        before = frozen(grid)
        for anchor in ANCHORS:
            with self.subTest(anchor=anchor):
                output = self.prototype.transform(grid, anchor)
                self.assertEqual(output, component_oracle(grid, anchor))
                self.assertEqual({value for row in output for value in row}, {0, 1, 2, 3, 4, 7, 8})
                self.assertEqual(frozen(grid), before)

    def test_analysis_rejects_grids_outside_the_admitted_grammar(self):
        invalid = {
            "empty": [],
            "ragged": [row[:] for row in BOUNDARY_INPUT[:-1]] + [[0]],
            "too_small": raw_lattice([1, 1, 1], [1, 2, 1]),
            "two_row_bands": raw_lattice([2, 3], [1, 2, 1]),
            "seven_column_bands": raw_lattice([2, 1, 1], [2, 1, 1, 1, 1, 1, 1]),
            "row_width_seven": raw_lattice([7, 1, 1], [1, 2, 1]),
            "too_large": raw_lattice([6, 5, 5, 5, 5, 5], [1, 2, 1]),
            "tied_row_maximum": raw_lattice([2, 2, 1], [1, 2, 1]),
            "tied_column_maximum": raw_lattice([2, 1, 1], [2, 2, 1]),
            "external_divider": [[3] * 6] + [row[:] for row in BOUNDARY_INPUT],
            "adjacent_dividers": [row[:] for row in BOUNDARY_INPUT[:3]] + [[3] * 6] + [row[:] for row in BOUNDARY_INPUT[3:]],
        }
        for name, row, col, value in (
            ("stray_green_cell", 0, 0, 3),
            ("broken_divider", 2, 2, 0),
            ("other_color", 0, 0, 7),
            ("boolean_cell", 0, 0, False),
            ("float_cell", 0, 0, 0.0),
        ):
            grid = [values[:] for values in BOUNDARY_INPUT]
            grid[row][col] = value
            invalid[name] = grid
        for name, grid in invalid.items():
            with self.subTest(case=name):
                self.assert_rejected(self.prototype.analyze, grid)

    def test_unknown_or_extra_settings_are_rejected_before_generation(self):
        settings = (
            None, {}, {"anchor": "center"}, {"anchor": True},
            {"anchor": ["largest"]}, {"anchor": "frame", "extra": 1},
        )
        for setting in settings:
            with self.subTest(setting=setting):
                self.assert_rejected(self.prototype.program, setting)
                self.assert_rejected(self.prototype.generate, 0, setting, demos=2, queries=1)
        self.assert_rejected(self.prototype.transform, BOUNDARY_INPUT, "center")

    def test_request_counts_are_independent_bounded_exact_integers(self):
        settings = {"anchor": "largest"}
        for demos in (1, 7, True, 3.0, "3", None):
            with self.subTest(demos=demos):
                self.assert_rejected(self.prototype.generate, 0, settings, demos=demos, queries=1)
        for queries in (0, 5, False, 1.0, "1", None):
            with self.subTest(queries=queries):
                self.assert_rejected(self.prototype.generate, 0, settings, demos=2, queries=queries)

    def test_seed_range_rejects_coercions_and_includes_both_endpoints(self):
        settings = {"anchor": "largest"}
        for seed in (-1, 2**63, True, False, 0.0, "0", None):
            with self.subTest(seed=seed):
                self.assert_rejected(self.prototype.generate, seed, settings, demos=2, queries=1)
        for seed in (0, 2**63 - 1):
            with self.subTest(seed=seed):
                episode = self.prototype.generate(seed, settings, demos=2, queries=1)
                self.assert_valid_episode(episode, "largest", 2, 1)

    def test_default_request_is_three_demonstrations_and_four_queries(self):
        episode = self.prototype.generate(0, {"anchor": "largest"})
        self.assert_valid_episode(episode, "largest", 3, 4)

    def test_seeds_match_inputs_across_settings_and_all_count_prefixes(self):
        for seed in (0, 17):
            complete = {
                anchor: self.prototype.generate(seed, {"anchor": anchor}, demos=6, queries=4)
                for anchor in ANCHORS
            }
            for role in ("train", "test"):
                self.assertEqual(
                    [pair["input"] for pair in complete["frame"][role]],
                    [pair["input"] for pair in complete["largest"][role]],
                )
            for anchor in ANCHORS:
                self.assert_valid_episode(complete[anchor], anchor, 6, 4)
                for demos in (2, 3, 6):
                    for queries in (1, 4):
                        with self.subTest(seed=seed, anchor=anchor, demos=demos, queries=queries):
                            actual = self.prototype.generate(seed, {"anchor": anchor}, demos=demos, queries=queries)
                            self.assertEqual(actual["train"], complete[anchor]["train"][:demos])
                            self.assertEqual(actual["test"], complete[anchor]["test"][:queries])
                            self.assertEqual(actual["program_solution"], complete[anchor]["program_solution"])
            self.assertEqual(
                [(len(pair["input"]), len(pair["input"][0])) for pair in complete["largest"]["test"]],
                [(6, 6), (13, 19), (24, 27), (30, 30)],
            )

    def test_two_visible_demonstrations_reject_finite_wrong_pivots(self):
        rivals = ("first", "last", "central_region", "smallest", "tallest_only", "widest_only")
        for seed in (0, 17):
            episode = self.prototype.generate(seed, {"anchor": "largest"}, demos=2, queries=1)
            demos = episode["train"]
            self.assertTrue(any(pair["output"] != component_oracle(pair["input"], "frame") for pair in demos))
            for rival in rivals:
                with self.subTest(seed=seed, rival=rival):
                    self.assertTrue(any(
                        pair["output"] != component_oracle(
                            pair["input"], "largest", wrong_pivot(pair["input"], rival)
                        )
                        for pair in demos
                    ))

    def test_two_demos_separate_row_and_column_maximum_selection(self):
        # Anti-diagonal pivots alone permit one maximum coordinate to stand in
        # for the other; the demonstrations must expose each independent step.
        for seed in (0, 17):
            demos = self.prototype.generate(
                seed, {"anchor": "largest"}, demos=2, queries=1
            )["train"]
            for rival in ("row_derived_column", "column_derived_row"):
                with self.subTest(seed=seed, rival=rival):
                    self.assertTrue(
                        any(
                            pair["output"] != component_oracle(
                                pair["input"], "largest", wrong_pivot(pair["input"], rival)
                            )
                            for pair in demos
                        ),
                        f"both visible demonstrations still fit {rival}",
                    )

    def test_thirty_square_query_has_full_lattice_content(self):
        episode = self.prototype.generate(17, {"anchor": "largest"}, demos=2, queries=4)
        pair = episode["test"][3]
        grid = pair["input"]
        self.assertEqual((len(grid), len(grid[0])), (30, 30))
        components = zero_components(grid)
        self.assertTrue(25 <= len(components) <= 36)
        self.assertGreaterEqual(sum(map(len, components)), 625)
        self.assertLessEqual(max(map(len, components)), 36)
        for corner in ((0, 0), (0, 29), (29, 0), (29, 29)):
            self.assertTrue(any(corner in component for component in components))
        self.assertEqual(pair["output"], component_oracle(grid, "largest"))

    def test_native_adapter_exposes_verified_episode_contract(self):
        adapter = load_local_module("anchor_adapter_under_test", PARAMETRIC / "adapter.py")
        for anchor in ANCHORS:
            with self.subTest(anchor=anchor):
                episode = adapter.generate(17, {"anchor": anchor}, demos=2, queries=1)
                self.assert_valid_episode(episode, anchor, 2, 1)
                self.assertEqual(episode["program_solution"], adapter.program({"anchor": anchor}))


if __name__ == "__main__":
    unittest.main()
