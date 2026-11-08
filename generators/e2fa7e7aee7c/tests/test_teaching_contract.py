"""Regressions for equality teaching, whole lessons, and dense exact controls."""
from __future__ import annotations

from collections import defaultdict
from itertools import product

import pytest
from puzzle_generators.per_puzzle.e2fa7e7aee7c import generator as gen


def _expected(grid):
    """Independent domain-specific expectation: each unique color has two endpoints."""
    cells = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                cells[value].append((r, c))
    result = [row[:] for row in grid]
    for color, ((r0, c0), (r1, c1)) in cells.items():
        result[(r0 + r1) // 2][(c0 + c1) // 2] = color
    return result


def _color_blind(grid, blind_axes=("horizontal", "vertical")):
    result = [row[:] for row in grid]
    for axis, (dr, dc) in (("horizontal", (0, 1)), ("vertical", (1, 0))):
        for r in range(len(grid) - 2 * dr):
            for c in range(len(grid[0]) - 2 * dc):
                a, b = grid[r][c], grid[r + 2 * dr][c + 2 * dc]
                if (a and b and grid[r + dr][c + dc] == 0
                        and (axis in blind_axes or a == b)):
                    result[r + dr][c + dc] = a
    return result


def _assert_no_ambiguity(pairs, rivals):
    for query_index, query in enumerate(pairs):
        demos = pairs[:query_index] + pairs[query_index + 1:]
        for name, rival in rivals.items():
            fits = all(rival(p["input"]) == p["output"] for p in demos)
            assert not (fits and rival(query["input"]) != query["output"]), (
                name, query_index, "rival fits every demonstration but changes the query"
            )


def test_original_seed_window_teaches_equal_colors_before_the_query():
    grids = [gen.generate(0, i, difficulty="medium") for i in (3, 4, 5, 6)]
    pairs = [{"input": grid, "output": _expected(grid)} for grid in grids]
    _assert_no_ambiguity(pairs, {"color_blind": _color_blind})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_schedule_start_and_query_rotation_teaches_each_axis(band):
    rivals = {
        "color_blind": _color_blind,
        "horizontal_color_blind": lambda grid: _color_blind(grid, ("horizontal",)),
        "vertical_color_blind": lambda grid: _color_blind(grid, ("vertical",)),
    }
    for seed in (0, 17, 43):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(11)]
        pairs = [{"input": grid, "output": _expected(grid)} for grid in grids]
        for start in range(8):
            _assert_no_ambiguity(pairs[start:start + 4], rivals)


@pytest.mark.parametrize("mode", ["horizontal", "vertical", "mixed"])
def test_dense_and_rectangular_controls_keep_a_real_equality_witness(mode):
    for height, width, count, index in product((7, 18), (7, 18), (2, 9), (0, 1)):
        controls = dict(grid_h=height, grid_w=width, triples=count, orientation_mode=mode)
        grid = gen.generate(3101, index, difficulty="hard", **controls)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == controls
        assert _color_blind(grid) != _expected(grid), (controls, index)


def test_false_gap_witness_excludes_an_actual_third_motif_midpoint():
    witness = getattr(gen, "_false_gap_midpoints", None)
    assert callable(witness), "a witness must distinguish unchanged false gaps from true midpoints"
    grid = [[0] * 7 for _ in range(7)]
    for r, c, color in ((2, 0, 2), (2, 2, 2), (1, 1, 4), (1, 3, 4), (3, 1, 6), (3, 3, 6)):
        grid[r][c] = color
    assert gen.self_check(grid) == []
    assert _expected(grid)[2][1] == 2
    vertical = witness(grid, "vertical")
    assert (2, 1) not in vertical
    assert (2, 3) in vertical


def test_lesson_hook_rejects_missing_equality_evidence_without_rejecting_equivalence():
    hook = getattr(gen, "lesson_identifiable", None)
    assert callable(hook), "materialization must check actual labeled demonstrations and query"
    demo = [[0] * 7 for _ in range(7)]
    for r, c, color in ((0, 0, 2), (0, 2, 2), (4, 4, 6), (6, 4, 6)):
        demo[r][c] = color
    query = [[0] * 7 for _ in range(7)]
    for r, c, color in ((0, 0, 2), (0, 2, 2), (0, 4, 6), (2, 4, 6)):
        query[r][c] = color
    pair = {"input": demo, "output": _expected(demo)}
    assert hook([pair, pair, pair], {"input": query, "output": _expected(query)})
    assert hook([pair, pair, pair], pair) == []


def test_all_declared_competitors_are_safe_in_the_default_lesson():
    rivals = getattr(gen, "LESSON_COMPETITORS", {})
    assert rivals, "the reviewed shortcuts must be executable lesson competitors"
    for band, seed, start in product(("easy", "medium", "hard"), (0, 29), range(4)):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(start, start + 4)]
        pairs = [{"input": grid, "output": _expected(grid)} for grid in grids]
        _assert_no_ambiguity(pairs, rivals)
