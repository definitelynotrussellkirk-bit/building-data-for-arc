"""Task-local regression tests for the repaired ff973026bfbe sampler."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    all_red_columns,
    canonical_pairs,
    changed_cells,
    intended_output,
    left_border_rows_only,
    load_generator,
    observed,
    off_border_witness,
    off_top_red_witness,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(7, 9), (7, 10), (8, 9), (8, 11), (9, 8)}


def test_canonical_pairs_are_accepted_and_oracle_matches_labels():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_all_exact_overrides_are_observable_in_every_band(band):
    options = {
        "grid_h": 7,
        "grid_w": 8,
        "n_row_marks": 5,
        "n_col_marks": 5,
        "n_red_decoys": 2,
        "n_neutral": 3,
        "row_marker_mode": "scattered",
        "distractor_color": 9,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "override",
    [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_w": 15},
        {"n_row_marks": 0},
        {"n_col_marks": 6},
        {"n_red_decoys": 3},
        {"n_neutral": 0},
        {"row_marker_mode": "mixed"},
        {"distractor_color": 3},
        {"grid_h": True},
        {"n_neutral": 1.5},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(override):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_has_canonical_profiles_palette_and_both_shortcut_witnesses(band):
    grids = [gen.generate(900 + i, i, difficulty=band) for i in range(20)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(len({value for row in grid for value in row}) == 4 for grid in grids)
    assert any((len(grid), len(grid[0])) in CANONICAL_PROFILES for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["off_border_row_marker"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["off_top_red_decoy"](grid) for grid in grids)


def test_every_four_pair_window_remains_identifying_after_any_query_rotation():
    for start in range(12):
        grids = [gen.generate(1200 + start, start + offset) for offset in range(4)]
        for held_out in range(4):
            demos = [grid for index, grid in enumerate(grids) if index != held_out]
            assert any(gen.SEMANTIC_WITNESSES["off_border_row_marker"](g) for g in demos)
            assert any(gen.SEMANTIC_WITNESSES["off_top_red_decoy"](g) for g in demos)


def test_declared_shortcuts_fit_canonical_but_exact_witnesses_refute_them():
    pairs = canonical_pairs()
    assert all(left_border_rows_only(p["input"]) == p["output"] for p in pairs)
    assert all(all_red_columns(p["input"]) == p["output"] for p in pairs)

    off_border = off_border_witness()
    intended = intended_output(off_border)
    rival = left_border_rows_only(off_border)
    assert changed_cells(intended, rival) == [
        (2, 2, 3, 0),
        (2, 5, 3, 0),
    ]

    off_top = off_top_red_witness()
    intended = intended_output(off_top)
    rival = all_red_columns(off_top)
    assert changed_cells(intended, rival) == [(2, 5, 0, 3)]


def test_semantic_declarations_name_executable_counterexamples():
    assert set(gen.SEMANTIC_WITNESSES) == {"off_border_row_marker", "off_top_red_decoy"}
    assert set(gen.SEMANTIC_RIVALS) == {"left_border_rows_only", "all_red_columns"}
    assert gen.WITNESS_RIVALS == {
        "off_border_row_marker": ["left_border_rows_only"],
        "off_top_red_decoy": ["all_red_columns"],
    }
    for name in gen.SEMANTIC_RIVALS:
        assert name in gen.CANONICAL_SHORTCUTS
        assert name in gen.LESSON_COMPETITORS


def test_self_check_rejects_semantically_damaged_inputs():
    base = gen.generate(
        4,
        2,
        grid_h=8,
        grid_w=9,
        n_row_marks=2,
        n_col_marks=2,
        n_red_decoys=1,
        n_neutral=1,
        row_marker_mode="scattered",
        distractor_color=4,
    )
    assert gen.self_check(base) == []

    mutations = []
    no_blue = [row[:] for row in base]
    for row in no_blue:
        for c, value in enumerate(row):
            if value == 1:
                row[c] = 0
    mutations.append(no_blue)

    no_top_red = [row[:] for row in base]
    no_top_red[0] = [0 if value == 2 else value for value in no_top_red[0]]
    mutations.append(no_top_red)

    output_color_in_input = [row[:] for row in base]
    output_color_in_input[-1][-1] = 3
    mutations.append(output_color_in_input)

    for damaged in mutations:
        assert gen.self_check(damaged)


def test_generation_is_deterministic_and_python_oracle_is_pure():
    for band in (None, "easy", "medium", "hard"):
        grid = gen.generate(412, 11, difficulty=band)
        assert grid == gen.generate(412, 11, difficulty=band)
        before = [row[:] for row in grid]
        intended_output(grid)
        assert grid == before
