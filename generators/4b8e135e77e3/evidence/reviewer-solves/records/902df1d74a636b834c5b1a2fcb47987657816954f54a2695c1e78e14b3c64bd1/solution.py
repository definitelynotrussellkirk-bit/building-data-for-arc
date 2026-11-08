"""Visible-example solution for ARC task 4b8e135e77e3."""


def solve(grid):
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(pivots) != 1:
        raise ValueError("expected exactly one color-9 pivot")
    pivot_r, pivot_c = pivots[0]

    k = min(4, sum(value == 1 for value in grid[0]))
    motif = [
        (r - pivot_r, c - pivot_c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if 2 <= value <= 8
    ]

    out = [[0] * width for _ in range(height)]
    out[pivot_r][pivot_c] = 9
    for quarter in range(k):
        for base_dr, base_dc, value in motif:
            dr, dc = base_dr, base_dc
            for _ in range(quarter):
                dr, dc = dc, -dr
            r, c = pivot_r + dr, pivot_c + dc
            if 0 <= r < height and 0 <= c < width:
                out[r][c] = value
    return out
