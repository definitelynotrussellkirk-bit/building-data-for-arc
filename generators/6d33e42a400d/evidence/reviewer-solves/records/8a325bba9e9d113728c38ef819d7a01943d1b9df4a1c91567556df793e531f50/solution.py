"""Visible-example-only solution for blind task 6d33e42a400d."""

from collections import Counter


def solve(grid):
    """Reflect the source drawing from the marker guide to the receiver guide.

    The least frequent non-background colour forms an evenly spaced horizontal
    or vertical marker guide.  The other non-background colour contains both a
    drawing attached on one side of that marker guide and a matching receiver
    guide on the opposite side.  Mirror the drawing across the two guides,
    recolouring the copied cells with the marker colour.
    """
    out = [row[:] for row in grid]
    counts = Counter(cell for row in grid for cell in row)
    background = counts.most_common(1)[0][0]
    non_background = [color for color in counts if color != background]
    if len(non_background) != 2:
        return out

    marker = min(non_background, key=lambda color: counts[color])
    drawing = next(color for color in non_background if color != marker)
    marker_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, color in enumerate(row)
        if color == marker
    ]
    if not marker_cells:
        return out

    marker_rows = {r for r, _ in marker_cells}
    marker_cols = {c for _, c in marker_cells}

    if len(marker_rows) == 1:
        marker_axis = next(iter(marker_rows))
        positions = sorted(c for _, c in marker_cells)
        candidates = [
            r
            for r, row in enumerate(grid)
            if r != marker_axis and all(row[c] == drawing for c in positions)
        ]
        if not candidates:
            return out
        receiver_axis = min(
            candidates,
            key=lambda r: (
                sum(cell == drawing for cell in grid[r]),
                abs(r - marker_axis),
            ),
        )
        source_sign = -1 if receiver_axis > marker_axis else 1
        for r, row in enumerate(grid):
            if (r - marker_axis) * source_sign <= 0:
                continue
            distance = abs(r - marker_axis)
            target_r = receiver_axis - source_sign * distance
            if not (0 <= target_r < len(grid)):
                continue
            for c, color in enumerate(row):
                if color == drawing and out[target_r][c] == background:
                    out[target_r][c] = marker

    elif len(marker_cols) == 1:
        marker_axis = next(iter(marker_cols))
        positions = sorted(r for r, _ in marker_cells)
        width = len(grid[0])
        candidates = [
            c
            for c in range(width)
            if c != marker_axis and all(grid[r][c] == drawing for r in positions)
        ]
        if not candidates:
            return out
        receiver_axis = min(
            candidates,
            key=lambda c: (
                sum(row[c] == drawing for row in grid),
                abs(c - marker_axis),
            ),
        )
        source_sign = -1 if receiver_axis > marker_axis else 1
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                if color != drawing or (c - marker_axis) * source_sign <= 0:
                    continue
                distance = abs(c - marker_axis)
                target_c = receiver_axis - source_sign * distance
                if 0 <= target_c < width and out[r][target_c] == background:
                    out[r][target_c] = marker

    return out
