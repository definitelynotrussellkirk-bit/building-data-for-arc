from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Repack each nonzero color as a top-aligned vertical bar.

    The bar height is the number of input rows occupied by that color.  Bars are
    ordered from tallest to shortest; the output height is the tallest bar.
    """
    occupied_rows: dict[int, set[int]] = {}
    for row_index, row in enumerate(grid):
        for color in row:
            if color != 0:
                occupied_rows.setdefault(color, set()).add(row_index)

    bars = sorted(
        ((len(rows), color) for color, rows in occupied_rows.items()),
        key=lambda item: (-item[0], item[1]),
    )
    if not bars:
        return []

    output_height = bars[0][0]
    return [
        [color if row_index < height else 0 for height, color in bars]
        for row_index in range(output_height)
    ]
