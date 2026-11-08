from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill inclusive 45-degree segments between same-color endpoints."""
    output = [row[:] for row in grid]
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((r, c))

    for color, cells in positions.items():
        if len(cells) < 2:
            continue
        (r1, c1), (r2, c2) = cells[0], cells[-1]
        dr, dc = r2 - r1, c2 - c1
        if dr == 0 or abs(dr) != abs(dc):
            continue
        row_step = 1 if dr > 0 else -1
        col_step = 1 if dc > 0 else -1
        for step in range(abs(dr) + 1):
            output[r1 + step * row_step][c1 + step * col_step] = color
    return output
