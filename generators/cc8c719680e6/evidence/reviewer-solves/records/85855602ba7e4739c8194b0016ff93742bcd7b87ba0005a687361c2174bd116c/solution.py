def solve(grid):
    """Replace each monochromatic edge-connected object by its box outline."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0] * width for _ in range(height)]
    visited = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue

            visited.add((row, col))
            stack = [(row, col)]
            top = bottom = row
            left = right = col

            while stack:
                r, c = stack.pop()
                top = min(top, r)
                bottom = max(bottom, r)
                left = min(left, c)
                right = max(right, c)
                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited
                            and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        stack.append((nr, nc))

            for c in range(left, right + 1):
                result[top][c] = color
                result[bottom][c] = color
            for r in range(top, bottom + 1):
                result[r][left] = color
                result[r][right] = color

    return result
