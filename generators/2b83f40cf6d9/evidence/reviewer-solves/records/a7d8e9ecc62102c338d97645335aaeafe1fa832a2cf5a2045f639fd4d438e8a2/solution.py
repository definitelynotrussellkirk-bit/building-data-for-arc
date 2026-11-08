from __future__ import annotations


def _step_toward(value: int, target: int) -> int:
    if value < target:
        return value + 1
    if value > target:
        return value - 1
    return value


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Join each equal-colored pair with a vertical-first staircase.

    Pairs are processed by the row-major position of their first endpoint, so a
    later pair paints over an earlier path at crossings.
    """
    out = [row[:] for row in grid]
    positions: dict[int, list[tuple[int, int]]] = {}

    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((r, c))

    pairs = sorted(
        ((cells[0], color, cells) for color, cells in positions.items() if len(cells) == 2),
        key=lambda item: item[0],
    )

    for _, color, ((r, c), (target_r, target_c)) in pairs:
        out[r][c] = color
        while (r, c) != (target_r, target_c):
            if r != target_r:
                r = _step_toward(r, target_r)
                out[r][c] = color
            if c != target_c:
                c = _step_toward(c, target_c)
                out[r][c] = color

    return out
