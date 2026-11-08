"""Visible-example solution for ARC task 270af96a99b0."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            occupied = set(cells)
            perimeter = sum(
                (r + dr, c + dc) not in occupied
                for r, c in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            result.append((perimeter, r1, c1, r2, c2, color, cells))
    return result


def solve(grid):
    parts = sorted(_components(grid), key=lambda part: part[:3])
    out_h = max(r2 - r1 + 1 for _, r1, _, r2, _, _, _ in parts)
    out_w = sum(c2 - c1 + 1 for _, _, c1, _, c2, _, _ in parts) + len(parts) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for _, r1, c1, r2, c2, color, cells in parts:
        for r, c in cells:
            out[r - r1][left + c - c1] = color
        left += c2 - c1 + 2
    return out
