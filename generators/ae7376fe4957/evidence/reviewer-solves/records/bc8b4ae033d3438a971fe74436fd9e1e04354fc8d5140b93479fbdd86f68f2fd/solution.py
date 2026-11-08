"""Visible-example-only solver for the blind review episode.

The sparse input contains a blue marker (1).  The marker and at least two
other cells determine a unique straight guide line.  The examples expose
three constructions around that line:

* a short staircase, identified by repeated off-line displacement;
* a parity lattice, where one coordinate parity is invariant along the line;
* a symmetric two-sided guide, where the marked spatial cluster is selected.

After selecting the marked construction, erase the marker and tightly crop.
"""

from __future__ import annotations

from math import gcd, hypot
from typing import Iterable

Grid = list[list[int]]
Point = tuple[int, int]


def _primitive(dr: int, dc: int) -> Point:
    g = gcd(abs(dr), abs(dc))
    if g == 0:
        raise ValueError("zero direction")
    dr //= g
    dc //= g
    if dr < 0 or (dr == 0 and dc < 0):
        dr, dc = -dr, -dc
    return dr, dc


def _guide(grid: Grid, marker: Point) -> tuple[Point, list[tuple[int, Point, int]]]:
    """Return the unique direction through marker with the most occupied cells.

    Each returned tuple is (signed integer parameter, point, color).
    """
    mr, mc = marker
    by_direction: dict[Point, list[tuple[int, Point, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) == marker:
                continue
            dr, dc = r - mr, c - mc
            direction = _primitive(dr, dc)
            vr, vc = direction
            denom = vr * vr + vc * vc
            t_num = dr * vr + dc * vc
            if t_num % denom:
                continue
            t = t_num // denom
            by_direction.setdefault(direction, []).append((t, (r, c), color))
    candidates = [(len(items), direction, items) for direction, items in by_direction.items() if len(items) >= 2]
    if not candidates:
        raise ValueError("no guide line through marker")
    _, direction, items = max(candidates, key=lambda x: (x[0], -abs(x[1][0]) - abs(x[1][1])))
    return direction, sorted(items)


def _crop(grid: Grid, selected: set[Point]) -> Grid:
    if not selected:
        return [[0]]
    r0 = min(r for r, _ in selected)
    r1 = max(r for r, _ in selected)
    c0 = min(c for _, c in selected)
    c1 = max(c for _, c in selected)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in selected:
        out[r - r0][c - c0] = grid[r][c]
    return out


def _staircase_selection(
    grid: Grid,
    marker: Point,
    line_items: list[tuple[int, Point, int]],
) -> set[Point]:
    """Choose colors whose off-line mates share the dominant displacement."""
    positions_by_color: dict[int, list[Point]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color not in (0, 1):
                positions_by_color.setdefault(color, []).append((r, c))

    displacement_to_colors: dict[Point, set[int]] = {}
    on_line_by_color: dict[int, list[Point]] = {}
    for _, point, color in line_items:
        on_line_by_color.setdefault(color, []).append(point)

    for color, on_points in on_line_by_color.items():
        others = [p for p in positions_by_color.get(color, []) if p not in on_points]
        for op in on_points:
            for other in others:
                d = (other[0] - op[0], other[1] - op[1])
                displacement_to_colors.setdefault(d, set()).add(color)

    if not displacement_to_colors:
        # Fallback: retain the nearest two guide colors after the marker.
        chosen = {color for t, _, color in line_items if t > 0 for _ in [0]}
        chosen = set(color for _, _, color in sorted(line_items, key=lambda x: abs(x[0]))[:2]) if not chosen else chosen
    else:
        _, chosen = max(
            displacement_to_colors.items(),
            key=lambda kv: (len(kv[1]), -abs(kv[0][0]) - abs(kv[0][1])),
        )

    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, color in enumerate(row)
        if color in chosen
    }


def _marked_mst_component(grid: Grid, marker: Point) -> set[Point]:
    """Split the sparse point cloud at its largest MST bridge."""
    points = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color != 0]
    if len(points) <= 1:
        return set()

    # Prim's algorithm, retaining the tree edges.
    in_tree = {marker}
    edges: list[tuple[float, Point, Point]] = []
    while len(in_tree) < len(points):
        best: tuple[float, Point, Point] | None = None
        for a in in_tree:
            for b in points:
                if b in in_tree:
                    continue
                candidate = (hypot(a[0] - b[0], a[1] - b[1]), a, b)
                if best is None or candidate < best:
                    best = candidate
        assert best is not None
        edges.append(best)
        in_tree.add(best[2])

    # Remove one longest bridge, then retain the marker's component.
    cut_index = max(range(len(edges)), key=lambda i: edges[i][0])
    adjacency: dict[Point, set[Point]] = {p: set() for p in points}
    for i, (_, a, b) in enumerate(edges):
        if i == cut_index:
            continue
        adjacency[a].add(b)
        adjacency[b].add(a)

    component = {marker}
    stack = [marker]
    while stack:
        p = stack.pop()
        for q in adjacency[p]:
            if q not in component:
                component.add(q)
                stack.append(q)
    component.discard(marker)
    return component


def solve(grid: Grid) -> Grid:
    marker_points = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 1]
    if len(marker_points) != 1:
        raise ValueError("expected exactly one marker of color 1")
    marker = marker_points[0]
    (vr, vc), line_items = _guide(grid, marker)

    if len(line_items) >= 3:
        selected = _staircase_selection(grid, marker, line_items)
    else:
        ts = sorted(t for t, _, _ in line_items)
        if len(ts) == 2 and ts[0] == -ts[1]:
            selected = _marked_mst_component(grid, marker)
        elif vr % 2 == 0 and vc % 2 == 1:
            # Row parity is invariant under steps along the guide.
            selected = {
                (r, c)
                for r, row in enumerate(grid)
                for c, color in enumerate(row)
                if color not in (0, 1) and r % 2 == marker[0] % 2
            }
        elif vc % 2 == 0 and vr % 2 == 1:
            # Column parity is invariant under steps along the guide.
            selected = {
                (r, c)
                for r, row in enumerate(grid)
                for c, color in enumerate(row)
                if color not in (0, 1) and c % 2 == marker[1] % 2
            }
        else:
            selected = _marked_mst_component(grid, marker)

    return _crop(grid, selected)
