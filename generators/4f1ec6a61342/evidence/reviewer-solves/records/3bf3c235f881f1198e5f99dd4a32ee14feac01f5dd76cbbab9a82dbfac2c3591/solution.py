"""Select rooms whose red-cell count equals the upper-left marker."""

from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    target = grid[0][0]
    result = [[5 if value == 5 else 0 for value in row] for row in grid]
    result[0][0] = 0
    seen = {(0, 0)}

    for row in range(height):
        for column in range(width):
            if (row, column) in seen or grid[row][column] == 5:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            room = []
            red_count = 0
            while queue:
                r, c = queue.popleft()
                room.append((r, c))
                red_count += grid[r][c] == 2
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] != 5):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            if red_count == target:
                for r, c in room:
                    result[r][c] = 8
    return result
