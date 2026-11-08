"""Visible-example solution for task 54628ce9692d.

The input contains several separated colour-1 objects.  Non-1 colours on an
object's boundary are connectors.  Equal connector colours are paired; the
objects are translated (not rotated) until paired connectors are cardinally
adjacent and face one another.  The assembled non-background cells are then
cropped to their bounding rectangle.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Iterable

Grid = list[list[int]]
Point = tuple[int, int]

_DIRS: tuple[Point, ...] = ((-1, 0), (0, 1), (1, 0), (0, -1))


def _add(a: Point, b: Point) -> Point:
    return a[0] + b[0], a[1] + b[1]


def _sub(a: Point, b: Point) -> Point:
    return a[0] - b[0], a[1] - b[1]


def _components(grid: Grid, background: int) -> list[set[Point]]:
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    }
    result: list[set[Point]] = []
    while cells:
        start = next(iter(cells))
        cells.remove(start)
        component = {start}
        queue = [start]
        while queue:
            p = queue.pop()
            for d in _DIRS:
                q = _add(p, d)
                if q in cells:
                    cells.remove(q)
                    component.add(q)
                    queue.append(q)
        result.append(component)
    return result


def _outward_score(component: set[Point], marker: Point, direction: Point) -> float:
    """Score how naturally ``direction`` points out of this rigid object."""

    outside = _add(marker, direction)
    if outside in component:
        return float("-inf")

    rows = [p[0] for p in component]
    cols = [p[1] for p in component]
    r, c = marker
    dr, dc = direction
    score = 0.0

    # Boundary extrema are the clearest visible cue in all demonstrations.
    if dr == -1 and r == min(rows):
        score += 100.0
    elif dr == 1 and r == max(rows):
        score += 100.0
    elif dc == -1 and c == min(cols):
        score += 100.0
    elif dc == 1 and c == max(cols):
        score += 100.0

    # Prefer a direction with object mass behind the connector.
    if _sub(marker, direction) in component:
        score += 15.0
    centre_r = sum(rows) / len(rows)
    centre_c = sum(cols) / len(cols)
    score += (r - centre_r) * dr + (c - centre_c) * dc

    # Nearby cells behind and beside the marker provide a stable tie-breaker.
    left = (-dc, dr)
    right = (dc, -dr)
    behind = _sub(marker, direction)
    for q, weight in (
        (behind, 4.0),
        (_add(behind, left), 1.0),
        (_add(behind, right), 1.0),
        (_sub(behind, direction), 0.5),
    ):
        if q in component:
            score += weight
    return score


def _pair_direction(
    comp_a: set[Point], marker_a: Point, comp_b: set[Point], marker_b: Point
) -> Point:
    """Choose opposite outward normals for a matching connector pair."""

    ranked: list[tuple[float, int, Point]] = []
    for order, d in enumerate(_DIRS):
        opposite = (-d[0], -d[1])
        score = _outward_score(comp_a, marker_a, d) + _outward_score(
            comp_b, marker_b, opposite
        )
        ranked.append((score, -order, d))
    return max(ranked)[2]


def solve(grid: Grid) -> Grid:
    if not grid or not grid[0]:
        return []

    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    components = _components(grid, background)
    if not components:
        return []

    owner: dict[Point, int] = {}
    markers: dict[int, list[tuple[int, Point]]] = defaultdict(list)
    for index, component in enumerate(components):
        for p in component:
            owner[p] = index
            value = grid[p[0]][p[1]]
            if value != 1:
                markers[value].append((index, p))

    # Each repeated marker colour contributes one rigid translation constraint.
    edges: dict[int, list[tuple[int, Point]]] = defaultdict(list)
    for occurrences in markers.values():
        if len(occurrences) != 2:
            continue  # an unpaired marker is decorative / the free endpoint
        (a, marker_a), (b, marker_b) = occurrences
        if a == b:
            continue
        d = _pair_direction(components[a], marker_a, components[b], marker_b)
        # If A is already placed, B's connector sits one step outward from A's.
        delta_b_from_a = _sub(_add(marker_a, d), marker_b)
        edges[a].append((b, delta_b_from_a))
        edges[b].append((a, (-delta_b_from_a[0], -delta_b_from_a[1])))

    translations: dict[int, Point] = {}
    for root in range(len(components)):
        if root in translations:
            continue
        # Valid tasks form one connector tree.  Retaining original relative
        # placement for an unexpected disconnected component is a safe fallback.
        translations[root] = (0, 0) if not translations else min(components[root])
        queue: deque[int] = deque([root])
        while queue:
            a = queue.popleft()
            for b, delta in edges.get(a, []):
                candidate = _add(translations[a], delta)
                if b not in translations:
                    translations[b] = candidate
                    queue.append(b)

    placed: dict[Point, int] = {}
    for index, component in enumerate(components):
        shift = translations[index]
        for r, c in component:
            q = (r + shift[0], c + shift[1])
            value = grid[r][c]
            # Intended examples never overlap.  In a malformed case, preserve a
            # non-background value rather than silently erasing it.
            if q in placed and placed[q] != value:
                raise ValueError("assembled objects overlap inconsistently")
            placed[q] = value

    min_r = min(r for r, _ in placed)
    max_r = max(r for r, _ in placed)
    min_c = min(c for _, c in placed)
    max_c = max(c for _, c in placed)
    output = [
        [background for _ in range(max_c - min_c + 1)]
        for _ in range(max_r - min_r + 1)
    ]
    for (r, c), value in placed.items():
        output[r - min_r][c - min_c] = value
    return output
