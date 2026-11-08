"""Visible-example-only analogy solver; no reference imports."""
from collections import Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    h, w = len(grid), len(grid[0])
    mid_r, mid_c = h // 2, w // 2
    separator = grid[mid_r][mid_c]
    if h % 2 != 1 or w % 2 != 1 or any(v != separator for v in grid[mid_r]) or any(row[mid_c] != separator for row in grid):
        raise ValueError('Expected four equal panels separated by a full cross')
    panels = [[row[c:c + mid_c] for row in grid[r:r + mid_r]]
              for r, c in [(0, 0), (0, mid_c + 1), (mid_r + 1, 0)]]
    background = Counter(v for panel in panels for row in panel for v in row).most_common(1)[0][0]

    def shape(panel):
        cells = {(r, c) for r, row in enumerate(panel) for c, v in enumerate(row) if v != background}
        if not cells:
            raise ValueError('An analogy panel is empty')
        top, left = min(r for r, _ in cells), min(c for _, c in cells)
        color = Counter(panel[r][c] for r, c in cells).most_common(1)[0][0]
        return {(r - top, c - left) for r, c in cells}, top, left, color

    a, _, _, _ = shape(panels[0])
    b, _, _, _ = shape(panels[1])
    c, top, left, color = shape(panels[2])
    result_shape = (c - (a - b)) | (b - a)
    out = [row[:] for row in grid]
    for r in range(mid_r):
        for col in range(mid_c):
            out[mid_r + 1 + r][mid_c + 1 + col] = background
    for r, col in result_shape:
        rr, cc = top + r, left + col
        if not (0 <= rr < mid_r and 0 <= cc < mid_c):
            raise ValueError('Transferred edit exceeds its output panel')
        out[mid_r + 1 + rr][mid_c + 1 + cc] = color
    return out
