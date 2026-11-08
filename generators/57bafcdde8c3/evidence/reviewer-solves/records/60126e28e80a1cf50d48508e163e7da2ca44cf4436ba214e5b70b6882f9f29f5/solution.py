from collections import Counter


def solve(grid):
    """Recolor every non-background 4-connected component of size > 1 azure."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=counts.get)

    result = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == background:
                continue

            color = grid[row][col]
            component = []
            stack = [(row, col)]
            seen.add((row, col))

            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for row_step, col_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + row_step
                    next_col = current_col + col_step
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            if len(component) > 1:
                for component_row, component_col in component:
                    result[component_row][component_col] = 8

    return result
