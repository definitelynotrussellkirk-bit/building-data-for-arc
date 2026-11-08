def solve(grid):
    """Erase each same-color, orthogonally connected object reaching an edge."""
    height, width = len(grid), len(grid[0])
    answer = [list(row) for row in grid]
    visited = set()
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in visited:
                continue
            cells = []
            stack = [(row, column)]
            visited.add((row, column))
            reaches_edge = False
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                reaches_edge |= r in (0, height - 1) or c in (0, width - 1)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            if reaches_edge:
                for r, c in cells:
                    answer[r][c] = 0
    return answer
