from collections import deque


def _components(grid, color):
    """Return 4-connected components of *color* as sets of (row, col)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.add((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == color
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components.append(component)

    return components


def _relation(component, reference):
    """Classify a component relative to the reference: axis, diagonal, or neither.

    Axis alignment takes precedence when a component has both an axis-aligned and
    a diagonal cell pair, matching the visible examples.
    """
    for row, col in component:
        for reference_row, reference_col in reference:
            if row == reference_row or col == reference_col:
                return "axis"

    for row, col in component:
        for reference_row, reference_col in reference:
            if abs(row - reference_row) == abs(col - reference_col):
                return "diagonal"

    return "neither"


def solve(grid):
    output = [row[:] for row in grid]
    non_background_colors = {
        value for row in grid for value in row if value not in (0, 1)
    }
    if len(non_background_colors) != 1:
        return output

    reference_color = next(iter(non_background_colors))
    references = _components(grid, reference_color)
    if len(references) != 1:
        return output
    reference = references[0]

    target_relation = {
        9: "axis",
        4: "diagonal",
        6: "neither",
    }.get(reference_color)
    if target_relation is None:
        return output

    for component in _components(grid, 1):
        if _relation(component, reference) == target_relation:
            for row, col in component:
                output[row][col] = 2

    return output
