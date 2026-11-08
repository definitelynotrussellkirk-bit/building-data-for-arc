from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Paint the selected all-zero square regions with color 1."""
    h, w = len(grid), len(grid[0])

    # largest[r][c] is the side length of the largest all-zero square whose
    # top-left corner is (r, c).
    largest = [[0] * w for _ in range(h)]
    for r in range(h - 1, -1, -1):
        for c in range(w - 1, -1, -1):
            if grid[r][c] != 0:
                continue
            largest[r][c] = 1
            if r + 1 < h and c + 1 < w:
                largest[r][c] += min(
                    largest[r + 1][c],
                    largest[r][c + 1],
                    largest[r + 1][c + 1],
                )

    global_max = max(max(row) for row in largest)
    maximal_union: set[tuple[int, int]] = set()
    for r in range(h):
        for c in range(w):
            if largest[r][c] == global_max:
                maximal_union.update(
                    (rr, cc)
                    for rr in range(r, r + global_max)
                    for cc in range(c, c + global_max)
                )

    paint = set(maximal_union)
    for side in range(2, global_max + 1):
        for r in range(h - side + 1):
            for c in range(w - side + 1):
                if largest[r][c] < side:
                    continue
                cells = {
                    (rr, cc)
                    for rr in range(r, r + side)
                    for cc in range(c, c + side)
                }
                if cells.isdisjoint(maximal_union):
                    paint.update(cells)

    output = [row[:] for row in grid]
    for r, c in paint:
        output[r][c] = 1
    return output
