from collections import deque


def _components_of_four(grid):
    """Return orthogonally connected components made from color 4."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 4 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == 4
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components.append(component)

    return components


def _distance_to_box(row, col, top, left, bottom, right):
    row_distance = top - row if row < top else row - bottom if row > bottom else 0
    col_distance = left - col if col < left else col - right if col > right else 0
    return row_distance + col_distance


def solve(grid):
    """Fill the hollow 4-rectangle indicated by the lone colored marker."""
    result = [row[:] for row in grid]
    marker_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 4)
    ]
    if not marker_cells:
        return result

    marker_color = marker_cells[0][2]
    marker_positions = [(row, col) for row, col, _ in marker_cells]

    candidates = []
    for component in _components_of_four(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top < 2 or right - left < 2:
            continue

        border = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if row in (top, bottom) or col in (left, right)
        }
        if not border.issubset(component):
            continue

        distance = min(
            _distance_to_box(row, col, top, left, bottom, right)
            for row, col in marker_positions
        )
        candidates.append((distance, top, left, bottom, right))

    if not candidates:
        return result

    _, top, left, bottom, right = min(candidates)
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            if result[row][col] == 0:
                result[row][col] = marker_color
    return result
