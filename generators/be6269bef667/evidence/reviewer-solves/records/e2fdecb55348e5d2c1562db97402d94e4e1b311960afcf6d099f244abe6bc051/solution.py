"""Visible-example solution for the blind ARC task.

Colors 1--4 emit a ray (up, right, down, left respectively).  A color-5
cell blocks a ray and is not painted.  The output records how many unblocked
rays cover each cell, including the emitter cell itself.
"""

DIRECTIONS = {
    1: (-1, 0),
    2: (0, 1),
    3: (1, 0),
    4: (0, -1),
}


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            direction = DIRECTIONS.get(grid[row][col])
            if direction is None:
                continue

            dr, dc = direction
            r, c = row, col
            while 0 <= r < height and 0 <= c < width:
                if grid[r][c] == 5:
                    break
                output[r][c] += 1
                r += dr
                c += dc

    return output
