"""Visible-example inference for the nested-rectangle task."""


def solve(grid):
    out = [list(row) for row in grid]
    height, width = len(out), len(out[0])
    cells = [(r, c) for r, row in enumerate(out)
             for c, value in enumerate(row) if value != 0]
    if not cells:
        return out
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    frame_color = out[top][left]
    inner_colors = {out[r][c] for r, c in cells} - {frame_color}
    if len(inner_colors) != 1:
        raise ValueError("Expected one frame color and one interior color")
    fill = inner_colors.pop()
    thickness = min(2, top, left, height - 1 - bottom, width - 1 - right)
    for r in range(top - thickness, bottom + thickness + 1):
        for c in range(left - thickness, right + thickness + 1):
            if r < top or r > bottom or c < left or c > right:
                out[r][c] = fill
    return out
