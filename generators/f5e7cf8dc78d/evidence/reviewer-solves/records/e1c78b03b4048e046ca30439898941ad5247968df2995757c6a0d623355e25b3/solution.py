def solve(grid):
    """Expand colored row markers into horizontal dividers and side walls.

    Every nonzero input cell marks a divider row and supplies that row's color.
    The top and bottom grid rows are also dividers, colored by the nearest marker.
    Other rows contain only the two side-wall cells, colored by the nearest marker
    row; an equal-distance tie is resolved toward the upper marker.
    """
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    if width == 0:
        return [[] for _ in grid]

    markers = []
    for row_index, row in enumerate(grid):
        for value in row:
            if value != 0:
                markers.append((row_index, value))

    if not markers:
        return [list(row) for row in grid]

    markers.sort(key=lambda item: item[0])
    marker_rows = {row for row, _ in markers}
    output = [[0] * width for _ in range(height)]

    for row_index in range(height):
        # Tuple ordering gives the upper marker priority on equal distance.
        _, marker_row, color = min(
            (abs(row_index - marker_row), marker_row, color)
            for marker_row, color in markers
        )

        if row_index in marker_rows or row_index in (0, height - 1):
            output[row_index] = [color] * width
        else:
            output[row_index][0] = color
            output[row_index][-1] = color

    return output
