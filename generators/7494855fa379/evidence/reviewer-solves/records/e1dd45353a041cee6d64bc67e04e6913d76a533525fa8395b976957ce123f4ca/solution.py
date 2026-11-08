"""Post-repair visible-example solution; earlier rule exposure is declared."""

def solve(grid):
    result = [list(row) for row in grid]
    height = len(grid)
    if height < 3:
        return result
    width = len(grid[0])
    for row in range(1, height - 1):
        for column in range(1, width - 1):
            if grid[row][column] != 0:
                continue
            complete = True
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (dr or dc) and grid[row + dr][column + dc] != 4:
                        complete = False
            if complete:
                result[row][column] = 6
    return result
