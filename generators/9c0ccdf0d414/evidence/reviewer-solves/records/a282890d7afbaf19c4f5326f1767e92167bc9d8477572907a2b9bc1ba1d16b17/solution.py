"""Visible-example solution for the quadrant-mosaic task."""


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _crop(grid, cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def solve(grid):
    """Crop each colored motif and place it in its source quadrant of a 2x2 mosaic."""
    h, w = len(grid), len(grid[0])
    slots = [None, None, None, None]  # TL, TR, BL, BR

    for _color, cells in _components(grid):
        # Compare the component centroid with the geometric center without floats.
        top = 2 * sum(r for r, _ in cells) < len(cells) * (h - 1)
        left = 2 * sum(c for _, c in cells) < len(cells) * (w - 1)
        slot = (0 if top else 2) + (0 if left else 1)
        if slots[slot] is None:
            slots[slot] = _crop(grid, cells)

    tl, tr, bl, br = slots
    top_h = max(len(tl) if tl else 1, len(tr) if tr else 1)
    bottom_h = max(len(bl) if bl else 1, len(br) if br else 1)
    left_w = max(len(tl[0]) if tl else 1, len(bl[0]) if bl else 1)
    right_w = max(len(tr[0]) if tr else 1, len(br[0]) if br else 1)

    out = [[0] * (left_w + 1 + right_w) for _ in range(top_h + 1 + bottom_h)]

    def paste(shape, r0, c0):
        if shape is None:
            return
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                if value != 0:
                    out[r0 + r][c0 + c] = value

    paste(tl, 0, 0)
    paste(tr, 0, left_w + 1)
    paste(bl, top_h + 1, 0)
    paste(br, top_h + 1, left_w + 1)
    return out
