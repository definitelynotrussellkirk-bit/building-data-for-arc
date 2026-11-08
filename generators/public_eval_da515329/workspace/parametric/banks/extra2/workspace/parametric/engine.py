"""Semantic engine for the four-arm square-spiral task."""
from __future__ import annotations

from typing import Any

Grid = list[list[int]]
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]


def _grid(grid: Any) -> Grid:
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be integer colors 0..9")
    return [row[:] for row in grid]


def _center_and_length(g: Grid) -> tuple[int, int, int]:
    h, w = len(g), len(g[0])
    candidates: list[tuple[int, int]] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if g[r][c] == 0 and all(g[r + dr][c + dc] == 8 for dr, dc in DIRECTIONS):
                candidates.append((r, c))
    if len(candidates) != 1:
        raise ValueError(f"expected one cross center, found {len(candidates)}")
    cr, cc = candidates[0]
    lengths = []
    for dr, dc in DIRECTIONS:
        n = 0
        rr, c2 = cr + dr, cc + dc
        while 0 <= rr < h and 0 <= c2 < w and g[rr][c2] == 8:
            n += 1
            rr += dr
            c2 += dc
        lengths.append(n)
    if min(lengths) < 1 or len(set(lengths)) != 1:
        raise ValueError(f"cross arms must have equal positive lengths, got {lengths}")
    expected = {
        (cr + dr * step, cc + dc * step)
        for dr, dc in DIRECTIONS
        for step in range(1, lengths[0] + 1)
    }
    actual = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    if actual != expected or any(g[r][c] != 8 for r, c in actual):
        raise ValueError("input must contain only the four equal color-8 arms")
    return cr, cc, lengths[0]


def _north_branch(length: int, turns: int = 10) -> set[tuple[int, int]]:
    m = max(2, length)
    cells = {(-i, 0) for i in range(1, m + 1)}
    x, y = -m, 0

    def move(direction: int, steps: int) -> None:
        nonlocal x, y
        dx, dy = DIRECTIONS[direction]
        for _ in range(steps):
            x += dx
            y += dy
            cells.add((x, y))

    move(1, 2)
    for k in range(turns):
        q = (2 + k) % 4
        move(q, m - 2)
        move((q - 1) % 4, m)
        move(q, 6 + 4 * k)
    return cells


def _rotate(cell: tuple[int, int], turns: int) -> tuple[int, int]:
    r, c = cell
    for _ in range(turns % 4):
        r, c = c, -r
    return r, c


def analyze(grid: Any) -> dict[str, Any]:
    g = _grid(grid)
    h, w = len(g), len(g[0])
    cr, cc, length = _center_and_length(g)
    north = _north_branch(length)
    relative = [{_rotate(cell, k) for cell in north} for k in range(4)]
    absolute = [
        {(cr + dr, cc + dc) for dr, dc in branch}
        for branch in relative
    ]
    # The intertwined branches are disjoint by construction.
    overlaps = set()
    seen: set[tuple[int, int]] = set()
    for branch in absolute:
        overlaps.update(seen.intersection(branch))
        seen.update(branch)
    if overlaps:
        raise ValueError("constructed spiral branches overlap")
    visible = [
        {(r, c) for r, c in branch if 0 <= r < h and 0 <= c < w}
        for branch in absolute
    ]
    return {
        "grid": g,
        "center": (cr, cc),
        "arm_length": length,
        # Historical field name retained for task-local review tooling; values
        # are absolute and intentionally include cells beyond the canvas.
        "relative_branches": [sorted(branch) for branch in absolute],
        "branches": [sorted(branch) for branch in absolute],
        "visible_branches": [sorted(branch) for branch in visible],
        "visible_counts": [len(branch) for branch in visible],
    }


def solve(grid: Any, finish: str = "spiral_only") -> Grid:
    if finish not in {"spiral_only", "highlight_most_visible"}:
        raise ValueError("finish must be spiral_only or highlight_most_visible")
    info = analyze(grid)
    h, w = len(info["grid"]), len(info["grid"][0])
    visible = [set(branch) for branch in info["visible_branches"]]
    winner = None
    if finish == "highlight_most_visible":
        counts = info["visible_counts"]
        maximum = max(counts)
        if counts.count(maximum) != 1:
            raise ValueError("alternate setting requires unique visible-branch counts")
        winner = counts.index(maximum)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for index, branch in enumerate(visible):
        color = 9 if index == winner else 8
        for r, c in branch:
            out[r][c] = color
    return out
