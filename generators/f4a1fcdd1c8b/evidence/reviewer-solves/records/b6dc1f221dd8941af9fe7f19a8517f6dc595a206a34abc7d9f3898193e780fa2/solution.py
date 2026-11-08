def solve(grid):
    """Erase nonzero 4-connected components that do not touch the border."""
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    output = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            stack = [(row, col)]
            seen.add((row, col))
            touches_border = False

            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                if (
                    current_row == 0
                    or current_row == height - 1
                    or current_col == 0
                    or current_col == width - 1
                ):
                    touches_border = True

                for row_step, col_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + row_step
                    next_col = current_col + col_step
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            if not touches_border:
                for component_row, component_col in component:
                    output[component_row][component_col] = 0

    return output
