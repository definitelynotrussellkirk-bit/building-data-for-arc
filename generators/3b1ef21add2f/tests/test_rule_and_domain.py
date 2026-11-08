"""Canonical, total-rule, and selected teaching-domain regressions.

The rule is total on rectangular digit grids. The input self-check intentionally
selects contrastful teaching scenes, so valid rule inputs need not pass it.
"""
from copy import deepcopy

import pytest

from oracle_3b1ef21add2f import red_windows, solve


def test_oracle_matches_every_canonical_pair(canonical):
    assert canonical
    assert {pair["split"] for pair in canonical} == {"train", "test"}
    for pair in canonical:
        before = deepcopy(pair["input"])
        assert solve(pair["input"]) == pair["output"], (
            pair["variant"], pair["split"], pair["pair_index"])
        assert pair["input"] == before


@pytest.mark.parametrize("grid, expected, count", [
    ([[2, 2, 2], [2, 2, 2]], [[3, 3, 3], [3, 3, 3]], 2),
    ([[2, 2], [2, 2], [2, 2]], [[3, 3], [3, 3], [3, 3]], 2),
    ([[2, 2, 2], [2, 2, 2], [2, 2, 2]],
     [[3, 3, 3], [3, 3, 3], [3, 3, 3]], 4),
    ([[2, 2, 2], [2, 2, 0]], [[3, 3, 2], [3, 3, 0]], 1),
    ([[2, 2, 0], [2, 2, 2], [0, 2, 2]],
     [[3, 3, 0], [3, 3, 3], [0, 3, 3]], 2),
    ([[4, 4, 3], [4, 4, 2]], [[4, 4, 3], [4, 4, 2]], 0),
], ids=["horizontal-overlap", "vertical-overlap", "dense-overlap",
        "attached-tail", "one-cell-overlap", "other-colors-preserved"])
def test_literal_oracle_witnesses(grid, expected, count):
    before = deepcopy(grid)
    output = solve(grid)
    assert output == expected
    assert len(red_windows(grid)) == count
    assert grid == before
    assert output is not grid
    assert all(new is not old for new, old in zip(output, grid))


VALID_GRIDS = [
    [[0]], [[2]], [[3]], [[0, 2, 0]], [[2], [0], [2]],
    [[2, 2], [2, 0]], [[2, 2], [2, 2]], [[4, 4], [4, 4]],
    [list(range(10))], [[2, 2, 2], [2, 2, 2]],
    [[2, 2, 2], [2, 2, 0]], [[3, 2, 0], [2, 9, 1]],
]


@pytest.mark.parametrize("grid", [
    [[2, 0, 2]], [[2], [0], [2]],
    [[2, 2, 0, 2], [2, 2, 0, 0]],
    [[2, 2, 0, 2, 2], [2, 0, 0, 0, 2]],
    [[2, 2, 2, 0, 2], [2, 2, 0, 0, 0]],
    [[2, 2, 2, 0, 2], [2, 2, 2, 0, 0]],
    [[2, 2, 0, 3], [2, 2, 0, 2]], [[1, 2, 0], [4, 0, 2]],
], ids=["separate-singletons-row", "separate-singletons-column",
        "square-plus-singleton", "two-incomplete-components",
        "square-tail-plus-singleton", "overlap-plus-singleton",
        "input-green-preserved", "colored-distractors"])
def test_self_check_accepts_contrastful_teaching_inputs_without_mutation(generator, grid):
    before = deepcopy(grid)
    assert generator.self_check(grid) == []
    assert grid == before


@pytest.mark.parametrize("grid", [
    [[0]], [[2]], [[2, 2], [2, 2]], [[2, 2, 2]],
    [[3, 0], [0, 3]], [[2, 2, 2], [2, 2, 0]],
    [[2, 2, 0, 2, 2], [2, 2, 0, 2, 2]],
    [[2, 3, 2]], [[2, 0, 2] + [0] * 28],
    [[2]] + [[0]] * 29 + [[2]],
], ids=["blank", "singleton", "solid-square", "single-component-line",
        "no-red", "one-attached-component", "two-squares-with-no-surviving-red",
        "no-zero-background", "too-wide", "too-high"])
def test_self_check_rejects_outside_selected_teaching_grammar(generator, grid):
    errors = generator.self_check(grid)
    assert isinstance(errors, list)
    assert errors and all(isinstance(error, str) and error for error in errors)


@pytest.mark.parametrize("grid", [
    None, 0, 2.0, True, "22", (), [], [[]], [()], [None], [2],
    [[2, 2], [2]], [[True]], [[False]], [[2.0]], [["2"]],
    [[None]], [[-1]], [[10]], [[float("nan")]], [[float("inf")]],
    [[[2]]], [[1 + 2j]],
], ids=["none", "integer", "float", "bool", "string", "tuple", "empty",
        "empty-row", "tuple-row", "none-row", "integer-row", "ragged",
        "bool-pixel-true", "bool-pixel-false", "float-pixel", "string-pixel",
        "none-pixel", "negative-pixel", "large-pixel", "nan-pixel",
        "infinite-pixel", "list-pixel", "complex-pixel"])
def test_self_check_reports_malformed_input_instead_of_raising(generator, grid):
    errors = generator.self_check(grid)
    assert isinstance(errors, list)
    assert errors and all(isinstance(error, str) and error for error in errors)


def test_canonical_inputs_are_in_teaching_domain(generator, canonical):
    for pair in canonical:
        assert generator.self_check(pair["input"]) == []


def test_public_reference_matches_immutable_oracle(library_root, canonical):
    from arcpuzzles import Catalog

    inputs = [pair["input"] for pair in canonical] + VALID_GRIDS + [
        [[2, 2, 2], [2, 2, 2]],
        [[2, 2, 2], [2, 2, 0]],
        [[2, 2, 0], [2, 2, 2], [0, 2, 2]],
        [[4, 4, 3], [4, 4, 2]],
        [[2]], [[2, 2, 2]], [[2], [2], [2]],
    ]
    before = deepcopy(inputs)
    applied = Catalog(library_root).apply("3b1ef21add2f", inputs, timeout=120)
    assert applied["rule_hash_matches_catalog"] is True
    assert len(applied["results"]) == len(inputs)
    assert [row["output"] for row in applied["results"]] == [solve(grid) for grid in inputs]
    assert inputs == before
