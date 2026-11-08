from __future__ import annotations


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        cells = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    stack.append(p)
                    cells.append(p)
        result.append(cells)
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def solve(grid):
    frames = []
    for cells in _components(grid, 9):
        r0, r1, c0, c1 = _bbox(cells)
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if set(cells) == perimeter:
            frames.append((r0, c0, r1, c1))
    frames.sort()

    parts = []
    for r0, c0, r1, c1 in frames:
        key = next(
            grid[r0 - 1][c]
            for c in range(c0, c1 + 1)
            if grid[r0 - 1][c] not in (0, 9)
        )
        blue = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] == 1
        ]
        red = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] == 2
        ]
        br0, br1, bc0, bc1 = _bbox(blue)
        rr0, rr1, rc0, rc1 = _bbox(red)
        height = min(br1, rr1) - max(br0, rr0) + 1
        width = min(bc1, rc1) - max(bc0, rc0) + 1
        parts.append((key, height, width))

    gallery_h = max(height for _, height, _ in parts)
    gallery_w = sum(width for _, _, width in parts) + len(parts) - 1
    output = [[0] * gallery_w for _ in range(gallery_h)]
    left = 0
    for key, height, width in parts:
        top = (gallery_h - height) // 2
        for r in range(top, top + height):
            for c in range(left, left + width):
                output[r][c] = key
        left += width + 1
    return output
