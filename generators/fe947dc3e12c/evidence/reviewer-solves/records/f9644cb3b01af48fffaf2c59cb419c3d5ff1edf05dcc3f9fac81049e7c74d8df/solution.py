from collections import deque


def solve(grid):
    """Recolor each 4-connected gray object according to its area."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    seen = set()
    color_by_size = {3: 2, 5: 4, 6: 1}

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 5:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            replacement = color_by_size.get(len(component), 5)
            for component_row, component_col in component:
                output[component_row][component_col] = replacement

    return output
