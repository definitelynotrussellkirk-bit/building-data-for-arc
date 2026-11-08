"""Focused semantic regressions for generator ec1c917f8de0."""
from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "ec1c917f8de0"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _without_marker(grid):
    frozen = tuple(tuple(row) for row in grid)
    height, width = len(frozen), len(frozen[0])
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    result = [list(row) for row in frozen]
    for row, col in corners:
        if result[row][col] == 9:
            result[row][col] = 0
    return tuple(tuple(row) for row in result)


class GeneratorEc1c917f8de0Tests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_pairs(self):
        row = _canonical_row()
        self.assertEqual(MODULE.RULE_HASH, "3a8a12acc2b6")
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            frozen = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.strict_canonical_like(source), [])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, frozen)

    def test_exact_overrides_all_bands(self):
        cases = [
            {
                "grid_h": 6,
                "grid_w": 6,
                "marker_corner": "TL",
                "blob_color": 1,
                "shape_profile": "zig5",
            },
            {
                "grid_h": 12,
                "grid_w": 12,
                "marker_corner": "BR",
                "blob_color": 8,
                "shape_profile": "crown8",
            },
        ]
        for difficulty in ("easy", "medium", "hard", None):
            for index, overrides in enumerate(cases):
                grid = MODULE.generate(3100 + index, index, difficulty=difficulty, **overrides)
                observed = MODULE.observe_overrides(grid)
                for axis, expected in overrides.items():
                    self.assertEqual(
                        observed[axis],
                        expected,
                        msg=f"{difficulty=} {axis=}",
                    )
                self.assertEqual(MODULE.self_check(grid, difficulty=difficulty), [])

    def test_causal_four_corner_lesson_and_novel_query(self):
        grids = [MODULE.generate(41, index, difficulty="medium") for index in range(5)]
        demos = [{"input": grid, "output": MODULE.rule_mirror(grid)} for grid in grids[:4]]
        query = {"input": grids[4], "output": MODULE.rule_mirror(grids[4])}

        self.assertEqual(
            {MODULE.observe_overrides(grid)["marker_corner"] for grid in grids[:4]},
            {"TL", "TR", "BL", "BR"},
        )
        self.assertEqual(len({_without_marker(grid) for grid in grids[:4]}), 1)
        self.assertEqual(len({tuple(map(tuple, pair["output"])) for pair in demos}), 4)
        self.assertNotEqual(_without_marker(grids[4]), _without_marker(grids[0]))
        self.assertEqual(MODULE.lesson_identifiable(demos, query), [])

    def test_self_check_rejects_targeted_impostors(self):
        base = MODULE.generate(
            9,
            0,
            difficulty="medium",
            grid_h=9,
            grid_w=9,
            marker_corner="TL",
            blob_color=4,
            shape_profile="spur6",
        )
        mutations = {}

        no_marker = copy.deepcopy(base)
        no_marker[0][0] = 0
        mutations["no_marker"] = no_marker

        middle_marker = copy.deepcopy(base)
        middle_marker[0][0] = 0
        middle_marker[4][4] = 9
        mutations["middle_marker"] = middle_marker

        second_marker = copy.deepcopy(base)
        second_marker[-1][-1] = 9
        mutations["second_marker"] = second_marker

        symmetric_rectangle = [[0] * 8 for _ in range(8)]
        symmetric_rectangle[0][0] = 9
        for row in (2, 3):
            for col in (2, 3, 4):
                symmetric_rectangle[row][col] = 3
        mutations["transform_collapsing_rectangle"] = symmetric_rectangle

        disconnected = copy.deepcopy(base)
        blob_cells = [
            (row, col)
            for row, values in enumerate(disconnected)
            for col, value in enumerate(values)
            if value not in (0, 9)
        ]
        row, col = blob_cells[0]
        disconnected[row][col] = 0
        disconnected[-2][-2] = 4
        mutations["disconnected_blob"] = disconnected

        multicolor = copy.deepcopy(base)
        row, col = blob_cells[0]
        multicolor[row][col] = 5
        mutations["multicolor_blob"] = multicolor

        too_small = copy.deepcopy(base)
        for row, col in blob_cells[:2]:
            too_small[row][col] = 0
        mutations["too_few_blob_cells"] = too_small

        for name, grid in mutations.items():
            self.assertTrue(MODULE.self_check(grid), msg=name)

    def test_determinism_fresh_returns_and_global_rng(self):
        state_before = random.getstate()
        first = MODULE.generate(123456, 17, difficulty="hard")
        state_after = random.getstate()
        second = MODULE.generate(123456, 17, difficulty="hard")
        self.assertEqual(state_before, state_after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

        first[0][0] = 7
        third = MODULE.generate(123456, 17, difficulty="hard")
        self.assertEqual(second, third)

    def test_all_profiles_are_connected_and_transform_distinct(self):
        self.assertGreaterEqual(len(MODULE.SHAPE_PROFILES), 12)
        for profile, cells in MODULE.SHAPE_PROFILES.items():
            self.assertTrue(MODULE._connected_4(cells), msg=profile)
            self.assertTrue(MODULE._four_distinct(cells), msg=profile)
            grid = MODULE.generate(
                77,
                3,
                difficulty="hard",
                grid_h=12,
                grid_w=12,
                marker_corner="TR",
                blob_color=6,
                shape_profile=profile,
            )
            self.assertEqual(MODULE.self_check(grid), [], msg=profile)
            self.assertEqual(MODULE.observe_overrides(grid)["shape_profile"], profile)


if __name__ == "__main__":
    unittest.main()
