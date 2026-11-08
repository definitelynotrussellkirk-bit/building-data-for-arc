from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete every color-2 cell's four-way reflection about the 2x2 color-3 marker."""
    out = [row[:] for row in grid]
    marker = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if not marker:
        return out

    min_r = min(r for r, _ in marker)
    max_r = max(r for r, _ in marker)
    min_c = min(c for _, c in marker)
    max_c = max(c for _, c in marker)

    # The reflection axes run through the center of the marker.  Keeping the
    # doubled center as an integer avoids floating-point coordinates.
    row_sum = min_r + max_r
    col_sum = min_c + max_c
    height = len(grid)
    width = len(grid[0]) if height else 0

    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    for r, c in sources:
        for rr in {r, row_sum - r}:
            for cc in {c, col_sum - c}:
                if 0 <= rr < height and 0 <= cc < width and out[rr][cc] != 3:
                    out[rr][cc] = 2
    return out
