"""General solver for ARC public-evaluation parent 6e4f6532.

The grid is partitioned by two-cell coloured guide strips.  Each movable object
contains an azure body, one or more maroon key cells, and coloured guide tabs.
A detached maroon key is the destination.  Match object to destination by key
shape, infer the rigid D4 transform that turns every tab toward the matching
coloured guide strip around the destination, erase the source, and stamp the
whole transformed object over the destination key.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

Grid = list[list[int]]
Point = tuple[int, int]
Pixels = dict[Point, int]

# D4 transforms about the origin.  Rotations are intentionally first so that
# a geometrically equivalent pure rotation wins the deterministic tie break.
_TRANSFORMS = (
    lambda r, c: (r, c),
    lambda r, c: (c, -r),
    lambda r, c: (-r, -c),
    lambda r, c: (-c, r),
    lambda r, c: (r, -c),
    lambda r, c: (-r, c),
    lambda r, c: (c, r),
    lambda r, c: (-c, -r),
)


@dataclass(frozen=True)
class Line:
    color: int
    axis: str  # "h" or "v"
    lo: int
    hi: int
    center: float
    cells: frozenset[Point]


def _mode(grid: Grid) -> int:
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def _uniform_line_cells(grid: Grid, background: int) -> set[Point]:
    """Find guide strips, allowing perpendicular strips to be removed first.

    A guide is a row/column whose remaining cells are one non-background
    colour.  Iteration handles crossings between horizontal and vertical
    strips without assuming which orientation is discovered first.
    """

    height, width = len(grid), len(grid[0])
    found: set[Point] = set()
    changed = True
    while changed:
        changed = False
        for r in range(height):
            active = [(r, c) for c in range(width) if (r, c) not in found]
            values = {grid[rr][cc] for rr, cc in active}
            if active and len(values) == 1 and next(iter(values)) != background:
                before = len(found)
                found.update(active)
                changed |= len(found) != before
        for c in range(width):
            active = [(r, c) for r in range(height) if (r, c) not in found]
            values = {grid[rr][cc] for rr, cc in active}
            if active and len(values) == 1 and next(iter(values)) != background:
                before = len(found)
                found.update(active)
                changed |= len(found) != before
    return found


def _components(points: Iterable[Point], *, diagonal: bool = True) -> list[set[Point]]:
    remaining = set(points)
    result: list[set[Point]] = []
    directions = (
        ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        if diagonal
        else ((-1, 0), (0, -1), (0, 1), (1, 0))
    )
    while remaining:
        seed = min(remaining)
        stack = [seed]
        component: set[Point] = set()
        while stack:
            p = stack.pop()
            if p not in remaining:
                continue
            remaining.remove(p)
            component.add(p)
            r, c = p
            for dr, dc in directions:
                q = (r + dr, c + dc)
                if q in remaining:
                    stack.append(q)
        result.append(component)
    return result


def _normalise(points: Iterable[Point]) -> frozenset[Point]:
    pts = tuple(points)
    min_r = min(r for r, _ in pts)
    min_c = min(c for _, c in pts)
    return frozenset((r - min_r, c - min_c) for r, c in pts)


def _centroid(points: Iterable[Point]) -> tuple[float, float]:
    pts = tuple(points)
    return (
        sum(r for r, _ in pts) / len(pts),
        sum(c for _, c in pts) / len(pts),
    )


def _extract_lines(grid: Grid, line_cells: set[Point]) -> list[Line]:
    """Recover maximal same-colour horizontal/vertical guide strips."""

    by_color: dict[int, set[Point]] = defaultdict(set)
    for p in line_cells:
        by_color[grid[p[0]][p[1]]].add(p)

    lines: list[Line] = []
    for color, cells in by_color.items():
        # Connected components are thick strips or their intersections.  Infer
        # each occupied row/column span and merge adjacent equal spans.
        rows: dict[int, set[int]] = defaultdict(set)
        cols: dict[int, set[int]] = defaultdict(set)
        for r, c in cells:
            rows[r].add(c)
            cols[c].add(r)

        used_rows: set[int] = set()
        for r in sorted(rows):
            if r in used_rows:
                continue
            span = rows[r]
            group = [r]
            nxt = r + 1
            while nxt in rows and rows[nxt] == span:
                group.append(nxt)
                used_rows.add(nxt)
                nxt += 1
            if len(span) >= len(group):
                pts = frozenset((rr, cc) for rr in group for cc in span)
                lines.append(Line(color, "h", min(group), max(group), sum(group) / len(group), pts))
            used_rows.add(r)

        used_cols: set[int] = set()
        for c in sorted(cols):
            if c in used_cols:
                continue
            span = cols[c]
            group = [c]
            nxt = c + 1
            while nxt in cols and cols[nxt] == span:
                group.append(nxt)
                used_cols.add(nxt)
                nxt += 1
            if len(span) >= len(group):
                pts = frozenset((rr, cc) for cc in group for rr in span)
                lines.append(Line(color, "v", min(group), max(group), sum(group) / len(group), pts))
            used_cols.add(c)
    return lines


def _side_toward_nearest_line(
    lines: list[Line], color: int, target: set[Point], orientation_mode: str
) -> str | None:
    cr, cc = _centroid(target)
    candidates: list[tuple[float, str]] = []
    for line in lines:
        if line.color != color:
            continue
        if line.axis == "h":
            candidates.append((abs(line.center - cr), "T" if line.center < cr else "B"))
        else:
            candidates.append((abs(line.center - cc), "L" if line.center < cc else "R"))
    if not candidates:
        return None
    side = min(candidates)[1]
    if orientation_mode == "toward":
        return side
    return {"T": "B", "B": "T", "L": "R", "R": "L"}[side]


def _tab_side(body: set[Point], tab_points: Iterable[Point]) -> str | None:
    dr_sum = dc_sum = 0
    for r, c in tab_points:
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (nr, nc) in body:
                dr_sum += r - nr
                dc_sum += c - nc
    if dr_sum == dc_sum == 0:
        return None
    if abs(dr_sum) >= abs(dc_sum):
        return "T" if dr_sum < 0 else "B"
    return "L" if dc_sum < 0 else "R"


def _transform_side(side: str, tid: int) -> str:
    vector = {"T": (-1, 0), "B": (1, 0), "L": (0, -1), "R": (0, 1)}[side]
    dr, dc = _TRANSFORMS[tid](*vector)
    if abs(dr) >= abs(dc):
        return "T" if dr < 0 else "B"
    return "L" if dc < 0 else "R"


def _transform_pixels(obj: Mapping[Point, int], tid: int, origin: Point) -> Pixels:
    result: Pixels = {}
    for (r, c), value in obj.items():
        dr, dc = r - origin[0], c - origin[1]
        rr, cc = _TRANSFORMS[tid](dr, dc)
        result[(rr, cc)] = value
    return result


def _place_on_target(relative: Pixels, target: set[Point]) -> Pixels | None:
    rel_keys = [p for p, value in relative.items() if value == 9]
    for rp in rel_keys:
        for tp in sorted(target):
            shift = (tp[0] - rp[0], tp[1] - rp[1])
            placed = {(r + shift[0], c + shift[1]): value for (r, c), value in relative.items()}
            if {p for p, value in placed.items() if value == 9} == target:
                return placed
    return None


def _match_target(obj: Pixels, targets: list[set[Point]], used: set[int]) -> tuple[int, set[Point]]:
    anchors = [p for p, value in obj.items() if value == 9]
    anchor_forms = {_normalise(_TRANSFORMS[tid](r - anchors[0][0], c - anchors[0][1]) for r, c in anchors) for tid in range(8)}
    candidates = [
        (index, target)
        for index, target in enumerate(targets)
        if index not in used and len(target) == len(anchors) and _normalise(target) in anchor_forms
    ]
    if not candidates:
        raise ValueError("no detached maroon key matches object anchor")
    # Official grammar uses unique anchor cardinality/shape.  Stable order makes
    # generated symmetric cases deterministic without encoding query order.
    return min(candidates, key=lambda item: (len(item[1]), min(item[1])))


def _orient_and_place(
    obj: Pixels, target: set[Point], lines: list[Line], orientation_mode: str
) -> Pixels:
    anchors = [p for p, value in obj.items() if value == 9]
    origin = anchors[0]
    body = {p for p, value in obj.items() if value in (8, 9)}
    tab_groups: dict[int, list[Point]] = defaultdict(list)
    for p, value in obj.items():
        if value not in (8, 9):
            tab_groups[value].append(p)
    source_sides = {color: _tab_side(body, points) for color, points in tab_groups.items()}
    target_sides = {
        color: _side_toward_nearest_line(lines, color, target, orientation_mode)
        for color in tab_groups
    }

    candidates: list[tuple[int, Pixels]] = []
    for tid in range(8):
        if any(
            source_sides[color] is not None
            and target_sides[color] is not None
            and _transform_side(source_sides[color], tid) != target_sides[color]
            for color in tab_groups
        ):
            continue
        relative = _transform_pixels(obj, tid, origin)
        placed = _place_on_target(relative, target)
        if placed is not None:
            candidates.append((tid, placed))
    if not candidates:
        raise ValueError("no rigid transform satisfies key and guide colors")
    return min(candidates, key=lambda item: item[0])[1]


def solve_grid(grid: Grid, orientation_mode: str = "toward") -> Grid:
    """Apply the 6e4f6532 relocation rule to one rectangular integer grid."""

    if orientation_mode not in {"toward", "away"}:
        raise ValueError("orientation_mode must be toward or away")
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    background = _mode(grid)
    line_cells = _uniform_line_cells(grid, background)
    lines = _extract_lines(grid, line_cells)

    interior: Pixels = {
        (r, c): value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background and (r, c) not in line_cells
    }
    objects: list[Pixels] = []
    targets: list[set[Point]] = []
    for component in _components(interior, diagonal=True):
        pixels = {p: interior[p] for p in component}
        values = set(pixels.values())
        if 8 in values:
            objects.append(pixels)
        elif values == {9}:
            targets.append(component)

    output = [row[:] for row in grid]
    for pixels in objects:
        for r, c in pixels:
            output[r][c] = background
    for target in targets:
        for r, c in target:
            output[r][c] = background

    used: set[int] = set()
    for obj in sorted(objects, key=lambda pixels: min(pixels)):
        target_index, target = _match_target(obj, targets, used)
        used.add(target_index)
        for (r, c), value in _orient_and_place(obj, target, lines, orientation_mode).items():
            if 0 <= r < len(output) and 0 <= c < len(output[0]):
                output[r][c] = value
    return output


__all__ = ["solve_grid"]
