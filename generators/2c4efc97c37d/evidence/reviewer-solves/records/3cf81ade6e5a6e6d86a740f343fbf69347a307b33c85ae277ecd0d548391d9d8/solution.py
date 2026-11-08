"""Visible-example solution for the post-repair reviewer episode."""
from __future__ import annotations


_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(cells)
    found.sort(key=lambda cells: (min(c for _, c in cells), min(r for r, _ in cells)))
    return found


def _onion_depth(cells):
    remaining = set(cells)
    depth = 0
    while remaining:
        depth += 1
        boundary = {
            (row, col)
            for row, col in remaining
            if any((row + dr, col + dc) not in remaining for dr, dc in _CARDINAL)
        }
        remaining.difference_update(boundary)
    return depth


def solve(grid):
    """Report each left-to-right component's cardinal onion-peel depth."""
    return [[_onion_depth(cells) for cells in _components(grid)]]
