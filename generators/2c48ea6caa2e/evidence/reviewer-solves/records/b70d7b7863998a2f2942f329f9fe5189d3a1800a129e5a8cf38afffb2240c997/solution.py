def solve(grid):
    """Complete the sparsest orthogonal line cover of the visible blue marks."""
    out = [list(row) for row in grid]
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if not points:
        return out
    rows = sorted({r for r, _ in points})
    edges = {r: sorted(c for rr, c in points if rr == r) for r in rows}
    matched_column = {}

    def augment(r, visited):
        for c in edges[r]:
            if c in visited:
                continue
            visited.add(c)
            if c not in matched_column or augment(matched_column[c], visited):
                matched_column[c] = r
                return True
        return False

    for r in rows:
        augment(r, set())
    matched_row = {r: c for c, r in matched_column.items()}
    reachable_rows = set(rows) - set(matched_row)
    reachable_columns = set()
    pending = list(reachable_rows)
    while pending:
        r = pending.pop()
        for c in edges[r]:
            if matched_row.get(r) == c or c in reachable_columns:
                continue
            reachable_columns.add(c)
            if c in matched_column and matched_column[c] not in reachable_rows:
                reachable_rows.add(matched_column[c])
                pending.append(matched_column[c])
    horizontal = set(rows) - reachable_rows
    vertical = reachable_columns
    top, bottom = min(r for r, _ in points), max(r for r, _ in points)
    left, right = min(c for _, c in points), max(c for _, c in points)
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if (r in horizontal or c in vertical) and out[r][c] == 0:
                out[r][c] = 2
    return out
