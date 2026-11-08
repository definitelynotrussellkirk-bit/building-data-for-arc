def solve(grid):
    """Connect aligned red anchors with a green spine, then attach every red point."""
    out = [row[:] for row in grid]
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]

    rows = {}
    cols = {}
    for r, c in points:
        rows.setdefault(r, []).append(c)
        cols.setdefault(c, []).append(r)

    row_candidates = [(r, cs) for r, cs in rows.items() if len(cs) >= 2]
    col_candidates = [(c, rs) for c, rs in cols.items() if len(rs) >= 2]

    # The examples contain one uniquely aligned anchor pair.  The deterministic
    # score below also handles a longer aligned group should one occur.
    candidates = []
    for r, cs in row_candidates:
        candidates.append((len(cs), max(cs) - min(cs), "row", r, cs))
    for c, rs in col_candidates:
        candidates.append((len(rs), max(rs) - min(rs), "col", c, rs))
    if not candidates:
        return out

    _, _, orientation, axis, aligned = max(candidates)

    if orientation == "row":
        spine_row = axis
        left, right = min(aligned), max(aligned)
        for c in range(left, right + 1):
            if out[spine_row][c] == 0:
                out[spine_row][c] = 3
        for r, c in points:
            if r == spine_row:
                continue
            lo, hi = sorted((r, spine_row))
            for rr in range(lo, hi + 1):
                if out[rr][c] == 0:
                    out[rr][c] = 3
    else:
        spine_col = axis
        top, bottom = min(aligned), max(aligned)
        for r in range(top, bottom + 1):
            if out[r][spine_col] == 0:
                out[r][spine_col] = 3
        for r, c in points:
            if c == spine_col:
                continue
            lo, hi = sorted((c, spine_col))
            for cc in range(lo, hi + 1):
                if out[r][cc] == 0:
                    out[r][cc] = 3

    return out
