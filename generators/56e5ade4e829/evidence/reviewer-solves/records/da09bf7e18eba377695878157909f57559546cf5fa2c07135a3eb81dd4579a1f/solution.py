"""Visible-example solution for the assigned blind ARC task."""


def _crop_mask(grid, color):
    cells = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == color
    ]
    if not cells:
        return []

    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)
    return [
        [grid[row][col] == color for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]


def _padded(mask, height, width):
    return [
        [
            row < len(mask)
            and col < len(mask[row])
            and mask[row][col]
            for col in range(width)
        ]
        for row in range(height)
    ]


def _trim(mask):
    occupied = [
        (row_index, col_index)
        for row_index, row in enumerate(mask)
        for col_index, value in enumerate(row)
        if value
    ]
    if not occupied:
        return [[False]]

    min_row = min(row for row, _ in occupied)
    max_row = max(row for row, _ in occupied)
    min_col = min(col for _, col in occupied)
    max_col = max(col for _, col in occupied)
    return [
        row[min_col : max_col + 1]
        for row in mask[min_row : max_row + 1]
    ]


def solve(grid):
    """Combine the cropped color-1 and color-2 shapes by the marker operation."""
    first = _crop_mask(grid, 1)
    second = _crop_mask(grid, 2)
    if not first or not second:
        raise ValueError("expected both a color-1 object and a color-2 object")

    marker_colors = {
        value
        for row in grid
        for value in row
        if value not in (0, 1, 2)
    }
    if len(marker_colors) != 1:
        raise ValueError("expected exactly one operation-marker color")
    marker = marker_colors.pop()

    height = max(len(first), len(second))
    width = max(len(first[0]), len(second[0]))
    first = _padded(first, height, width)
    second = _padded(second, height, width)

    operations = {
        3: lambda a, b: a and b,
        4: lambda a, b: a or b,
        7: lambda a, b: a != b,
        8: lambda a, b: a and not b,
    }
    if marker not in operations:
        raise ValueError(f"unsupported operation-marker color: {marker}")
    operation = operations[marker]

    combined = [
        [operation(first[row][col], second[row][col]) for col in range(width)]
        for row in range(height)
    ]
    return [[8 if value else 0 for value in row] for row in _trim(combined)]
