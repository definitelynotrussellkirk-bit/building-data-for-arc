def solve(grid):
    """Replace each colored point with a same-colored hollow 3x3 square."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0 for _ in range(width)] for _ in range(height)]

    points = [
        (row, col, color)
        for row, line in enumerate(grid)
        for col, color in enumerate(line)
        if color != 0
    ]

    for row, col, color in points:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width:
                    result[rr][cc] = color

    return result
