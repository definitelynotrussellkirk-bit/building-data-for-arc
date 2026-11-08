"""Solve the visible lesson by preserving each monochrome component's boundary."""
from collections import deque


def solve(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError('expected a nonempty grid')
    width = len(grid[0])
    if not width or any(len(row) != width for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    height = len(grid)
    result = [list(row) for row in grid]
    visited = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            queue = deque([(row, col)])
            visited.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in visited and grid[rr][cc] == color):
                        visited.add((rr, cc))
                        queue.append((rr, cc))
            top = min(r for r, c in component)
            bottom = max(r for r, c in component)
            left = min(c for r, c in component)
            right = max(c for r, c in component)
            for r, c in component:
                if top < r < bottom and left < c < right:
                    result[r][c] = 0
    return result
