"""Portable regressions for the axis-chosen reflection generator."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

TASK_ID = "aeb31f908966"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
from reference_probe import (  # noqa: E402
    has_left_axis,
    has_negative_side_source,
    has_occupied_target,
    has_out_of_bounds_target,
    has_positive_side_source,
    has_top_axis,
    horizontal_axis_only,
    identity,
    load_generator,
    negative_side_only,
    observed,
    overwrite_occupied,
    positive_side_only,
    profile,
    rule_output,
    vertical_axis_only,
    wrap_out_of_bounds,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
CANONICAL_PROFILES = {profile(pair["input"]) for pair in PAIRS}


def labeled(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": rule_output(grid)}


def test_metadata_pins_authority_and_keeps_only_exact_observable_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "efb0a4280598"
    assert gen.VERSION == "4.0.0"
    assert gen.EXAMPLES_NEEDED == 5
    assert gen.LESSON_SCHEDULE_PERIOD == 6
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "orientation",
        "shape_side",
        "n_5cells",
        "edge_case",
    }
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    frozen = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == frozen


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 10,
            "grid_w": 12,
            "orientation": "top",
            "shape_side": "negative",
            "n_5cells": 3,
            "edge_case": "clean",
        },
        {
            "grid_h": 12,
            "grid_w": 10,
            "orientation": "left",
            "shape_side": "positive",
            "n_5cells": 8,
            "edge_case": "occupied",
        },
        {
            "grid_h": 16,
            "grid_w": 16,
            "orientation": "top",
            "shape_side": "positive",
            "n_5cells": 5,
            "edge_case": "out_of_bounds",
        },
    ],
)
def test_exact_overrides_are_constructive_observable_and_band_independent(band, requested):
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert observed(grid) == requested
    assert rule_output(grid) != grid


@pytest.mark.parametrize(
    "seed,index",
    [
        (True, 0), (0.0, 0), ("0", 0), (-1, 0),
        (0, True), (0, 0.0), (0, "0"), (0, -1),
    ],
)
def test_invalid_seed_and_sample_index_fail_loudly(seed, index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, index)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 9}, {"grid_h": 17}, {"grid_h": True}, {"grid_h": 12.0},
        {"grid_w": 9}, {"grid_w": 17}, {"grid_w": False}, {"grid_w": "12"},
        {"orientation": "vertical"}, {"orientation": 1},
        {"shape_side": "left"}, {"shape_side": False},
        {"n_5cells": 2}, {"n_5cells": 9}, {"n_5cells": True}, {"n_5cells": 4.0},
        {"edge_case": "target_occupied"}, {"edge_case": 1},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_six_consecutive_pairs_cover_the_complete_teaching_schedule(band):
    seen_profiles = set()
    for start in range(18):
        cycle = [gen.generate(900 + start, start + offset, difficulty=band) for offset in range(6)]
        states = [observed(grid) for grid in cycle]
        seen_profiles.update(profile(grid) for grid in cycle)
        assert {state["orientation"] for state in states} == {"top", "left"}
        assert {state["shape_side"] for state in states} == {"negative", "positive"}
        assert {state["edge_case"] for state in states} == {"clean", "occupied", "out_of_bounds"}
        assert sum(state["edge_case"] == "occupied" for state in states) == 2
        assert sum(state["edge_case"] == "out_of_bounds" for state in states) == 2
        assert all(gen.self_check(grid) == [] for grid in cycle)
        assert all(rule_output(grid) != grid for grid in cycle)
    assert seen_profiles == CANONICAL_PROFILES
    assert set(gen.SCHEDULE_PROFILES) == {
        gen.schedule_profile(0, index, band) for index in range(gen.LESSON_SCHEDULE_PERIOD)
    }


def test_declared_shortcuts_fit_canonical_labels_and_fixed_counterexamples_refute_them():
    assert all(overwrite_occupied(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(wrap_out_of_bounds(pair["input"]) == pair["output"] for pair in PAIRS)

    occupied = json.loads((HOME / "counterexamples" / "occupied-target.json").read_text())
    occupied_grid = occupied["input"]
    assert gen.self_check(occupied_grid) == []
    assert rule_output(occupied_grid) == occupied["intended_output"]
    assert overwrite_occupied(occupied_grid) == occupied["overwrite_occupied_output"]
    assert rule_output(occupied_grid) != overwrite_occupied(occupied_grid)
    assert gen.CANONICAL_SHORTCUTS["overwrite_occupied"](occupied_grid) == overwrite_occupied(occupied_grid)
    assert gen.SEMANTIC_WITNESSES["occupied_target"](occupied_grid)

    out_of_bounds = json.loads((HOME / "counterexamples" / "out-of-bounds-wrap.json").read_text())
    oob_grid = out_of_bounds["input"]
    assert gen.self_check(oob_grid) == []
    assert rule_output(oob_grid) == out_of_bounds["intended_output"]
    assert wrap_out_of_bounds(oob_grid) == out_of_bounds["wrap_out_of_bounds_output"]
    assert rule_output(oob_grid) != wrap_out_of_bounds(oob_grid)
    assert gen.CANONICAL_SHORTCUTS["wrap_out_of_bounds"](oob_grid) == wrap_out_of_bounds(oob_grid)
    assert gen.SEMANTIC_WITNESSES["out_of_bounds_target"](oob_grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_six_pair_lesson_and_query_rotation_identifies_rule(band):
    for start in range(24):
        pairs = [
            labeled(gen.generate(1300 + start, start + offset, difficulty=band))
            for offset in range(6)
        ]
        for held_out in range(6):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert gen.lesson_identifiable(demos, pairs[held_out]) == []


def test_schedule_witnesses_refute_every_named_lesson_competitor():
    grids = [gen.generate(747, index) for index in range(6)]
    assert any(has_occupied_target(grid) for grid in grids)
    assert any(has_out_of_bounds_target(grid) for grid in grids)
    assert any(has_negative_side_source(grid) for grid in grids)
    assert any(has_positive_side_source(grid) for grid in grids)
    assert any(has_top_axis(grid) for grid in grids)
    assert any(has_left_axis(grid) for grid in grids)
    expected = [rule_output(grid) for grid in grids]
    independent_competitors = {
        "overwrite_occupied": overwrite_occupied,
        "wrap_out_of_bounds": wrap_out_of_bounds,
        "negative_side_only": negative_side_only,
        "positive_side_only": positive_side_only,
        "vertical_axis_only": vertical_axis_only,
        "horizontal_axis_only": horizontal_axis_only,
        "identity": identity,
    }
    for name, rival in independent_competitors.items():
        assert any(rival(grid) != output for grid, output in zip(grids, expected)), name
        assert name in gen.LESSON_COMPETITORS


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_marker",
        "extra_marker",
        "corner_marker",
        "axis_five",
        "too_few_fives",
        "too_many_fives",
        "identity_only",
        "bad_color",
        "ragged",
        "bool_cell",
    ],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(41, 0, edge_case="clean", n_5cells=4)
    state = observed(grid)
    marker = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    fives = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if mutation == "missing_marker":
        grid[marker[0]][marker[1]] = 0
    elif mutation == "extra_marker":
        candidates = ([(0, col) for col in range(len(grid[0]))] +
                      [(row, 0) for row in range(1, len(grid))])
        extra = next((point for point in candidates if point != marker and grid[point[0]][point[1]] == 0), None)
        assert extra is not None
        grid[extra[0]][extra[1]] = 2
    elif mutation == "corner_marker":
        grid[marker[0]][marker[1]] = 0
        grid[0][0] = 2
    elif mutation == "axis_five":
        if state["orientation"] == "top":
            grid[1][marker[1]] = 5
        else:
            grid[marker[0]][1] = 5
    elif mutation == "too_few_fives":
        for row, col in fives[2:]:
            grid[row][col] = 0
    elif mutation == "too_many_fives":
        placed = 0
        for row in range(len(grid) - 1, 0, -1):
            for col in range(len(grid[0]) - 1, -1, -1):
                if grid[row][col] == 0:
                    grid[row][col] = 5
                    placed += 1
                    if placed == 5:
                        break
            if placed == 5:
                break
    elif mutation == "identity_only":
        for row, col in fives:
            grid[row][col] = 0
        if state["orientation"] == "top":
            axis = marker[1]
            for row in (2, 3):
                grid[row][axis - 1] = 5
                grid[row][axis + 1] = 5
        else:
            axis = marker[0]
            for col in (2, 3):
                grid[axis - 1][col] = 5
                grid[axis + 1][col] = 5
    elif mutation == "bad_color":
        grid[-1][-1] = 9
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "bool_cell":
        grid[-1][-1] = True
    assert gen.self_check(grid)


def test_generation_is_deterministic_hashseed_independent_and_helpers_do_not_mutate_inputs():
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = gen.generate(8128, index, difficulty=band)
            assert first == gen.generate(8128, index, difficulty=band)
            frozen = deepcopy(first)
            assert gen.observe_overrides(first) == observed(first)
            _ = rule_output(first)
            _ = gen.strict_canonical_like(first)
            for rival in gen.LESSON_COMPETITORS.values():
                _ = rival(first)
            assert first == frozen


def test_every_generated_output_retains_background_and_adds_orange():
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            output = rule_output(gen.generate(71, index, difficulty=band))
            assert any(value == 0 for row in output for value in row)
            assert any(value == 7 for row in output for value in row)
