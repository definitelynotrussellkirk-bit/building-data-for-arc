from collections import Counter


def solve(grid):
    """Move one cell from each smaller object to the largest object.

    The four colored objects sit in the four quadrants around the canvas center.
    Each smaller object loses its uniquely innermost cell.  The largest object
    receives the three cells as a straight bar continuing its outward-facing
    end; the side and alignment of that bar are determined by its quadrant.
    """
    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    objects = {}
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color != background:
                objects.setdefault(color, set()).add((row, column))

    largest_color = max(objects, key=lambda color: len(objects[color]))
    center_row = (height - 1) / 2
    center_column = (width - 1) / 2

    # The three smaller objects surrender their closest-to-center cell.
    for color, cells in objects.items():
        if color == largest_color:
            continue
        inward_cell = min(
            cells,
            key=lambda point: (
                (point[0] - center_row) ** 2 + (point[1] - center_column) ** 2,
                point,
            ),
        )
        result[inward_cell[0]][inward_cell[1]] = background

    cells = objects[largest_color]
    minimum_row = min(row for row, _ in cells)
    maximum_row = max(row for row, _ in cells)
    minimum_column = min(column for _, column in cells)
    maximum_column = max(column for _, column in cells)
    mean_row = sum(row for row, _ in cells) / len(cells)
    mean_column = sum(column for _, column in cells) / len(cells)

    top = mean_row < center_row
    left = mean_column < center_column

    if top and left:
        additions = [(row, minimum_column - 1) for row in range(maximum_row - 1, maximum_row + 2)]
    elif top and not left:
        additions = [(minimum_row - 1, column) for column in range(minimum_column - 1, minimum_column + 2)]
    elif not top and left:
        additions = [(maximum_row + 1, column) for column in range(maximum_column - 1, maximum_column + 2)]
    else:
        additions = [(row, maximum_column + 1) for row in range(minimum_row - 1, minimum_row + 2)]

    for row, column in additions:
        if 0 <= row < height and 0 <= column < width:
            result[row][column] = largest_color

    return result
