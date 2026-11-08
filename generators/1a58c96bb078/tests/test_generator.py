"""Regression tests for the repaired column-legend-painter sampler."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1a58c96bb078"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"reviewed_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _foreign_body_cells(grid):
    header_colors = {value for value in grid[0] if value != 0}
    return [
        (row, col, value)
        for row, values in enumerate(grid[1:], start=1)
        for col, value in enumerate(values)
        if value not in {0, 8, *header_colors}
    ]


def _inert_eights(grid):
    return [
        (row, col)
        for row, values in enumerate(grid[1:], start=1)
        for col, value in enumerate(values)
        if value == 8 and grid[0][col] == 0
    ]


def test_metadata_and_semantic_contract_are_pinned():
    assert GEN.RULE_HASH == "341c4a414d7c"
    assert GEN.VERSION == "2.0.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_legend_cols",
        "markers_per_col",
        "n_preserved",
        "n_inert_eights",
        "distractor_color",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "preserved_foreign_body",
        "inert_eight_outside_legend",
    }
    assert GEN.WITNESS_RIVALS == {
        "preserved_foreign_body": ["clear_body_then_paint"],
        "inert_eight_outside_legend": ["drop_unmapped_eights"],
    }


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_all_canonical_pairs_are_accepted_and_mirrored(pair):
    original = [row[:] for row in pair["input"]]
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_all_exact_overrides_round_trip_in_every_band(difficulty):
    requested = {
        "grid_h": 7,
        "grid_w": 7,
        "n_legend_cols": 5,
        "markers_per_col": 4,
        "n_preserved": 4,
        "n_inert_eights": 3,
        "distractor_color": 9,
    }
    grid = GEN.generate(917, 11, difficulty=difficulty, **requested)
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": requested}) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.generate(917, 11, difficulty=difficulty, **requested) == grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 6},
        {"grid_w": 17},
        {"n_legend_cols": 0},
        {"n_legend_cols": 6},
        {"markers_per_col": 0},
        {"markers_per_col": 5},
        {"n_preserved": 0},
        {"n_preserved": 5},
        {"n_inert_eights": -1},
        {"n_inert_eights": 4},
        {"distractor_color": 0},
        {"distractor_color": 8},
        {"grid_h": True},
        {"markers_per_col": 2.5},
        {"distractor_color": "6"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


def test_invalid_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="impossible")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_contains_preservation_and_scheduled_inert_witnesses(difficulty):
    grids = [GEN.generate(7000 + index, index, difficulty=difficulty) for index in range(20)]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert all(_foreign_body_cells(grid) for grid in grids)
    assert any(_inert_eights(grid) for grid in grids)
    assert all(GEN.SEMANTIC_WITNESSES["preserved_foreign_body"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["inert_eight_outside_legend"](grid) for grid in grids)
    assert any((len(grid), len(grid[0])) in {(7, 7), (8, 8), (9, 9)} for grid in grids)


def test_every_four_consecutive_pairs_remain_identifying_under_query_rotation():
    for start in range(12):
        pairs = [_pair(GEN.generate(8100 + start, start + offset)) for offset in range(4)]
        for held_out in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert GEN.lesson_identifiable(demos, pairs[held_out]) == []


def test_declared_rivals_are_concrete_and_refuted_by_generated_witnesses():
    drop = GEN.SEMANTIC_RIVALS["drop_unmapped_eights"]
    clear = GEN.SEMANTIC_RIVALS["clear_body_then_paint"]

    # Canonical examples already refute destructive clearing, but contain no
    # unmapped cyan marker and therefore do not refute that narrower shortcut.
    assert any(clear(pair["input"]) != pair["output"] for pair in PAIRS)
    assert all(drop(pair["input"]) == pair["output"] for pair in PAIRS)

    anchor = GEN.generate(93, 0)
    broad = GEN.generate(93, 3)
    assert clear(anchor) != GEN.rule_mirror(anchor)
    assert _inert_eights(broad)
    assert drop(broad) != GEN.rule_mirror(broad)


def test_self_check_rejects_semantically_damaged_inputs():
    base = GEN.generate(33, 3)
    assert GEN.self_check(base) == []

    no_header = [row[:] for row in base]
    no_header[0] = [0] * len(no_header[0])

    no_foreign = [row[:] for row in base]
    for row, col, _ in _foreign_body_cells(no_foreign):
        no_foreign[row][col] = 0

    unequal_marker_counts = [row[:] for row in base]
    active_col = next(col for col, value in enumerate(base[0]) if value != 0)
    marker_row = next(row for row in range(1, len(base)) if base[row][active_col] == 8)
    unequal_marker_counts[marker_row][active_col] = 0

    for damaged in (no_header, no_foreign, unequal_marker_counts):
        assert GEN.self_check(damaged)
