"""Visible-example solution for ee602abaa45a."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] < 7 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            found.append((min(rows), min(cols), max(rows), max(cols), color))
    return sorted(found, key=lambda item: (item[0], item[1]))


def _crop(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    bottom = max(r for r, _ in cells)
    right = max(c for _, c in cells)
    out = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for r, c in cells:
        out[r - top][c - left] = 1
    return out


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, code):
    if code == 3:
        return [row[:] for row in grid]
    if code == 4:
        return _rotate_cw(grid)
    if code == 5:
        return [row[::-1] for row in grid[::-1]]
    if code == 6:
        return [row[::-1] for row in grid]
    raise ValueError(f"unexpected transform code {code}")


def solve(grid):
    """Select, transform, recolor, and pack the two framed templates."""
    frames = _components(grid)
    pieces = []
    for top, left, bottom, right, frame_color in frames:
        selector = grid[bottom - 1][left + 1]
        transform_code = grid[bottom - 1][left + 2]
        if selector == 1:
            col_start = left + 1
        elif selector == 2:
            col_start = left + 4
        else:
            raise ValueError(f"unexpected selector {selector}")
        cells = [
            (r, c)
            for r in range(top + 1, top + 4)
            for c in range(col_start, col_start + 3)
            if grid[r][c] == selector
        ]
        shape = _transform(_crop(cells), transform_code)
        pieces.append(
            [[frame_color if value else 0 for value in row] for row in shape]
        )

    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for piece in pieces:
        top = (out_h - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out
