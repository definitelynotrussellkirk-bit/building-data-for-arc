"""Black-box regressions for the row-key/template generator's public contract.

The same file runs in the library and in its relocated task-test runtime.
Canonical data is loaded through the public reviewer helper, never through
fixed-depth paths or a neighboring checkout.
"""

from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path
import sys

import pytest


def _add_local_runtime_to_path():
    for ancestor in Path(__file__).resolve().parents:
        for candidate in (ancestor, ancestor / "shared" / "runtime"):
            if (candidate / "reviewer_support.py").is_file():
                sys.path.insert(0, str(candidate))
                return
    raise ImportError("No local reviewer_support runtime found")


_add_local_runtime_to_path()
from reviewer_support import canonical_pairs, find_root


TASK_ID = "2f58238f8bb6"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path
    for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    if path.is_file()
)
_spec = importlib.util.spec_from_file_location("row_key_contract_generator", GENERATOR_PATH)
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)

DIFFICULTIES = (None, "easy", "medium", "hard")
DOMAINS = {
    "grid_h": range(6, 15),
    "grid_w": range(8, 17),
    "n": range(1, 7),
    "template_color": range(1, 10),
}
BASE_OVERRIDES = {"grid_h": 10, "grid_w": 12, "n": 3, "template_color": 6}


def _assert_generated_contract(grid):
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and row for row in grid)
    height, width = len(grid), len(grid[0])
    assert 6 <= height <= 14
    assert 8 <= width <= 16
    assert all(len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)

    keys = [value for value in grid[0] if value]
    assert 1 <= len(keys) <= 6
    assert set(keys) <= {1, 2, 3, 4}
    assert all(value == 0 for value in grid[1]), "row 1 must separate keys from the body"

    body = {
        (row, column)
        for row in range(2, height)
        for column in range(width)
        if grid[row][column]
    }
    assert 3 <= len(body) <= 12, "the template must contain 3..12 cells"
    colors = {grid[row][column] for row, column in body}
    assert len(colors) == 1, "the template must be monochrome"

    pending = [next(iter(body))]
    reached = set(pending)
    while pending:
        row, column = pending.pop()
        for neighbor in (
            (row - 1, column), (row + 1, column),
            (row, column - 1), (row, column + 1),
        ):
            if neighbor in body and neighbor not in reached:
                reached.add(neighbor)
                pending.append(neighbor)
    assert reached == body, "the body must be one 4-connected component"

    template_height = max(row for row, _ in body) - min(row for row, _ in body) + 1
    template_width = max(column for _, column in body) - min(column for _, column in body) + 1
    assert template_height <= 4
    assert template_width <= 4
    # Only a clockwise rotation swaps dimensions. Every rendered key is
    # separated by exactly one column, regardless of its position in row 0.
    output_height = max(template_width if key == 2 else template_height for key in keys)
    output_width = sum(template_height if key == 2 else template_width for key in keys) + len(keys) - 1
    assert output_height <= 4
    assert output_width <= 29
    assert generator.self_check(grid) == []
    return {"grid_h": height, "grid_w": width, "n": len(keys), "template_color": colors.pop()}


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize(
    "axis,value", [(axis, value) for axis, values in DOMAINS.items() for value in values]
)
def test_each_exact_axis_value_is_available_in_every_difficulty(difficulty, axis, value):
    overrides = {**BASE_OVERRIDES, axis: value}
    grid = generator.generate(73, 5, difficulty=difficulty, **overrides)
    assert _assert_generated_contract(grid) == overrides


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize(
    "height,width,key_count,color", list(product((6, 14), (8, 16), (1, 6), (1, 9)))
)
def test_exact_axis_boundary_cross_products(difficulty, height, width, key_count, color):
    overrides = {"grid_h": height, "grid_w": width, "n": key_count, "template_color": color}
    grid = generator.generate(771, 0, difficulty=difficulty, **overrides)
    assert _assert_generated_contract(grid) == overrides


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("seed", range(48))
def test_default_samples_preserve_input_and_output_envelope(difficulty, seed):
    grid = generator.generate(seed, seed % 3, difficulty=difficulty)
    _assert_generated_contract(grid)


