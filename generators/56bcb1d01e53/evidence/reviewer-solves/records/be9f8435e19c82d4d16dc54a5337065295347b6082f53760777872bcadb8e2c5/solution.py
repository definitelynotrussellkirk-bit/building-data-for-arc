"""Visible-example solution for the repaired complete-icon-symmetry lesson."""
from collections import Counter

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


def _components(grid, bg):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != bg
    }
    groups = []
    while remaining:
        point = min(remaining)
        remaining.remove(point)
        stack = [point]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in DIR8:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        groups.append(cells)
    return groups


def _one_gap_bridge(a, b, grid, bg):
    b = set(b)
    for r, c in a:
        for dr, dc in DIR4:
            far = (r + 2 * dr, c + 2 * dc)
            mid = (r + dr, c + dc)
            if far in b and grid[mid[0]][mid[1]] == bg:
                return True
    return False


def _logical_icons(grid, bg):
    groups = _components(grid, bg)
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            j = next(
                (j for j in range(i + 1, len(groups))
                 if _one_gap_bridge(groups[i], groups[j], grid, bg)),
                None,
            )
            if j is not None:
                groups[i] += groups[j]
                del groups[j]
                changed = True
                break
    return groups


def solve(grid):
    height, width = len(grid), len(grid[0])
    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    result = [row[:] for row in grid]

    for icon in _logical_icons(grid, bg):
        rows = [r for r, _ in icon]
        cols = [c for _, c in icon]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        box_h, box_w = r2 - r1 + 1, c2 - c1 + 1
        square = box_h == box_w
        center_r = round((r1 + r2) / 2)
        center_c = round((c1 + c2) / 2)

        if square:
            sr1, sr2, sc1, sc2 = r1, r2, c1, c2
            cr, cc = (r1 + r2) / 2, (c1 + c2) / 2
        else:
            rr = max(center_r - r1, r2 - center_r)
            rc = max(center_c - c1, c2 - center_c)
            sr1, sr2 = max(0, center_r - rr), min(height - 1, center_r + rr)
            sc1, sc2 = max(0, center_c - rc), min(width - 1, center_c + rc)
            cr, cc = center_r, center_c

        for r in range(sr1, sr2 + 1):
            for c in range(sc1, sc2 + 1):
                if result[r][c] != bg:
                    continue
                if square:
                    partners = (
                        (round(cr + c - cc), round(cc - (r - cr))),
                        (round(cr - (r - cr)), round(cc - (c - cc))),
                        (round(cr - (c - cc)), round(cc + (r - cr))),
                    )
                else:
                    partners = (
                        (r, round(2 * cc - c)),
                        (round(2 * cr - r), c),
                        (round(2 * cr - r), round(2 * cc - c)),
                    )
                for rr, cc2 in partners:
                    if 0 <= rr < height and 0 <= cc2 < width and grid[rr][cc2] != bg:
                        result[r][c] = grid[rr][cc2]
                        break

        # The demonstrations also reveal a center-hole convention: an odd square
        # with all four immediate cardinal neighbors present receives its center.
        if square and box_h % 2 == 1 and result[center_r][center_c] == bg:
            color = grid[icon[0][0]][icon[0][1]]

            def has(rr, cc2):
                return (
                    sr1 <= rr <= sr2
                    and sc1 <= cc2 <= sc2
                    and result[rr][cc2] == color
                )

            cardinal = (
                center_r > sr1
                and center_r < sr2
                and center_c > sc1
                and center_c < sc2
                and has(center_r, center_c - 1)
                and has(center_r, center_c + 1)
                and has(center_r - 1, center_c)
                and has(center_r + 1, center_c)
            )
            diagonal = (
                box_h >= 7
                and has(center_r - 1, center_c - 1)
                and has(center_r - 1, center_c + 1)
                and has(center_r + 1, center_c - 1)
                and has(center_r + 1, center_c + 1)
                and has(sr1, center_c)
                and has(sr2, center_c)
                and has(center_r, sc1)
                and has(center_r, sc2)
            )
            if cardinal or diagonal:
                result[center_r][center_c] = color

    return result
