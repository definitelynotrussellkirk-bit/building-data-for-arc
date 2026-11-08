def solve(grid):
    """Extend each red seed upward, stepping right around gray blockers."""
    out = [row[:] for row in grid]
    if not out:
        return out

    height = len(out)
    width = len(out[0])
    seeds = [col for col, value in enumerate(grid[-1]) if value == 2]

    for seed_col in seeds:
        col = seed_col
        for row in range(height - 2, -1, -1):
            if grid[row][col] == 5:
                next_col = col + 1
                if next_col >= width:
                    # The visible rule always turns right; an edge blocker leaves
                    # no lawful continuation within the grid.
                    break
                col = next_col
                out[row + 1][col] = 2
            out[row][col] = 2

    return out
