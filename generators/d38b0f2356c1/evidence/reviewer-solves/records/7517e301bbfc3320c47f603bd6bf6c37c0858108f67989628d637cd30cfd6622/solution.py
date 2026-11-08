from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand the unique cyan-free 3x3 cell block as a macro-template."""
    if len(grid) != 11 or any(len(row) != 11 for row in grid):
        raise ValueError("expected an 11x11 grid")

    separator_rows = (3, 7)
    separator_cols = (3, 7)
    starts = (0, 4, 8)

    candidates: list[list[list[int]]] = []
    for row0 in starts:
        for col0 in starts:
            block = [row[col0 : col0 + 3] for row in grid[row0 : row0 + 3]]
            if all(8 not in row for row in block):
                candidates.append(block)

    if len(candidates) != 1:
        raise ValueError(f"expected one cyan-free block, found {len(candidates)}")
    template = candidates[0]

    output = [[0 for _ in range(11)] for _ in range(11)]
    for r in separator_rows:
        output[r] = [5] * 11
    for r in range(11):
        for c in separator_cols:
            output[r][c] = 5

    for macro_r, row0 in enumerate(starts):
        for macro_c, col0 in enumerate(starts):
            color = template[macro_r][macro_c]
            for r in range(row0, row0 + 3):
                for c in range(col0, col0 + 3):
                    output[r][c] = color

    return output
