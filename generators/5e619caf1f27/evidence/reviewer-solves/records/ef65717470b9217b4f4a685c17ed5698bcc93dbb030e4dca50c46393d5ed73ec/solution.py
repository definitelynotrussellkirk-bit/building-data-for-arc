from __future__ import annotations


def solve(grid):
    """Add an inner-color frame around the outer rectangle.

    Its thickness is the smallest of the inner rectangle's two dimensions and
    the four available grid margins around the outer rectangle.
    """
    height = len(grid)
    width = len(grid[0])
    nonzero = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    r1 = min(row for row, _ in nonzero)
    c1 = min(col for _, col in nonzero)
    r2 = max(row for row, _ in nonzero)
    c2 = max(col for _, col in nonzero)

    outer_color = grid[r1][c1]
    inner_cells = [
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if grid[row][col] != outer_color
    ]
    inner_color = grid[inner_cells[0][0]][inner_cells[0][1]]
    ir1 = min(row for row, _ in inner_cells)
    ic1 = min(col for _, col in inner_cells)
    ir2 = max(row for row, _ in inner_cells)
    ic2 = max(col for _, col in inner_cells)

    thickness = min(
        ir2 - ir1 + 1,
        ic2 - ic1 + 1,
        r1,
        c1,
        height - 1 - r2,
        width - 1 - c2,
    )

    result = [row[:] for row in grid]
    for row in range(r1 - thickness, r2 + thickness + 1):
        for col in range(c1 - thickness, c2 + thickness + 1):
            if not (r1 <= row <= r2 and c1 <= col <= c2):
                result[row][col] = inner_color
    return result
