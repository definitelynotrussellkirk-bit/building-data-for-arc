"""Keep odd-sized monochromatic orthogonal components."""


def solve(grid):
    """Return a copy with even-sized nonzero components erased."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                current_row, current_col = pending.pop()
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
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        pending.append((next_row, next_col))

            if len(component) % 2 == 0:
                for component_row, component_col in component:
                    result[component_row][component_col] = 0

    return result
