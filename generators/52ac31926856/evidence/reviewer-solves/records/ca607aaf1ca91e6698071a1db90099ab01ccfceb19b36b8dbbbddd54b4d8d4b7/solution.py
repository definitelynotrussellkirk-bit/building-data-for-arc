"""Visible-example solution for the blind ARC episode."""


def _bands_with_color(grid, color):
    """Return inclusive row bands containing *color*, split by empty rows."""
    rows = [r for r, row in enumerate(grid) if color in row]
    if not rows:
        return []

    bands = []
    start = previous = rows[0]
    for row in rows[1:]:
        if row != previous + 1:
            bands.append((start, previous))
            start = row
        previous = row
    bands.append((start, previous))
    return bands


def _closed_basin(grid, top, bottom, drop_column):
    """Find the narrowest closed, vertical-sided basin under the drop column."""
    width = len(grid[0])
    walls = [
        column
        for column in range(width)
        if all(grid[row][column] == 2 for row in range(top, bottom + 1))
    ]

    candidates = []
    for left_index, left in enumerate(walls):
        for right in walls[left_index + 1 :]:
            if not (left < drop_column < right):
                continue
            if all(grid[bottom][column] == 2 for column in range(left, right + 1)):
                candidates.append((right - left, left, right))

    if not candidates:
        return None
    _, left, right = min(candidates)
    return left, right


def solve(grid):
    """Drop color 1 through leaky color-2 vessels and fill the first closed one."""
    result = [row[:] for row in grid]
    marker_columns = []

    for row_index, row in enumerate(result):
        for column, value in enumerate(row):
            if value == 1:
                marker_columns.append(column)
                result[row_index][column] = 0

    if not marker_columns:
        return result
    drop_column = marker_columns[0]

    for top, bottom in _bands_with_color(result, 2):
        basin = _closed_basin(result, top, bottom, drop_column)
        if basin is None:
            continue
        left, right = basin
        for row in range(top, bottom):
            for column in range(left + 1, right):
                if result[row][column] == 0:
                    result[row][column] = 1
        return result

    # Every aligned vessel leaks, so the liquid reaches and spreads along the floor.
    floor = len(result) - 1
    for column, value in enumerate(result[floor]):
        if value == 0:
            result[floor][column] = 1
    return result
