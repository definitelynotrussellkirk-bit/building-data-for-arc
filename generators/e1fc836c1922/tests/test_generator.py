"""Regression tests for the reviewed e1fc836c1922 generator."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    TASK_ID,
    load_generator,
    malformed_grids,
    mirror_output,
    observed,
    teaching_errors,
    upper_triangle_only,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_is_pinned_to_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == "c0c41dfe5b49"


@pytest.mark.parametrize("pair", PAIRS)
def test_canonical_inputs_are_owned_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert mirror_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_size": 5, "n_marks": 3, "n_colors": 1},
        {"grid_size": 8, "n_marks": 4, "n_colors": 2},
        {"grid_size": 12, "n_marks": 9, "n_colors": 3},
    ],
)
def test_exact_overrides_are_constructive_in_every_band(band, overrides):
    grid = gen.generate(1701, 29, difficulty=band, **overrides)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert observed(grid) == overrides
    assert gen.observe_overrides(grid) == overrides
    assert teaching_errors(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_size": 4},
        {"grid_size": 13},
        {"n_marks": 2},
        {"n_marks": 10},
        {"n_colors": 0},
        {"n_colors": 4},
        {"grid_size": True},
        {"n_marks": 3.0},
        {"n_colors": "2"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_canonical_shortcut_fits_all_demonstrations_but_not_generated_inputs():
    assert all(upper_triangle_only(pair["input"]) == pair["output"] for pair in PAIRS)
    for index in range(64):
        grid = gen.generate(8100 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert teaching_errors(grid) == []
        assert gen.CANONICAL_SHORTCUTS["upper_triangle_only"](grid) == upper_triangle_only(grid)
        assert upper_triangle_only(grid) != mirror_output(grid)


def test_default_distribution_is_deterministic_and_covers_declared_ranges():
    sizes: set[int] = set()
    marks: set[int] = set()
    colors: set[int] = set()
    inputs: set[tuple[tuple[int, ...], ...]] = set()
    for index in range(256):
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(9100 + index, index * 7 + 3, difficulty=band)
        assert grid == gen.generate(9100 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        assert teaching_errors(grid) == []
        stats = observed(grid)
        sizes.add(stats["grid_size"])
        marks.add(stats["n_marks"])
        colors.add(stats["n_colors"])
        inputs.add(tuple(tuple(row) for row in grid))
    assert {5, 6, 7, 8} <= sizes
    assert {3, 9} <= marks
    assert colors == {1, 2, 3}
    assert len(inputs) >= 250


@pytest.mark.parametrize("grid", malformed_grids())
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_semantic_contract_names_a_real_witness_and_rival():
    for index in range(16):
        grid = gen.generate(111 + index, index)
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_WITNESSES["lower_triangle_source"](grid)
        assert gen.SEMANTIC_RIVALS["upper_triangle_only"](grid) != mirror_output(grid)
        assert gen.WITNESS_RIVALS["lower_triangle_source"] == ["upper_triangle_only"]

@pytest.mark.parametrize(
    "grid",
    [
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [7, 7, 0, 7, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 7, 0, 0],
            [0, 0, 7, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 7, 0, 0],
            [0, 0, 0, 0, 0],
        ],
    ],
    ids=["horizontal_short_line", "vertical_short_line"],
)
def test_self_check_rejects_collinear_source_impostors(grid):
    """A valid training input must exercise a two-dimensional placement."""
    assert gen.self_check(grid)


def test_generated_sources_span_multiple_rows_and_columns():
    for index in range(256):
        grid = gen.generate(22000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        coords = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value != 0
        ]
        assert len({row for row, _ in coords}) >= 2
        assert len({col for _, col in coords}) >= 2
