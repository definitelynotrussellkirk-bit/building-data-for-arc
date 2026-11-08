"""Visible-example solution for the generated dc0a7662670b episode."""


def _components_by_color(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = row + drow
                    next_col = col + dcol
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == color
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            components.append((color, cells))

    return components


def _perimeter(cells):
    occupied = set(cells)
    return sum(
        (row + drow, col + dcol) not in occupied
        for row, col in occupied
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _crop(grid, cells):
    occupied = set(cells)
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)

    return [
        [
            grid[row][col] if (row, col) in occupied else 0
            for col in range(min_col, max_col + 1)
        ]
        for row in range(min_row, max_row + 1)
    ]


def solve(grid):
    """Stack cropped objects by descending exposed-edge perimeter.

    Equal-perimeter objects are ordered by ascending color, matching the fourth
    training example. Crops are left-aligned and separated by one blank row.
    """
    objects = []
    for color, cells in _components_by_color(grid):
        objects.append(
            {
                "color": color,
                "perimeter": _perimeter(cells),
                "crop": _crop(grid, cells),
            }
        )

    objects.sort(key=lambda item: (-item["perimeter"], item["color"]))
    width = max(len(item["crop"][0]) for item in objects)
    output = []

    for index, item in enumerate(objects):
        if index:
            output.append([0] * width)
        for row in item["crop"]:
            output.append(row + [0] * (width - len(row)))

    return output
