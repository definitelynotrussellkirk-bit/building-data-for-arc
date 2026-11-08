def solve(grid):
    """Copy the colored motif across the applicable axis through color 9."""
    output = [list(row) for row in grid]
    pivot = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )
    motif = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not motif:
        return output

    pr, pc = pivot
    columns = [c for _, c in motif]
    rows = [r for r, _ in motif]

    if max(columns) < pc or min(columns) > pc:
        reflected = ((r, 2 * pc - c) for r, c in motif)
    elif max(rows) < pr or min(rows) > pr:
        reflected = ((2 * pr - r, c) for r, c in motif)
    else:
        return output

    for (r, c), (rr, cc) in zip(motif, reflected):
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            output[rr][cc] = grid[r][c]
    return output
