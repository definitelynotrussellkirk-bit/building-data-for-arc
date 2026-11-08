from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete the zero-marked lines independently inside each color panel."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    colors = {cell for row in grid for cell in row if cell != 0}
    for color in colors:
        cells = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == color
        ]
        if not cells:
            continue

        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)

        holes = [
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if grid[r][c] == 0
        ]
        if not holes:
            continue

        left = min(c for _, c in holes)
        right = max(c for _, c in holes)
        for r in range(r0, r1 + 1):
            for c in range(left, right + 1):
                out[r][c] = 0

        original_holes = set(holes)
        for r, c in holes:
            if (r - 1, c) in original_holes:
                for cc in range(c0, c1 + 1):
                    out[r][cc] = 0

    return out
