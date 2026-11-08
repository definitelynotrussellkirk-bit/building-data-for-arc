from __future__ import annotations


def _separator_column(grid: list[list[int]]) -> int:
    """Return the full-height, non-background vertical divider column."""
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    candidates: list[int] = []
    for col in range(width):
        value = grid[0][col]
        if value != 0 and all(row[col] == value for row in grid):
            candidates.append(col)
    if len(candidates) != 1:
        raise ValueError(f"expected one full-height divider, found {candidates}")
    return candidates[0]


def _cropped_row_counts(region: list[list[int]]) -> list[int]:
    """Count foreground cells in each row from first occupied row to last."""
    occupied_rows = [i for i, row in enumerate(region) if any(value != 0 for value in row)]
    if not occupied_rows:
        return []
    top, bottom = occupied_rows[0], occupied_rows[-1]
    return [sum(value != 0 for value in region[i]) for i in range(top, bottom + 1)]


def solve(grid: list[list[int]]) -> list[list[int]]:
    divider = _separator_column(grid)
    left_counts = _cropped_row_counts([row[:divider] for row in grid])
    right_counts = _cropped_row_counts([row[divider + 1 :] for row in grid])

    height = max(len(left_counts), len(right_counts))
    differences = [
        abs(
            (left_counts[i] if i < len(left_counts) else 0)
            - (right_counts[i] if i < len(right_counts) else 0)
        )
        for i in range(height)
    ]
    width = max(differences, default=0)

    # The visible task always has a positive difference.  Keep a rectangular
    # one-cell background result for the otherwise degenerate equal-shape case.
    if width == 0:
        return [[0] for _ in range(max(height, 1))]
    return [[8] * length + [0] * (width - length) for length in differences]
