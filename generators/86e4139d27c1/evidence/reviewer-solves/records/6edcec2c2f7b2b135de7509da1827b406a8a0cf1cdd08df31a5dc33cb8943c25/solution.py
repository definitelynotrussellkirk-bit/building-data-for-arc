def solve(grid):
    """Paint a green plus at the midpoint of the two blue markers."""
    out = [list(row) for row in grid]
    markers = [(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 1]
    if len(markers) != 2:
        raise ValueError("Expected two blue markers")
    r = (markers[0][0] + markers[1][0]) // 2
    c = (markers[0][1] + markers[1][1]) // 2
    for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
            out[rr][cc] = 3
    return out
