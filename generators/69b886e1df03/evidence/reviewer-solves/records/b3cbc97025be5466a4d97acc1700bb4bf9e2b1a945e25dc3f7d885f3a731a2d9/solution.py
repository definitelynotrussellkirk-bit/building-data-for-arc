def solve(grid):
    """Complete each monochromatic object to its bounding rectangle."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [list(row) for row in grid]
    visited = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            pending = [(row, col)]
            visited.add((row, col))
            component = []
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in visited and grid[rr][cc] == color):
                        visited.add((rr, cc))
                        pending.append((rr, cc))
            top = min(r for r, c in component)
            bottom = max(r for r, c in component)
            left = min(c for r, c in component)
            right = max(c for r, c in component)
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    result[r][c] = color
    return result
