"""Behavioral regression tests for the review repair, portable to staged runtimes.

The local component oracle is deliberately independent of generator helpers.
Actual labels are separately cross-checked with the unchanged Racket authority.
"""
from __future__ import annotations

import importlib.util
from collections import deque

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "c7070676c606"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_contract_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def candidates(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        pending = deque([start])
        cells = {start}
        while pending:
            r, c = pending.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    pending.append(point)
                    cells.add(point)
        if all(r > 0 for r, _ in cells):
            result.append(cells)
    return sorted(result, key=lambda cells: (-len(cells), min(cells)))


def reference_prediction(grid):
    ranked = candidates(grid)
    k = sum(v == 1 for v in grid[0])
    assert 1 <= k <= len(ranked)
    out = [row[:] for row in grid]
    for r, c in ranked[k - 1]:
        out[r][c] = 2
    return out


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("height,width", ((10, 11), (12, 12), (13, 13), (24, 24)))
def test_requested_dimensions_are_realized_in_every_band(band, height, width):
    grid = GEN.generate(17, 7, difficulty=band, grid_h=height, grid_w=width)
    assert (len(grid), len(grid[0])) == (height, width)
    assert GEN.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("count", (1, 2, 3, 4, 5))
def test_shape_count_override_counts_eligible_components(band, count):
    grid = GEN.generate(91, 3, difficulty=band, n_shapes=count)
    assert len(candidates(grid)) == count
    assert 1 <= sum(v == 1 for v in grid[0]) <= count
    assert GEN.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("rank", (1, 2, 3, 4, 5))
def test_rank_only_override_constructs_enough_candidates(band, rank):
    grid = GEN.generate(8, 2, difficulty=band, k_select=rank)
    assert sum(v == 1 for v in grid[0]) == rank
    assert len(candidates(grid)) >= rank
    assert GEN.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("count,rank", ((1, 1), (3, 2), (5, 5)))
def test_joint_minimum_canvas_controls_are_exact(count, rank):
    controls = {"grid_h": 10, "grid_w": 11, "n_shapes": count, "k_select": rank}
    grid = GEN.generate(37, 9, difficulty="hard", **controls)
    assert (len(grid), len(grid[0]), len(candidates(grid)), grid[0].count(1)) == (10, 11, count, rank)
    observer = getattr(GEN, "observe_overrides", None)
    assert callable(observer), "Exact semantic axes require a pixel-based observer"
    observed = observer(grid)
    assert {key: observed[key] for key in controls} == controls


@pytest.mark.parametrize("controls", ({"n_shapes": 1, "k_select": 2}, {"n_shapes": 3, "k_select": 5}))
def test_incompatible_rank_and_count_fail_explicitly(controls):
    with pytest.raises(ValueError) as error:
        GEN.generate(0, 0, **controls)
    assert str(error.value)
    declared = getattr(GEN, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None)
    axes = getattr(error.value, "incompatible_axes", getattr(error.value, "axes", None))
    assert declared or axes, "Rejection must carry a structured compatibility contract"


@pytest.mark.parametrize("name,value", (
    ("grid_h", 9), ("grid_h", 25), ("grid_w", 10), ("grid_w", 25),
    ("n_shapes", 0), ("n_shapes", 6), ("k_select", 0), ("k_select", 6),
    ("grid_h", True), ("grid_w", 12.0), ("n_shapes", "3"), ("k_select", False),
))
def test_invalid_integer_controls_are_rejected(name, value):
    with pytest.raises(ValueError):
        GEN.generate(17, 0, **{name: value})


@pytest.mark.parametrize("controls", ({"grid_height": 12}, {"palette_size": 2}, {"texture": "warm"}, {"position_bias": "shapes_below_markers"}))
def test_unknown_and_removed_fictitious_controls_are_not_silently_accepted(controls):
    with pytest.raises((ValueError, TypeError, KeyError)):
        GEN.generate(17, 0, **controls)


def test_none_is_no_override():
    for index in range(4):
        assert GEN.generate(12, index, grid_h=None, n_shapes=None) == GEN.generate(12, index)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_draws_are_lawful_deterministic_and_cover_canonical_sizes(band):
    profiles = {(10, 11), (12, 12), (13, 13)}
    grids = [GEN.generate(0, index, difficulty=band) for index in range(20)]
    assert any((len(grid), len(grid[0])) in profiles for grid in grids)
    for index, grid in enumerate(grids):
        assert GEN.self_check(grid, difficulty=band) == []
        assert grid == GEN.generate(0, index, difficulty=band)
        assert grid[0].count(1) <= len(candidates(grid))


def test_declared_rivals_fit_all_labeled_canonical_pairs():
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert rivals, "Canonical-fitting rivals must be executable, not prose only"
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        for name, rival in rivals.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_three_demo_lessons_retain_a_rival_refutation_after_every_query_rotation(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals, "A finite executable lesson contract is required"
    assert getattr(GEN, "EXAMPLES_NEEDED", None) == 3
    for seed in (0, 17, 91):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(12)]
        for start in range(8):
            lesson = grids[start:start + 4]
            assert len({str(grid) for grid in lesson}) == 4, (seed, start, "duplicate pair")
            for name, rival in rivals.items():
                witnesses = [rival(grid) != reference_prediction(grid) for grid in lesson]
                assert sum(witnesses) == 0 or sum(witnesses) >= 2, (seed, start, name, witnesses)

