"""Regression for the canonical-fitting visible-corner completion shortcut.

The shortcut outlines broad components only when the input already contains two
complete adjacent bounding-box edges; thin boxes are filled because their border
is their full box.  It fits all retained canonical pairs and every predecessor
production draw, but it is not the selected per-component bbox-outline rule.
"""
from __future__ import annotations

from collections import deque

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "623cca1dd5a8"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    groups = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        unseen.remove(start)
        cells = set()
        while queue:
            r, c = queue.popleft()
            cells.add((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
        groups.append((color, cells))
    return groups


def bounds(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def adjacent_complete_edges(cells):
    r0, c0, r1, c1 = bounds(cells)
    edges = {
        "top": all((r0, c) in cells for c in range(c0, c1 + 1)),
        "bottom": all((r1, c) in cells for c in range(c0, c1 + 1)),
        "left": all((r, c0) in cells for r in range(r0, r1 + 1)),
        "right": all((r, c1) in cells for r in range(r0, r1 + 1)),
    }
    return any(
        edges[first] and edges[second]
        for first, second in (
            ("top", "left"),
            ("top", "right"),
            ("bottom", "left"),
            ("bottom", "right"),
        )
    )


def outline_truth(grid):
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        r0, c0, r1, c1 = bounds(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    result[r][c] = color
    return result


def visible_corner_completion(grid):
    """A narrower hypothesis that predecessor production never refuted."""
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        r0, c0, r1, c1 = bounds(cells)
        height, width = r1 - r0 + 1, c1 - c0 + 1
        if min(height, width) <= 2 or adjacent_complete_edges(cells):
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if r in (r0, r1) or c in (c0, c1):
                        result[r][c] = color
        else:
            for r, c in cells:
                result[r][c] = color
    return result


def has_broad_branched_component(grid):
    return any(
        min(r1 - r0 + 1, c1 - c0 + 1) >= 3 and not adjacent_complete_edges(cells)
        for _, cells in components(grid)
        for r0, c0, r1, c1 in [bounds(cells)]
    )


def refutes_shortcut(grid):
    return visible_corner_completion(grid) != outline_truth(grid)


def test_visible_corner_completion_fits_all_retained_canonical_pairs():
    assert len(CANONICAL) == 3
    for pair in CANONICAL:
        assert visible_corner_completion(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_each_default_rich_draw_refutes_visible_corner_completion(difficulty):
    for seed in range(8):
        for sample_index in range(0, 8, 2):
            grid = GEN.generate(seed, sample_index, difficulty=difficulty)
            assert GEN.schedule_profile(seed, sample_index, difficulty) == "rich"
            assert has_broad_branched_component(grid), (difficulty, seed, sample_index)
            assert refutes_shortcut(grid), (difficulty, seed, sample_index)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_query_holdout_retains_a_branched_shortcut_witness(difficulty):
    for seed in (0, 17):
        for start in range(4):
            grids = [GEN.generate(seed, index, difficulty=difficulty)
                     for index in range(start, start + 4)]
            for query_index in range(4):
                demonstrations = [grid for index, grid in enumerate(grids)
                                  if index != query_index]
                assert any(refutes_shortcut(grid) for grid in demonstrations), (
                    difficulty, seed, start, query_index
                )
