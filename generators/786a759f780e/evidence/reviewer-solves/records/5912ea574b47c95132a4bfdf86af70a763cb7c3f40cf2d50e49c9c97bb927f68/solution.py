from __future__ import annotations


def solve(grid):
    """Crop nonzero components, sort by (holes, area, first color), and pack."""
    h, w = len(grid), len(grid[0])
    neighbors = ((-1, 0), (1, 0), (0, -1), (0, 1))
    seen = set()
    items = []

    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            key_color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in neighbors:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [row[left : right + 1] for row in grid[top : bottom + 1]]

            ch, cw = len(crop), len(crop[0])
            zeros = {
                (r, c)
                for r in range(ch)
                for c in range(cw)
                if crop[r][c] == 0
            }
            holes = 0
            while zeros:
                start = min(zeros)
                zeros.remove(start)
                todo = [start]
                touches_border = False
                while todo:
                    r, c = todo.pop()
                    if r in (0, ch - 1) or c in (0, cw - 1):
                        touches_border = True
                    for dr, dc in neighbors:
                        nxt = (r + dr, c + dc)
                        if nxt in zeros:
                            zeros.remove(nxt)
                            todo.append(nxt)
                if not touches_border:
                    holes += 1

            items.append((holes, len(cells), key_color, crop))

    items.sort(key=lambda item: item[:3])
    out_h = max(len(crop) for _, _, _, crop in items)
    out_w = sum(len(crop[0]) for _, _, _, crop in items) + len(items) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for _, _, _, crop in items:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][left + c] = value
        left += len(crop[0]) + 1
    return out
