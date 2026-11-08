from __future__ import annotations


def solve(grid):
    """Fill the framed rectangle with the nearer/farther marker checkerboard."""
    out = [row[:] for row in grid]

    frame = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not frame:
        return out

    r0 = min(r for r, _ in frame)
    r1 = max(r for r, _ in frame)
    c0 = min(c for _, c in frame)
    c1 = max(c for _, c in frame)

    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if len(markers) != 2 or r1 - r0 < 2 or c1 - c0 < 2:
        return out

    # Visible examples indicate that the marker nearer the gray frame owns the
    # top-left/bottom-right diagonal.  Python's stable min keeps row-major order
    # as the deterministic tie-break seen in the equal-distance example.
    def distance_sq_to_frame(marker):
        mr, mc, _ = marker
        return min((mr - fr) ** 2 + (mc - fc) ** 2 for fr, fc in frame)

    near = min(markers, key=distance_sq_to_frame)
    far = markers[1] if near is markers[0] else markers[0]
    near_color = near[2]
    far_color = far[2]

    height = r1 - r0 - 1
    width = c1 - c0 - 1
    top_height = (height + 1) // 2
    left_width = (width + 1) // 2

    for ir, r in enumerate(range(r0 + 1, r1)):
        top = ir < top_height
        for ic, c in enumerate(range(c0 + 1, c1)):
            left = ic < left_width
            out[r][c] = near_color if top == left else far_color

    return out
