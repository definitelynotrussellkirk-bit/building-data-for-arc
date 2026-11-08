"""Behavioral contract for the normalized-overlap input generator.

The small output oracle below is independent of generator internals.  These
regressions cover the canonical repair; parametric prototypes have separate
tests and never change the selected canonical rule.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

for _ancestor in Path(__file__).resolve().parents:
    _helper_dir = _ancestor / "shared" / "runtime"
    if (_helper_dir / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_helper_dir))
        break
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "659980b6f715"
ROOT = find_root(__file__)
GEN, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")


def normalized_overlap_oracle(grid):
    colors = sorted({v for row in grid for v in row if v != 0})
    assert len(colors) == 2

    def normalized(color):
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        return {(r - r0, c - c0) for r, c in cells}

    low, high = colors
    a, b = normalized(low), normalized(high)
    h = 1 + max(r for r, _ in a | b)
    w = 1 + max(c for _, c in a | b)
    return [
        [9 if (r, c) in a & b else low if (r, c) in a else high if (r, c) in b else 0
         for c in range(w)]
        for r in range(h)
    ]


def components_for_color(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    components = []
    while remaining:
        start = next(iter(remaining))
        pending = [start]
        remaining.remove(start)
        component = {start}
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        components.append(component)
    return components


def test_rule_pin_and_canonical_examples_are_preserved():
    assert GEN.RULE_HASH == "df22257022fe"
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert GEN.self_check(deepcopy(pair["input"])) == []
        assert normalized_overlap_oracle(pair["input"]) == pair["output"]
        assert GEN._predict(deepcopy(pair["input"])) == pair["output"]


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": False}, {"seed": -1}, {"seed": 1.0}, {"seed": "1"},
    {"sample_index": True}, {"sample_index": False}, {"sample_index": -1},
    {"sample_index": 1.0}, {"sample_index": "1"},
    {"difficulty": False}, {"difficulty": 1}, {"difficulty": "unknown"},
])
def test_invalid_draw_identity_is_rejected(kwargs):
    request = {"seed": 0, "sample_index": 0}
    request.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**request)


def test_large_nonnegative_seed_used_by_profile_census_is_supported():
    grid = GEN.generate(104_903_813_062_390, 2426, difficulty="easy")
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("overrides", [
    {"unknown_axis": 1}, {"texture": "no_overlap"},
    {"grid_h": True}, {"grid_h": 7}, {"grid_h": 11}, {"grid_h": 8.0},
    {"grid_w": False}, {"grid_w": 10}, {"grid_w": 14}, {"grid_w": "12"},
    {"low_color_cells": True}, {"low_color_cells": 3}, {"low_color_cells": 9},
    {"high_color_cells": 4.0}, {"high_color_cells": "4"},
    {"row_order": 0}, {"row_order": "side_by_side"},
])
def test_invalid_or_retired_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", BANDS)
def test_every_advertised_joint_override_is_exact_and_observable(band):
    for h in range(8, 11):
        for w in range(11, 14):
            for low_n in range(4, 9):
                for high_n in range(4, 9):
                    for row_order in ("low_above", "high_above"):
                        requested = {
                            "grid_h": h,
                            "grid_w": w,
                            "low_color_cells": low_n,
                            "high_color_cells": high_n,
                            "row_order": row_order,
                        }
                        grid = GEN.generate(19, low_n * 100 + high_n, difficulty=band, **requested)
                        assert GEN.self_check(grid, difficulty=band) == []
                        assert GEN.observe_overrides(grid) == requested
                        assert len(grid) == h and len(grid[0]) == w


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_reserve_overlap_marker_and_have_connected_operands(band):
    seen_shapes = set()
    for index in range(24):
        grid = GEN.generate(911, index, difficulty=band)
        assert GEN.self_check(grid, difficulty=band) == []
        assert 9 not in {v for row in grid for v in row}
        colors = sorted({v for row in grid for v in row if v})
        assert len(colors) == 2
        for color in colors:
            components = components_for_color(grid, color)
            assert len(components) == 1
            assert 4 <= len(components[0]) <= 8
        assert GEN._predict(grid) == normalized_overlap_oracle(grid)
        seen_shapes.add(str(normalized_overlap_oracle(grid)))
    assert len(seen_shapes) >= 8


def test_input_color_nine_collision_is_rejected_regression():
    grid = [[0] * 11 for _ in range(8)]
    for r, c in ((0, 0), (0, 1), (1, 0), (0, 2)):
        grid[r][c] = 2
    for r, c in ((4, 7), (5, 7), (4, 8), (6, 7)):
        grid[r][c] = 9
    errors = GEN.self_check(grid)
    assert errors
    assert any("reserved" in error.lower() or "color 9" in error.lower() for error in errors)


def test_malformed_grids_are_reported_without_crashing():
    bad = [
        None, [], [[]], [[0], [0, 1]], [[False] * 11 for _ in range(8)],
        [[0.0] * 11 for _ in range(8)], [[10] * 11 for _ in range(8)],
        [[0] * 10 for _ in range(8)], [[0] * 11 for _ in range(7)],
    ]
    for grid in bad:
        errors = GEN.self_check(deepcopy(grid))
        assert isinstance(errors, list) and errors


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_hits_only_canonical_dimension_profiles(band):
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs(TASK_ID, root=ROOT)
    }
    profiles = []
    for index in range(20):
        grid = GEN.generate(31, index, difficulty=band)
        profiles.append((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert all(profile in canonical_profiles for profile in profiles)
    assert len(set(profiles)) >= 4


def test_semantic_witnesses_are_live_and_truthful():
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)
    grids = [GEN.generate(707, index, difficulty="hard") for index in range(12)]
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        matching = [grid for grid in grids if witness(deepcopy(grid))]
        assert matching, witness_name
        for grid in matching:
            expected = normalized_overlap_oracle(grid)
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](deepcopy(grid)) != expected
                for rival_name in GEN.WITNESS_RIVALS[witness_name]
            ), witness_name


def test_every_three_demo_window_refutes_declared_lesson_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(1234, index, difficulty=band)
                pairs.append({"input": grid, "output": normalized_overlap_oracle(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
