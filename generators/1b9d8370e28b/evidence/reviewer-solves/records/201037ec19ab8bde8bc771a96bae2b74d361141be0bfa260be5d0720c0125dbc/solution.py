from __future__ import annotations


def solve(grid):
    """Pack red overlays left on color 8 and right on color 1 regions."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    background_colors = (1, 8)

    row_labels = []
    row_cost = 0
    for row in grid:
        counts = {color: sum(value == color for value in row) for color in background_colors}
        label = max(background_colors, key=lambda color: (counts[color], -color))
        row_labels.append(label if counts[label] else None)
        row_cost += sum(value not in (2, label) for value in row)

    column_labels = []
    column_cost = 0
    for column in range(width):
        counts = {
            color: sum(grid[row][column] == color for row in range(height))
            for color in background_colors
        }
        label = max(background_colors, key=lambda color: (counts[color], -color))
        column_labels.append(label if counts[label] else None)
        column_cost += sum(
            grid[row][column] not in (2, label) for row in range(height)
        )

    if row_cost <= column_cost:
        known = [label for label in row_labels if label is not None]
        fallback = max(background_colors, key=known.count) if known else 8
        for index, label in enumerate(row_labels):
            if label is None:
                nearest = next(
                    (
                        row_labels[other]
                        for distance in range(1, height)
                        for other in (index - distance, index + distance)
                        if 0 <= other < height and row_labels[other] is not None
                    ),
                    fallback,
                )
                row_labels[index] = nearest
        background = [[row_labels[row]] * width for row in range(height)]
    else:
        known = [label for label in column_labels if label is not None]
        fallback = max(background_colors, key=known.count) if known else 8
        for index, label in enumerate(column_labels):
            if label is None:
                nearest = next(
                    (
                        column_labels[other]
                        for distance in range(1, width)
                        for other in (index - distance, index + distance)
                        if 0 <= other < width and column_labels[other] is not None
                    ),
                    fallback,
                )
                column_labels[index] = nearest
        background = [list(column_labels) for _ in range(height)]

    result = [row[:] for row in background]
    for row in range(height):
        start = 0
        while start < width:
            color = background[row][start]
            end = start + 1
            while end < width and background[row][end] == color:
                end += 1

            red_count = sum(grid[row][column] == 2 for column in range(start, end))
            if color == 8:
                red_columns = range(start, start + red_count)
            else:
                red_columns = range(end - red_count, end)
            for column in red_columns:
                result[row][column] = 2
            start = end

    return result
