from __future__ import annotations


def solve(grid):
    """Complete every adjacent same-colour diagonal into its 2x2 square."""
    source = [list(row) for row in grid]
    output = [list(row) for row in grid]

    colors = []
    seen = set()
    for row in source:
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                colors.append(value)

    positions = {
        color: {
            (row, col)
            for row, values in enumerate(source)
            for col, value in enumerate(values)
            if value == color
        }
        for color in colors
    }

    for color in colors:
        cells = positions[color]
        for row, col in sorted(cells):
            for drow, dcol in ((1, 1), (1, -1)):
                other = (row + drow, col + dcol)
                if other not in cells:
                    continue
                row0, row1 = sorted((row, other[0]))
                col0, col1 = sorted((col, other[1]))
                for rr in range(row0, row1 + 1):
                    for cc in range(col0, col1 + 1):
                        output[rr][cc] = color
    return output
