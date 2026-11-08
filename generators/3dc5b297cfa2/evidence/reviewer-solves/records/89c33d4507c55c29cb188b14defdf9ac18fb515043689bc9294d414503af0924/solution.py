from collections import Counter


def solve(grid):
    """Swap the shape's two colors; move its top bbox half right."""
    h = len(grid)
    w = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    cells = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != background
    ]
    colors = sorted({value for _, _, value in cells})
    if len(colors) != 2:
        return [row[:] for row in grid]

    first, second = colors
    swapped = {first: second, second: first}
    rows = [r for r, _, _ in cells]
    cols = [c for _, c, _ in cells]
    r_min, r_max = min(rows), max(rows)
    c_min, c_max = min(cols), max(cols)
    midpoint = (r_min + r_max) // 2

    if 0 in colors:
        nonzero_cols = [c for _, c, value in cells if value != 0]
        shift = max(nonzero_cols) - min(nonzero_cols) + 1
    else:
        shift = c_max - c_min + 1

    result = [[background for _ in range(w)] for _ in range(h)]
    for r, c, value in cells:
        out_c = c + shift if r <= midpoint else c
        result[r][out_c] = swapped[value]
    return result
