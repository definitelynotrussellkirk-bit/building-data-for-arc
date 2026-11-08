def solve(grid):
    """Recolor filled or hollow orange objects as selected by the corner."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    marker = grid[0][0]
    result = [list(row) for row in grid]
    result[0][0] = 0
    seen = set()

    for row in range(height):
        for column in range(width):
            if grid[row][column] != 7 or (row, column) in seen:
                continue

            component = []
            pending = [(row, column)]
            seen.add((row, column))
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == 7 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))

            min_row = min(r for r, c in component)
            max_row = max(r for r, c in component)
            min_column = min(c for r, c in component)
            max_column = max(c for r, c in component)
            box_area = (max_row - min_row + 1) * (max_column - min_column + 1)
            filled = len(component) == box_area

            if (marker == 2 and filled) or (marker == 1 and not filled):
                for r, c in component:
                    result[r][c] = 8

    return result
