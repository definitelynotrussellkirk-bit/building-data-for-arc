"""Visible-example hypothesis: four rays from each red seed, blocked by grey."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2:
                continue
            result[row][col] = 8
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + dr, col + dc
                while 0 <= rr < height and 0 <= cc < width:
                    if grid[rr][cc] == 5:
                        break
                    result[rr][cc] = 8
                    rr += dr
                    cc += dc
    return result
