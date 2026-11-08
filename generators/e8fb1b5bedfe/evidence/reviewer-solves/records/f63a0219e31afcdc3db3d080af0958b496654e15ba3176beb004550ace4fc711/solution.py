"""Visible-example solution for the frame-ranking task."""
from copy import deepcopy


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    frames = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 4 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            frames.append(
                {
                    "bbox": (r0, c0, r1, c1),
                    "interior_area": (r1 - r0 - 1) * (c1 - c0 - 1),
                }
            )
    return frames


def _fill_interior(grid, frame, color):
    r0, c0, r1, c1 = frame["bbox"]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            grid[r][c] = color


def solve(grid):
    frames = sorted(_components(grid), key=lambda frame: frame["interior_area"])
    out = deepcopy(grid)
    _fill_interior(out, frames[0], 2)
    _fill_interior(out, frames[-1], 8)
    return out
