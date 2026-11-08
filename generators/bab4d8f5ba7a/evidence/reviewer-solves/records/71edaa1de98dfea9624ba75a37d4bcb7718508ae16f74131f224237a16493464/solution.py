def solve(grid):
    """Recolor each gray (8) cell from the row's leftmost colored key."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        key = next((value for value in row if value not in (0, 8)), None)
        if key is None:
            continue
        out[r] = [key if value == 8 else value for value in row]
    return out
