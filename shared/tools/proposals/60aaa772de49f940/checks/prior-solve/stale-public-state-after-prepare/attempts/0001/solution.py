def solve(grid):
    red = next((r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 2)
    green = next((r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == 3)
    rr, rc = red
    gr, gc = green
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            on_horizontal = r == rr and min(rc, gc) <= c <= max(rc, gc)
            on_vertical = c == gc and min(rr, gr) <= r <= max(rr, gr)
            if (r, c) not in (red, green) and (on_horizontal or on_vertical):
                result[r][c] = 8
    return result
