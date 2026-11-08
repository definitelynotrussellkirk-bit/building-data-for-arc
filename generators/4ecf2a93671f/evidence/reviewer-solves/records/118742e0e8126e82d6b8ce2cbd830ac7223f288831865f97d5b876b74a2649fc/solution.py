def solve(grid):
    """Use the empty-cell pattern as both block selector and within-block stencil."""
    n = len(grid)
    if not n or any(len(row) != n for row in grid):
        raise ValueError("expected a square input")
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError("expected one foreground color")
    paint = next(iter(colors))
    zeros = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == 0]
    output = [[0] * (n * n) for _ in range(n * n)]
    for block_r, block_c in zeros:
        for inner_r, inner_c in zeros:
            output[block_r * n + inner_r][block_c * n + inner_c] = paint
    return output
