from __future__ import annotations


def solve(grid):
    """Expand the two lowest-colored markers into alternating full bands."""
    height = len(grid)
    width = len(grid[0])

    markers = sorted(
        (value, row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )
    if len(markers) < 2:
        raise ValueError("expected at least two nonzero markers")

    color1, row1, col1 = markers[0]
    color2, row2, col2 = markers[1]
    delta_row = abs(row2 - row1)
    delta_col = abs(col2 - col1)
    use_rows = delta_col == 0 or (delta_row > 0 and delta_row < delta_col)

    distance = delta_row if use_rows else delta_col
    if distance == 0:
        raise ValueError("selected markers must differ on the active axis")
    period = 2 * distance
    output = [[0 for _ in range(width)] for _ in range(height)]

    if use_rows:
        first = min(row1, row2)
        for row in range(first, height):
            value = (
                color1
                if (row - row1) % period == 0
                else color2
                if (row - row2) % period == 0
                else 0
            )
            if value:
                output[row] = [value] * width
    else:
        first = min(col1, col2)
        for col in range(first, width):
            value = (
                color1
                if (col - col1) % period == 0
                else color2
                if (col - col2) % period == 0
                else 0
            )
            if value:
                for row in range(height):
                    output[row][col] = value

    return output
