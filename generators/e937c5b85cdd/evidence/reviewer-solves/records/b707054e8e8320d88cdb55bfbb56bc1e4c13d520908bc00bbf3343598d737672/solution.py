"""Visible-example solution for the exposed e937c5b85cdd episode."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            color = grid[r][c]
            if color in (6, 7) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def solve(grid):
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    directions = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    for color, cells in _components(grid):
        cell_set = set(cells)
        center = max(
            cells,
            key=lambda p: sum(
                (p[0] + dr, p[1] + dc) in cell_set
                for dr, dc in directions.values()
            ),
        )
        r, c = center
        arm_lengths = {
            "up": sum(cc == c and rr < r for rr, cc in cells),
            "down": sum(cc == c and rr > r for rr, cc in cells),
            "left": sum(rr == r and cc < c for rr, cc in cells),
            "right": sum(rr == r and cc > c for rr, cc in cells),
        }
        longest = max(arm_lengths, key=arm_lengths.get)
        if longest == "up":
            out[0][c] = 0
            out[h - 1][c] = color
        elif longest == "down":
            out[h - 1][c] = 0
            out[0][c] = color
        elif longest == "left":
            out[r][0] = 0
            out[r][w - 1] = color
        else:
            out[r][w - 1] = 0
            out[r][0] = color

    return out
