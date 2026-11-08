"""Visible-example solution for blind ARC task 0bd65c18b34c."""
from __future__ import annotations


def _blue_blocks(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    """Return bounding boxes of four-connected color-2 components."""
    height = len(grid)
    width = len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2}
    blocks: list[tuple[int, int, int, int]] = []

    while unseen:
        start = unseen.pop()
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    component.add((nr, nc))
                    stack.append((nr, nc))

        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        blocks.append((min(rows), max(rows), min(cols), max(cols)))

    return blocks


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Pull each aligned color-1 marker next to its nearest 2×2 color-2 block."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    blocks = _blue_blocks(grid)
    result = [row[:] for row in grid]
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]

    # Move all markers simultaneously: clear their old locations before placing
    # their destinations, so one marker's update cannot affect another's rule.
    for r, c in markers:
        result[r][c] = 0

    max_gap = 7
    for r, c in markers:
        candidates: list[tuple[int, int, int]] = []
        for top, bottom, left, right in blocks:
            if top <= r <= bottom:
                if c < left:
                    gap = left - c - 1
                    if gap <= max_gap:
                        candidates.append((gap, r, left - 1))
                elif c > right:
                    gap = c - right - 1
                    if gap <= max_gap:
                        candidates.append((gap, r, right + 1))
            if left <= c <= right:
                if r < top:
                    gap = top - r - 1
                    if gap <= max_gap:
                        candidates.append((gap, top - 1, c))
                elif r > bottom:
                    gap = r - bottom - 1
                    if gap <= max_gap:
                        candidates.append((gap, bottom + 1, c))

        if candidates:
            _, dest_r, dest_c = min(candidates)
        else:
            dest_r, dest_c = r, c
        result[dest_r][dest_c] = 1

    return result
