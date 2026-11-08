def solve(grid):
    """Stretch the green motif toward aligned purple markers."""
    out = [list(row) for row in grid]
    green = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if not green:
        return out
    r0, r1 = min(r for r, _ in green), max(r for r, _ in green)
    c0, c1 = min(c for _, c in green), max(c for _, c in green)
    marks = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6]
    above = [r for r, c in marks if r < r0 and c0 <= c <= c1]
    below = [r for r, c in marks if r > r1 and c0 <= c <= c1]
    left = [c for r, c in marks if c < c0 and r0 <= r <= r1]
    right = [c for r, c in marks if c > c1 and r0 <= r <= r1]
    nr0 = max(above) + 1 if above else r0
    nr1 = min(below) - 1 if below else r1
    nc0 = max(left) + 1 if left else c0
    nc1 = min(right) - 1 if right else c1
    motif = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]

    # Enlarge the outermost gaps, retaining full border bands and interior lines.
    gap_rows = [i for i, row in enumerate(motif) if 0 in row]
    top_gap = min(gap_rows) if gap_rows else 1
    bottom_gap = max(gap_rows) if gap_rows else len(motif) - 2
    motif[bottom_gap:bottom_gap] = [motif[bottom_gap][:] for _ in range(nr1 - r1)]
    motif[top_gap:top_gap] = [motif[top_gap][:] for _ in range(r0 - nr0)]
    gap_cols = [c for c in range(len(motif[0])) if any(row[c] == 0 for row in motif)]
    left_gap = min(gap_cols) if gap_cols else 1
    right_gap = max(gap_cols) if gap_cols else len(motif[0]) - 2
    for row in motif:
        row[right_gap:right_gap] = [row[right_gap]] * (nc1 - c1)
        row[left_gap:left_gap] = [row[left_gap]] * (c0 - nc0)
    for r, c in green:
        out[r][c] = 0
    for r, row in enumerate(motif, nr0):
        for c, value in enumerate(row, nc0):
            out[r][c] = value
    return out
