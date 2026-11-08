from __future__ import annotations

from collections import Counter, defaultdict


def solve(grid):
    """Connect equal-colored 2x2 markers across the coarse divider lattice."""
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    counts = Counter(value for row in grid for value in row if value != 0)
    divider = counts.most_common(1)[0][0]
    coarse_rows = (height + 1) // 3
    coarse_cols = (width + 1) // 3

    markers = defaultdict(list)
    for cell_r in range(coarse_rows):
        for cell_c in range(coarse_cols):
            r0, c0 = 3 * cell_r, 3 * cell_c
            values = {
                grid[r0 + dr][c0 + dc]
                for dr in range(2)
                for dc in range(2)
            }
            if len(values) == 1:
                color = next(iter(values))
                if color not in (0, divider):
                    markers[color].append((cell_r, cell_c))

    def paint(cell_r, cell_c, color):
        r0, c0 = 3 * cell_r, 3 * cell_c
        for dr in range(2):
            for dc in range(2):
                out[r0 + dr][c0 + dc] = color

    for color, cells in markers.items():
        by_row = defaultdict(list)
        by_col = defaultdict(list)
        for cell_r, cell_c in cells:
            by_row[cell_r].append(cell_c)
            by_col[cell_c].append(cell_r)
        for cell_r, cols in by_row.items():
            if len(cols) >= 2:
                for cell_c in range(min(cols), max(cols) + 1):
                    paint(cell_r, cell_c, color)
        for cell_c, rows in by_col.items():
            if len(rows) >= 2:
                for cell_r in range(min(rows), max(rows) + 1):
                    paint(cell_r, cell_c, color)
    return out
