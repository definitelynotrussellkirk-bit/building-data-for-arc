"""Visible-only solution for reviewer task ed98575459d2."""


def solve(grid):
    """Move colored cells upward inside each vertical segment bounded by 8s."""
    result = [row[:] for row in grid]
    if not result:
        return result

    height = len(result)
    width = len(result[0])

    for column in range(width):
        start = 0
        while start < height:
            if result[start][column] == 8:
                start += 1
                continue

            end = start
            while end < height and result[end][column] != 8:
                end += 1

            colors = [
                grid[row][column]
                for row in range(start, end)
                if grid[row][column] != 0
            ]
            for offset, row in enumerate(range(start, end)):
                result[row][column] = colors[offset] if offset < len(colors) else 0

            start = end

    return result
