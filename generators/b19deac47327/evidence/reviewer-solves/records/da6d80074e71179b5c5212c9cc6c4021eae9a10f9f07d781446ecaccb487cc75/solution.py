"""Use the visible pair of colored borders to extend each blue marker."""


def solve(grid):
    result = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    top, bottom = grid[0], grid[-1]
    horizontal = (len(set(top)) == len(set(bottom)) == 1
                  and top[0] not in (0, 1) and bottom[0] not in (0, 1)
                  and top[0] != bottom[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1:
                continue
            if horizontal:
                if row <= height - 1 - row:
                    result[row - 1][col] = top[0]
                else:
                    result[row + 1][col] = bottom[0]
            else:
                if col <= width - 1 - col:
                    result[row][col - 1] = grid[0][0]
                else:
                    result[row][col + 1] = grid[0][-1]
    return result
