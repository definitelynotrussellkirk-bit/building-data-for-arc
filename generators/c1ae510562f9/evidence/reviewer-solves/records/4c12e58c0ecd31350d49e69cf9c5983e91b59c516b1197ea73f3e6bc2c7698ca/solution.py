"""Visible-example solution for the post-repair ARC challenge."""


def solve(grid):
    gray = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not gray:
        return [[0] * 3 for _ in range(3)]

    top = min(r for r, _ in gray)
    floor = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)

    empty_rows = sum(
        all(grid[r][c] == 0 for c in range(left + 1, right))
        for r in range(top, floor)
    )

    clockwise = (
        (0, 0), (0, 1), (0, 2),
        (1, 2),
        (2, 2), (2, 1), (2, 0),
        (1, 0),
        (1, 1),
    )
    output = [[0] * 3 for _ in range(3)]
    for r, c in clockwise[:empty_rows]:
        output[r][c] = 8
    return output
