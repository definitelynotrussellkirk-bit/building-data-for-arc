"""Regression tests for the 38200022d1b7 point-reflection repair."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "38200022d1b7"
TASK_HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", TASK_HOME / "generator.py")
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

PROFILES = (
    "canonical_two_blobs",
    "quadrant_blob",
    "axis_mix",
    "multi_quadrant",
)


def intended_output(grid):
    """Independent row-major mirror of the selected Racket authority."""
    out = copy.deepcopy(grid)
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not anchors:
        raise ValueError("missing color-5 pivot")
    pr, pc = anchors[0]
    height, width = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5):
                continue
            rr, cc = 2 * pr - r, 2 * pc - c
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value
    return out


def components(cells):
    remaining = set(cells)
    groups = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        group = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    group.add(nxt)
                    stack.append(nxt)
        groups.append(group)
    return groups


def test_rule_pin_and_exact_axis_contract():
    assert GEN.RULE_HASH == "514de6262239"
    assert GEN.EXAMPLES_NEEDED == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == PROFILES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "pivot_dr",
        "pivot_dc",
        "n_cells",
        "n_colors",
        "layout_profile",
    }


def test_canonical_inputs_are_owned_and_independent_oracle_matches_answers():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert intended_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 9,
            "grid_w": 9,
            "pivot_dr": -1,
            "pivot_dc": -1,
            "n_cells": 4,
            "n_colors": 2,
            "layout_profile": "canonical_two_blobs",
        },
        {
            "grid_h": 13,
            "grid_w": 9,
            "pivot_dr": 1,
            "pivot_dc": 1,
            "n_cells": 8,
            "n_colors": 3,
            "layout_profile": "quadrant_blob",
        },
        {
            "grid_h": 9,
            "grid_w": 13,
            "pivot_dr": -1,
            "pivot_dc": 1,
            "n_cells": 8,
            "n_colors": 2,
            "layout_profile": "axis_mix",
        },
        {
            "grid_h": 13,
            "grid_w": 13,
            "pivot_dr": 1,
            "pivot_dc": -1,
            "n_cells": 8,
            "n_colors": 3,
            "layout_profile": "multi_quadrant",
        },
    ],
)
def test_joint_exact_overrides_are_constructive_and_observable(band, requested):
    grid = GEN.generate(901, 7, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert intended_output(grid) != grid


def test_unknown_and_invalid_controls_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 1, difficulty="impossible")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, grid_h=True)


def test_every_five_pair_window_is_rotation_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for sample_index in range(start, start + 5):
                grid = GEN.generate(7000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_declared_canonical_shortcuts_fit_public_pairs_and_have_counterexamples():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {"grid_center", "above_only"}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(
            shortcut(GEN.generate(123, index, difficulty=band))
            != intended_output(GEN.generate(123, index, difficulty=band))
            for band in ("easy", "medium", "hard")
            for index in range(8)
        ), name


def test_default_schedule_covers_profiles_witnesses_and_canonical_morphology():
    expected_profiles = set(PROFILES)
    strict_counts = {}
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(411, index, difficulty=band) for index in range(60)]
        strict = [grid for grid in grids if GEN.strict_canonical_like(grid) == []]
        strict_counts[band] = len(strict)
        assert len(strict) >= 12
        assert {GEN.observe_overrides(grid)["layout_profile"] for grid in grids} == expected_profiles
        assert all(GEN.self_check(grid) == [] for grid in grids)
        for grid in strict:
            cells = [
                (r, c)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value not in (0, 5)
            ]
            assert len(cells) in (5, 7)
            assert len(components(cells)) == 2
    assert all(count >= 12 for count in strict_counts.values())

    for start in range(8):
        lesson_grids = [GEN.generate(520 + start, index, difficulty="medium") for index in range(start, start + 4)]
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in lesson_grids), (start, name)


def test_self_check_rejects_targeted_malformed_inputs():
    valid = GEN.generate(13, 0, difficulty="easy")
    assert GEN.self_check(valid) == []

    no_pivot = copy.deepcopy(valid)
    for row in no_pivot:
        for c, value in enumerate(row):
            if value == 5:
                row[c] = 0
    assert GEN.self_check(no_pivot)

    two_pivots = copy.deepcopy(valid)
    two_pivots[0][0] = 5
    assert GEN.self_check(two_pivots)

    ragged = copy.deepcopy(valid)
    ragged[0].pop()
    assert GEN.self_check(ragged)

    bad_color = copy.deepcopy(valid)
    bad_color[0][0] = True
    assert GEN.self_check(bad_color)

    target_occupied = copy.deepcopy(valid)
    pivot = next(
        (r, c)
        for r, row in enumerate(valid)
        for c, value in enumerate(row)
        if value == 5
    )
    source = next(
        (r, c)
        for r, row in enumerate(valid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    )
    rr, cc = 2 * pivot[0] - source[0], 2 * pivot[1] - source[1]
    target_occupied[rr][cc] = 8 if target_occupied[source[0]][source[1]] != 8 else 7
    assert GEN.self_check(target_occupied)


def test_generation_and_helpers_are_deterministic_fresh_and_nonmutating():
    random.seed(24680)
    before = random.getstate()
    first = GEN.generate(44, 7, difficulty="hard")
    second = GEN.generate(44, 7, difficulty="hard")
    after = random.getstate()
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]

    original = copy.deepcopy(first)
    assert GEN.rule_mirror(first) == intended_output(first)
    GEN.observe_overrides(first)
    GEN.strict_canonical_like(first)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(first)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(first)
    assert first == original
