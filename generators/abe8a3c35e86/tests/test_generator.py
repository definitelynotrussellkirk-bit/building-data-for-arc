"""Task-local contract tests for the hinge-reflection sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (canonical_output, canonical_pairs, classify_layout,
                             load_generator, row_priority_output)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
LAYOUTS = (
    "left", "right", "above", "below",
    "upper_left", "upper_right", "lower_left", "lower_right",
)


def test_canonical_inputs_are_accepted_and_oracle_matches_labels():
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert canonical_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("layout", LAYOUTS)
def test_every_exact_control_is_realized_in_every_band(band, layout):
    requested = {
        "grid_h": 7,
        "grid_w": 7,
        "motif_size": 5,
        "motif_color": 8,
        "layout": layout,
    }
    grid = gen.generate(17, 29, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert classify_layout(grid) == layout
    assert canonical_output(grid) != grid


@pytest.mark.parametrize("key,value", [
    ("unknown", 1),
    ("grid_h", 6), ("grid_h", 15), ("grid_h", True),
    ("grid_w", 6), ("grid_w", 15), ("grid_w", 7.0),
    ("motif_size", 2), ("motif_size", 6), ("motif_size", "3"),
    ("motif_color", 0), ("motif_color", 9), ("motif_color", False),
    ("layout", "diagonal"), ("layout", 1),
])
def test_invalid_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_default_schedule_has_canonical_profiles_and_all_required_witnesses():
    for band in (None, "easy", "medium", "hard"):
        grids = [gen.generate(2100 + i, i, difficulty=band) for i in range(20)]
        observed = [gen.observe_overrides(grid) for grid in grids]
        assert any((item["grid_h"], item["grid_w"]) == (7, 7) for item in observed)
        assert any(item["layout"] in {"above", "below"} for item in observed)
        assert any("_" in item["layout"] for item in observed)
        assert all(gen.self_check(grid) == [] for grid in grids)


def test_every_five_pair_lesson_and_rotation_distinguishes_declared_rivals():
    for start in range(20):
        pairs = []
        for index in range(start, start + 5):
            grid = gen.generate(8000 + start, index, difficulty="medium")
            pairs.append({"input": grid, "output": canonical_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []


def test_row_priority_shortcut_fits_canonical_but_generated_witness_refutes_it():
    assert all(row_priority_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witnesses = []
    for index in range(20):
        grid = gen.generate(91, index)
        if gen.SEMANTIC_WITNESSES["column_priority_when_both"](grid):
            witnesses.append(grid)
    assert witnesses
    for grid in witnesses:
        assert gen.SEMANTIC_RIVALS["row_priority_when_both"](grid) == row_priority_output(grid)
        assert row_priority_output(grid) != canonical_output(grid)


def test_generation_is_deterministic_and_does_not_mutate_inputs():
    first = gen.generate(412, 111, difficulty="hard")
    assert first == gen.generate(412, 111, difficulty="hard")
    original = deepcopy(first)
    canonical_output(first)
    assert first == original


@pytest.mark.parametrize("mutation", ["extra_anchor", "erase_anchor", "split_color", "erase_motif", "disconnect"])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(4, 2, grid_h=7, grid_w=7, motif_size=5,
                        motif_color=4, layout="upper_left")
    motif = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 9)]
    anchor = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9)
    if mutation == "extra_anchor":
        grid[0][6] = 9
    elif mutation == "erase_anchor":
        grid[anchor[0]][anchor[1]] = 0
    elif mutation == "split_color":
        r, c = motif[0]
        grid[r][c] = 5
    elif mutation == "erase_motif":
        for r, c in motif:
            grid[r][c] = 0
    elif mutation == "disconnect":
        for r, c in motif:
            grid[r][c] = 0
        grid[0][0] = grid[0][1] = grid[6][6] = 4
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(7)]])
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_default_schedule_anchors_canonical_7x7_profile_above_warning_floor():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(31_000 + index, index, difficulty=band) for index in range(40)]
        exact = sum(len(grid) == 7 and len(grid[0]) == 7 for grid in grids)
        assert exact >= 10, f"{band}: only {exact}/40 canonical-size draws"
