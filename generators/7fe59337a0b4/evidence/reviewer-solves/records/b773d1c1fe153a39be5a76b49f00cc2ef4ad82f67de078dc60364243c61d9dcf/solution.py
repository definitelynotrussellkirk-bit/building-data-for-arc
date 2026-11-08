from __future__ import annotations


def _rotate_clockwise(shape: list[list[int]]) -> list[list[int]]:
    """Rotate a rectangular matrix 90 degrees clockwise."""
    return [list(row) for row in zip(*shape[::-1])]


def _stamp(
    out: list[list[int]], shape: list[list[int]], top: int, left: int
) -> None:
    """Stamp non-background cells, clipping only at the outer grid boundary."""
    height = len(out)
    width = len(out[0]) if height else 0
    for dr, row in enumerate(shape):
        rr = top + dr
        if not 0 <= rr < height:
            continue
        for dc, value in enumerate(row):
            cc = left + dc
            if value != 0 and 0 <= cc < width:
                out[rr][cc] = value


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Place four successive rotations of the colored motif around the 9 marker."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height, width = len(grid), len(grid[0])
    marker_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    motif_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if len(marker_cells) != 1 or not motif_cells:
        return [row[:] for row in grid]

    marker_r, marker_c = marker_cells[0]
    min_r = min(r for r, _ in motif_cells)
    max_r = max(r for r, _ in motif_cells)
    min_c = min(c for _, c in motif_cells)
    max_c = max(c for _, c in motif_cells)
    motif = [row[min_c : max_c + 1] for row in grid[min_r : max_r + 1]]

    rotations = [motif]
    for _ in range(3):
        rotations.append(_rotate_clockwise(rotations[-1]))

    out = [[0 for _ in range(width)] for _ in range(height)]
    out[marker_r][marker_c] = 9

    # Each copy is separated from the marker by one blank row/column.  For an
    # even cross-axis size, align the marker with the lower/right central cell,
    # matching the visible examples' floor(size/2) convention.
    top_shape = rotations[0]
    top_h, top_w = len(top_shape), len(top_shape[0])
    _stamp(
        out,
        top_shape,
        marker_r - 1 - top_h,
        marker_c - top_w // 2,
    )

    right_shape = rotations[1]
    right_h, right_w = len(right_shape), len(right_shape[0])
    _stamp(
        out,
        right_shape,
        marker_r - right_h // 2,
        marker_c + 2,
    )

    bottom_shape = rotations[2]
    bottom_h, bottom_w = len(bottom_shape), len(bottom_shape[0])
    _stamp(
        out,
        bottom_shape,
        marker_r + 2,
        marker_c - bottom_w // 2,
    )

    left_shape = rotations[3]
    left_h, left_w = len(left_shape), len(left_shape[0])
    _stamp(
        out,
        left_shape,
        marker_r - left_h // 2,
        marker_c - 1 - left_w,
    )

    return out
