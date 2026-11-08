"""Visible-example solution for e4cb0224ca42."""
from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            row0, row1 = min(rows), max(rows)
            col0, col1 = min(cols), max(cols)
            middle_row = (row0 + row1) // 2
            middle_col = (col0 + col1) // 2
            for cc in range(col0, col1 + 1):
                output[middle_row][cc] = color
            for rr in range(row0, row1 + 1):
                output[rr][middle_col] = color

    return output
