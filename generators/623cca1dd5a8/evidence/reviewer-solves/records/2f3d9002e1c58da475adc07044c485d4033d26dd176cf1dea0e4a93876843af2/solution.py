def solve(grid):
    """Draw the bounding rectangle border of each connected colored object."""
    height, width = len(grid), len(grid[0])
    result = [[0 for _ in range(width)] for _ in range(height)]
    visited = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            pending = [(row, col)]
            visited.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        pending.append((nr, nc))
            top = min(r for r, c in cells)
            bottom = max(r for r, c in cells)
            left = min(c for r, c in cells)
            right = max(c for r, c in cells)
            for r in range(top, bottom + 1):
                result[r][left] = result[r][right] = color
            for c in range(left, right + 1):
                result[top][c] = result[bottom][c] = color
    return result
