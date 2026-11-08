"""Extract zero-cell components that cannot reach a grid edge."""
from collections import deque


def solve(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError('expected a nonempty grid')
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError('expected integer colors 0 through 9')
    output = [[0 for _ in range(width)] for _ in range(height)]
    visited = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in visited:
                continue
            frontier = deque([(row, col)])
            visited.add((row, col))
            cells = []
            reaches_edge = False
            while frontier:
                r, c = frontier.popleft()
                cells.append((r, c))
                reaches_edge |= r == 0 or c == 0 or r == height-1 or c == width-1
                for nr, nc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                    if (0 <= nr < height and 0 <= nc < width and grid[nr][nc] == 0
                            and (nr,nc) not in visited):
                        visited.add((nr,nc))
                        frontier.append((nr,nc))
            if not reaches_edge:
                for r, c in cells:
                    output[r][c] = 8
    return output
