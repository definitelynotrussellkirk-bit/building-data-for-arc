from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Paint the full row and column through the sole nonzero seed cell."""
    output = [row[:] for row in grid]
    seed = next(
        ((r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0),
        None,
    )
    if seed is None:
        return output

    seed_row, seed_col, color = seed
    output[seed_row] = [color] * len(output[seed_row])
    for row in output:
        row[seed_col] = color
    return output
