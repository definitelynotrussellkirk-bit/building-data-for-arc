def solve(grid):
    """Fill each non-gray region that contains exactly one colored marker."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 5 or (start_row, start_col) in seen:
                continue

            component = []
            markers = []
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))

            while stack:
                row, col = stack.pop()
                component.append((row, col))
                if grid[row][col] not in (0, 5):
                    markers.append((row, col))

                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row, next_col = row + drow, col + dcol
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 5:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            if len(markers) == 1:
                marker_row, marker_col = markers[0]
                fill_color = grid[marker_row][marker_col]
                for row, col in component:
                    if result[row][col] == 0:
                        result[row][col] = fill_color

    return result
