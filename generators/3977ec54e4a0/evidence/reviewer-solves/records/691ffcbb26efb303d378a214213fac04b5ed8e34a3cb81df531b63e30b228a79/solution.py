"""Visible-example chevron fill solver; prior authoring exposure declared."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color == 3}
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        group, pending = {first}, [first]
        while pending:
            r, c = pending.pop()
            adjacent = set()
            for rr, cc in remaining:
                dr, dc = abs(rr - r), abs(cc - c)
                if max(dr, dc) <= 2 and (dr == dc or dr == 0 or dc == 0):
                    adjacent.add((rr, cc))
            remaining.difference_update(adjacent)
            group.update(adjacent)
            pending.extend(adjacent)
        groups.append(group)

    for group in groups:
        for ar, ac in sorted(group):
            for vr, vc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                coordinates = [((r-ar)*vr + (c-ac)*vc,
                                -(r-ar)*vc + (c-ac)*vr) for r, c in group]
                if not all(t >= 0 and abs(u) == t for t, u in coordinates):
                    continue
                if not any(u < 0 for t, u in coordinates):
                    continue
                if not any(u > 0 for t, u in coordinates):
                    continue
                depth = max(t for t, u in coordinates)
                for r in range(height):
                    for c in range(width):
                        t = (r-ar)*vr + (c-ac)*vc
                        u = -(r-ar)*vc + (c-ac)*vr
                        if 0 <= t <= depth and abs(u) <= t and grid[r][c] != 3:
                            result[r][c] = 8
    return result
