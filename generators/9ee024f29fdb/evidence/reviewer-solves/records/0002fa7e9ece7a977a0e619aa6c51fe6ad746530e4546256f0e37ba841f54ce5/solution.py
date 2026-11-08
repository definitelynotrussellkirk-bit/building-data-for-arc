from __future__ import annotations


def solve(grid):
    """Clear every fourth row/column; invert cyan-vs-other in each interior block."""
    return [
        [
            0 if row_index % 4 == 0 or column_index % 4 == 0 or value == 8 else 2
            for column_index, value in enumerate(row)
        ]
        for row_index, row in enumerate(grid)
    ]
