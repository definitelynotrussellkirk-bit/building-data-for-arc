"""Visible-example solution for blind task d70726fd510f."""


def solve(grid):
    """XOR the two panels separated by a solid vertical divider.

    Each side uses an arbitrary non-zero foreground color.  The result keeps
    cells occupied on exactly one side and recolors them 2.
    """
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_candidates = [
        c
        for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    ]
    balanced = [c for c in divider_candidates if c == width - c - 1]
    if len(balanced) != 1:
        raise ValueError("expected one centered solid non-zero divider column")

    divider = balanced[0]
    panel_width = divider
    result = []
    for row in grid:
        left = row[:divider]
        right = row[divider + 1 :]
        if len(right) != panel_width:
            raise ValueError("divider must split equal-width panels")
        result.append([2 if (a != 0) ^ (b != 0) else 0 for a, b in zip(left, right)])
    return result
