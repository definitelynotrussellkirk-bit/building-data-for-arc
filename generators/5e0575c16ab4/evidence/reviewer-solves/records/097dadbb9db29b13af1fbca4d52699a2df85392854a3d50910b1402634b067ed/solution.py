from collections import Counter


def solve(grid):
    """Fill clear horizontal gaps for colors that occur exactly twice."""
    out = [row[:] for row in grid]
    counts = Counter(cell for row in grid for cell in row if cell != 0)

    for row_index, row in enumerate(grid):
        positions_by_color = {}
        for column_index, cell in enumerate(row):
            if cell != 0:
                positions_by_color.setdefault(cell, []).append(column_index)

        for color, positions in positions_by_color.items():
            if counts[color] != 2 or len(positions) != 2:
                continue
            left, right = positions
            if all(row[column] == 0 for column in range(left + 1, right)):
                for column in range(left, right + 1):
                    out[row_index][column] = color

    return out
