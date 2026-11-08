from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Paint the rectangle outline encoded by markers 1, 2 and 3."""
    positions: dict[int, tuple[int, int]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (1, 2, 3):
                if value in positions:
                    raise ValueError(f"duplicate marker color {value}")
                positions[value] = (r, c)
    if set(positions) != {1, 2, 3}:
        raise ValueError("expected exactly one marker each of colors 1, 2 and 3")

    r1, c1 = positions[1]
    r2, c2 = positions[2]
    r3, c3 = positions[3]
    if r1 != r2 or c1 != c3:
        raise ValueError("markers do not form the typed L")
    top, bottom = sorted((r1, r3))
    left, right = sorted((c1, c2))
    out = [[0 for _ in row] for row in grid]
    for c in range(left, right + 1):
        out[top][c] = 8
        out[bottom][c] = 8
    for r in range(top, bottom + 1):
        out[r][left] = 8
        out[r][right] = 8
    return out
