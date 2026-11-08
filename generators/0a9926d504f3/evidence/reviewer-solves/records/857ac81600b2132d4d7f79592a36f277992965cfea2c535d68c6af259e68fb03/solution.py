from collections import Counter


def solve(grid):
    """Draw the extremal-color frame and the gray cross through color 2."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    marker = None
    anchors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == background:
                continue
            if value == 2 and marker is None:
                marker = (r, c)
            else:
                anchors.append((r, c, value))

    # The visible examples define the four frame sides by the non-marker
    # point with the most extreme coordinate in that direction.  A single
    # point may therefore define two adjacent sides.
    if marker is None or not anchors:
        return [row[:] for row in grid]

    top_anchor = min(anchors, key=lambda p: p[0])
    bottom_anchor = max(anchors, key=lambda p: p[0])
    left_anchor = min(anchors, key=lambda p: p[1])
    right_anchor = max(anchors, key=lambda p: p[1])

    top, top_color = top_anchor[0], top_anchor[2]
    bottom, bottom_color = bottom_anchor[0], bottom_anchor[2]
    left, left_color = left_anchor[1], left_anchor[2]
    right, right_color = right_anchor[1], right_anchor[2]
    marker_r, marker_c = marker

    out = [[background for _ in range(width)] for _ in range(height)]

    # Interior cross.  Restrict it to the frame interior so the side colors
    # always win at the boundary; the red marker likewise disappears when it
    # lies on a boundary, as in a visible training example.
    if top < marker_r < bottom:
        for c in range(left + 1, right):
            out[marker_r][c] = 5
    if left < marker_c < right:
        for r in range(top + 1, bottom):
            out[r][marker_c] = 5
    if top < marker_r < bottom and left < marker_c < right:
        out[marker_r][marker_c] = 2

    # Vertical sides first; horizontal sides own the four corners.
    for r in range(top, bottom + 1):
        out[r][left] = left_color
        out[r][right] = right_color
    for c in range(left, right + 1):
        out[top][c] = top_color
        out[bottom][c] = bottom_color

    return out
