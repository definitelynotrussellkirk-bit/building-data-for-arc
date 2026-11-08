"""Visible-example solution for task 067449d7a3b3."""
from __future__ import annotations


def solve(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    boxes = []

    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        rr, cc = r + dr, c + dc
                        if (
                            0 <= rr < h
                            and 0 <= cc < w
                            and grid[rr][cc] != 0
                            and (rr, cc) not in seen
                        ):
                            seen.add((rr, cc))
                            stack.append((rr, cc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            border = max(r2 - r1 + 1, c2 - c1 + 1) // 2
            boxes.append((r1, c1, r2, c2, border))

    out = [row[:] for row in grid]

    # Blue stems are laid down first.
    for r1, c1, r2, c2, border in boxes:
        for r in range(r2 + border + 1, h):
            for c in range(c1, c2 + 1):
                out[r][c] = 1

    # Green bbox halos are painted second, so they can cover stem cells.
    for r1, c1, r2, c2, border in boxes:
        for r in range(r1 - border, r2 + border + 1):
            for c in range(c1 - border, c2 + border + 1):
                if r1 <= r <= r2 and c1 <= c <= c2:
                    continue
                if 0 <= r < h and 0 <= c < w and grid[r][c] != 9:
                    out[r][c] = 3

    return out
