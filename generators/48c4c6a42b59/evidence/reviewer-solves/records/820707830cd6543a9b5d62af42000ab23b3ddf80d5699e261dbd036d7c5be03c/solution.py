"""Visible-example solution for reviewer solve episode 48c4c6a42b59."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append((color, cells))
    return objects


def solve(grid):
    """Complete left-right symmetry separately inside each object's tight box."""
    out = [row[:] for row in grid]
    for color, cells in _components(grid):
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        for r, c in cells:
            out[r][left + right - c] = color
    return out
