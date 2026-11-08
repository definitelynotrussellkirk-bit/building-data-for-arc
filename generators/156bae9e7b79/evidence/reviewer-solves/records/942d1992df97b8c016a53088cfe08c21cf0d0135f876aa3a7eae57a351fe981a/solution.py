from collections import Counter


def solve(grid):
    """Expand the top-row palette into a tent around the vertical marker."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    # The only object below the header is a vertical marker.  Select the
    # column with the most non-background cells below row zero.
    marker_rows_by_column = {
        col: [row for row in range(1, height) if grid[row][col] != background]
        for col in range(width)
    }
    marker_col, marker_rows = max(
        marker_rows_by_column.items(), key=lambda item: len(item[1])
    )
    if not marker_rows:
        return [row[:] for row in grid]

    marker_top = min(marker_rows)
    marker_bottom = max(marker_rows)
    marker_length = marker_bottom - marker_top + 1
    header = grid[0]

    result = [[background for _ in range(width)] for _ in range(height)]

    # A column at horizontal distance d from the marker has height L-d,
    # where L is the marker length.  Every column ends at the marker bottom.
    for col, color in enumerate(header):
        if col == marker_col:
            continue
        column_height = marker_length - abs(col - marker_col)
        if column_height <= 0 or color == background:
            continue
        start_row = max(0, marker_bottom - column_height + 1)
        for row in range(start_row, marker_bottom + 1):
            result[row][col] = color

    # Keep the original marker itself unchanged.
    for row in marker_rows:
        result[row][marker_col] = grid[row][marker_col]

    return result
