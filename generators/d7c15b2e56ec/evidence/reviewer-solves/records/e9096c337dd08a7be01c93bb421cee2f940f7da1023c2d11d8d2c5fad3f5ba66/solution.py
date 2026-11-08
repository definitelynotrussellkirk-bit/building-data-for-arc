from collections import deque


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            yield cells


def _is_hollow_rectangle(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None
    perimeter = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return (r0, r1, c0, c1) if set(cells) == perimeter else None


def solve(grid):
    """Recolor every non-background object inside a rectangular frame.

    A nested object inherits the color of the outermost enclosing frame.
    """
    out = [row[:] for row in grid]
    background = max(set(v for row in grid for v in row), key=lambda v: sum(row.count(v) for row in grid))

    frames = []
    for color in set(v for row in grid for v in row if v != background):
        for cells in _components(grid, color):
            box = _is_hollow_rectangle(cells)
            if box is not None:
                r0, r1, c0, c1 = box
                frames.append(((r1 - r0 + 1) * (c1 - c0 + 1), color, box))

    # Inner frames first, outer frames last, so the outermost frame wins.
    for _, color, (r0, r1, c0, c1) in sorted(frames):
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if out[r][c] != background:
                    out[r][c] = color
    return out
