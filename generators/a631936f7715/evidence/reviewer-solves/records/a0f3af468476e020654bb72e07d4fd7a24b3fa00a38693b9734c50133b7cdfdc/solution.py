"""Visible-example solution for a631936f7715."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor each 4-connected 6-component from its adjacent label, then erase labels."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [[7 for _ in range(w)] for _ in range(h)]
    seen: set[tuple[int, int]] = set()
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] != 6 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            labels: set[int] = set()
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    value = grid[nr][nc]
                    if value == 6 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
                    elif value not in (6, 7):
                        labels.add(value)
            color = min(labels) if labels else 6
            for r, c in cells:
                out[r][c] = color
    return out
