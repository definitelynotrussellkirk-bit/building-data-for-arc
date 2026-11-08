def solve(grid):
    """Rotate marked tiles clockwise, recolor every retained shape cell to 8."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    separator_rows = {r for r, row in enumerate(grid) if all(v == 9 for v in row)}
    separator_cols = {
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    }

    out = [[0 for _ in range(width)] for _ in range(height)]
    for r in separator_rows:
        out[r] = [9] * width
    for c in separator_cols:
        for r in range(height):
            out[r][c] = 9

    def spans(limit, separators):
        start = 0
        for cut in sorted(separators):
            if start < cut:
                yield start, cut
            start = cut + 1
        if start < limit:
            yield start, limit

    row_spans = list(spans(height, separator_rows))
    col_spans = list(spans(width, separator_cols))

    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            block_h = r1 - r0
            block_w = c1 - c0
            marked = any(
                grid[r][c] == 3
                for r in range(r0, r1)
                for c in range(c0, c1)
            )
            twos = [
                (r - r0, c - c0)
                for r in range(r0, r1)
                for c in range(c0, c1)
                if grid[r][c] == 2
            ]

            if marked and block_h == block_w:
                # A 3 anywhere in a square tile is an instruction marker:
                # discard all 3s and rotate the 2-pattern one quarter-turn clockwise.
                twos = [(c, block_h - 1 - r) for r, c in twos]

            for r, c in twos:
                out[r0 + r][c0 + c] = 8

    return out
