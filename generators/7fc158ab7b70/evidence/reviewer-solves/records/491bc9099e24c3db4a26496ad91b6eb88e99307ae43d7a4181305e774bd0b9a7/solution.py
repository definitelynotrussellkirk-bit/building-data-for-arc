def solve(grid):
    """Expand every input cell into a k-by-k block, k = nonzero cell count."""
    k = sum(value != 0 for row in grid for value in row)
    if k <= 0:
        # The visible tasks always contain colored cells; preserve a meaningful
        # total function for an all-background input rather than returning [].
        k = 1
    out = []
    for row in grid:
        expanded_row = [value for value in row for _ in range(k)]
        out.extend([expanded_row.copy() for _ in range(k)])
    return out
