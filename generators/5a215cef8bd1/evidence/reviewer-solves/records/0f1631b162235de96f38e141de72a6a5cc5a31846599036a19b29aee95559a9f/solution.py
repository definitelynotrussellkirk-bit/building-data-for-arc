from collections import deque


def _component(grid, color):
    """Return the only 4-connected component of ``color``."""
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    if not remaining:
        raise ValueError(f"missing color {color} template")

    start = next(iter(remaining))
    queue = deque([start])
    seen = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (r + dr, c + dc)
            if p in remaining and p not in seen:
                seen.add(p)
                queue.append(p)

    if seen != remaining:
        raise ValueError("expected exactly one connected color-2 template")
    return seen


def _crop_binary(grid, cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [1 if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _rotate_cw(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _rotate_180(shape):
    return [row[::-1] for row in shape[::-1]]


def _flip_lr(shape):
    return [row[::-1] for row in shape]


def solve(grid):
    template = _crop_binary(grid, _component(grid, 2))
    th, tw = len(template), len(template[0])

    controls = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (1, 3, 4, 6):
                controls[value] = (r, c)
    if set(controls) != {1, 3, 4, 6}:
        raise ValueError("expected one control cell of each color 1, 3, 4, and 6")

    control_rows = {r: i for i, r in enumerate(sorted({r for r, _ in controls.values()}))}
    control_cols = {c: i for i, c in enumerate(sorted({c for _, c in controls.values()}))}
    if len(control_rows) != 2 or len(control_cols) != 2:
        raise ValueError("control cells must form a 2-by-2 arrangement")

    transformed = {
        1: template,
        3: _rotate_cw(template),
        4: _rotate_180(template),
        6: _flip_lr(template),
    }

    out = [[0 for _ in range(2 * tw + 1)] for _ in range(2 * th + 1)]
    for color, (r, c) in controls.items():
        shape = transformed[color]
        top = control_rows[r] * (th + 1)
        left = control_cols[c] * (tw + 1)
        for sr, row in enumerate(shape):
            for sc, value in enumerate(row):
                if value:
                    out[top + sr][left + sc] = 7
    return out
