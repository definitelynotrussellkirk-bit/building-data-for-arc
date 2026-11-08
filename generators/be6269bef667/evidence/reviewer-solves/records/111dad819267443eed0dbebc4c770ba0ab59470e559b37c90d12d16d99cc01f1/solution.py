"""Visible-example solution for the post-repair episode."""


def solve(grid):
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    directions = {
        1: (-1, 0),
        2: (0, 1),
        3: (1, 0),
        4: (0, -1),
    }
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in directions:
                continue
            dr, dc = directions[value]
            rr, cc = row, col
            while 0 <= rr < height and 0 <= cc < width:
                if grid[rr][cc] == 5:
                    break
                output[rr][cc] += 1
                rr += dr
                cc += dc
    return output
