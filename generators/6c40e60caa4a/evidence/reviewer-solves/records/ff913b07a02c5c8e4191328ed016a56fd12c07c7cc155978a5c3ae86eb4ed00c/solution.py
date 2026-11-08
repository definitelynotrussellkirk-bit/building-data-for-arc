from __future__ import annotations


def _is_frame(grid, top, left, bottom, right):
    """Return whether the inclusive box boundary is entirely color 1."""
    return (
        all(grid[top][c] == 1 for c in range(left, right + 1))
        and all(grid[bottom][c] == 1 for c in range(left, right + 1))
        and all(grid[r][left] == 1 for r in range(top, bottom + 1))
        and all(grid[r][right] == 1 for r in range(top, bottom + 1))
    )


def _smallest_enclosing_frame(grid, row, col):
    """Find the smallest axis-aligned color-1 frame strictly enclosing a cell."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    best = None

    for top in range(row):
        for bottom in range(row + 1, height):
            for left in range(col):
                for right in range(col + 1, width):
                    if not _is_frame(grid, top, left, bottom, right):
                        continue
                    interior_area = (bottom - top - 1) * (right - left - 1)
                    key = (interior_area, (bottom - top + 1) * (right - left + 1))
                    if best is None or key < best[0]:
                        best = (key, (top, left, bottom, right))

    return None if best is None else best[1]


def solve(grid):
    """Fill the interior of each red marker's smallest enclosing 1-frame green."""
    out = [row[:] for row in grid]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]

    for row, col in markers:
        frame = _smallest_enclosing_frame(grid, row, col)
        if frame is None:
            # Generated tasks are expected to enclose every marker.  Converting an
            # unmatched marker is the least destructive total-function fallback.
            out[row][col] = 3
            continue

        top, left, bottom, right = frame
        for r in range(top + 1, bottom):
            for c in range(left + 1, right):
                out[r][c] = 3

    return out
