from copy import deepcopy


def solve(grid):
    """Complete only aligned, equal-color marker pairs across the color-5 frame."""
    out = deepcopy(grid)
    fives = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not fives:
        return out

    r1 = min(r for r, _ in fives)
    r2 = max(r for r, _ in fives)
    c1 = min(c for _, c in fives)
    c2 = max(c for _, c in fives)

    border_colors = {
        grid[r1][c] for c in range(c1, c2 + 1)
    } | {
        grid[r2][c] for c in range(c1, c2 + 1)
    } | {
        grid[r][c1] for r in range(r1, r2 + 1)
    } | {
        grid[r][c2] for r in range(r1, r2 + 1)
    }

    for color in sorted(border_colors - {0, 5}):
        for c in range(c1 + 1, c2):
            if grid[r1][c] == color and grid[r2][c] == color:
                for r in range(r1 + 1, r2):
                    out[r][c] = color
        for r in range(r1 + 1, r2):
            if grid[r][c1] == color and grid[r][c2] == color:
                for c in range(c1 + 1, c2):
                    out[r][c] = color
    return out
