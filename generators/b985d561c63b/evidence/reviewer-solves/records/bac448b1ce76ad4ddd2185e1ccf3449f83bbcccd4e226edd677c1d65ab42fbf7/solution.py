from collections import deque


def _components_of_color(grid, color):
    """Return 4-connected components as lists of (row, column) cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
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
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(component)
    return components


def solve(grid):
    """Stamp the multicolored template into every gray rectangular canvas."""
    if not grid:
        return []
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    template_cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]
    if not template_cells:
        return [row[:] for row in grid]

    min_row = min(row for row, _ in template_cells)
    max_row = max(row for row, _ in template_cells)
    min_col = min(col for _, col in template_cells)
    max_col = max(col for _, col in template_cells)
    template = [
        grid[row][min_col : max_col + 1]
        for row in range(min_row, max_row + 1)
    ]
    template_height = len(template)
    template_width = len(template[0])

    result = [row[:] for row in grid]
    for component in _components_of_color(grid, 5):
        target_min_row = min(row for row, _ in component)
        target_max_row = max(row for row, _ in component)
        target_min_col = min(col for _, col in component)
        target_max_col = max(col for _, col in component)
        target_height = target_max_row - target_min_row + 1
        target_width = target_max_col - target_min_col + 1

        component_set = set(component)
        is_rectangle = all(
            (row, col) in component_set
            for row in range(target_min_row, target_max_row + 1)
            for col in range(target_min_col, target_max_col + 1)
        )
        if not is_rectangle:
            continue
        if template_height > target_height or template_width > target_width:
            continue

        for row_offset, template_row in enumerate(template):
            for col_offset, value in enumerate(template_row):
                result[target_min_row + row_offset][target_min_col + col_offset] = value

    return result
