from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Turn each 2 into an 8 and cast four 8-rays stopped by 5-walls."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    emitters = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    for source_row, source_col in emitters:
        output[source_row][source_col] = 8
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            row = source_row + delta_row
            col = source_col + delta_col
            while 0 <= row < height and 0 <= col < width:
                if grid[row][col] == 5:
                    break
                output[row][col] = 8
                row += delta_row
                col += delta_col
    return output
