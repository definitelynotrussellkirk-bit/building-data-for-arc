from collections import deque


def _components(grid):
    """Return nonzero 4-connected components below the marker row."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []

            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (1 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            components.append((color, cells))

    return components


def solve(grid):
    if not grid or not grid[0]:
        return []

    marker_colors = [color for color in grid[0] if color != 0]
    components = _components(grid)

    # Largest shapes are used first.  Equal-sized shapes retain their
    # left-to-right order in the source scene.
    components.sort(
        key=lambda item: (
            -len(item[1]),
            min(col for _, col in item[1]),
            min(row for row, _ in item[1]),
        )
    )

    if len(marker_colors) != len(components):
        raise ValueError(
            f"expected one marker per object, got {len(marker_colors)} markers "
            f"and {len(components)} objects"
        )

    bounds = []
    for _, cells in components:
        min_row = min(row for row, _ in cells)
        max_row = max(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        max_col = max(col for _, col in cells)
        bounds.append((min_row, max_row, min_col, max_col))

    output_width = max((max_col - min_col + 1 for _, _, min_col, max_col in bounds), default=0)
    output = []

    for index, ((_, cells), marker_color, bound) in enumerate(
        zip(components, marker_colors, bounds)
    ):
        min_row, max_row, min_col, max_col = bound
        shape_width = max_col - min_col + 1
        left_padding = (output_width - shape_width) // 2
        cell_set = set(cells)

        for row in range(min_row, max_row + 1):
            output_row = [0] * output_width
            for col in range(min_col, max_col + 1):
                if (row, col) in cell_set:
                    output_row[left_padding + col - min_col] = marker_color
            output.append(output_row)

        if index + 1 < len(components):
            output.append([0] * output_width)

    return output
