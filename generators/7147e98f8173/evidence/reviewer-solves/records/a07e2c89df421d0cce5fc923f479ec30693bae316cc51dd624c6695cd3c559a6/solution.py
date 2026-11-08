"""Visible-example solution for task 7147e98f8173."""


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _rotate_once(cells):
    cells = _normalize(cells)
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def solve(grid):
    h, w = len(grid), len(grid[0])
    blue = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1)
    corner_turns = {
        (0, 0): 0,
        (0, w - 1): 1,
        (h - 1, w - 1): 2,
        (h - 1, 0): 3,
    }
    turns = corner_turns[blue]

    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    origin = (min(r for r, _ in red), min(c for _, c in red))
    shape = _normalize(red)
    for _ in range(turns):
        shape = _rotate_once(shape)

    green = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3)
    orange = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6)
    dr, dc = orange[0] - green[0], orange[1] - green[1]

    out = [[0] * w for _ in range(h)]
    for r, c in shape:
        out[origin[0] + dr + r][origin[1] + dc + c] = 8
    return out
