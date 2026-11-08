def _transform(panel, code):
    n = len(panel)
    out = [[0] * n for _ in range(n)]
    for row in range(n):
        for col in range(n):
            if code == 0:       # identity
                nr, nc = row, col
            elif code == 1:     # rotate 90 degrees clockwise
                nr, nc = col, n - 1 - row
            elif code == 2:     # rotate 180 degrees
                nr, nc = n - 1 - row, n - 1 - col
            elif code == 3:     # rotate 90 degrees counter-clockwise
                nr, nc = n - 1 - col, row
            elif code == 4:     # reflect left/right
                nr, nc = row, n - 1 - col
            elif code == 5:     # reflect up/down
                nr, nc = n - 1 - row, col
            elif code == 6:     # transpose across the main diagonal
                nr, nc = col, row
            elif code == 7:     # transpose across the anti-diagonal
                nr, nc = n - 1 - col, n - 1 - row
            else:
                raise ValueError("unknown transform")
            out[nr][nc] = panel[row][col]
    return out


def solve(grid):
    """Infer the A->B square symmetry and apply it to panel C."""
    n = len(grid)
    if n == 0 or any(len(row) != 3 * n + 2 for row in grid):
        raise ValueError("expected three n-by-n panels separated by two columns")

    panel_a = [row[:n] for row in grid]
    panel_b = [row[n + 1 : 2 * n + 1] for row in grid]
    panel_c = [row[2 * n + 2 :] for row in grid]

    matches = [code for code in range(8) if _transform(panel_a, code) == panel_b]
    if len(matches) != 1:
        raise ValueError(f"expected one square symmetry mapping A to B, found {matches}")
    return _transform(panel_c, matches[0])
