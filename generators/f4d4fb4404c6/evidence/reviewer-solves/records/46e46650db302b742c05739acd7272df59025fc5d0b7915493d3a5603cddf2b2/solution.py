"""Visible-example transformation for the final reviewer solve episode."""


def _components(grid, value):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == value}
    comps = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen:
                    unseen.remove(q)
                    comp.add(q)
                    stack.append(q)
        comps.append(comp)
    return comps


def _paint_ring(out, color, top, left):
    h, w = len(out), len(out[0])
    for r in range(top, top + 4):
        for c in range(left, left + 4):
            if (r in (top, top + 3) or c in (left, left + 3)) and 0 <= r < h and 0 <= c < w:
                out[r][c] = color


def solve(grid):
    h, w = len(grid), len(grid[0])

    frames = []
    claimed = set()
    for top in range(h - 3):
        for left in range(w - 3):
            ring = {
                (r, c)
                for r in range(top, top + 4)
                for c in range(left, left + 4)
                if r in (top, top + 3) or c in (left, left + 3)
            }
            colors = {grid[r][c] for r, c in ring}
            if len(colors) != 1:
                continue
            color = next(iter(colors))
            if color in (0, 1) or ring & claimed:
                continue
            if any(grid[r][c] != 0 for r in (top + 1, top + 2) for c in (left + 1, left + 2)):
                continue
            frames.append((color, top, left))
            claimed |= ring

    out = [[0] * w for _ in range(h)]
    for color, top, left in frames:
        _paint_ring(out, color, top, left)

    for marker in _components(grid, 1):
        rows = [r for r, _ in marker]
        cols = [c for _, c in marker]
        if min(rows) == max(rows) == 0:
            direction = "up"
        elif min(rows) == max(rows) == h - 1:
            direction = "down"
        elif min(cols) == max(cols) == 0:
            direction = "left"
        elif min(cols) == max(cols) == w - 1:
            direction = "right"
        else:
            continue

        candidates = []
        for frame in frames:
            _, top, left = frame
            if direction in ("up", "down"):
                overlaps = not (left + 3 < min(cols) or max(cols) < left)
            else:
                overlaps = not (top + 3 < min(rows) or max(rows) < top)
            if overlaps:
                candidates.append(frame)
        if not candidates:
            continue
        color, top, left = candidates[0]

        if direction == "up":
            top -= 4
            while top + 3 >= 0:
                _paint_ring(out, color, top, left)
                top -= 4
        elif direction == "down":
            top += 4
            while top < h:
                _paint_ring(out, color, top, left)
                top += 4
        elif direction == "left":
            left -= 4
            while left + 3 >= 0:
                _paint_ring(out, color, top, left)
                left -= 4
        else:
            left += 4
            while left < w:
                _paint_ring(out, color, top, left)
                left += 4

    return out
