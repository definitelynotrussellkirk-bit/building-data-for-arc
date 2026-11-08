"""Focused regression tests for the 17a429a40b62 generator repair."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "17a429a40b62"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_inputs() -> list[list[list[int]]]:
    row = _canonical_row()
    inputs = [pair["input"] for pair in row["train"]]
    test = row["test"]
    if isinstance(test, list):
        inputs.extend(pair["input"] for pair in test)
    else:
        inputs.append(test["input"])
    return inputs


def _role_signature(grid):
    cols = [c for c in range(len(grid[0])) if grid[0][c] and grid[1][c]]
    srcs = [grid[0][c] for c in cols]
    dsts = [grid[1][c] for c in cols]
    src_index = {value: index for index, value in enumerate(srcs)}
    dst_index = {value: index for index, value in enumerate(dsts)}
    roles = []
    for row in grid[2:]:
        role_row = []
        for value in row:
            if value == 0:
                role_row.append("0")
            elif value in src_index:
                role_row.append(f"S{src_index[value]}")
            elif value in dst_index:
                role_row.append(f"D{dst_index[value]}")
            else:
                role_row.append("X")
        roles.append(tuple(role_row))
    return (len(grid), len(grid[0]), tuple(cols), tuple(roles))


class TestRuleAndCanonicalEnvelope(unittest.TestCase):
    def test_rule_hash_matches_active_authorities(self):
        row = _canonical_row()
        base = json.loads(
            (
                ROOT
                / "data/base/solutions/banks/22a17f7a0399/M66__17a429a40b62.json"
            ).read_text()
        )
        self.assertEqual(gen.RULE_HASH, _normalized_hash(row["program_solution"]))
        self.assertEqual(
            gen.RULE_HASH,
            _normalized_hash(base["racket_target"]["target_code"]),
        )

    def test_all_canonical_inputs_are_accepted(self):
        for index, grid in enumerate(_canonical_inputs()):
            self.assertEqual(gen.self_check(grid), [], f"canonical input {index}")

    def test_scheduled_prior_matches_linked_canonical_signatures(self):
        canonical_signatures = {_role_signature(grid) for grid in _canonical_inputs()}
        for band in ("easy", "medium", "hard"):
            for sample_index in (0, 4, 8, 12):
                grid = gen.generate(117 + sample_index, sample_index, difficulty=band)
                self.assertIn(_role_signature(grid), canonical_signatures)
                observed = gen.observe_overrides(grid)
                self.assertEqual(observed["n_pairs"], 3)
                self.assertEqual(observed["unchanged_body_colors"], 0)
                self.assertEqual(observed["legend_layout"], "canonical_even")
                self.assertEqual(observed["body_style"], "canonical_template")


class TestDeterminismAndPurity(unittest.TestCase):
    def test_replay_is_equal_but_fresh(self):
        first = gen.generate(9182, 7, difficulty="hard")
        second = gen.generate(9182, 7, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        for left, right in zip(first, second):
            self.assertIsNot(left, right)
        pristine = copy.deepcopy(second)
        first[2][0] = (first[2][0] + 1) % 10
        self.assertEqual(gen.generate(9182, 7, difficulty="hard"), pristine)

    def test_generate_does_not_touch_process_global_rng(self):
        random.seed(773311)
        state = random.getstate()
        gen.generate(4, 1, difficulty="medium")
        self.assertEqual(random.getstate(), state)


class TestExactOverrides(unittest.TestCase):
    def _draw(self, **case):
        grid = gen.generate(41, 5, difficulty="medium", **case)
        self.assertEqual(
            gen.self_check(grid, meta={"overrides": case}),
            [],
            case,
        )
        return grid

    def test_numeric_boundaries_are_exact(self):
        for value in (5, 10):
            self.assertEqual(len(self._draw(grid_h=value)), value)
        for value in (6, 12):
            self.assertEqual(len(self._draw(grid_w=value)[0]), value)
        for value in (2, 3):
            grid = self._draw(n_pairs=value)
            self.assertEqual(gen.observe_overrides(grid)["n_pairs"], value)
        for value in (0, 2):
            grid = self._draw(unchanged_body_colors=value)
            self.assertEqual(
                gen.observe_overrides(grid)["unchanged_body_colors"], value
            )

    def test_categorical_overrides_are_observable(self):
        for profile in gen.PALETTE_PROFILES:
            grid = self._draw(palette_profile=profile)
            self.assertEqual(gen.observe_overrides(grid)["palette_profile"], profile)
        for layout in gen.LEGEND_LAYOUTS:
            grid = self._draw(legend_layout=layout)
            self.assertEqual(gen.observe_overrides(grid)["legend_layout"], layout)
        for style in gen.BODY_STYLES:
            grid = self._draw(body_style=style)
            self.assertEqual(gen.observe_overrides(grid)["body_style"], style)

    def test_fully_compatible_combination_is_exact(self):
        case = {
            "grid_h": 10,
            "grid_w": 12,
            "n_pairs": 3,
            "unchanged_body_colors": 2,
            "palette_profile": "gray_destination",
            "legend_layout": "scattered",
            "body_style": "scattered",
        }
        grid = self._draw(**case)
        self.assertEqual((len(grid), len(grid[0])), (10, 12))
        observed = gen.observe_overrides(grid)
        for key in case:
            if key not in ("grid_h", "grid_w"):
                self.assertEqual(observed[key], case[key])

    def test_incompatible_combinations_reject_loudly(self):
        for case in (
            {"n_pairs": 2, "body_style": "canonical_template"},
            {"grid_w": 6, "body_style": "canonical_template"},
            {"n_pairs": 1},
            {"unchanged_body_colors": 3},
            {"palette_profile": "rainbow"},
            {"legend_layout": "diagonal"},
            {"body_style": "solid"},
        ):
            with self.assertRaises(ValueError, msg=case):
                gen.generate(3, 2, difficulty="easy", **case)


class TestStructuralSelfCheck(unittest.TestCase):
    def _base(self):
        return gen.generate(
            9901,
            7,
            difficulty="medium",
            grid_h=8,
            grid_w=10,
            n_pairs=3,
            unchanged_body_colors=2,
            palette_profile="gray_destination",
            legend_layout="scattered",
            body_style="scattered",
        )

    def test_rejects_misaligned_legend(self):
        grid = self._base()
        column = next(c for c, value in enumerate(grid[1]) if value)
        destination = grid[1][column]
        grid[1][column] = 0
        empty = next(c for c in range(len(grid[0])) if grid[0][c] == grid[1][c] == 0)
        grid[1][empty] = destination
        self.assertTrue(any("align exactly" in error for error in gen.self_check(grid)))

    def test_rejects_duplicate_source(self):
        grid = self._base()
        columns = [c for c, value in enumerate(grid[0]) if value]
        grid[0][columns[1]] = grid[0][columns[0]]
        self.assertTrue(any("source legend colors" in error for error in gen.self_check(grid)))

    def test_rejects_source_destination_overlap(self):
        grid = self._base()
        columns = [c for c, value in enumerate(grid[0]) if value]
        grid[1][columns[0]] = grid[0][columns[1]]
        self.assertTrue(any("mutually disjoint" in error or "disjoint" in error for error in gen.self_check(grid)))

    def test_rejects_missing_source_witnesses(self):
        grid = self._base()
        source = next(value for value in grid[0] if value)
        for row in grid[2:]:
            for c, value in enumerate(row):
                if value == source:
                    row[c] = 0
        self.assertTrue(any("appears only" in error for error in gen.self_check(grid)))

    def test_rejects_unknown_body_color(self):
        grid = self._base()
        used = {value for row in grid for value in row}
        unknown = next(color for color in range(1, 10) if color not in used)
        grid[2][0] = unknown
        self.assertTrue(any("absent from the legend" in error for error in gen.self_check(grid)))

    def test_rejects_body_without_background(self):
        grid = self._base()
        source = next(value for value in grid[0] if value)
        for row in grid[2:]:
            for c, value in enumerate(row):
                if value == 0:
                    row[c] = source
        self.assertTrue(any("background cell" in error for error in gen.self_check(grid)))


class TestSequentialLessonSchedule(unittest.TestCase):
    @staticmethod
    def _fixed_even_shortcut(grid):
        out = copy.deepcopy(grid)
        mapping = {
            grid[0][c]: grid[1][c]
            for c in (0, 2, 4)
            if c < len(grid[0]) and grid[0][c] and grid[1][c]
        }
        for r in range(2, len(grid)):
            for c, value in enumerate(grid[r]):
                if value in mapping:
                    out[r][c] = mapping[value]
        return out

    @staticmethod
    def _expected(grid):
        out = copy.deepcopy(grid)
        mapping = {
            grid[0][c]: grid[1][c]
            for c in range(len(grid[0]))
            if grid[0][c] and grid[1][c]
        }
        for r in range(2, len(grid)):
            for c, value in enumerate(grid[r]):
                if value in mapping:
                    out[r][c] = mapping[value]
        return out

    def test_every_three_consecutive_demos_rebut_key_shortcuts(self):
        for start in range(8):
            grids = [gen.generate(20260724, start + offset) for offset in range(3)]
            observed = [gen.observe_overrides(grid) for grid in grids]
            self.assertTrue(
                any(item["unchanged_body_colors"] >= 1 for item in observed),
                (start, observed),
            )
            self.assertTrue(
                any(self._fixed_even_shortcut(grid) != self._expected(grid) for grid in grids),
                (start, observed),
            )


if __name__ == "__main__":
    unittest.main()
