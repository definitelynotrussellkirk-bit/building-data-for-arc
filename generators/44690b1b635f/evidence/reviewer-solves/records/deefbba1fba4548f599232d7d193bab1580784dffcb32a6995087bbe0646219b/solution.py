from collections import Counter, deque


def solve(grid):
    """Fill the open component containing the one-cell colour anchor as a checkerboard."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]

    # Colour 8 is the fixed maze/wall colour in every visible example.  Of the
    # remaining non-background colours, the checkerboard phase colour occurs
    # exactly once; the companion colour supplies the adjacent cells.
    counts = Counter(v for row in grid for v in row if v not in (0, 8))
    if len(counts) < 2:
        return out
    anchor_colour = min(counts, key=lambda colour: (counts[colour], colour))
    companion_colour = next(
        colour for colour, _ in counts.most_common() if colour != anchor_colour
    )

    anchor = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == anchor_colour
    )

    # Flood through every non-wall cell.  Only the open maze component carrying
    # the anchor is painted; disconnected chambers remain untouched.
    seen = {anchor}
    queue = deque([anchor])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and grid[nr][nc] != 8
                and (nr, nc) not in seen
            ):
                seen.add((nr, nc))
                queue.append((nr, nc))

    anchor_parity = (anchor[0] + anchor[1]) & 1
    for r, c in seen:
        out[r][c] = (
            anchor_colour
            if ((r + c) & 1) == anchor_parity
            else companion_colour
        )
    return out
