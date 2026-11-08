"""Focused repair tests for strict inputs and lesson-level semantics."""
from __future__ import annotations

import importlib

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.22e428cda452.generator")


def _grid(*, top_left=None, top_right=None, bottom_left=None, bottom_right=None):
    grid = [[7 for _ in range(8)] for _ in range(8)]
    for value, (row, col) in (
        (top_left, (0, 0)),
        (top_right, (0, 7)),
        (bottom_left, (7, 0)),
        (bottom_right, (7, 7)),
    ):
        if value is not None:
            grid[row][col] = value
    return grid


def _non_background(grid):
    return {
        (row, col): value
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 7
    }


def _mask(grid):
    return gen.observe_overrides(grid)["corner_mask"]


def test_invalid_call_and_override_scalars_are_rejected():
    valid = dict(seed=11, sample_index=3, difficulty="medium")

    for seed in (True, False, 1.0, 1.75, "11"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(seed, valid["sample_index"], difficulty=valid["difficulty"])
    for sample_index in (True, False, 3.0, 3.75, "3", -1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(valid["seed"], sample_index, difficulty=valid["difficulty"])
    for difficulty in (True, 1, 0.5, "expert"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(valid["seed"], valid["sample_index"], difficulty=difficulty)

    invalid_by_axis = {
        "grid_h": (True, 8.0, 8.75, "8", 7, 19),
        "grid_w": (True, 8.0, 8.75, "8", 7, 19),
        "corner_mask": (True, 1.0, 1.75, "1", 0, 16),
        "palette_size": (True, 1.0, 1.75, "1", 0, 5),
    }
    for axis, invalid_values in invalid_by_axis.items():
        for value in invalid_values:
            with pytest.raises((TypeError, ValueError)):
                gen.generate(**valid, **{axis: value})


def test_three_phase_schedule_keeps_both_corner_branches_in_every_rotation():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 3
    assert gen.SCHEDULE_PROFILES == ("top_only", "bottom_only", "mixed")

    for sample_index in range(18):
        assert gen.schedule_profile(41, sample_index, "medium") == (
            gen.SCHEDULE_PROFILES[sample_index % 3]
        )

    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                gen.generate(9001 + start, start + offset, difficulty=difficulty)
                for offset in range(4)
            ]
            for held_out in range(4):
                demo_masks = [
                    _mask(grid) for index, grid in enumerate(grids) if index != held_out
                ]
                assert any(mask & 0b0011 for mask in demo_masks), (difficulty, start, held_out)
                assert any(mask & 0b1100 for mask in demo_masks), (difficulty, start, held_out)


def test_rule_mirror_and_rivals_have_hand_checked_corner_geometry():
    grid = _grid(top_left=2, bottom_right=4)
    expected = {
        (1, 1): 2,
        (1, 2): 2,
        (2, 1): 2,
        (2, 2): 2,
        (4, 5): 4,
        (5, 5): 4,
        (6, 4): 4,
    }
    assert gen.strict_canonical_like(grid) == []
    assert _non_background(gen.rule_mirror(grid)) == expected

    all_square = gen.SEMANTIC_RIVALS["all_corners_square"](grid)
    assert _non_background(all_square) == {
        (1, 1): 2,
        (1, 2): 2,
        (2, 1): 2,
        (2, 2): 2,
        (5, 5): 4,
        (5, 6): 4,
        (6, 5): 4,
        (6, 6): 4,
    }
    all_bent = gen.SEMANTIC_RIVALS["all_corners_bent"](grid)
    assert _non_background(all_bent) == {
        (1, 3): 2,
        (2, 2): 2,
        (3, 2): 2,
        (4, 5): 4,
        (5, 5): 4,
        (6, 4): 4,
    }


def test_lesson_identifiability_exposes_one_branch_shortcuts_and_accepts_schedule():
    top_inputs = [_grid(top_left=color) for color in (2, 3, 4)]
    bottom_inputs = [_grid(bottom_right=color) for color in (2, 3, 4)]
    top_demos = [
        {"input": grid, "output": gen.rule_mirror(grid)} for grid in top_inputs
    ]
    bottom_demos = [
        {"input": grid, "output": gen.rule_mirror(grid)} for grid in bottom_inputs
    ]

    findings = gen.lesson_identifiable(
        top_demos, {"input": bottom_inputs[0], "output": gen.rule_mirror(bottom_inputs[0])}
    )
    assert any("all_corners_square" in finding for finding in findings)
    findings = gen.lesson_identifiable(
        bottom_demos, {"input": top_inputs[0], "output": gen.rule_mirror(top_inputs[0])}
    )
    assert any("all_corners_bent" in finding for finding in findings)

    for difficulty in ("easy", "medium", "hard"):
        for start in range(9):
            pairs = []
            for offset in range(4):
                grid = gen.generate(7123 + start, start + offset, difficulty=difficulty)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                assert gen.lesson_identifiable(demos, pairs[held_out]) == []


def test_declared_witnesses_refute_their_mapped_rivals():
    top = _grid(top_right=5)
    bottom = _grid(bottom_left=6)
    assert gen.SEMANTIC_WITNESSES["top_corner_branch"](top)
    assert gen.SEMANTIC_WITNESSES["bottom_corner_branch"](bottom)
    assert gen.WITNESS_RIVALS == {
        "top_corner_branch": ["all_corners_bent"],
        "bottom_corner_branch": ["all_corners_square"],
    }
    for witness_name, grid in (
        ("top_corner_branch", top),
        ("bottom_corner_branch", bottom),
    ):
        expected = gen.rule_mirror(grid)
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected
