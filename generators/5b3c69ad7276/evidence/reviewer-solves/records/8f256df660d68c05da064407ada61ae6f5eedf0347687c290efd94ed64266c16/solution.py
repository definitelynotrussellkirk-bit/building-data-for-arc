from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend the single nonzero cell across its full row and column."""
    out = [row[:] for row in grid]
    marker: tuple[int, int, int] | None = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                if marker is not None:
                    raise ValueError("expected exactly one nonzero marker")
                marker = (r, c, value)
    if marker is None:
        raise ValueError("expected one nonzero marker")
    r, c, value = marker
    for x in range(len(out[r])):
        out[r][x] = value
    for y in range(len(out)):
        out[y][c] = value
    return out
