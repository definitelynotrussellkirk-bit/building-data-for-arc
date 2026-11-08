from collections import Counter


def solve(grid):
    """Apply row-1-gated vertical XOR sweeps from non-background top cells."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    out = [list(row) for row in grid]
    if len(grid) < 2:
        return out
    for col, marker in enumerate(grid[0]):
        if marker == background or marker == grid[1][col]:
            continue
        for row in range(1, len(grid)):
            out[row][col] = background if grid[row][col] == marker else marker
    return out
