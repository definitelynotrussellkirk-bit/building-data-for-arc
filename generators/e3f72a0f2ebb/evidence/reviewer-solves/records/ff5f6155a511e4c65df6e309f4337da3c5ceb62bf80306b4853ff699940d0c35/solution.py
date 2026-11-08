from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    visited = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            pending = deque([(row, col)])
            visited.add((row, col))
            top = bottom = row
            left = right = col
            while pending:
                rr, cc = pending.popleft()
                top, bottom = min(top, rr), max(bottom, rr)
                left, right = min(left, cc), max(right, cc)
                for nr, nc in ((rr - 1, cc), (rr + 1, cc),
                               (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        pending.append((nr, nc))
            for cc in range(left, right + 1):
                output[top][cc] = color
                output[bottom][cc] = color
            for rr in range(top, bottom + 1):
                output[rr][left] = color
                output[rr][right] = color
    return output
