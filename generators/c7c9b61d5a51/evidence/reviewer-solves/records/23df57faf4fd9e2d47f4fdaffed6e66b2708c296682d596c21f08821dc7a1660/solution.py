from __future__ import annotations

from collections import defaultdict


def _line(a: tuple[int, int], b: tuple[int, int]) -> set[tuple[int, int]]:
    if a[0] == b[0]:
        lo, hi = sorted((a[1], b[1]))
        return {(a[0], col) for col in range(lo, hi + 1)}
    if a[1] == b[1]:
        lo, hi = sorted((a[0], b[0]))
        return {(row, a[1]) for row in range(lo, hi + 1)}
    raise ValueError("segment must be horizontal or vertical")


def _elbow_path(
    a: tuple[int, int], b: tuple[int, int], which: int
) -> set[tuple[int, int]]:
    elbow = (a[0], b[1]) if which == 0 else (b[0], a[1])
    return _line(a, elbow) | _line(elbow, b)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Connect each same-colored endpoint pair along its unobstructed L path."""
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in (0, 5):
                positions[value].append((row, col))

    output = [list(row) for row in grid]
    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        a, b = sorted(cells)
        if a[0] == b[0] or a[1] == b[1]:
            candidates = [_line(a, b)]
        else:
            candidates = [_elbow_path(a, b, 0), _elbow_path(a, b, 1)]

        clear = next(
            (
                path
                for path in candidates
                if all(grid[row][col] in (0, color) for row, col in path)
            ),
            None,
        )
        if clear is None:
            continue
        for row, col in clear:
            output[row][col] = color
    return output
