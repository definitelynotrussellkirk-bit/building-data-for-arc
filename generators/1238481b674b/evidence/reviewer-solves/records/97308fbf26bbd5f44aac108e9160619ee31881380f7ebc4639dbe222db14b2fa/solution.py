from __future__ import annotations

import copy


def solve(grid):
    """Draw the missing-corner triangle boundary without mutating ``grid``."""
    marks = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(marks) != 4:
        raise ValueError("expected exactly four gray cells")

    r0 = min(r for r, _ in marks)
    r1 = max(r for r, _ in marks)
    c0 = min(c for _, c in marks)
    c1 = max(c for _, c in marks)
    if r1 - r0 != c1 - c0 or r1 == r0:
        raise ValueError("gray extrema must define a nondegenerate square")

    corners = ((r0, c0), (r0, c1), (r1, c0), (r1, c1))
    present = [corner in marks for corner in corners]
    if sum(present) != 3:
        raise ValueError("expected exactly three gray square corners")
    missing = present.index(False)

    output = copy.deepcopy(grid)
    side = r1 - r0
    for u in range(side + 1):
        for v in range(side + 1 - u):
            if u != 0 and v != 0 and u + v != side:
                continue
            r = r0 + u if missing in (0, 1) else r1 - u
            c = c0 + v if missing in (0, 2) else c1 - v
            if output[r][c] == 7:
                output[r][c] = 8
    return output
