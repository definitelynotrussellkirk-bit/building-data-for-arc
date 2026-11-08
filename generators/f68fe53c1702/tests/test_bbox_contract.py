"""Portable regressions for exact controls and informative bbox lessons."""
from __future__ import annotations

import importlib.util
from itertools import combinations
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "f68fe53c1702"
ROOT = find_root(__file__)
SOURCE = next(p for p in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if p.is_file())
SPEC = importlib.util.spec_from_file_location("bbox_generator_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def points(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def witness_flags(grid):
    """Independent geometry: no two points span the box; some point is inside."""
    pts = points(grid)
    top, bottom = min(r for r, _ in pts), max(r for r, _ in pts)
    left, right = min(c for _, c in pts), max(c for _, c in pts)
    any_spanning_pair = any(
        {a[0], b[0]} == {top, bottom} and {a[1], b[1]} == {left, right}
        for a, b in combinations(pts, 2)
    )
    interior = any(top < r < bottom and left < c < right for r, c in pts)
    return not any_spanning_pair, interior


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,color,count", [
    (4, 5, 1, 2), (4, 5, 9, 7), (24, 24, 1, 7), (7, 10, 4, 4),
])
def test_exact_joint_controls_at_geometry_boundaries(band, height, width, color, count):
    """Catch ignored controls, silent clipping and duplicate marker placements."""
    for index in range(3):
        grid = GEN.generate(0, index, difficulty=band, grid_h=height,
                            grid_w=width, color=color, num_cells=count)
        assert (len(grid), len(grid[0])) == (height, width)
        assert {value for row in grid for value in row if value} == {color}
        assert len(points(grid)) == count
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("axis,value", [
    ("grid_h", True), ("grid_w", 7.0), ("color", "2"), ("num_cells", False),
    ("grid_h", 3), ("grid_h", 25), ("grid_w", 4), ("grid_w", 25),
    ("color", 0), ("color", 10), ("num_cells", 1), ("num_cells", 8),
])
def test_invalid_exact_controls_fail_instead_of_being_coerced_or_ignored(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


@pytest.mark.parametrize("axis,value", [
    ("typo_axis", 123), ("texture", "no_cells"), ("palette_kind", "warm"),
    ("palette_size", 1), ("position_bias", "diagonal"),
    ("bbox_aspect", "rectangle"), ("n_distinct_colors", 1),
])
def test_unknown_and_retired_controls_are_explicit_errors(axis, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{axis: value})


def test_none_preserves_the_default_and_draws_are_deterministic():
    for index in range(6):
        expected = GEN.generate(42, index, difficulty="hard")
        assert GEN.generate(42, index, difficulty="hard") == expected
        assert GEN.generate(42, index, difficulty="hard", grid_h=None,
                            grid_w=None, color=None, num_cells=None) == expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_schedule_window_and_query_holdout_keeps_both_witnesses(band):
    """A shuffled query must not remove the lesson's only useful demonstration."""
    for seed in (0, 1, 7, 42):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(15)]
        flags = [witness_flags(grid) for grid in grids]
        for start in range(12):
            window = flags[start:start + 4]
            for held_out in range(4):
                demos = [row for i, row in enumerate(window) if i != held_out]
                assert all(any(row[feature] for row in demos) for feature in (0, 1)), (
                    band, seed, start, held_out, window)


def test_all_canonical_inputs_remain_supported():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("bad", [
    [], [[0] * 5] * 4, [[2] * 5] * 4,
    [[0, 0, 0, 0, 0], [0, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
    [[True, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, True, 0, 0], [0, 0, 0, 0, 0]],
    [[10, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 10, 0, 0], [0, 0, 0, 0, 0]],
    [[2.5, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 2.5, 0, 0], [0, 0, 0, 0, 0]],
    [[2, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 3, 0, 0], [0, 0, 0, 0, 0]],
])
def test_validator_rejects_malformed_or_out_of_domain_inputs(bad):
    assert GEN.self_check(bad)


WITNESS = [
    [2, 0, 0, 0, 0],
    [0, 2, 2, 0, 0],
    [0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0],
]
WITNESS_OUTPUT = [
    [2, 2, 2, 0, 0],
    [2, 0, 2, 0, 0],
    [2, 2, 2, 0, 0],
    [0, 0, 0, 0, 0],
]


def test_declared_shortcuts_fit_canonicals_but_fail_a_hand_checked_witness():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert GEN.self_check(WITNESS) == []
    assert len(GEN.CANONICAL_SHORTCUTS) >= 2
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        assert rival(WITNESS) != WITNESS_OUTPUT, name


def test_lesson_hook_reports_actual_ambiguity_and_accepts_refuting_demo():
    demos = canonical_pairs(TASK, root=ROOT, labeled_only=True)[:3]
    query = {"input": WITNESS, "output": WITNESS_OUTPUT}
    assert GEN.lesson_identifiable(demos, query)
    assert GEN.lesson_identifiable([demos[0], demos[1], query], query) == []


def test_lesson_hook_accepts_surviving_but_answer_equivalent_rivals():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
