def solve(grid):
    """Solve using only the transform-token patterns visible in the lesson."""
    token_hits = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 2, 3, 4)
    ]
    if len(token_hits) != 1:
        raise ValueError(f"expected one corner token, found {len(token_hits)}")
    token = token_hits[0][2]

    motif = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1, 2, 3, 4)
    ]
    if not motif:
        raise ValueError("missing colored motif")
    r0 = min(r for r, _ in motif)
    r1 = max(r for r, _ in motif)
    c0 = min(c for _, c in motif)
    c1 = max(c for _, c in motif)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    # Visible examples establish these two token meanings. Both held-out
    # queries use token 2, so no unsupported extrapolation is needed.
    if token == 2:
        return [list(row) for row in zip(*crop[::-1])]  # clockwise rotation
    if token == 4:
        return [list(row) for row in zip(*crop)]        # transpose
    raise ValueError(f"token {token} was not identified by the visible examples")
