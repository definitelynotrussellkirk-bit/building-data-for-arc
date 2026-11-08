"""Visible-example solution for ARC task 6afe10b621e4."""


def _components(grid, color):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
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
                    if grid[next_row][next_col] == color:
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            result.append(component)
    return result


def solve(grid):
    """Keep each source color's largest 4-connected object and recolor it."""
    output = [[0 for _ in row] for row in grid]
    for source_color, target_color in ((3, 1), (2, 4)):
        components = _components(grid, source_color)
        if not components:
            continue
        largest = max(components, key=len)
        for row, col in largest:
            output[row][col] = target_color
    return output
