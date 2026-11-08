"""Infer the frame and enlarge the separate thumbnail to its interior."""
from collections import Counter


def solve(grid):
    height, width = len(grid), len(grid[0])
    background = Counter(v for row in grid for v in row).most_common(1)[0][0]
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != background:
                positions.setdefault(value, []).append((r, c))
    frames = []
    for color, cells in positions.items():
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        if bottom - top < 2 or right - left < 2:
            continue
        border = {(r, c) for r in range(top, bottom + 1)
                  for c in range(left, right + 1)
                  if r in (top, bottom) or c in (left, right)}
        if set(cells) == border:
            frames.append((len(cells), color, top, bottom, left, right))
    if len(frames) != 1:
        raise ValueError("Expected one monochrome rectangular frame")
    _, frame, top, bottom, left, right = frames[0]
    thumbnail = [(r, c) for color, cells in positions.items()
                 if color != frame for r, c in cells]
    if not thumbnail:
        raise ValueError("No thumbnail to enlarge")
    tr = min(r for r, _ in thumbnail)
    br = max(r for r, _ in thumbnail)
    lc = min(c for _, c in thumbnail)
    rc = max(c for _, c in thumbnail)
    inner_h, inner_w = bottom - top - 1, right - left - 1
    th, tw = br - tr + 1, rc - lc + 1
    if inner_h % th or inner_w % tw:
        raise ValueError("Thumbnail dimensions do not divide the frame interior")
    scale_h, scale_w = inner_h // th, inner_w // tw
    result = [[frame] * (inner_w + 2) for _ in range(inner_h + 2)]
    for r in range(inner_h):
        for c in range(inner_w):
            result[r + 1][c + 1] = grid[tr + r // scale_h][lc + c // scale_w]
    return result
