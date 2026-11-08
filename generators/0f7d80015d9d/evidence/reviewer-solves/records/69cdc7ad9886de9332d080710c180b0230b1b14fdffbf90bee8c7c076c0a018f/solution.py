from collections import Counter


def solve(grid):
    """Advance the two markers around the lower rectangle.

    The 2 takes the 8's former position.  The 8 then moves to the lower
    outside corner on the same horizontal side indicated by its position
    relative to the 2 (left when 8 is left of 2, right otherwise).
    """
    out = [row[:] for row in grid]
    positions = {}
    five_cells = []
    counts = Counter()

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            counts[value] += 1
            if value in (2, 8):
                positions[value] = (r, c)
            elif value == 5:
                five_cells.append((r, c))

    if 2 not in positions or 8 not in positions or not five_cells:
        return out

    background = counts.most_common(1)[0][0]
    r2, c2 = positions[2]
    r8, c8 = positions[8]

    out[r2][c2] = background
    out[r8][c8] = 2

    bottom = max(r for r, _ in five_cells)
    left = min(c for _, c in five_cells)
    right = max(c for _, c in five_cells)
    destination_col = left - 1 if c8 < c2 else right + 1
    out[bottom][destination_col] = 8
    return out
