from __future__ import annotations

import importlib
import random
from collections import defaultdict

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "80bd3177b03c"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BIASES = ("horizontal_row_pairs", "vertical_column_pairs", "mixed_pairs")


def points_by_color(grid):
    result = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                result[value].append((row, col))
    return dict(result)


def orientation_counts(grid):
    counts = {"horizontal": 0, "vertical": 0, "other": 0}
    for points in points_by_color(grid).values():
        if len(points) != 2:
            counts["other"] += 1
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            counts["horizontal"] += 1
        elif c1 == c2:
            counts["vertical"] += 1
        else:
            counts["other"] += 1
    return counts


def independent_rule(grid):
    output = [row[:] for row in grid]
    for color, points in points_by_color(grid).items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(points)
        if r1 == r2:
            cells = [(r1, col) for col in range(min(c1, c2), max(c1, c2) + 1)]
        elif c1 == c2:
            cells = [(row, c1) for row in range(min(r1, r2), max(r1, r2) + 1)]
        else:
            continue
        if all((row, col) in points or grid[row][col] == 0 for row, col in cells):
            for row, col in cells:
                output[row][col] = color
    return output


def test_canonical_pairs_match_exact_rule_mirror():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert MODULE.rule_mirror(pair["input"]) == independent_rule(pair["input"]) == pair["output"]


@pytest.mark.parametrize("bias", BIASES)
def test_explicit_position_bias_is_exact_observable_and_rule_valid(bias):
    for seed in range(8):
        grid = MODULE.generate(
            20_000 + seed,
            seed * 17,
            grid_h=12,
            grid_w=12,
            n_pairs=5,
            position_bias=bias,
        )
        counts = orientation_counts(grid)
        assert counts["other"] == 0
        if bias == "horizontal_row_pairs":
            assert counts == {"horizontal": 5, "vertical": 0, "other": 0}
        elif bias == "vertical_column_pairs":
            assert counts == {"horizontal": 0, "vertical": 5, "other": 0}
        else:
            assert counts["horizontal"] >= 1 and counts["vertical"] >= 1
            assert counts["horizontal"] + counts["vertical"] == 5
        assert MODULE.observe_overrides(grid) == {"position_bias": bias, "n_pairs": 5}
        assert MODULE.self_check(grid) == []
        assert MODULE.rule_mirror(grid) == independent_rule(grid)


def test_default_three_example_schedule_teaches_horizontal_vertical_and_mixed():
    observed = []
    for sample_index in range(3):
        grid = MODULE.generate(8123, sample_index, grid_h=12, grid_w=12, n_pairs=4)
        observed.append(MODULE.observe_overrides(grid)["position_bias"])
    assert observed == list(BIASES)


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(9163)
    state = random.getstate()
    first = MODULE.generate(31, 2, position_bias="mixed_pairs")
    assert random.getstate() == state
    second = MODULE.generate(31, 2, position_bias="mixed_pairs")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(31, 2, position_bias="mixed_pairs") == second


def test_axis_contract_advertises_the_three_position_families():
    assert MODULE.AXES["position_bias"]["valid"].split("|") == list(BIASES)
    assert MODULE.AXES["n_pairs"]["valid"] == "2..8"
    assert MODULE.EXAMPLES_NEEDED >= 3


@pytest.mark.parametrize(
    "kwargs",
    [
        {"position_bias": "diagonal_pairs"},
        {"position_bias": "mixed_pairs", "n_pairs": 1},
        {"unknown_control": 3},
    ],
)
def test_invalid_or_unknown_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(1, 0, **kwargs)


def test_self_check_rejects_reused_vertical_column():
    grid = [[0] * 8 for _ in range(10)]
    grid[0][3] = grid[3][3] = 1
    grid[6][3] = grid[9][3] = 2
    assert "active column reused by more than one pair" in MODULE.self_check(grid)
