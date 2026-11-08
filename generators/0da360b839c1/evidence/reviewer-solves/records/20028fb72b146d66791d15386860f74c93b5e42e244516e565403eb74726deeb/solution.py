"""Visible-example solution for the prepared reviewer solve episode."""


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Point-reflect every colored source cell about the unique color-9 anchor."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        raise ValueError(f"expected exactly one color-9 anchor, found {len(anchors)}")
    ar, ac = anchors[0]

    output = [[0 for _ in range(w)] for _ in range(h)]
    output[ar][ac] = 9
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            rr, cc = 2 * ar - r, 2 * ac - c
            if not (0 <= rr < h and 0 <= cc < w):
                raise ValueError(f"reflected cell {(r, c)} -> {(rr, cc)} is out of bounds")
            output[rr][cc] = value
    return output
