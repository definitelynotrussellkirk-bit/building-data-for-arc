def solve(grid):
    """Replace the two orange endpoints by one azure cell at their midpoint."""
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two cells of color 4, found {len(points)}")

    (r1, c1), (r2, c2) = points
    if (r1 + r2) % 2 or (c1 + c2) % 2:
        raise ValueError("the two endpoints do not have an integral midpoint")

    out = [[0 for _ in row] for row in grid]
    out[(r1 + r2) // 2][(c1 + c2) // 2] = 8
    return out
