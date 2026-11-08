"""Visible-example solution for 504e304a77f1."""
from __future__ import annotations


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r, c - 1), (r, c + 1), (r + 1, c)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc))
                    stack.append((nr, nc))
        cells.sort()
        out.append((color, cells, _bbox(cells)))
    return out


def _is_frame(cells, bbox):
    r0, c0, r1, c1 = bbox
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    outline = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return set(cells) == outline


def solve(grid):
    """Rank objects by cell count, rank frames by interior area, and center."""
    parts = _components(grid)
    frames = [part for part in parts if _is_frame(part[1], part[2])]
    shapes = [part for part in parts if not _is_frame(part[1], part[2])]

    # Visible examples show strict ranks; column then row is only a stable tie-break.
    frames.sort(
        key=lambda part: (
            (part[2][2] - part[2][0] - 1) * (part[2][3] - part[2][1] - 1),
            part[2][1],
            part[2][0],
        )
    )
    shapes.sort(key=lambda part: (len(part[1]), part[2][1], part[2][0]))

    out = [[0 for _ in row] for row in grid]
    for color, cells, _ in frames:
        for r, c in cells:
            out[r][c] = color

    for frame, shape in zip(frames, shapes):
        color, cells, (sr0, sc0, sr1, sc1) = shape
        fr0, fc0, fr1, fc1 = frame[2]
        sh, sw = sr1 - sr0 + 1, sc1 - sc0 + 1
        ih, iw = fr1 - fr0 - 1, fc1 - fc0 - 1
        top = fr0 + 1 + (ih - sh) // 2
        left = fc0 + 1 + (iw - sw) // 2
        for r, c in cells:
            out[top + r - sr0][left + c - sc0] = color
    return out
