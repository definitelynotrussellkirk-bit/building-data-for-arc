from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.6c94243d2258.generator")
TASK_ID = "6c94243d2258"


def _lesson(seed: int, start: int, difficulty: str = "medium"):
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    return pairs[: gen.EXAMPLES_NEEDED], pairs[-1]


def _find_isolated_zero(grid: list[list[int]]) -> tuple[int, int]:
    for r in range(2, len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != 0:
                continue
            neighbors = []
            for dr, dc in gen._CARDINAL:
                rr, cc = r + dr, c + dc
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    neighbors.append(grid[rr][cc])
            if all(value != 2 for value in neighbors):
                return r, c
    raise AssertionError("no isolated zero available")


def test_rule_pin_and_every_canonical_pair_are_exact():
    assert gen.RULE_HASH == "9a3732447464"
    assert gen.VERSION == "3.0.0"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original
        assert {value for row in pair["output"] for value in row} <= {0, 8}


def test_every_sliding_schedule_window_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos, query = _lesson(1729 + start, start, difficulty)
            assert gen.lesson_identifiable(demos, query) == []
            observed = [gen.observe_overrides(pair["input"]) for pair in demos]
            assert {item["transform_key"] for item in observed} == {1, 2, 3, 4}
            assert {item["operation_key"] for item in observed} == {6, 7, 8}


def test_override_boundaries_are_exact_and_unknown_axes_reject():
    boundary_cases = {
        "grid_h": (9, 15),
        "grid_w": (13, 22),
        "transform_key": (1, 4),
        "operation_key": (6, 8),
        "shape_cells": (4, 8),
        "gap": (2, 4),
    }
    for difficulty in ("easy", "medium", "hard"):
        for axis, values in boundary_cases.items():
            for offset, value in enumerate(values):
                grid = gen.generate(
                    9000 + offset,
                    17 + offset,
                    difficulty=difficulty,
                    **{axis: value},
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid)[axis] == value

    exact = {
        "grid_h": 15,
        "grid_w": 22,
        "transform_key": 4,
        "operation_key": 7,
        "shape_cells": 8,
        "gap": 4,
    }
    grid = gen.generate(20260727, 11, difficulty="hard", **exact)
    assert gen.observe_overrides(grid) == exact
    assert {value for row in gen.rule_mirror(grid) for value in row} <= {0, 8}

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_structural_self_check_rejects_targeted_impostors():
    valid = gen.generate(
        314159,
        7,
        difficulty="medium",
        grid_h=15,
        grid_w=22,
        transform_key=4,
        operation_key=8,
        shape_cells=6,
        gap=4,
    )
    facts = gen._analysis(valid)
    assert facts["errors"] == []

    missing_operation_key = copy.deepcopy(valid)
    missing_operation_key[0][facts["operation_col"]] = 0

    reversed_key_order = copy.deepcopy(valid)
    tk_col, op_col = facts["transform_col"], facts["operation_col"]
    reversed_key_order[0][tk_col], reversed_key_order[0][op_col] = (
        reversed_key_order[0][op_col],
        reversed_key_order[0][tk_col],
    )

    disconnected_red = copy.deepcopy(valid)
    rr, cc = _find_isolated_zero(disconnected_red)
    disconnected_red[rr][cc] = 2

    illegal_body_color = copy.deepcopy(valid)
    rr, cc = _find_isolated_zero(illegal_body_color)
    illegal_body_color[rr][cc] = 9

    destroyed_separator = copy.deepcopy(valid)
    destroyed_separator[1][0] = 2

    fixtures = {
        "missing_operation_key": missing_operation_key,
        "reversed_key_order": reversed_key_order,
        "disconnected_red": disconnected_red,
        "illegal_body_color": illegal_body_color,
        "destroyed_separator": destroyed_separator,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(12345, 67, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(12345, 67, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second
