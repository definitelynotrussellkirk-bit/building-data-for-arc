"""Recolor separate same-color components according to bounding-box aspect."""
from collections import deque


def solve(grid):
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError('Expected a nonempty grid')
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError('Expected rectangular rows')
    result = [[0 for _ in range(width)] for _ in range(height)]
    visited = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in visited:
                continue
            original_color = grid[row][col]
            queue = deque([(row, col)])
            visited.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in visited
                            and grid[rr][cc] == original_color):
                        visited.add((rr, cc)); queue.append((rr, cc))
            dh = max(r for r,c in cells) - min(r for r,c in cells)
            dw = max(c for r,c in cells) - min(c for r,c in cells)
            color = 2 if dh > dw else 3 if dw > dh else 4
            for r, c in cells:
                result[r][c] = color
    return result
