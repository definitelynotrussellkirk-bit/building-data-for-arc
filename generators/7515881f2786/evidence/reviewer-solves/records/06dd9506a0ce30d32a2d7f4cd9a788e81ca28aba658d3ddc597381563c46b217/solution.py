"""Visible-only solution for blind task 7515881f2786."""


def solve(grid):
    """Fill spans between same-colored markers aligned in original rows/columns.

    The transformation is deliberately computed from the original marker set in
    one pass.  Newly filled cells do not create further row/column spans.
    """
    if not grid:
        return []

    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    # The visible examples use 0 as background and a single nonzero marker color.
    markers = {(r, c): grid[r][c]
               for r in range(height)
               for c in range(width)
               if grid[r][c] != 0}

    for r in range(height):
        by_color = {}
        for c in range(width):
            color = markers.get((r, c))
            if color is not None:
                by_color.setdefault(color, []).append(c)
        for color, cols in by_color.items():
            if len(cols) >= 2:
                for c in range(min(cols), max(cols) + 1):
                    out[r][c] = color

    for c in range(width):
        by_color = {}
        for r in range(height):
            color = markers.get((r, c))
            if color is not None:
                by_color.setdefault(color, []).append(r)
        for color, rows in by_color.items():
            if len(rows) >= 2:
                for r in range(min(rows), max(rows) + 1):
                    out[r][c] = color

    return out
