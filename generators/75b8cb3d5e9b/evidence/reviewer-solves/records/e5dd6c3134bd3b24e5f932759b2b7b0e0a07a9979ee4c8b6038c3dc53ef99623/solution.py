"""Visible-example solution for task 75b8cb3d5e9b."""
from __future__ import annotations


def _transform(grid, code):
    src = [list(row) for row in grid]
    if code == 0:
        return [row[:] for row in src]
    if code == 1:
        return [list(row) for row in zip(*src[::-1])]
    if code == 2:
        return [row[::-1] for row in src[::-1]]
    if code == 3:
        return [list(row) for row in zip(*src)][::-1]
    if code == 4:
        return [row[::-1] for row in src]
    if code == 5:
        return _transform(_transform(src, 4), 1)
    if code == 6:
        return _transform(_transform(src, 4), 2)
    if code == 7:
        return _transform(_transform(src, 4), 3)
    raise ValueError(code)


def _crop(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        raise ValueError("empty panel")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in panel[r0 : r1 + 1]]


def solve(grid):
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 2:
        raise ValueError(f"expected two dividers, got {dividers}")

    cuts = (
        (0, dividers[0]),
        (dividers[0] + 1, dividers[1]),
        (dividers[1] + 1, w),
    )
    source, target, query = (
        _crop([[grid[r][c] for c in range(left, right)] for r in range(h)])
        for left, right in cuts
    )
    for code in range(8):
        if _transform(source, code) == target:
            return _transform(query, code)
    raise ValueError("no dihedral transform maps source to target")
