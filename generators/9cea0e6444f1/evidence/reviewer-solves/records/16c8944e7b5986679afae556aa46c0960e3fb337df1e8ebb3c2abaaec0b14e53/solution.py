from __future__ import annotations


def _normalize_color(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if not cells:
        return set()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return {(r - min_r, c - min_c) for r, c in cells}


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Top-left align colors 1 and 2, then paint their normalized union green."""
    union = _normalize_color(grid, 1) | _normalize_color(grid, 2)
    if not union:
        return []

    height = max(r for r, _ in union) + 1
    width = max(c for _, c in union) + 1
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in union:
        out[r][c] = 3
    return out
