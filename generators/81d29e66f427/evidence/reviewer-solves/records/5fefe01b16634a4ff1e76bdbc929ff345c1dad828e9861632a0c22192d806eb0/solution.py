from __future__ import annotations

from collections import deque


def _frames(grid):
    """Find exact hollow color-5 rectangular components, left to right."""
    h, w = len(grid), len(grid[0])
    seen = set()
    boxes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while q:
                rr, cc = q.popleft()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            box = min(rs), min(cs), max(rs), max(cs)
            r1, c1, r2, c2 = box
            border = {
                (rr, cc)
                for rr in range(r1, r2 + 1)
                for cc in range(c1, c2 + 1)
                if rr in (r1, r2) or cc in (c1, c2)
            }
            if cells == border:
                boxes.append(box)
    return sorted(boxes, key=lambda box: box[1])


def solve(grid):
    keys = [value for value in grid[0] if value != 0]
    left, right = _frames(grid)
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    ih, iw = lr2 - lr1 - 1, lc2 - lc1 - 1

    a = {
        (r - lr1 - 1, c - lc1 - 1)
        for r in range(lr1 + 1, lr2)
        for c in range(lc1 + 1, lc2)
        if grid[r][c] == 2
    }
    b = {
        (r - rr1 - 1, c - rc1 - 1)
        for r in range(rr1 + 1, rr2)
        for c in range(rc1 + 1, rc2)
        if grid[r][c] == 3
    }

    output = [[0] * (len(keys) * iw + len(keys) - 1) for _ in range(ih)]
    for panel_index, key in enumerate(keys):
        if key == 2:
            cells = a | b
        elif key == 3:
            cells = a & b
        else:
            cells = a ^ b
        left_col = panel_index * (iw + 1)
        for r, c in cells:
            output[r][left_col + c] = 8
    return output
