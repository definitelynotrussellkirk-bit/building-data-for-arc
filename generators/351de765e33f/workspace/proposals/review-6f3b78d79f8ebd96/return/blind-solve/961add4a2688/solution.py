from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Compact each interior column upward inside the cyan (8) frame."""
    result = [row[:] for row in grid]
    frame_cells = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == 8
    ]
    if not frame_cells:
        return result
    top = min(row for row, _ in frame_cells)
    bottom = max(row for row, _ in frame_cells)
    left = min(column for _, column in frame_cells)
    right = max(column for _, column in frame_cells)
    if bottom - top < 2 or right - left < 2:
        return result
    for column in range(left + 1, right):
        colors = [
            grid[row][column]
            for row in range(top + 1, bottom)
            if grid[row][column] not in (0, 8)
        ]
        for offset, row in enumerate(range(top + 1, bottom)):
            result[row][column] = colors[offset] if offset < len(colors) else 0
    return result
