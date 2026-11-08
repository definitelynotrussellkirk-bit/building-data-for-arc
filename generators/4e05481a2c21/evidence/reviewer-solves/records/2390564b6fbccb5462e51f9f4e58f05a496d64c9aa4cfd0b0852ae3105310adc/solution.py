"""Visible-example solution for reviewer episode 4e05481a2c21."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            for y, x in queue:
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < h and 0 <= nx < w
                            and (ny, nx) not in seen
                            and grid[ny][nx] == color):
                        seen.add((ny, nx))
                        queue.append((ny, nx))
            result.append((color, set(cells)))
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _enclosed_zeros(cells):
    r0, c0, r1, c1 = _bbox(cells)
    candidates = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r, c) not in cells
    }
    seen = set()
    enclosed = set()
    for start in sorted(candidates):
        if start in seen:
            continue
        queue = [start]
        seen.add(start)
        region = []
        touches_edge = False
        for r, c in queue:
            region.append((r, c))
            touches_edge |= r in (r0, r1) or c in (c0, c1)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = r + dr, c + dc
                if nxt in candidates and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not touches_edge:
            enclosed.update(region)
    return enclosed


def solve(grid):
    pieces = []
    for color, cells in _components(grid):
        holes = _enclosed_zeros(cells)
        if not holes:
            continue
        hr0, hc0, hr1, hc1 = _bbox(holes)
        normalized = {(r - hr0, c - hc0) for r, c in holes}
        _or0, object_left, _or1, _oc1 = _bbox(cells)
        pieces.append((object_left, color, normalized, hr1 - hr0 + 1, hc1 - hc0 + 1))

    pieces.sort(key=lambda item: item[0])
    if not pieces:
        return []
    out_h = max(item[3] for item in pieces)
    out_w = sum(item[4] for item in pieces) + len(pieces) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for _object_left, color, shape, _height, width in pieces:
        for r, c in shape:
            out[r][left + c] = color
        left += width + 1
    return out
