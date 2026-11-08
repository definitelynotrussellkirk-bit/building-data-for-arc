"""Visible-example solver for the rectangle-interior task."""


def solve(grid):
    """Fill every strict interior whose four axis-aligned corners are yellow (4)."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [list(row) for row in grid]

    yellow_by_row = {
        row: {col for col, value in enumerate(grid[row]) if value == 4}
        for row in range(height)
    }
    yellow_rows = [row for row, cols in yellow_by_row.items() if len(cols) >= 2]

    for top_index, top in enumerate(yellow_rows):
        for bottom in yellow_rows[top_index + 1 :]:
            if bottom - top < 2:
                continue
            shared_columns = sorted(yellow_by_row[top] & yellow_by_row[bottom])
            for left_index, left in enumerate(shared_columns):
                for right in shared_columns[left_index + 1 :]:
                    if right - left < 2:
                        continue
                    for row in range(top + 1, bottom):
                        for col in range(left + 1, right):
                            if output[row][col] == 0:
                                output[row][col] = 2

    return output
