from __future__ import annotations


def _bands(total: int, separators: set[int]) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    start = 0
    while start < total:
        if start in separators:
            start += 1
            continue
        end = start
        while end + 1 < total and end + 1 not in separators:
            end += 1
        bands.append((start, end))
        start = end + 1
    return bands


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    zero_rows = {
        row
        for row in range(height)
        if all(grid[row][col] == 0 for col in range(width))
    }
    zero_cols = {
        col
        for col in range(width)
        if all(grid[row][col] == 0 for row in range(height))
    }
    row_bands = _bands(height, zero_rows)
    col_bands = _bands(width, zero_cols)

    tiles = [
        (row_start, row_end, col_start, col_end, grid[row_start][col_start])
        for row_start, row_end in row_bands
        for col_start, col_end in col_bands
    ]
    offsets_by_color: dict[int, set[tuple[int, int]]] = {}
    for row_start, row_end, col_start, col_end, color in tiles:
        offsets = offsets_by_color.setdefault(color, set())
        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                if grid[row][col] == color:
                    offsets.add((row - row_start, col - col_start))

    output = [row[:] for row in grid]
    for row_start, _, col_start, _, color in tiles:
        for dr, dc in offsets_by_color[color]:
            output[row_start + dr][col_start + dc] = color
    return output
