from __future__ import annotations


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _frame_box(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    top, bottom = min(rs), max(rs)
    left, right = min(cs), max(cs)
    border = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }
    return (top, left, bottom, right) if cells == border else None


def solve(grid):
    """Fill the control-selected band of the three nested color-4 frames."""
    result = [row[:] for row in grid]

    control = next(
        value
        for row in grid
        for value in row
        if value in (1, 2, 3)
    )

    frames = []
    for component in _components(grid, 4):
        box = _frame_box(component)
        if box is not None:
            frames.append(box)
    frames.sort(
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )

    selected = frames[control - 1]
    inner = frames[control] if control < len(frames) else None
    top, left, bottom, right = selected
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] != 0:
                continue
            if inner is not None:
                it, il, ib, ir = inner
                if it <= r <= ib and il <= c <= ir:
                    continue
            result[r][c] = 8
    return result
