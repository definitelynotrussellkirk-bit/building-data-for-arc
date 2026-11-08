"""Visible-only attempted rule: label by earlier strictly shorter bars."""

def solve(grid):
    result = [list(row) for row in grid]
    if not grid:
        return result
    marker_columns = [c for c, value in enumerate(grid[0]) if value == 5]
    if len(marker_columns) != 1:
        raise ValueError("Expected one gray header marker")
    marker_col = marker_columns[0]
    palette = [1, 4, 9, 5]
    earlier_lengths = []
    for r, row in enumerate(grid[1:], 1):
        length = sum(value != 0 for c, value in enumerate(row) if c != marker_col)
        if not length:
            continue
        rank = sum(other < length for other in earlier_lengths)
        result[r][marker_col] = palette[rank % len(palette)]
        earlier_lengths.append(length)
    return result
