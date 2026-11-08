"""Blind solution for task bdd177308a5b.

The color-5 L-shaped frame encloses a reference polyomino.  Exactly one
same-colored connected component elsewhere has the same normalized shape in
the same orientation; recolor that component with the frame color.
"""

from collections import deque


def _shape(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _components(grid, forbidden=frozenset({0, 5})):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in forbidden or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            yield color, cells


def solve(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])

    # Locate the corner of the top-left color-5 frame.  It is the first row
    # and column whose prefixes are entirely 5 and meet at the same cell.
    corner = None
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5:
                continue
            if all(grid[rr][c] == 5 for rr in range(r + 1)) and all(
                grid[r][cc] == 5 for cc in range(c + 1)
            ):
                if any(grid[rr][cc] not in (0, 5) for rr in range(r) for cc in range(c)):
                    corner = (r, c)
                    break
        if corner is not None:
            break
    if corner is None:
        return out

    frame_r, frame_c = corner
    reference = [
        (r, c)
        for r in range(frame_r)
        for c in range(frame_c)
        if grid[r][c] not in (0, 5)
    ]
    if not reference:
        return out
    reference_shape = _shape(reference)

    for _color, cells in _components(grid):
        # Do not select the reference object itself.
        if all(r < frame_r and c < frame_c for r, c in cells):
            continue
        if _shape(cells) == reference_shape:
            for r, c in cells:
                out[r][c] = 5
    return out
