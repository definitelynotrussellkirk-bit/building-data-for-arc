def solve(grid):
    """Bend every red rod at its black pivot toward the grid centre.

    Each rod is a straight run from a green endpoint (5), through red cells (2),
    to a black pivot (0), with a red tail beyond the pivot.  The endpoint-to-
    pivot part stays fixed; the tail is rotated 90 degrees toward the centre.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]
    if not h or not w:
        return out

    background = 7
    red = 2
    pivot_color = 0
    endpoint_color = 5
    cardinal = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    rods = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != endpoint_color:
                continue
            candidates = []
            for dr, dc in cardinal:
                rr, cc = r + dr, c + dc
                body = []
                while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == red:
                    body.append((rr, cc))
                    rr += dr
                    cc += dc
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                if grid[rr][cc] != pivot_color:
                    continue
                pivot = (rr, cc)
                rr += dr
                cc += dc
                tail = []
                while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == red:
                    tail.append((rr, cc))
                    rr += dr
                    cc += dc
                if tail:
                    candidates.append((len(body) + len(tail), body, pivot, tail, (dr, dc)))
            if candidates:
                # Genuine rods are unique.  Longest wins defensively at crossings.
                _, body, pivot, tail, direction = max(candidates, key=lambda x: x[0])
                rods.append({
                    "endpoint": (r, c),
                    "body": body,
                    "pivot": pivot,
                    "tail": tail,
                    "direction": direction,
                })

    protected = set()
    tails = set()
    for rod in rods:
        protected.add(rod["endpoint"])
        protected.add(rod["pivot"])
        protected.update(rod["body"])
        tails.update(rod["tail"])

    # Erase only cells used solely by a tail; intersections/core cells survive.
    for r, c in tails - protected:
        out[r][c] = background

    center_r = (h - 1) / 2.0
    center_c = (w - 1) / 2.0

    for rod in rods:
        pr, pc = rod["pivot"]
        dr, dc = rod["direction"]
        tail_len = len(rod["tail"])
        if dr != 0:  # vertical rod: bend horizontally
            options = [(0, -1), (0, 1)]
        else:        # horizontal rod: bend vertically
            options = [(-1, 0), (1, 0)]

        def option_score(turn):
            tr, tc = turn
            cells = [(pr + tr * k, pc + tc * k) for k in range(1, tail_len + 1)]
            in_bounds = all(0 <= rr < h and 0 <= cc < w for rr, cc in cells)
            collisions = sum(
                1 for rr, cc in cells
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] not in (background, red)
            )
            centre_distance = sum(
                abs(rr - center_r) + abs(cc - center_c)
                for rr, cc in cells
                if 0 <= rr < h and 0 <= cc < w
            )
            return (not in_bounds, collisions, centre_distance)

        turn = min(options, key=option_score)
        tr, tc = turn
        for k in range(1, tail_len + 1):
            rr, cc = pr + tr * k, pc + tc * k
            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] not in (pivot_color, endpoint_color):
                out[rr][cc] = red

    return out
