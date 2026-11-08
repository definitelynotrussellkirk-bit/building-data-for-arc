"""Visible-example solution for the post-repair ARC solve episode."""


def solve(grid):
    """Mark cells reached by cardinal rays from at least two colored seeds.

    Color 9 is an opaque wall and is preserved.  Every other nonzero color is
    a seed.  Each seed illuminates its own cell and extends in the four cardinal
    directions until a 9 cell or the grid boundary.  Non-wall cells seen by at
    least two distinct seeds become 8; all other non-wall cells become 0.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    ]
    visibility = [[0 for _ in range(width)] for _ in range(height)]

    for seed_row, seed_col in seeds:
        seen = {(seed_row, seed_col)}
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            row = seed_row + delta_row
            col = seed_col + delta_col
            while 0 <= row < height and 0 <= col < width:
                if grid[row][col] == 9:
                    break
                seen.add((row, col))
                row += delta_row
                col += delta_col
        for row, col in seen:
            visibility[row][col] += 1

    return [
        [
            9 if grid[row][col] == 9 else 8 if visibility[row][col] >= 2 else 0
            for col in range(width)
        ]
        for row in range(height)
    ]
