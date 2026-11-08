from collections import Counter


def solve(grid):
    """Erase the foreground and mark its exterior cardinal neighbors."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    counts = Counter(value for row in grid for value in row)
    background = max(counts, key=counts.get)
    foreground_colors = [color for color in counts if color != background]
    if not foreground_colors:
        return [list(row) for row in grid]
    marker = min(foreground_colors, key=counts.get)
    height, width = len(grid), len(grid[0])
    output = [[background] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background:
                continue
            for rr, cc in ((row - 1, col), (row + 1, col),
                           (row, col - 1), (row, col + 1)):
                if (0 <= rr < height and 0 <= cc < width
                        and grid[rr][cc] == background):
                    output[rr][cc] = marker
    return output
