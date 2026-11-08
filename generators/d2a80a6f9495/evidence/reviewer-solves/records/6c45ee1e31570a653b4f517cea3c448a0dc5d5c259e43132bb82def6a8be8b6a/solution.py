def solve(grid):
    """Swap colors in each two-color nonzero connected object."""
    result = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            component = []
            stack = [(row, column)]
            seen.add((row, column))
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            colors = {grid[r][c] for r, c in component}
            if len(colors) == 2:
                first, second = sorted(colors)
                for r, c in component:
                    result[r][c] = second if grid[r][c] == first else first
    return result
