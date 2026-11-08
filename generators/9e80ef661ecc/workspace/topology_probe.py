"""Independent topology diagnostics; no label authority or training admission."""
from collections import deque

from reference_probe import components, output_color


def shape_signature(cells):
    """Translation/color/D4-invariant shape, including all zero positions."""
    variants = []
    points = set(cells)
    for reflected in (False, True):
        current = {(r, -c if reflected else c) for r, c in points}
        for _ in range(4):
            r0 = min(r for r, _ in current)
            c0 = min(c for _, c in current)
            variants.append(tuple(sorted((r-r0, c-c0) for r, c in current)))
            current = {(c, -r) for r, c in current}
    return min(variants)


def scene_signature(grid):
    """Object multiset quotient; intentionally omits placement and palette.

    This measures morphological support, not all relations between objects.
    Duplicate objects retain their multiplicity.
    """
    return tuple(sorted(shape_signature(o['cells']) for o in components(grid)))


def _recolor(grid, objects, counter):
    out = [list(row) for row in grid]
    for obj in objects:
        color = output_color(counter(obj))
        for r, c in obj['cells']:
            out[r][c] = color
    return out


def _gap_runs(obj, transpose=False):
    points = {(c, r) if transpose else (r, c) for r, c in obj['cells']}
    r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
    c0, c1 = min(c for _, c in points), max(c for _, c in points)
    maximum = 0
    for r in range(r0+1, r1):
        count, start = 0, None
        for c in range(c0, c1+2):
            if c <= c1 and (r, c) not in points:
                if start is None:
                    start = c
            elif start is not None:
                count += start > c0 and c-1 < c1
                start = None
        maximum = max(maximum, count)
    return maximum


def row_gap_rival(grid):
    return _recolor(grid, components(grid), _gap_runs)


def row_column_gap_rival(grid):
    return _recolor(grid, components(grid),
                    lambda o: max(_gap_runs(o), _gap_runs(o, True)))


def _neighbors(point, diagonal):
    r, c = point
    return [(r+dr, c+dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
            if (dr or dc) and (diagonal or abs(dr)+abs(dc) == 1)]


def complement_regions(obj, diagonal=False):
    r0, c0, r1, c1 = obj['bbox']
    pending = {(r, c) for r in range(r0, r1+1) for c in range(c0, c1+1)} - obj['cells']
    holes = 0
    while pending:
        first = min(pending)
        pending.remove(first)
        todo = deque([first])
        touches = False
        while todo:
            r, c = todo.popleft()
            touches |= r in (r0, r1) or c in (c0, c1)
            for p in _neighbors((r, c), diagonal):
                if p in pending:
                    pending.remove(p)
                    todo.append(p)
        holes += not touches
    return holes


def eight_holes_rival(grid):
    return _recolor(grid, components(grid), lambda o: complement_regions(o, True))


def eight_objects(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c]}
    objects = []
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        remaining.remove(first)
        todo, cells = [first], {first}
        while todo:
            for p in _neighbors(todo.pop(), True):
                if p in remaining and grid[p[0]][p[1]] == color:
                    remaining.remove(p)
                    cells.add(p)
                    todo.append(p)
        objects.append({'cells': cells, 'color': color,
                        'bbox': (min(r for r, _ in cells), min(c for _, c in cells),
                                 max(r for r, _ in cells), max(c for _, c in cells))})
    return objects


def eight_objects_rival(grid):
    return _recolor(grid, eight_objects(grid), complement_regions)


def four_only_rival(grid):
    return _recolor(grid, components(grid),
                    lambda o: complement_regions(o) if complement_regions(o) <= 4 else 3)


LEGACY_MASKS = [
    (('11', '11'), 2), (('111', '111', '111'), 2),
    (('111', '101', '111'), 3), (('1111', '1001', '1001', '1111'), 3),
    (('11111', '10101', '11111'), 4),
    (('10011', '11111', '11111'), 2), (('11111', '10011', '11111'), 3),
    (('1111111', '1010101', '1111111'), 6),
    (('111111111', '101010101', '111111111'), 9),
]


def template_rival(grid):
    table = {shape_signature({(r, c) for r, row in enumerate(rows)
                              for c, v in enumerate(row) if v == '1'}): color
             for rows, color in LEGACY_MASKS}
    out = [list(row) for row in grid]
    for obj in components(grid):
        color = table.get(shape_signature(obj['cells']), 9)
        for r, c in obj['cells']:
            out[r][c] = color
    return out


ADDITIONAL_RIVALS = {'max_horizontal_interior_gap_runs': row_gap_rival,
                     'max_row_or_column_gap_runs': row_column_gap_rival,
                     'eight_connected_holes': eight_holes_rival,
                     'eight_connected_objects': eight_objects_rival,
                     'four_only_not_four_plus': four_only_rival,
                     'shape_template_lookup': template_rival}
