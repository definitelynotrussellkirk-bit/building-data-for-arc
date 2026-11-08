from __future__ import annotations


def _find_key(grid: list[list[int]]) -> tuple[int, int, str]:
    """Return the top-left cell and corner name of the unique 2x2 colour key."""
    h, w = len(grid), len(grid[0])
    candidates = (
        (0, 0, "tl"),
        (0, w - 2, "tr"),
        (h - 2, 0, "bl"),
        (h - 2, w - 2, "br"),
    )
    matches = []
    for r, c, corner in candidates:
        values = [grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]]
        if all(value not in (0, 8) for value in values) and len(set(values)) == 4:
            matches.append((r, c, corner))
    if len(matches) != 1:
        raise ValueError(f"expected one corner key, found {len(matches)}")
    return matches[0]


def solve(grid):
    h, w = len(grid), len(grid[0])
    kr, kc, corner = _find_key(grid)

    if corner == "tl":
        r0, r1, c0, c1 = 2, h - 1, 2, w - 1
    elif corner == "tr":
        r0, r1, c0, c1 = 2, h - 1, 0, w - 3
    elif corner == "bl":
        r0, r1, c0, c1 = 0, h - 3, 2, w - 1
    else:  # br
        r0, r1, c0, c1 = 0, h - 3, 0, w - 3

    # The first coloured body cell in reading order is the marker colour.
    marker = None
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] not in (0, 8):
                marker = grid[r][c]
                break
        if marker is not None:
            break
    if marker is None:
        return [row[:] for row in grid]

    key = (
        (grid[kr][kc], grid[kr][kc + 1]),
        (grid[kr + 1][kc], grid[kr + 1][kc + 1]),
    )
    out = [row[:] for row in grid]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != marker:
                continue
            # Strictly before the midpoint is top/left; an exact midpoint is
            # assigned to bottom/right, as shown by the midline example.
            qr = 0 if 2 * r < r0 + r1 else 1
            qc = 0 if 2 * c < c0 + c1 else 1
            out[r][c] = key[qr][qc]
    return out
