from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand each four-corner color into its rectangle border.

    Colors are painted in numeric order, so a larger color wins at a border
    intersection.  The output otherwise starts as background color 0.
    """
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]

    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        points = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(points) != 4:
            continue
        rows = sorted({r for r, _ in points})
        cols = sorted({c for _, c in points})
        if len(rows) != 2 or len(cols) != 2:
            continue
        expected = {(r, c) for r in rows for c in cols}
        if set(points) != expected:
            continue

        r0, r1 = rows
        c0, c1 = cols
        for c in range(c0, c1 + 1):
            output[r0][c] = color
            output[r1][c] = color
        for r in range(r0 + 1, r1):
            output[r][c0] = color
            output[r][c1] = color

    return output
