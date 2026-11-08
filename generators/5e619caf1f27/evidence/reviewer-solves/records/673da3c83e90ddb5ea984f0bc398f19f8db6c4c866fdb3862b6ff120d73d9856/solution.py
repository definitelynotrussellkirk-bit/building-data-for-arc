from __future__ import annotations


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def solve(grid):
    """Continue the nested rectangle with one outer layer of the core color.

    The visible examples all contain a solid inner rectangle inside a frame of a
    second color.  The output preserves that object and fills a clipped,
    uniformly expanded bounding box with the inner color.
    """
    height = len(grid)
    width = len(grid[0])
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))

    if len(by_color) != 2:
        return [row[:] for row in grid]

    all_cells = [cell for cells in by_color.values() for cell in cells]
    top, bottom, left, right = _bbox(all_cells)

    inner_color = None
    inner_box = None
    for color, cells in by_color.items():
        box = _bbox(cells)
        r0, r1, c0, c1 = box
        if len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1):
            if top < r0 <= r1 < bottom and left < c0 <= c1 < right:
                inner_color = color
                inner_box = box
                break

    if inner_color is None or inner_box is None:
        return [row[:] for row in grid]

    ir0, ir1, ic0, ic1 = inner_box
    outer_h = bottom - top + 1
    outer_w = right - left + 1
    inner_h = ir1 - ir0 + 1
    inner_w = ic1 - ic0 + 1
    frame_top = ir0 - top
    frame_bottom = bottom - ir1
    frame_left = ic0 - left
    frame_right = right - ic1

    # This is the simplest color-invariant descriptor I found that explains all
    # four visible layer widths: aspect mismatch of either rectangle, or total
    # opposite-side imbalance of the frame.
    layer = max(
        abs(outer_h - outer_w),
        abs(inner_h - inner_w),
        abs(frame_top - frame_bottom) + abs(frame_left - frame_right),
    )
    if layer == 0:
        layer = 1

    out = [row[:] for row in grid]
    r0 = max(0, top - layer)
    r1 = min(height - 1, bottom + layer)
    c0 = max(0, left - layer)
    c1 = min(width - 1, right + layer)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if out[r][c] == 0:
                out[r][c] = inner_color
    return out
