"""Visible-only solution for task ceef568b1cd4.

Remove every 4-connected non-background component whose area is a non-trivial
power of two (2, 4, 8, ...).  Keep all other components unchanged.
"""


def _is_nontrivial_power_of_two(value: int) -> bool:
    return value > 1 and (value & (value - 1)) == 0


def solve(grid):
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]
    seen = [[False] * width for _ in range(height)]

    for row in range(height):
        if len(grid[row]) != width:
            raise ValueError("grid must be rectangular")
        for col in range(width):
            color = grid[row][col]
            if color == 0 or seen[row][col]:
                continue

            component = []
            stack = [(row, col)]
            seen[row][col] = True

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
                    if seen[next_row][next_col]:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen[next_row][next_col] = True
                    stack.append((next_row, next_col))

            if _is_nontrivial_power_of_two(len(component)):
                for component_row, component_col in component:
                    result[component_row][component_col] = 0

    return result
