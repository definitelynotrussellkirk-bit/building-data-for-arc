def solve(grid):
    """Fill each non-wall region according to the parity of its blue markers."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in seen:
                continue

            component = []
            stack = [(row, col)]
            seen.add((row, col))
            marker_count = 0

            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                marker_count += grid[current_row][current_col] == 2

                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 5:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            fill = 0 if marker_count == 0 else (7 if marker_count % 2 == 0 else 8)
            for component_row, component_col in component:
                result[component_row][component_col] = fill

    return result
