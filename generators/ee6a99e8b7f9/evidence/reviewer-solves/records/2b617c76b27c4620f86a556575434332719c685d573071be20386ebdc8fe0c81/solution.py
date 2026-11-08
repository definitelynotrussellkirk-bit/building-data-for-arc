from __future__ import annotations


def solve(grid):
    """Apply the color-dependent marker rule inferred from the visible pairs.

    6-rectangles remain: each adjacent 9 is moved onto the rectangle's
    horizontal/vertical centre line, preserving its coordinate along the edge.
    5-rectangles disappear: each adjacent 9 remains and is copied one step
    inward onto the rectangle's boundary cell.
    """
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]

    # Find orthogonally connected monochrome 5/6 components in the untouched input.
    seen = set()
    shapes = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color not in (5, 6) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < h and 0 <= nx < w and
                            (ny, nx) not in seen and grid[ny][nx] == color):
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            rs = [y for y, _ in cells]
            cs = [x for _, x in cells]
            shapes.append((color, cells, min(rs), max(rs), min(cs), max(cs)))

    pink_sources = set()
    targets = set()

    for color, cells, r0, r1, c0, c1 in shapes:
        if color == 5:
            for y, x in cells:
                out[y][x] = 8

        # A marker belongs to an edge when it is exactly one cell outside that
        # edge and its other coordinate lies within the edge span.
        adjacent = []
        for c in range(c0, c1 + 1):
            if r0 > 0 and grid[r0 - 1][c] == 9:
                adjacent.append((r0 - 1, c, "above"))
            if r1 + 1 < h and grid[r1 + 1][c] == 9:
                adjacent.append((r1 + 1, c, "below"))
        for r in range(r0, r1 + 1):
            if c0 > 0 and grid[r][c0 - 1] == 9:
                adjacent.append((r, c0 - 1, "left"))
            if c1 + 1 < w and grid[r][c1 + 1] == 9:
                adjacent.append((r, c1 + 1, "right"))

        # De-duplicate only exact marker/side triples; corner-near markers are
        # never orthogonally adjacent to two sides of the same rectangle.
        for y, x, side in dict.fromkeys(adjacent):
            if color == 6:
                pink_sources.add((y, x))
                if side in ("above", "below"):
                    targets.add(((r0 + r1) // 2, x))
                else:
                    targets.add((y, (c0 + c1) // 2))
            else:
                if side == "above":
                    targets.add((r0, x))
                elif side == "below":
                    targets.add((r1, x))
                elif side == "left":
                    targets.add((y, c0))
                else:
                    targets.add((y, c1))

    for y, x in pink_sources:
        out[y][x] = 8
    for y, x in targets:
        out[y][x] = 9
    return out