@pytest.mark.parametrize("axis", tuple(DOMAINS))
@pytest.mark.parametrize("kind", ("bool", "float", "fraction", "string", "list"))
def test_exact_integer_axes_reject_type_coercion(axis, kind):
    value = BASE_OVERRIDES[axis]
    invalid = {
        "bool": True,
        "float": float(value),
        "fraction": value + 0.25,
        "string": str(value),
        "list": [value],
    }[kind]
    with pytest.raises((TypeError, ValueError)):
        generator.generate(29, 1, **{axis: invalid})


@pytest.mark.parametrize(
    "axis,value",
    [(axis, value) for axis, values in DOMAINS.items() for value in (min(values) - 1, max(values) + 1)],
)
def test_exact_integer_axes_reject_out_of_domain_values(axis, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(29, 1, **{axis: value})


@pytest.mark.parametrize("axis", ("unknown_axis", "grid_height", "template_colour", "key_count"))
def test_unknown_override_names_are_not_silently_ignored(axis):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(29, 1, **{axis: 3})


def _valid_input():
    grid = [[0] * 8 for _ in range(6)]
    grid[0][0] = 1
    grid[0][4] = 2
    for row, column in ((2, 2), (3, 2), (3, 3)):
        grid[row][column] = 6
    return grid


def _malformed_inputs():
    cases = [
        ("none", None),
        ("empty", []),
        ("empty_rows", [[], []]),
        ("non_grid_integer", 1),
        ("non_grid_string", "bad grid"),
    ]
    for name, row_value in (("ragged", [0] * 7), ("empty_row", []), ("non_row", None), ("string_row", "00000000")):
        grid = _valid_input()
        grid[-1] = row_value
        cases.append((name, grid))
    for location, row, column in (("header", 0, 0), ("body", 2, 2)):
        for name, value in (
            ("bool", True), ("float", 1.0), ("string", "1"),
            ("none", None), ("negative_color", -1), ("color_above_nine", 10),
        ):
            grid = _valid_input()
            grid[row][column] = value
            cases.append((f"{location}_{name}", grid))
    grid = _valid_input()
    grid[0][1] = 5
    cases.append(("unsupported_key_beside_valid_keys", grid))
    grid = _valid_input()
    grid[0] = [0] * 8
    cases.append(("no_header_keys", grid))
    grid = _valid_input()
    grid[1:] = [[0] * 8 for _ in range(5)]
    cases.append(("empty_body", grid))
    grid = _valid_input()
    grid[5][7] = 6
    cases.append(("disconnected_same_color_body", grid))
    grid = _valid_input()
    grid[5][7] = 7
    cases.append(("disconnected_multicolor_body", grid))
    grid = _valid_input()
    grid[3][3] = 7
    cases.append(("connected_multicolor_body", grid))
    grid = _valid_input()
    grid[3][2] = 0
    cases.append(("diagonal_contact_only", grid))
    grid = _valid_input()
    grid[1][2] = 6
    cases.append(("body_in_separator_row", grid))
    return cases


@pytest.mark.parametrize("name,grid", _malformed_inputs(), ids=lambda value: value if isinstance(value, str) else None)
def test_self_check_rejects_malformed_input_without_crashing(name, grid):
    errors = generator.self_check(grid)
    assert isinstance(errors, list), name
    assert errors, name
    assert all(isinstance(error, str) and error for error in errors), name


CANONICAL_PAIRS = canonical_pairs(TASK_ID, root=ROOT)


@pytest.mark.parametrize(
    "pair", CANONICAL_PAIRS,
    ids=[f"variant-{pair['variant']}-{pair['split']}-{pair['pair_index']}" for pair in CANONICAL_PAIRS],
)
def test_self_check_accepts_every_canonical_input(pair):
    assert generator.self_check(pair["input"]) == []


def test_self_check_accepts_a_valid_monochrome_connected_template():
    assert generator.self_check(_valid_input()) == []
