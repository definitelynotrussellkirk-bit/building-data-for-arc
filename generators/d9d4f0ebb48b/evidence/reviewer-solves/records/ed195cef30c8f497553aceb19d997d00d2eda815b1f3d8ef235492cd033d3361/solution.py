def solve(grid):
    """Fill each monochrome five-cell orthogonal plus into a 3x3 square."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            component = set()
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                component.add((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (row + drow, col + dcol)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)

            if len(component) != 5:
                continue

            rows = [row for row, _ in component]
            cols = [col for _, col in component]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            if bottom - top != 2 or right - left != 2:
                continue

            center = (top + 1, left + 1)
            expected_plus = {
                center,
                (center[0] - 1, center[1]),
                (center[0] + 1, center[1]),
                (center[0], center[1] - 1),
                (center[0], center[1] + 1),
            }
            if component != expected_plus:
                continue

            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    result[row][col] = color

    return result
