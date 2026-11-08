from collections import deque


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            comps.append(
                {
                    "color": color,
                    "top": min(rs),
                    "bottom": max(rs),
                    "left": min(cs),
                    "right": max(cs),
                }
            )
    return comps


def solve(grid):
    """Join aligned same-colour rectangles with inset grey (8) bridges."""
    out = [row[:] for row in grid]
    comps = _components(grid)

    for i, a in enumerate(comps):
        for b in comps[i + 1 :]:
            if a["color"] != b["color"]:
                continue

            # Horizontal bridge: the rectangles are separated left/right and
            # their row spans overlap by at least three cells.  The bridge is
            # inset one cell from both ends of that overlap.
            left, right = (a, b) if a["left"] < b["left"] else (b, a)
            if left["right"] < right["left"] - 1:
                lo = max(left["top"], right["top"])
                hi = min(left["bottom"], right["bottom"])
                if hi - lo + 1 >= 3:
                    rows = range(lo + 1, hi)
                    cols = range(left["right"] + 1, right["left"])
                    if all(grid[r][c] == 0 for r in rows for c in cols):
                        for r in rows:
                            for c in cols:
                                out[r][c] = 8

            # Vertical bridge, defined symmetrically.
            top, bottom = (a, b) if a["top"] < b["top"] else (b, a)
            if top["bottom"] < bottom["top"] - 1:
                lo = max(top["left"], bottom["left"])
                hi = min(top["right"], bottom["right"])
                if hi - lo + 1 >= 3:
                    rows = range(top["bottom"] + 1, bottom["top"])
                    cols = range(lo + 1, hi)
                    if all(grid[r][c] == 0 for r in rows for c in cols):
                        for r in rows:
                            for c in cols:
                                out[r][c] = 8

    return out
