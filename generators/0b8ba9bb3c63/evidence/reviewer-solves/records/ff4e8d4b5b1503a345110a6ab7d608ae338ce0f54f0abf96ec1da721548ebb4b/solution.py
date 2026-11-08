from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Project green rays from the cyan rectangle through black/red cells.

    The cyan (8) rectangle emits one ray from each of its rows to the left and
    right and one ray from each of its columns upward and downward.  A ray
    paints black (0) and red (2) cells green (4), and stops immediately before
    any other color.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not cyan:
        return [row[:] for row in grid]

    top = min(r for r, _ in cyan)
    bottom = max(r for r, _ in cyan)
    left = min(c for _, c in cyan)
    right = max(c for _, c in cyan)

    out = [row[:] for row in grid]
    paintable = {0, 2}

    def cast(r: int, c: int, dr: int, dc: int) -> None:
        while 0 <= r < height and 0 <= c < width:
            value = grid[r][c]
            if value not in paintable:
                break
            out[r][c] = 4
            r += dr
            c += dc

    for r in range(top, bottom + 1):
        cast(r, left - 1, 0, -1)
        cast(r, right + 1, 0, 1)

    for c in range(left, right + 1):
        cast(top - 1, c, -1, 0)
        cast(bottom + 1, c, 1, 0)

    return out
