"""Translate the visible object's tight crop to its nearest corner placement."""

def solve(grid):
    h, w = len(grid), len(grid[0])
    pixels = [(r, c, value) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value != 0]
    if not pixels:
        return [list(row) for row in grid]
    top = min(r for r, c, value in pixels)
    left = min(c for r, c, value in pixels)
    bottom = max(r for r, c, value in pixels)
    right = max(c for r, c, value in pixels)
    crop_h, crop_w = bottom-top+1, right-left+1
    center2 = (top+bottom, left+right)
    anchors = [(0, 0), (0, w-crop_w), (h-crop_h, 0), (h-crop_h, w-crop_w)]
    target_r, target_c = min(
        anchors,
        key=lambda p: (2*p[0]+crop_h-1-center2[0])**2
                    + (2*p[1]+crop_w-1-center2[1])**2,
    )
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r, c, value in pixels:
        output[target_r+r-top][target_c+c-left] = value
    return output
