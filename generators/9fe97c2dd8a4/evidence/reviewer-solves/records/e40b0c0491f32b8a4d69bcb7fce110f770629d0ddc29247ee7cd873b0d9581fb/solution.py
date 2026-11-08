from __future__ import annotations

from collections import Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Write each bar's squared length code in the column marked on row 0."""
    out = [row[:] for row in grid]
    marker_col = next(c for c, value in enumerate(grid[0]) if value == 5)

    bars: list[tuple[int, int, bool]] = []
    for r in range(1, len(grid)):
        cells = [value for value in grid[r] if value != 0]
        if cells:
            bars.append((r, len(cells), 5 not in cells))

    eligible_lengths = [length for _, length, eligible in bars if eligible]
    counts = Counter(eligible_lengths)
    repeated = next(
        (length for length in eligible_lengths if counts[length] > 1),
        None,
    )

    for r, length, _eligible in bars:
        if repeated is not None and length != repeated:
            base = length - repeated
        else:
            base = length - 1
        out[r][marker_col] = (base * base) % 10
    return out
