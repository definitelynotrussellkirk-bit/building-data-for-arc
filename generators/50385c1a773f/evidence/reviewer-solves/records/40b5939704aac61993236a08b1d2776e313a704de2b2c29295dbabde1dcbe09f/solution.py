"""Visible-example solution for the blind ARC episode."""


def solve(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])

    def first(color):
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == color:
                    return r, c
        return None

    red = first(2)
    yellow = first(4)
    green = first(3)
    gray = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]

    points = [p for p in (red, yellow, green) if p is not None]
    if not points:
        return out

    # Join the ordered colored waypoints with axis-aligned azure segments.
    for (r1, c1), (r2, c2) in zip(points, points[1:]):
        if r1 == r2:
            for c in range(min(c1, c2) + 1, max(c1, c2)):
                if out[r1][c] == 0:
                    out[r1][c] = 8
        elif c1 == c2:
            for r in range(min(r1, r2) + 1, max(r1, r2)):
                if out[r][c1] == 0:
                    out[r][c1] = 8

    if len(points) < 2 or not gray:
        return out

    prev_r, prev_c = points[-2]
    end_r, end_c = points[-1]
    incoming_horizontal = prev_r == end_r

    # The final ray turns 90 degrees. Prefer a gray stop already aligned with
    # that ray; otherwise use the nearest gray clue to choose the side and run
    # to the boundary.
    if incoming_horizontal:
        aligned = [(abs(r - end_r), r, c) for r, c in gray if c == end_c and r != end_r]
        if aligned:
            _, target_r, _ = min(aligned)
            dr = 1 if target_r > end_r else -1
        else:
            target_r, _ = min(gray, key=lambda p: (abs(p[1] - end_c), abs(p[0] - end_r)))
            dr = 1 if target_r > end_r else -1
        r = end_r + dr
        while 0 <= r < h and out[r][end_c] != 5:
            if out[r][end_c] == 0:
                out[r][end_c] = 8
            r += dr
    else:
        aligned = [(abs(c - end_c), r, c) for r, c in gray if r == end_r and c != end_c]
        if aligned:
            _, _, target_c = min(aligned)
            dc = 1 if target_c > end_c else -1
        else:
            _, target_c = min(gray, key=lambda p: (abs(p[0] - end_r), abs(p[1] - end_c)))
            dc = 1 if target_c > end_c else -1
        c = end_c + dc
        while 0 <= c < w and out[end_r][c] != 5:
            if out[end_r][c] == 0:
                out[end_r][c] = 8
            c += dc

    return out
