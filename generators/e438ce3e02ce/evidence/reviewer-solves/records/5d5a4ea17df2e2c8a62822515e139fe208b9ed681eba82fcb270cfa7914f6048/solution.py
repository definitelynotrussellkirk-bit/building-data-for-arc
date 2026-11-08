from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill blanks by Manhattan-nearest seed; mark nearest-color ties with 8."""
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not seeds:
        return [list(row) for row in grid]

    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            distances = [abs(r - sr) + abs(c - sc) for sr, sc, _ in seeds]
            nearest = min(distances)
            colors = {
                color
                for distance, (_sr, _sc, color) in zip(distances, seeds)
                if distance == nearest
            }
            out[r][c] = next(iter(colors)) if len(colors) == 1 else 8
    return out
