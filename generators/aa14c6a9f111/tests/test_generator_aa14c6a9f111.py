"""Focused semantic and override regressions for generator aa14c6a9f111."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import os
import random
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)

TASK_ID = "aa14c6a9f111"
ROOT = find_root(__file__)
MODULE_FILE = os.environ.get("GENERATOR_AA14C6A9F111_FILE")
if MODULE_FILE:
    spec = importlib.util.spec_from_file_location(
        f"focused_{TASK_ID}_generator", MODULE_FILE
    )
    assert spec and spec.loader
    GENERATOR = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GENERATOR)
else:
    GENERATOR = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )

EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "rectangles",
    "palette_kind",
    "layout_mode",
    "orientation_mode",
}
EXPECTED_PALETTES = ("low", "middle", "high", "mixed")
EXPECTED_LAYOUTS = ("disjoint", "nested")
EXPECTED_ORIENTATIONS = ("main", "anti", "mixed")
BASE_RELATIVE = Path(
    "data/base/solutions/banks/84602fe0e9ce/E103__aa14c6a9f111.json"
)
_BASE_CANDIDATES = (ROOT / BASE_RELATIVE, ROOT / "shared" / BASE_RELATIVE)
BASE_PATH = next(
    (candidate for candidate in _BASE_CANDIDATES if candidate.is_file()),
    _BASE_CANDIDATES[0],
)


def canonical_row():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def canonical_pairs():
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in load_canonical_pairs(TASK_ID, root=ROOT)
    ]


def independent_rule(grid):
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    cells = defaultdict(list)
    for row in range(height):
        for col, value in enumerate(grid[row]):
            if value:
                cells[value].append((row, col))
    for color, pair in cells.items():
        if len(pair) != 2:
            continue
        (row_a, col_a), (row_b, col_b) = pair
        if row_a == row_b or col_a == col_b:
            continue
        row0, row1 = sorted((row_a, row_b))
        col0, col1 = sorted((col_a, col_b))
        for col in range(col0, col1 + 1):
            output[row0][col] = color
            output[row1][col] = color
        for row in range(row0, row1 + 1):
            output[row][col0] = color
            output[row][col1] = color
    return output


def support(grid):
    return [[value != 0 for value in row] for row in grid]


def solid_boxes(grid):
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    cells = defaultdict(list)
    for row in range(height):
        for col, value in enumerate(grid[row]):
            if value:
                cells[value].append((row, col))
    for color, pair in cells.items():
        if len(pair) != 2:
            continue
        rows = [row for row, _ in pair]
        cols = [col for _, col in pair]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                output[row][col] = color
    return output


class GeneratorAa14c6a9f111Tests(unittest.TestCase):
    def test_rule_pin_base_sync_and_every_canonical_pair(self):
        row = canonical_row()
        source = row["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        base = json.loads(BASE_PATH.read_text())
        self.assertEqual(digest, "3f7149fda1ec")
        self.assertEqual(GENERATOR.RULE_HASH, digest)
        self.assertEqual(base["racket_target"]["target_code"], source)

        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 3)
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            self.assertEqual(GENERATOR.self_check(before), [])
            self.assertEqual(independent_rule(before), pair["output"])
            self.assertEqual(before, pair["input"])

    def test_axis_surface_and_full_boundary_cross_are_exactly_observable(self):
        self.assertEqual(set(GENERATOR.AXES), EXPECTED_AXES)
        case_index = 0
        for height in (7, 16):
            for width in (7, 16):
                for rectangles in (2, 3):
                    for palette_kind in EXPECTED_PALETTES:
                        for layout_mode in EXPECTED_LAYOUTS:
                            for orientation_mode in EXPECTED_ORIENTATIONS:
                                band = ("easy", "medium", "hard")[case_index % 3]
                                expected = {
                                    "grid_h": height,
                                    "grid_w": width,
                                    "rectangles": rectangles,
                                    "palette_kind": palette_kind,
                                    "layout_mode": layout_mode,
                                    "orientation_mode": orientation_mode,
                                }
                                grid = GENERATOR.generate(
                                    10_000 + case_index,
                                    29 * case_index + 7,
                                    difficulty=band,
                                    **expected,
                                )
                                self.assertEqual(GENERATOR.self_check(grid), [])
                                self.assertEqual(GENERATOR.observe_overrides(grid), expected)
                                self.assertTrue(any(value for row in independent_rule(grid) for value in row))
                                case_index += 1

    def test_every_branch_is_witnessed_in_every_band(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            palettes = Counter()
            layouts = Counter()
            orientations = Counter()
            rectangle_counts = Counter()
            dimensions = set()
            inputs = set()
            outputs = set()
            for seed in range(240):
                grid = GENERATOR.generate(
                    50_000 + band_index * 10_000 + seed,
                    seed * 31 + band_index,
                    difficulty=band,
                )
                self.assertEqual(GENERATOR.self_check(grid), [])
                observed = GENERATOR.observe_overrides(grid)
                palettes[observed["palette_kind"]] += 1
                layouts[observed["layout_mode"]] += 1
                orientations[observed["orientation_mode"]] += 1
                rectangle_counts[observed["rectangles"]] += 1
                dimensions.add((observed["grid_h"], observed["grid_w"]))
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, independent_rule(grid))))
            self.assertEqual(set(palettes), set(EXPECTED_PALETTES))
            self.assertEqual(set(layouts), set(EXPECTED_LAYOUTS))
            self.assertEqual(set(orientations), set(EXPECTED_ORIENTATIONS))
            self.assertEqual(set(rectangle_counts), {2, 3})
            self.assertGreaterEqual(len(dimensions), 3)
            self.assertGreaterEqual(len(inputs), 235)
            self.assertGreaterEqual(len(outputs), 235)

    def test_targeted_structural_impostors_are_rejected(self):
        valid = GENERATOR.generate(
            424242,
            17,
            difficulty="medium",
            grid_h=9,
            grid_w=9,
            rectangles=2,
            palette_kind="mixed",
            layout_mode="disjoint",
            orientation_mode="main",
        )
        invalid = []

        invalid.append([[0] * 9 for _ in range(9)])

        singleton = [[0] * 9 for _ in range(9)]
        singleton[1][1] = 2
        singleton[6][6] = 7
        singleton[7][7] = 7
        invalid.append(singleton)

        collinear = copy.deepcopy(valid)
        color = next(value for row in collinear for value in row if value)
        positions = [(r, c) for r, row in enumerate(collinear) for c, value in enumerate(row) if value == color]
        collinear[positions[1][0]][positions[1][1]] = 0
        collinear[positions[0][0]][min(8, positions[0][1] + 1)] = color
        invalid.append(collinear)

        extra_corner = copy.deepcopy(valid)
        extra_corner[0][0] = color
        invalid.append(extra_corner)

        no_hollow = [[0] * 9 for _ in range(9)]
        for value, first, second in ((2, (1, 1), (2, 2)), (7, (6, 6), (7, 7))):
            no_hollow[first[0]][first[1]] = value
            no_hollow[second[0]][second[1]] = value
        invalid.append(no_hollow)

        overlap = [[0] * 9 for _ in range(9)]
        for value, first, second in ((2, (1, 1), (6, 6)), (7, (1, 6), (6, 1))):
            overlap[first[0]][first[1]] = value
            overlap[second[0]][second[1]] = value
        invalid.append(overlap)

        partial_overlap = [[0] * 9 for _ in range(9)]
        for value, first, second in ((2, (0, 0), (5, 5)), (7, (3, 3), (8, 8))):
            partial_overlap[first[0]][first[1]] = value
            partial_overlap[second[0]][second[1]] = value
        invalid.append(partial_overlap)

        ragged = [[0] * 9 for _ in range(9)]
        ragged[-1].pop()
        invalid.append(ragged)

        for grid in invalid:
            self.assertTrue(GENERATOR.self_check(grid), grid)
            self.assertEqual(GENERATOR.observe_overrides(grid), {})

    def test_palette_does_not_encode_geometry(self):
        supports = set()
        observations = set()
        for palette_kind in EXPECTED_PALETTES:
            grid = GENERATOR.generate(
                77,
                19,
                difficulty="hard",
                grid_h=12,
                grid_w=13,
                rectangles=3,
                palette_kind=palette_kind,
                layout_mode="nested",
                orientation_mode="mixed",
            )
            supports.add(tuple(map(tuple, support(grid))))
            observations.add(GENERATOR.observe_overrides(grid)["palette_kind"])
        self.assertEqual(len(supports), 1)
        self.assertEqual(observations, set(EXPECTED_PALETTES))

    def test_shortcut_recombinations_have_counterexamples(self):
        grid = GENERATOR.generate(
            991,
            73,
            difficulty="hard",
            grid_h=12,
            grid_w=13,
            rectangles=3,
            palette_kind="mixed",
            layout_mode="disjoint",
            orientation_mode="mixed",
        )
        expected = independent_rule(grid)
        self.assertNotEqual(grid, expected, "copy-input shortcut must fail")
        self.assertNotEqual(solid_boxes(grid), expected, "filled-bbox shortcut must fail")

        horizontal_only = [[0] * len(grid[0]) for _ in grid]
        by_color = defaultdict(list)
        for row in range(len(grid)):
            for col, value in enumerate(grid[row]):
                if value:
                    by_color[value].append((row, col))
        for color, cells in by_color.items():
            rows = sorted(row for row, _ in cells)
            cols = sorted(col for _, col in cells)
            for col in range(cols[0], cols[1] + 1):
                horizontal_only[rows[0]][col] = color
                horizontal_only[rows[1]][col] = color
        self.assertNotEqual(horizontal_only, expected, "horizontal-edge-only shortcut must fail")

        global_box = [[0] * len(grid[0]) for _ in grid]
        active = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        row0, row1 = min(r for r, _ in active), max(r for r, _ in active)
        col0, col1 = min(c for _, c in active), max(c for _, c in active)
        for col in range(col0, col1 + 1):
            global_box[row0][col] = 1
            global_box[row1][col] = 1
        for row in range(row0, row1 + 1):
            global_box[row][col0] = 1
            global_box[row][col1] = 1
        self.assertNotEqual(global_box, expected, "single-global-box shortcut must fail")

    def test_invalid_and_unknown_overrides_reject_loudly(self):
        invalid = (
            {"grid_h": 6},
            {"grid_w": 17},
            {"rectangles": 1},
            {"rectangles": 4},
            {"palette_kind": "default"},
            {"layout_mode": "overlap"},
            {"orientation_mode": "random"},
            {"texture": "degenerate"},
        )
        for overrides in invalid:
            with self.assertRaises((TypeError, ValueError), msg=overrides):
                GENERATOR.generate(1, 2, **overrides)

    def test_determinism_fresh_returns_and_global_rng(self):
        random.seed(20260723)
        state = random.getstate()
        first = GENERATOR.generate(73, 109, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GENERATOR.generate(73, 109, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        third = GENERATOR.generate(73, 109, difficulty="hard")
        self.assertEqual(second, third)


if __name__ == "__main__":
    unittest.main()
