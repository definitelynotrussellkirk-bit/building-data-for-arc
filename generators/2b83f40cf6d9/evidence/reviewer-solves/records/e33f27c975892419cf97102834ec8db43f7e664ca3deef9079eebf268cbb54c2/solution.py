from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Connect each repeated nonzero color with the demonstrated staircase path."""
    output = [list(row) for row in grid]

    # Preserve the examples' row-major color order. Each demonstrated marker
    # color occurs exactly twice; unrelated multiplicities are left alone.
    colors: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in colors:
                colors.append(value)

    for color in colors:
        points = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(points) != 2:
            continue

        r, c = points[0]
        target_r, target_c = points[1]
        output[r][c] = color

        # A cycle moves one row toward the second marker, then one column.
        # Once either coordinate agrees, the remaining leg is straight.
        while (r, c) != (target_r, target_c):
            if r != target_r:
                r += 1 if target_r > r else -1
                output[r][c] = color
            if c != target_c:
                c += 1 if target_c > c else -1
                output[r][c] = color

    return output
