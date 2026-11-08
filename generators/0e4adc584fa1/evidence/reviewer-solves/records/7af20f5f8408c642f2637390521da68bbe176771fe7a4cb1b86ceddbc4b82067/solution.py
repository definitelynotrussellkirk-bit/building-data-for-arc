from collections import Counter


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid):
    """Crop the payload object and rotate it according to a 1..4 marker."""
    counts = Counter(value for row in grid for value in row if value != 0)
    marker_colors = [color for color, count in counts.items() if count == 1 and 1 <= color <= 4]
    if len(marker_colors) != 1:
        raise ValueError(f"expected one isolated 1..4 marker color, found {marker_colors}")
    marker = marker_colors[0]

    payload_cells = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != 0 and value != marker
    ]
    if not payload_cells:
        raise ValueError("payload object is empty")

    top = min(row for row, _ in payload_cells)
    bottom = max(row for row, _ in payload_cells)
    left = min(column for _, column in payload_cells)
    right = max(column for _, column in payload_cells)

    cropped = [
        [0 if value == marker else value for value in row[left : right + 1]]
        for row in grid[top : bottom + 1]
    ]

    result = cropped
    for _ in range(marker - 1):
        result = _rotate_clockwise(result)
    return result
