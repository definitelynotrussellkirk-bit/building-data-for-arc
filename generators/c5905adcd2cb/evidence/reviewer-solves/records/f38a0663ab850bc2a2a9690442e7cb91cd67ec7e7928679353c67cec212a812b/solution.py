from __future__ import annotations


def _spans(length: int, dividers: list[int]) -> list[tuple[int, int]]:
    """Return half-open intervals between divider indices."""
    spans: list[tuple[int, int]] = []
    start = 0
    for divider in dividers:
        if start < divider:
            spans.append((start, divider))
        start = divider + 1
    if start < length:
        spans.append((start, length))
    return spans


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy the marker panel to the panel selected by the marker's local cell."""
    height = len(grid)
    width = len(grid[0])

    divider_rows = [
        r for r, row in enumerate(grid)
        if row and row[0] != 0 and all(value == row[0] for value in row)
    ]
    divider_cols = [
        c for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    ]
    row_spans = _spans(height, divider_rows)
    col_spans = _spans(width, divider_cols)

    marker_positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4 and r not in divider_rows and c not in divider_cols
    ]
    if len(marker_positions) != 1:
        raise ValueError(f"expected one off-divider color-4 marker, found {len(marker_positions)}")
    marker_r, marker_c = marker_positions[0]

    source_row_index, (source_r0, source_r1) = next(
        (i, span) for i, span in enumerate(row_spans) if span[0] <= marker_r < span[1]
    )
    source_col_index, (source_c0, source_c1) = next(
        (i, span) for i, span in enumerate(col_spans) if span[0] <= marker_c < span[1]
    )
    del source_row_index, source_col_index  # Only the marker's local position selects the target.

    target_row_index = marker_r - source_r0
    target_col_index = marker_c - source_c0
    if target_row_index >= len(row_spans) or target_col_index >= len(col_spans):
        raise ValueError("marker local position does not name an output panel")

    target_r0, target_r1 = row_spans[target_row_index]
    target_c0, target_c1 = col_spans[target_col_index]
    if (source_r1 - source_r0, source_c1 - source_c0) != (
        target_r1 - target_r0,
        target_c1 - target_c0,
    ):
        raise ValueError("source and target panels have different shapes")

    result = [[0 for _ in range(width)] for _ in range(height)]
    for r in divider_rows:
        result[r] = list(grid[r])
    for c in divider_cols:
        for r in range(height):
            result[r][c] = grid[r][c]

    for dr, source_r in enumerate(range(source_r0, source_r1)):
        for dc, source_c in enumerate(range(source_c0, source_c1)):
            result[target_r0 + dr][target_c0 + dc] = grid[source_r][source_c]

    return result
