"""Visible-example solution for the generated complete-icon task."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _objects8(grid, background):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    }
    objects = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in DIR8:
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    stack.append(q)
        objects.append(sorted(cells))
    return objects


def _bridged(a, b, grid, background):
    b = set(b)
    h, w = len(grid), len(grid[0])
    for r, c in a:
        for dr, dc in DIR4:
            midpoint = (r + dr, c + dc)
            far = (r + 2 * dr, c + 2 * dc)
            if (
                0 <= midpoint[0] < h
                and 0 <= midpoint[1] < w
                and grid[midpoint[0]][midpoint[1]] == background
                and far in b
            ):
                return True
    return False


def _logical_icons(grid, background):
    groups = _objects8(grid, background)
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            partner = next(
                (
                    j
                    for j in range(i + 1, len(groups))
                    if _bridged(groups[i], groups[j], grid, background)
                    or _bridged(groups[j], groups[i], grid, background)
                ),
                None,
            )
            if partner is not None:
                groups[i] = sorted(set(groups[i]) | set(groups[partner]))
                del groups[partner]
                changed = True
                break
    return groups


def _rounded_midpoint(lo, hi):
    # Both Python and the visible examples use ties-to-even rounding.
    return int(round((lo + hi) / 2.0))


def _complete_icon(output, source, icon, background):
    h, w = len(source), len(source[0])
    rows = [r for r, _ in icon]
    cols = [c for _, c in icon]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    bh, bw = r2 - r1 + 1, c2 - c1 + 1
    square = bh == bw
    cri, cci = _rounded_midpoint(r1, r2), _rounded_midpoint(c1, c2)

    if square:
        sr1, sr2, sc1, sc2 = r1, r2, c1, c2
        cr, cc = (r1 + r2) / 2.0, (c1 + c2) / 2.0
    else:
        row_radius = max(cri - r1, r2 - cri)
        col_radius = max(cci - c1, c2 - cci)
        sr1, sr2 = max(0, cri - row_radius), min(h - 1, cri + row_radius)
        sc1, sc2 = max(0, cci - col_radius), min(w - 1, cci + col_radius)
        cr, cc = cri, cci

    def partners(r, c):
        if square:
            return (
                (round(cr + (c - cc)), round(cc - (r - cr))),
                (round(cr - (r - cr)), round(cc - (c - cc))),
                (round(cr - (c - cc)), round(cc + (r - cr))),
            )
        return (
            (r, round(2 * cc - c)),
            (round(2 * cr - r), c),
            (round(2 * cr - r), round(2 * cc - c)),
        )

    for r in range(sr1, sr2 + 1):
        for c in range(sc1, sc2 + 1):
            if output[r][c] != background:
                continue
            for rr, cc2 in partners(r, c):
                rr, cc2 = int(rr), int(cc2)
                if 0 <= rr < h and 0 <= cc2 < w and source[rr][cc2] != background:
                    output[r][c] = source[rr][cc2]
                    break

    if square and bh % 2 == 1 and bw % 2 == 1 and output[cri][cci] == background:
        fill = source[icon[0][0]][icon[0][1]]

        def painted(rr, cc2):
            return (
                sr1 <= rr <= sr2
                and sc1 <= cc2 <= sc2
                and output[rr][cc2] == fill
            )

        cardinal_support = (
            cri > sr1
            and cri < sr2
            and cci > sc1
            and cci < sc2
            and painted(cri, cci - 1)
            and painted(cri, cci + 1)
            and painted(cri - 1, cci)
            and painted(cri + 1, cci)
        )
        diagonal_support = (
            bh >= 7
            and bw >= 7
            and painted(cri - 1, cci - 1)
            and painted(cri - 1, cci + 1)
            and painted(cri + 1, cci - 1)
            and painted(cri + 1, cci + 1)
            and painted(sr1, cci)
            and painted(sr2, cci)
            and painted(cri, sc1)
            and painted(cri, sc2)
        )
        if cardinal_support or diagonal_support:
            output[cri][cci] = fill


def solve(grid):
    """Complete each monochrome icon under the symmetry shown in the examples."""
    if not grid or not grid[0]:
        return deepcopy(grid)
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    output = deepcopy(grid)
    for icon in _logical_icons(grid, background):
        _complete_icon(output, grid, icon, background)
    return output
