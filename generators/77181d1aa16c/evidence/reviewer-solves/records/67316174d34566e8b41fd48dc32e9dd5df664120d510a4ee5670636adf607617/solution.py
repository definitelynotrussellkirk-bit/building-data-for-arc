"""Visible-example solution for ARC task 77181d1aa16c."""
from collections import Counter


def _largest_solid_nonzero_rectangle(grid):
    h, w = len(grid), len(grid[0])
    # Prefix sum of zeros lets us test every rectangle exactly.
    zeros = [[0] * (w + 1) for _ in range(h + 1)]
    for r in range(h):
        for c in range(w):
            zeros[r + 1][c + 1] = (
                zeros[r][c + 1]
                + zeros[r + 1][c]
                - zeros[r][c]
                + (grid[r][c] == 0)
            )
    best = (0, 0, 0, -1, -1)
    for r1 in range(h):
        for r2 in range(r1, h):
            for c1 in range(w):
                for c2 in range(c1, w):
                    area = (r2 - r1 + 1) * (c2 - c1 + 1)
                    if area <= best[0]:
                        continue
                    count_zeros = (
                        zeros[r2 + 1][c2 + 1]
                        - zeros[r1][c2 + 1]
                        - zeros[r2 + 1][c1]
                        + zeros[r1][c1]
                    )
                    if count_zeros == 0:
                        best = (area, r1, c1, r2, c2)
    if best[0] == 0:
        return None
    return best[1:]


def solve(grid):
    h, w = len(grid), len(grid[0])
    rect = _largest_solid_nonzero_rectangle(grid)
    if rect is None:
        return [[0] * w for _ in range(h)]
    r1, c1, r2, c2 = rect
    ph, pw = r2 - r1 + 1, c2 - c1 + 1
    pattern = [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]

    counts = Counter(value for row in pattern for value in row if value != 0)
    roles = [color for color, _ in sorted(counts.items(), key=lambda item: -item[1])[:2]]
    if len(roles) < 2:
        return [[0] * w for _ in range(h)]

    def block_and_role(r, c):
        lower = r >= r1 + ph
        right = c >= c1 + pw
        lr = r - (r1 + ph if lower else r1)
        lc = c - (c1 + pw if right else c1)
        if not (0 <= lr < ph and 0 <= lc < pw):
            return None, None
        sr = ph - 1 - lr if lower else lr
        sc = pw - 1 - lc if right else lc
        role = pattern[sr][sc]
        if role not in roles:
            return None, None
        return 2 * int(lower) + int(right), role

    # Dots outside the source specify target-block recolorings.  Scan order
    # matters when a descriptor appears twice: the first observed color wins.
    mapping = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 or (r1 <= r <= r2 and c1 <= c <= c2):
                continue
            block, role = block_and_role(r, c)
            if block in (1, 2, 3) and (block, role) not in mapping:
                mapping[(block, role)] = value

    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            block, role = block_and_role(r, c)
            if role is None:
                continue
            if block == 0:
                out[r][c] = role
            else:
                out[r][c] = mapping.get((block, role), 0)
    return out
