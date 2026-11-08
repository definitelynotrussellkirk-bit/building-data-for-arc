def solve(grid):
    """Replace solid colored rectangles with their one-cell-wide outlines."""
    output = [list(row) for row in grid]
    if not grid:
        return output

    height, width = len(grid), len(grid[0])
    visited = set()
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in visited:
                continue

            component = []
            pending = [(row, column)]
            visited.add((row, column))
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited
                            and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        pending.append((nr, nc))

            top = min(r for r, c in component)
            bottom = max(r for r, c in component)
            left = min(c for r, c in component)
            right = max(c for r, c in component)
            if len(component) == (bottom - top + 1) * (right - left + 1):
                for r in range(top + 1, bottom):
                    for c in range(left + 1, right):
                        output[r][c] = 0

    return output
