"""Visible-example hypothesis: each object rises by its number of cells."""


def solve(grid):
    """Translate each connected foreground object upward by its area.

    The public examples use 7 as background and 8 as a stationary floor.
    Objects join orthogonally even when adjacent cells have different colors.
    """
    if not grid:
        return []

    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("The input must be rectangular.")

    result = [list(row) for row in grid]
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] not in (7, 8)
    }

    # Clear all source cells before drawing any translated object.
    for r, c in remaining:
        result[r][c] = 7

    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        stack = [seed]
        cells = []

        while stack:
            r, c = stack.pop()
            cells.append((r, c, grid[r][c]))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)

        distance = len(cells)
        if any(r < distance for r, _, _ in cells):
            raise ValueError("The inferred upward translation leaves the grid.")
        for r, c, color in cells:
            result[r - distance][c] = color

    return result
