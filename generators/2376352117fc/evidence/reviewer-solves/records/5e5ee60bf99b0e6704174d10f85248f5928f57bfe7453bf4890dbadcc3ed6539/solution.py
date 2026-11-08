def solve(grid):
    """Translate the green shape by the vector from blue to red; recolor cyan."""
    height, width = len(grid), len(grid[0])
    markers = {
        color: [(r, c) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value == color]
        for color in (1, 2)
    }
    if len(markers[1]) != 1 or len(markers[2]) != 1:
        raise ValueError("Expected one blue marker and one red marker")
    start, end = markers[1][0], markers[2][0]
    dr, dc = end[0] - start[0], end[1] - start[1]
    output = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            rr, cc = r + dr, c + dc
            if value == 3 and 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = 8
    return output
