"""Retain foreground objects connected to the outer frame."""

from collections import deque


def solve(grid):
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            if any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells):
                for r, c in cells:
                    output[r][c] = color
    return output
