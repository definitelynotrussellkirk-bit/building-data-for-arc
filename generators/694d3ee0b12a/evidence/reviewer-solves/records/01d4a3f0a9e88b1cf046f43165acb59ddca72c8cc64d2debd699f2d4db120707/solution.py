from __future__ import annotations


def _framed_panels(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return top-left coordinates of every 7x7 color-7 frame."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    panels: list[tuple[int, int]] = []
    for r in range(height - 6):
        for c in range(width - 6):
            if not all(grid[r][c + dc] == 7 for dc in range(7)):
                continue
            if not all(grid[r + 6][c + dc] == 7 for dc in range(7)):
                continue
            if not all(grid[r + dr][c] == 7 for dr in range(7)):
                continue
            if not all(grid[r + dr][c + 6] == 7 for dr in range(7)):
                continue
            panels.append((r, c))
    return panels


def solve(grid):
    out = [row[:] for row in grid]

    for top, left in _framed_panels(grid):
        interior = [grid[top + 1 + dr][left + 1 : left + 6] for dr in range(5)]

        marked_rows = {
            dr for dr, row in enumerate(interior) if 2 in row
        }
        marked_cols = {
            dc
            for dc in range(5)
            if any(interior[dr][dc] == 3 for dr in range(5))
        }
        signal_colors = {
            value
            for row in interior
            for value in row
            if value not in {0, 2, 3, 7}
        }

        # Each visible panel supplies exactly one payload color.  Leave malformed
        # or under-specified panels unchanged rather than guessing.
        if len(signal_colors) != 1:
            continue
        signal = next(iter(signal_colors))

        for dr in marked_rows:
            for dc in marked_cols:
                out[top + 1 + dr][left + 1 + dc] = signal

    return out
