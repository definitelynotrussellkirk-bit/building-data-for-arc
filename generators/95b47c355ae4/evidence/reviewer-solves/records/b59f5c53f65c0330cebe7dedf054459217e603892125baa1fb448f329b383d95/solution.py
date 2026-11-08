"""Visible-example solution for the final 95b47c355ae4 generator bytes."""


def solve(grid):
    output = [list(row) for row in grid]
    sources = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    for r, c in sources:
        output[r][c] = 0
    height = len(output)
    width = len(output[0]) if output else 0
    for r, c in sources:
        nr, nc = r + 1, c + 1
        if nr < height and nc < width:
            output[nr][nc] = 6
    return output
