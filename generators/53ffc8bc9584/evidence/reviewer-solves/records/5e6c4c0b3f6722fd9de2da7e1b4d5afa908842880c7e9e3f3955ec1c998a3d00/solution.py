"""Fresh exposed solve, written from the displayed challenge examples."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            for vertical in (-1, 1):
                for horizontal in (-1, 1):
                    other_row, other_col = row + vertical, col + horizontal
                    if not (0 <= other_row < height and 0 <= other_col < width):
                        continue
                    if (grid[other_row][col] == 4
                            and grid[row][other_col] == 4
                            and grid[other_row][other_col] == 4):
                        result[row][col] = 9
    return result
