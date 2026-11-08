"""Visible-example solution for the generated stream-and-bars ARC task."""

from __future__ import annotations


def _copy_grid(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return [row[:] for row in grid]


def solve(grid):
    """Trace the edge-entering red stream, routing around intersecting bars.

    The single red cell (2) is on the top or left edge and fixes the forward
    direction.  A blue bar (1) sends the stream to its left-hand side; a green
    bar (3) sends it to its right-hand side.  The stream then resumes its
    original forward direction.  Only zero cells on the route are recolored.
    """
    out = _copy_grid(grid)
    height, width = len(out), len(out[0])
    markers = [(r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value == 2]
    if len(markers) != 1:
        raise ValueError("expected exactly one red marker")

    r, c = markers[0]
    if r == 0 and 0 < c < width - 1:
        dr, dc = 1, 0
    elif c == 0 and 0 < r < height - 1:
        dr, dc = 0, 1
    else:
        raise ValueError("red marker must be on the non-corner top or left edge")

    def inside(rr, cc):
        return 0 <= rr < height and 0 <= cc < width

    def paint(rr, cc):
        if out[rr][cc] == 0:
            out[rr][cc] = 2

    paint(r, c)
    while True:
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            break
        cell = out[nr][nc]
        if cell == 0 or cell == 2:
            r, c = nr, nc
            paint(r, c)
            continue
        if cell not in (1, 3):
            raise ValueError(f"unexpected obstacle color {cell}")

        # The obstacle is perpendicular to the stream.  Blue means a
        # left-hand detour; green means a right-hand detour.
        if dr:  # entering from the top; obstacle run is horizontal
            lo = hi = nc
            while lo > 0 and out[nr][lo - 1] == cell:
                lo -= 1
            while hi + 1 < width and out[nr][hi + 1] == cell:
                hi += 1
            target_c = hi + 1 if cell == 1 else lo - 1
            if not inside(r, target_c):
                raise ValueError("bar detour leaves grid")
            step = 1 if target_c > c else -1
            for cc in range(c + step, target_c + step, step):
                if out[r][cc] not in (0, 2):
                    raise ValueError("detour is blocked")
                paint(r, cc)
            c = target_c
        else:  # entering from the left; obstacle run is vertical
            lo = hi = nr
            while lo > 0 and out[lo - 1][nc] == cell:
                lo -= 1
            while hi + 1 < height and out[hi + 1][nc] == cell:
                hi += 1
            target_r = lo - 1 if cell == 1 else hi + 1
            if not inside(target_r, c):
                raise ValueError("bar detour leaves grid")
            step = 1 if target_r > r else -1
            for rr in range(r + step, target_r + step, step):
                if out[rr][c] not in (0, 2):
                    raise ValueError("detour is blocked")
                paint(rr, c)
            r = target_r

        # Move one step forward past the bar and continue straight.
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            break
        if out[nr][nc] not in (0, 2):
            raise ValueError("bar exit is blocked")
        r, c = nr, nc
        paint(r, c)

    return out
