"""Visible-example solution for e5dc3d423bd9."""
from __future__ import annotations


def solve(grid):
    out = [list(row) for row in grid]
    if not out or not out[0]:
        return out
    height, width = len(out), len(out[0])
    seen = set()

    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue

            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            frame_h, frame_w = r2 - r1 + 1, c2 - c1 + 1
            if frame_h < 3 or frame_w < 3:
                continue

            perimeter = {
                (rr, cc)
                for rr in range(r1, r2 + 1)
                for cc in range(c1, c2 + 1)
                if rr in (r1, r2) or cc in (c1, c2)
            }
            if set(cells) != perimeter:
                continue

            if frame_h % 2 == 1 and frame_w % 2 == 1:
                out[(r1 + r2) // 2][(c1 + c2) // 2] = color

    return out
