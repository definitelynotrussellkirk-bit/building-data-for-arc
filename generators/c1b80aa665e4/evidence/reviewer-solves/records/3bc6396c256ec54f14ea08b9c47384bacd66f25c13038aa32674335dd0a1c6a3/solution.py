def solve(grid):
    """Recolor singleton orthogonal nonzero components to 9."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
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
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            if len(component) == 1:
                singleton_row, singleton_col = component[0]
                out[singleton_row][singleton_col] = 9

    return out
