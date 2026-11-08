from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

generator = importlib.import_module(
    "puzzle_generators.per_puzzle.56a06c9b29a3.generator"
)


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "56a06c9b29a3"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/b9cb6b5db49d"
    / "H75__56a06c9b29a3.json"
)
OPS = ("union", "intersection", "xor", "a-minus-b", "b-minus-a")
PALETTE_KINDS = ("paired", "demo_mixed", "query_mixed", "all_distinct")
ALL_RELATIONS = {(False, False), (True, False), (False, True), (True, True)}


def _coerce(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else list(row)
        for row in grid
    ]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"]
    return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def _split(grid):
    grid = _coerce(grid)
    height = len(grid)
    width = len(grid[0])
    separators = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    panels = []
    start = 0
    for separator in separators + [width]:
        panels.append([row[start:separator] for row in grid])
        start = separator + 1
    return separators, panels


def _support(panel):
    return [[value != 0 for value in row] for row in panel]


def _relations(left, right):
    return {
        (left[row][col], right[row][col])
        for row in range(len(left))
        for col in range(len(left[0]))
    }


def _apply(operation, left, right):
    left = _support(left)
    right = _support(right)
    output = []
    for left_row, right_row in zip(left, right):
        row = []
        for left_on, right_on in zip(left_row, right_row):
            if operation == "union":
                on = left_on or right_on
            elif operation == "intersection":
                on = left_on and right_on
            elif operation == "xor":
                on = left_on != right_on
            elif operation == "a-minus-b":
                on = left_on and not right_on
            elif operation == "b-minus-a":
                on = right_on and not left_on
            else:  # pragma: no cover - guarded by every caller
                raise AssertionError(operation)
            row.append(2 if on else 0)
        output.append(row)
    return output


def _matches(panels):
    return [
        operation
        for operation in OPS
        if _apply(operation, panels[0], panels[1]) == _coerce(panels[2])
    ]


def _independent_rule(grid):
    _separators, panels = _split(grid)
    operation = _matches(panels)[0]
    return _apply(operation, panels[3], panels[4])


def _panel_colors(panels):
    colors = []
    for index in (0, 1, 3, 4):
        nonzero = {value for row in panels[index] for value in row if value != 0}
        if len(nonzero) != 1:
            raise AssertionError((index, nonzero))
        colors.append(next(iter(nonzero)))
    return tuple(colors)


def _swap_query_panels(grid):
    grid = _coerce(grid)
    _separators, panels = _split(grid)
    width = len(panels[0][0])
    fourth_start = 3 * (width + 1)
    fifth_start = 4 * (width + 1)
    swapped = [row[:] for row in grid]
    for row in range(len(grid)):
        fourth = grid[row][fourth_start : fourth_start + width]
        fifth = grid[row][fifth_start : fifth_start + width]
        swapped[row][fourth_start : fourth_start + width] = fifth
        swapped[row][fifth_start : fifth_start + width] = fourth
    return swapped


