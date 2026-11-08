def solve(grid):
    """Replace each colored marker with its hollow 3-by-3 neighborhood."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0] * width for _ in range(height)]
    for row, line in enumerate(grid):
        for col, color in enumerate(line):
            if color == 0:
                continue
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = row + dr, col + dc
                    if (dr or dc) and 0 <= rr < height and 0 <= cc < width:
                        result[rr][cc] = color
    return result
