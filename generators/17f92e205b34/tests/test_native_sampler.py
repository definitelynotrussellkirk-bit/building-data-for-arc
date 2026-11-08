"""Focused input-support checks; these do not provide reference labels."""

from functools import lru_cache
import importlib.util
from pathlib import Path
import random

import pytest


@lru_cache(maxsize=1)
def _sampler():
    source = Path(__file__).resolve().parents[1] / "workspace/parametric/sampler.py"
    assert source.is_file(), "the native input sampler has not been implemented"
    spec = importlib.util.spec_from_file_location("_reflection_sampler_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.sample_inputs


def _completed(grid):
    return [[grid[c][r] or grid[r][c] for c in range(len(grid))]
            for r in range(len(grid))]


def _ignore_coordinate_zero(grid):
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and r > 0 and c > 0:
                result[c][r] = value
    return result


def _cancel_initial_pairs(grid):
    result = [row[:] for row in grid]
    for r in range(len(grid)):
        for c in range(r):
            if grid[r][c] and grid[c][r]:
                result[r][c] = result[c][r] = 0
    return _completed(result)


def _components(grid, *, diagonal=False, same_color=True):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value}
    found = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        cells, todo = {start}, [start]
        remaining.remove(start)
        while todo:
            r, c = todo.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (dr == dc == 0 or (not diagonal and abs(dr) + abs(dc) != 1)):
                        continue
                    p = r + dr, c + dc
                    if (p in remaining and
                            (not same_color or grid[p[0]][p[1]] == color)):
                        remaining.remove(p)
                        cells.add(p)
                        todo.append(p)
        found.append((color, cells))
    return found


def _bbox_area(cells):
    rows, cols = zip(*cells)
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _select(grid, mode, *, diagonal=False, same_color=True,
            score=len, first_only=False, whole_color=False):
    components = _components(grid, diagonal=diagonal, same_color=same_color)
    best = (max if mode == "largest" else min)(score(cells) for _, cells in components)
    picked = [(color, cells) for color, cells in components if score(cells) == best]
    if first_only:
        picked = picked[:1]
    if whole_color:
        colors = {color for color, _ in picked}
        kept = {(r, c) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value in colors}
    else:
        kept = set().union(*(cells for _, cells in picked))
    return [[value if (r, c) in kept else 0 for c, value in enumerate(row)]
            for r, row in enumerate(grid)]


def _color_total_select(grid, mode):
    totals = {}
    for row in grid:
        for value in row:
            if value:
                totals[value] = totals.get(value, 0) + 1
    target = (max if mode == "largest" else min)(totals.values())
    colors = {color for color, size in totals.items() if size == target}
    return [[value if value in colors else 0 for value in row] for row in grid]


@pytest.mark.parametrize("seed", [0, 1, 17, (1 << 63) - 1])
def test_sampler_builds_ten_distinct_lawful_inputs(seed):
    demos, queries = _sampler()(seed, demos=6, queries=4)
    assert len(demos) == 6 and len(queries) == 4
    signatures = []
    for grid in demos + queries:
        n = len(grid)
        assert 1 <= n <= 30
        assert all(type(row) is list and len(row) == n for row in grid)
        assert all(type(value) is int and 0 <= value <= 9
                   for row in grid for value in row)
        assert any(0 in row for row in grid)
        assert all(not grid[r][c] or not grid[c][r] or grid[r][c] == grid[c][r]
                   for r in range(n) for c in range(n))
        assert any(bool(grid[r][c]) != bool(grid[c][r])
                   for r in range(n) for c in range(r))
        signatures.append(tuple(map(tuple, grid)))
    assert len(set(signatures)) == 10


@pytest.mark.parametrize("seed", [0, 23, (1 << 63) - 1])
def test_requested_counts_do_not_change_input_or_query_order(seed):
    sample = _sampler()
    all_demos, all_queries = sample(seed, demos=6, queries=4)
    for demo_count in range(3, 7):
        for query_count in range(1, 5):
            demos, queries = sample(seed, demos=demo_count, queries=query_count)
            assert demos == all_demos[:demo_count]
            assert queries == all_queries[:query_count]


def test_fresh_returns_and_private_rng_state():
    sample = _sampler()
    state = random.getstate()
    demos, queries = sample(91)
    assert random.getstate() == state
    expected_demos, expected_queries = sample(91)
    demos[0][0][0] = (demos[0][0][0] + 1) % 10
    queries[0][0][0] = (queries[0][0][0] + 2) % 10
    assert sample(91) == (expected_demos, expected_queries)
    objects = [row for grid in expected_demos + expected_queries for row in grid]
    assert len({id(row) for row in objects}) == len(objects)


@pytest.mark.parametrize("name,value,error", [
    ("seed", True, TypeError), ("seed", False, TypeError),
    ("seed", 1.0, TypeError), ("seed", "1", TypeError),
    ("seed", None, TypeError), ("seed", -1, ValueError),
    ("seed", 1 << 63, ValueError),
    ("demos", True, TypeError), ("demos", 3.0, TypeError),
    ("demos", "3", TypeError), ("demos", None, TypeError),
    ("demos", 2, ValueError), ("demos", 7, ValueError),
    ("queries", False, TypeError), ("queries", 1.0, TypeError),
    ("queries", "1", TypeError), ("queries", None, TypeError),
    ("queries", 0, ValueError), ("queries", 5, ValueError),
])
def test_strict_scalar_call_contract(name, value, error):
    arguments = {"seed": 0, "demos": 3, "queries": 4}
    arguments[name] = value
    with pytest.raises(error):
        _sampler()(**arguments)


