from collections import Counter


def solve(grid):
    """Move each colored corner cue inward and expand it into its corner glyph."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w:
        return [row[:] for row in grid]

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    out = [[background for _ in range(w)] for _ in range(h)]

    # The visible examples define two corner-local glyphs.  Top cues become a
    # 2x2 block one cell in from the edge; bottom cues become a three-cell
    # rising/falling stroke.  Mirror the templates for right-hand corners.
    templates = {
        (0, 0): ((1, 1), (1, 2), (2, 1), (2, 2)),
        (0, w - 1): ((1, w - 3), (1, w - 2), (2, w - 3), (2, w - 2)),
        (h - 1, 0): ((h - 4, 2), (h - 3, 2), (h - 2, 3)),
        (h - 1, w - 1): ((h - 4, w - 3), (h - 3, w - 3), (h - 2, w - 4)),
    }

    for corner, cells in templates.items():
        r, c = corner
        color = grid[r][c]
        if color == background:
            continue
        for rr, cc in cells:
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = color

    return out
