"""Infer the transformation from visible examples only."""


def solve(grid):
    output = [list(row) for row in grid]
    height = len(grid)
    if height == 0:
        return output
    width = len(grid[0])
    visited = set()

    for row in range(height):
        for column in range(width):
            start = (row, column)
            if grid[row][column] == 5 or start in visited:
                continue

            visited.add(start)
            stack = [start]
            region = []
            red_count = 0
            while stack:
                r, c = stack.pop()
                region.append((r, c))
                red_count += grid[r][c] == 2
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in visited
                        and grid[nr][nc] != 5
                    ):
                        visited.add((nr, nc))
                        stack.append((nr, nc))

            if red_count == 2:
                for r, c in region:
                    if grid[r][c] == 0:
                        output[r][c] = 8

    return output