@pytest.mark.parametrize("seed", [0, 17, 91, (1 << 63) - 1])
def test_core_lesson_rejects_each_component_shortcut_for_each_extremum(seed):
    demos, _ = _sampler()(seed)
    for mode in ("largest", "smallest"):
        rejected = set()
        for grid in demos:
            complete = _completed(grid)
            correct = _select(complete, mode)
            predictions = {
                "selection_before_completion": _completed(_select(grid, mode)),
                "eight_connected": _select(complete, mode, diagonal=True),
                "bounding_box_area": _select(complete, mode, score=_bbox_area),
                "all_foreground_connected": _select(complete, mode, same_color=False),
                "one_tie": _select(complete, mode, first_only=True),
                "winning_colors": _select(complete, mode, whole_color=True),
                "color_aggregation": _color_total_select(complete, mode),
                "completion_only": complete,
            }
            rejected.update(name for name, prediction in predictions.items()
                            if prediction != correct)
        assert rejected == {
            "selection_before_completion", "eight_connected", "bounding_box_area",
            "all_foreground_connected", "one_tie", "winning_colors",
            "color_aggregation", "completion_only",
        }, (seed, mode, rejected)


@pytest.mark.parametrize("seed", [0, 17, (1 << 63) - 1])
@pytest.mark.parametrize("mode", ["complete", "largest", "smallest"])
def test_core_lesson_exposes_ignored_coordinate_zero_sources(seed, mode):
    demos, _ = _sampler()(seed)
    disagreements = []
    for grid in demos:
        correct = _completed(grid)
        rival = _ignore_coordinate_zero(grid)
        if mode != "complete":
            correct = _select(correct, mode)
            rival = _select(rival, mode)
        disagreements.append(correct != rival)
    assert any(disagreements), (seed, mode, "coordinate-zero completion is unexposed")


@pytest.mark.parametrize("seed", [0, 17, (1 << 63) - 1])
@pytest.mark.parametrize("mode", ["complete", "largest", "smallest"])
def test_core_lesson_exposes_cancellation_of_initial_occupied_pairs(seed, mode):
    demos, _ = _sampler()(seed)
    disagreements = []
    for grid in demos:
        correct = _completed(grid)
        rival = _cancel_initial_pairs(grid)
        if mode != "complete":
            correct = _select(correct, mode)
            rival = _select(rival, mode)
        disagreements.append(correct != rival)
    assert any(disagreements), (seed, mode, "preserving matching pairs is unexposed")


@pytest.mark.parametrize("seed", [0, 17, 91, (1 << 63) - 1])
def test_core_lesson_has_selected_diagonal_border_and_interior_cells(seed):
    demos, _ = _sampler()(seed)
    for mode in ("largest", "smallest"):
        diagonal = border = interior = irregular = solid = False
        for grid in demos:
            selected = _select(_completed(grid), mode)
            n = len(selected)
            for _, cells in _components(selected):
                diagonal |= any(r == c for r, c in cells)
                border |= any(r in (0, n - 1) or c in (0, n - 1) for r, c in cells)
                interior |= all(0 < r < n - 1 and 0 < c < n - 1 for r, c in cells)
                irregular |= _bbox_area(cells) > len(cells)
                solid |= _bbox_area(cells) == len(cells)
        assert diagonal and border and interior and irregular and solid, (seed, mode)


def test_complete_component_sizes_make_the_rank_reversal_explicit():
    demos, _ = _sampler()(0)
    # These are hand-derived component areas, independent of color and orientation.
    # Corner squares and the matching source pair are included in these counts.
    assert sorted(len(cells) for _, cells in _components(demos[0])) == [2, 3, 3, 3, 3]
    assert sorted(len(cells) for _, cells in _components(_completed(demos[0]))) == [3, 3, 4, 4, 4, 4]
    assert sorted(len(cells) for _, cells in _components(_completed(demos[1]))) == [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3]
    assert sorted(len(cells) for _, cells in _components(_completed(demos[2]))) == [5, 5, 5, 5, 6, 6]


@pytest.mark.parametrize("seed", [0, 17, (1 << 63) - 1])
def test_queries_mix_sizes_and_large_geometry_with_lawful_prefilled_pairs(seed):
    demos, queries = _sampler()(seed, demos=6, queries=4)
    assert sorted(map(len, queries)) == [14, 24, 28, 30]
    large = [grid for grid in queries if len(grid) == 30]
    assert len(large) == 1
    for grid in large:
        cells = {(r, c) for r, row in enumerate(_completed(grid))
                 for c, value in enumerate(row) if value}
        rows, cols = zip(*cells)
        assert max(rows) - min(rows) + 1 >= 22
        assert max(cols) - min(cols) + 1 >= 22
        assert len(cells) >= 64
    assert any(grid[r][c] and grid[c][r]
               for grid in demos + queries
               for r in range(len(grid)) for c in range(r))


def test_seeds_change_palette_and_geometry_without_a_setting_argument():
    banks = [_sampler()(seed, demos=6, queries=4) for seed in range(8)]
    assert len({tuple(tuple(tuple(row) for row in grid) for grid in demos + queries)
                for demos, queries in banks}) == 8
    assert len({tuple(len(grid) for grid in demos) for demos, _ in banks}) > 1
    assert len({tuple(sorted({value for grid in demos for row in grid
                             for value in row if value}))
                for demos, _ in banks}) > 1
