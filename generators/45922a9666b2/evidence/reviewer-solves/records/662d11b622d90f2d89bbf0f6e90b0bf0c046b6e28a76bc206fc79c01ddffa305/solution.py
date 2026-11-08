"""Extend red starts upward, making right detours at gray obstacles."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    starts = [col for col, value in enumerate(grid[-1]) if value == 2]
    for start_col in starts:
        row, col = height - 1, start_col
        while True:
            output[row][col] = 2
            if row == 0:
                break
            if grid[row - 1][col] != 5:
                row -= 1
            elif col + 1 < width and grid[row][col + 1] != 5:
                col += 1
            else:
                break
    return output