class Generator56a06c9b29a3Tests(unittest.TestCase):
    def test_source_pin_and_all_canonical_pairs_follow_ordered_inference(self):
        row = _canonical_row()
        base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
        canonical_rule = row["program_solution"]
        self.assertEqual(base["racket_target"]["target_code"], canonical_rule)
        self.assertEqual(generator.RULE_HASH, _normalized_hash(canonical_rule)[:12])
        self.assertEqual(generator.RULE_HASH, "d79838837a8c")

        pairs = _canonical_pairs()
        self.assertEqual(len(pairs), 3)
        match_sets = []
        for pair in pairs:
            before = _coerce(pair["input"])
            _separators, panels = _split(before)
            matches = _matches(panels)
            self.assertTrue(matches)
            self.assertEqual(generator.self_check(before), [])
            self.assertEqual(_independent_rule(before), _coerce(pair["output"]))
            self.assertEqual(before, _coerce(pair["input"]))
            match_sets.append(tuple(matches))
        self.assertEqual(
            match_sets,
            [("union",), ("xor", "a-minus-b"), ("intersection",)],
        )

    def test_exact_override_boundaries_and_discrete_crosses_are_observable(self):
        case_index = 0
        for height in (3, 6):
            for width in (3, 5):
                for operation in OPS:
                    for color in (1, 8):
                        for palette_kind in PALETTE_KINDS:
                            overrides = {
                                "panel_h": height,
                                "panel_w": width,
                                "operation": operation,
                                "op1_color": color,
                                "palette_kind": palette_kind,
                            }
                            grid = generator.generate(
                                10_000 + case_index,
                                20_000 + case_index,
                                difficulty=("easy", "medium", "hard")[case_index % 3],
                                **overrides,
                            )
                            self.assertEqual(generator.self_check(grid), [])
                            self.assertEqual(generator.observe_overrides(grid), overrides)
                            self.assertEqual(
                                generator.self_check(
                                    grid,
                                    meta={"overrides": overrides},
                                ),
                                [],
                            )
                            case_index += 1

        for color in range(1, 9):
            grid = generator.generate(30_000 + color, 7, op1_color=color)
            self.assertEqual(generator.observe_overrides(grid)["op1_color"], color)

    def test_every_operation_has_unique_positive_witnesses_in_every_palette_mode(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for operation_index, operation in enumerate(OPS):
                for palette_index, palette_kind in enumerate(PALETTE_KINDS):
                    grid = generator.generate(
                        40_000 + band_index * 100 + operation_index * 10 + palette_index,
                        23,
                        difficulty=band,
                        operation=operation,
                        palette_kind=palette_kind,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    _separators, panels = _split(grid)
                    self.assertEqual(_matches(panels), [operation])
                    self.assertEqual(
                        _relations(_support(panels[0]), _support(panels[1])),
                        ALL_RELATIONS,
                    )
                    self.assertEqual(
                        _relations(_support(panels[3]), _support(panels[4])),
                        ALL_RELATIONS,
                    )
                    output = _independent_rule(grid)
                    self.assertGreater(sum(value == 2 for row in output for value in row), 0)
                    self.assertEqual(
                        generator.observe_overrides(grid)["palette_kind"],
                        palette_kind,
                    )

    def test_linked_default_census_is_stable_and_not_a_fixed_template(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            operation_counts = Counter()
            palette_counts = Counter()
            dimensions = set()
            inputs = set()
            outputs = set()
            for offset in range(240):
                grid = generator.generate(
                    50_000 + band_index * 10_000 + offset,
                    97 * offset + 11,
                    difficulty=band,
                )
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                operation_counts[observed["operation"]] += 1
                palette_counts[observed["palette_kind"]] += 1
                dimensions.add((observed["panel_h"], observed["panel_w"]))
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, _independent_rule(grid))))
            self.assertEqual(set(operation_counts), set(OPS))
            self.assertEqual(set(palette_counts), set(PALETTE_KINDS))
            self.assertGreaterEqual(len(dimensions), 2)
            self.assertGreaterEqual(len(inputs), 235)
            self.assertGreaterEqual(len(outputs), 190)

    def test_colors_do_not_encode_the_operation(self):
        operand_colors = set()
        outputs = set()
        for operation in OPS:
            grid = generator.generate(
                61_337,
                29,
                difficulty="hard",
                operation=operation,
                palette_kind="all_distinct",
            )
            _separators, panels = _split(grid)
            operand_colors.add(_panel_colors(panels))
            outputs.add(tuple(map(tuple, _independent_rule(grid))))
        self.assertEqual(len(operand_colors), 1)
        self.assertEqual(len(outputs), len(OPS))

        same_operation_colors = set()
        for seed in range(32):
            grid = generator.generate(seed, seed * 13 + 5, operation="xor")
            same_operation_colors.add(_panel_colors(_split(grid)[1]))
        self.assertGreaterEqual(len(same_operation_colors), 20)

    def test_histogram_preserving_query_recombination_changes_the_answer(self):
        grid = generator.generate(
            73,
            91,
            difficulty="hard",
            operation="a-minus-b",
            palette_kind="paired",
        )
        swapped = _swap_query_panels(grid)
        self.assertEqual(
            Counter(value for row in grid for value in row),
            Counter(value for row in swapped for value in row),
        )
        self.assertEqual(len(grid), len(swapped))
        self.assertEqual(len(grid[0]), len(swapped[0]))
        self.assertEqual(generator.self_check(grid), [])
        self.assertEqual(generator.self_check(swapped), [])
        self.assertEqual(
            generator.observe_overrides(swapped)["operation"],
            "a-minus-b",
        )
        self.assertNotEqual(_independent_rule(grid), _independent_rule(swapped))

    def test_structural_mutations_are_rejected(self):
        grid = generator.generate(
            83,
            101,
            difficulty="hard",
            operation="xor",
            palette_kind="all_distinct",
            panel_h=6,
            panel_w=5,
        )
        width = 5
        panel_starts = [index * (width + 1) for index in range(5)]

        broken_divider = [row[:] for row in grid]
        broken_divider[0][width] = 0

        leaked_divider_color = [row[:] for row in grid]
        leaked_divider_color[0][0] = 9

        multicolor_operand = [row[:] for row in grid]
        first_color = generator.observe_overrides(grid)["op1_color"]
        replacement = 1 if first_color != 1 else 3
        changed = False
        for row in range(len(grid)):
            for col in range(width):
                if multicolor_operand[row][col] != 0:
                    multicolor_operand[row][col] = replacement
                    changed = True
                    break
            if changed:
                break

        empty_demo_result = [row[:] for row in grid]
        for row in range(len(grid)):
            for col in range(panel_starts[2], panel_starts[2] + width):
                empty_demo_result[row][col] = 0

        missing_query_relation = [row[:] for row in grid]
        fourth_start = panel_starts[3]
        fifth_start = panel_starts[4]
        for row in range(len(grid)):
            for col in range(width):
                left_on = grid[row][fourth_start + col] != 0
                right_on = grid[row][fifth_start + col] != 0
                if not left_on and right_on:
                    missing_query_relation[row][fifth_start + col] = 0

        for mutation in (
            broken_divider,
            leaked_divider_color,
            multicolor_operand,
            empty_demo_result,
            missing_query_relation,
            [row[:] for row in grid[:-1]] + [grid[-1][:-1]],
            [],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_invalid_controls_reject_loudly(self):
        invalid_cases = (
            {"panel_h": 2},
            {"panel_h": 7},
            {"panel_w": 2},
            {"panel_w": 6},
            {"operation": "nand"},
            {"op1_color": 0},
            {"op1_color": 9},
            {"palette_kind": "rainbow"},
            {"texture": "warm"},
        )
        for overrides in invalid_cases:
            with self.assertRaises(ValueError, msg=overrides):
                generator.generate(1, 2, **overrides)
        for difficulty in (True, "expert", object()):
            with self.assertRaises(ValueError, msg=repr(difficulty)):
                generator.generate(1, 2, difficulty=difficulty)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        state = random.getstate()
        first = generator.generate(
            107,
            109,
            difficulty="hard",
            operation="b-minus-a",
            palette_kind="query_mixed",
        )
        self.assertEqual(random.getstate(), state)
        snapshot = [row[:] for row in first]
        generator.generate(211, 223, difficulty="easy")
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, snapshot)

        again = generator.generate(
            107,
            109,
            difficulty="hard",
            operation="b-minus-a",
            palette_kind="query_mixed",
        )
        self.assertEqual(first, again)
        self.assertIsNot(first, again)
        self.assertTrue(all(old is not new for old, new in zip(first, again)))
        first[0][0] = 9 if first[0][0] != 9 else 0
        self.assertEqual(
            generator.generate(
                107,
                109,
                difficulty="hard",
                operation="b-minus-a",
                palette_kind="query_mixed",
            ),
            again,
        )


if __name__ == "__main__":
    unittest.main()
