"""Fresh generators and Python mirror for public ARC parent 3dc255db.

Mixed-color 8-connected objects are spacecraft.  The majority color is the
hull; minority cells are exhaust particles stored inside the rear.  Remove the
stored particles and emit the same color from the geometric nose, either for
the measured particle count (canonical) or all the way to the boundary.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import random
from typing import Iterable

RULE_TASK_ID = 'ee_3dc255db'

Grid = list[list[int]]
Point = tuple[int, int]
DIRECTIONS: tuple[tuple[str, int, int], ...] = (
    ('up', -1, 0), ('right', 0, 1), ('down', 1, 0), ('left', 0, -1),
)


def _validate_grid(grid: Grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError('grid must be a non-empty list of rows')
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError('grid must be rectangular')
    if len(grid) > 30 or width > 30:
        raise ValueError('ARC grids are at most 30x30')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('grid cells must be integer colors 0..9')
    return len(grid), width


def _components8(grid: Grid) -> list[list[Point]]:
    h, w = _validate_grid(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out: list[list[Point]] = []
    while unseen:
        start = min(unseen); unseen.remove(start)
        stack = [start]; comp = [start]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    q = (r + dr, c + dc)
                    if q in unseen:
                        unseen.remove(q); stack.append(q); comp.append(q)
        out.append(sorted(comp))
    return out


def _direction_record(grid: Grid, cells: list[Point], hull_cells: list[Point],
                      particle_cells: list[Point]) -> dict:
    candidates: list[tuple[float, float, int, dict]] = []
    for order, (name, dr, dc) in enumerate(DIRECTIONS):
        projections = [r * dr + c * dc for r, c in hull_cells]
        extreme = max(projections)
        tips = [p for p, projection in zip(hull_cells, projections) if projection == extreme]
        if len(tips) != 1:
            continue
        tip = tips[0]
        slices: dict[int, list[int]] = defaultdict(list)
        if dr:
            for r, c in cells:
                slices[r].append(c)
            lateral_tip = tip[1]
        else:
            for r, c in cells:
                slices[c].append(r)
            lateral_tip = tip[0]
        widest = max(map(len, slices.values()))
        centers = [sum(values) / len(values) for values in slices.values() if len(values) == widest]
        center = sum(centers) / len(centers)
        alignment = abs(lateral_tip - center)
        depths = [extreme - (r * dr + c * dc) for r, c in particle_cells]
        mean_depth = sum(depths) / len(depths)
        record = {'direction': name, 'delta': [dr, dc], 'tip': list(tip),
                  'alignment': alignment, 'particle_depth': mean_depth}
        candidates.append((alignment, -mean_depth, order, record))
    if not candidates:
        raise ValueError('mixed component has no unique geometric nose')
    return min(candidates, key=lambda row: row[:3])[3]


def derive(grid: Grid) -> dict:
    ships: list[dict] = []
    for cells in _components8(grid):
        counts = Counter(grid[r][c] for r, c in cells)
        if len(counts) != 2:
            continue
        ordered = sorted(counts, key=lambda color: (-counts[color], color))
        hull_color, particle_color = ordered
        if counts[hull_color] <= counts[particle_color]:
            continue
        hull_cells = [p for p in cells if grid[p[0]][p[1]] == hull_color]
        particle_cells = [p for p in cells if grid[p[0]][p[1]] == particle_color]
        direction = _direction_record(grid, cells, hull_cells, particle_cells)
        ships.append({
            'cells': [list(p) for p in cells],
            'hull_cells': [list(p) for p in hull_cells],
            'particle_cells': [list(p) for p in particle_cells],
            'hull_color': hull_color,
            'particle_color': particle_color,
            'particle_count': len(particle_cells),
            **direction,
        })
    return {'ships': ships}


def solve(grid: Grid, extension: str = 'particle_count') -> Grid:
    if extension not in ('particle_count', 'to_edge'):
        raise ValueError('unknown extension policy')
    h, w = _validate_grid(grid)
    info = derive(grid)
    out = [row[:] for row in grid]
    for ship in info['ships']:
        for r, c in ship['particle_cells']:
            out[r][c] = 0
    for ship in info['ships']:
        dr, dc = ship['delta']; r, c = ship['tip']
        limit = ship['particle_count'] if extension == 'particle_count' else h + w
        for step in range(1, limit + 1):
            rr, cc = r + step * dr, c + step * dc
            if not (0 <= rr < h and 0 <= cc < w):
                break
            out[rr][cc] = ship['particle_color']
    return out


def _rng(seed: int, stream: str, index: int) -> random.Random:
    raw = hashlib.sha256(f'{seed}:{stream}:{index}:3dc255db'.encode()).digest()
    return random.Random(int.from_bytes(raw, 'big'))


def _shape(size: int) -> set[Point]:
    if size == 5:
        widths = (1, 3, 5, 5, 3)
    elif size == 7:
        widths = (1, 3, 5, 7, 7, 5, 3)
    else:
        raise ValueError('supported ship sizes are 5 and 7')
    center = size // 2
    cells: set[Point] = set()
    for r, width in enumerate(widths):
        start = center - width // 2
        cells.update((r, c) for c in range(start, start + width))
    return cells


def _rotate(p: Point, size: int, direction: str) -> Point:
    r, c = p
    if direction == 'up':
        return r, c
    if direction == 'right':
        return c, size - 1 - r
    if direction == 'down':
        return size - 1 - r, size - 1 - c
    if direction == 'left':
        return size - 1 - c, r
    raise ValueError(direction)


def _place_ship(grid: Grid, top: int, left: int, direction: str, size: int,
                hull_color: int, particle_color: int, particle_count: int) -> None:
    h, w = len(grid), len(grid[0])
    cells = _shape(size)
    center = size // 2
    # Deep, interior rear cells.  Recoloring rather than removing them preserves
    # the component outline and keeps the majority hull connected.
    if size == 5:
        pool = [(3, 2), (2, 2), (3, 1), (3, 3)]
    else:
        pool = [(5, 3), (4, 3), (5, 2), (5, 4), (3, 3), (4, 2)]
    if not 1 <= particle_count <= len(pool):
        raise ValueError('particle count outside ship template')
    particles = set(pool[:particle_count])
    transformed = {_rotate(p, size, direction): (particle_color if p in particles else hull_color) for p in cells}
    for (r, c), color in transformed.items():
        rr, cc = top + r, left + c
        if not (0 <= rr < h and 0 <= cc < w) or grid[rr][cc] != 0:
            raise ValueError('ship placement overlaps or leaves grid')
        grid[rr][cc] = color


def _place_singletons(grid: Grid, rng: random.Random, forbidden_colors: set[int], count: int) -> None:
    h, w = len(grid), len(grid[0])
    colors = [c for c in range(1, 10) if c not in forbidden_colors]
    candidates = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0 and
                  all(not (0 <= r+dr < h and 0 <= c+dc < w) or grid[r+dr][c+dc] == 0
                      for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc)!=(0,0))]
    rng.shuffle(candidates)
    for i, (r, c) in enumerate(candidates[:count]):
        grid[r][c] = colors[i % len(colors)]


def _scene(seed: int, index: int, *, query: bool = False) -> Grid:
    rng = _rng(seed, 'scene', 1000 + index if query else index)
    if query:
        sizes = (18, 22, 26, 30)
        n = sizes[index]
        ship_count = (1, 2, 3, 4)[index]
        size = 7
        absolute = 1000 + index
    else:
        sizes = (12, 13, 14, 15, 16, 17)
        n = sizes[index]
        ship_count = 1
        size = 5
        absolute = index
    grid = [[0] * n for _ in range(n)]
    palette = list(range(1, 10)); rng.shuffle(palette)
    directions = ('up', 'right', 'down', 'left')
    # Fixed well-separated placements with outward rays and more free distance
    # than the stored particle count.
    if size == 5:
        direction = directions[absolute % 4]
        top = (n - size) // 2
        left = (n - size) // 2
        # Leave four empty cells beyond the geometric nose so that a stored
        # count of at most three is distinguishable from extension to edge.
        if direction == 'up':
            top = 4
        elif direction == 'down':
            top = n - size - 4
        elif direction == 'left':
            left = 4
        else:
            left = n - size - 4
        placements = [(top, left, direction)]
    else:
        placements = [
            (4, 1, 'up'),
            (1, n - 11, 'right'),
            (n - 11, n - 8, 'down'),
            (n - 8, 4, 'left'),
        ]
    used_colors: set[int] = set()
    for i in range(ship_count):
        top, left, direction = placements[i]
        hull = palette[(2*i) % len(palette)]
        particle = palette[(2*i+1) % len(palette)]
        used_colors.update((hull, particle))
        count = 1 + ((absolute + i) % (3 if size == 5 else 4))
        _place_ship(grid, top, left, direction, size, hull, particle, count)
    _place_singletons(grid, rng, used_colors, 1 + (absolute % 2))
    findings = self_check(grid)
    if findings:
        raise AssertionError(findings)
    return grid


def candidate_solve(grid: Grid, name: str, intended: str) -> Grid:
    if name == 'intended':
        return solve(grid, intended)
    if name == 'other_setting':
        return solve(grid, 'to_edge' if intended == 'particle_count' else 'particle_count')
    if name == 'identity':
        return [row[:] for row in grid]
    info = derive(grid); h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for ship in info['ships']:
        for r, c in ship['particle_cells']:
            out[r][c] = 0
    for ship in info['ships']:
        dr, dc = ship['delta']; r, c = ship['tip']
        if name == 'opposite_direction':
            dr, dc = -dr, -dc
            limit = ship['particle_count']
        elif name == 'fixed_one':
            limit = 1
        elif name == 'clear_only':
            limit = 0
        else:
            raise ValueError(name)
        for step in range(1, limit + 1):
            rr, cc = r + step*dr, c + step*dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = ship['particle_color']
    return out


def survivors(demos: list[dict], intended: str) -> list[str]:
    names = ('intended', 'other_setting', 'identity', 'opposite_direction', 'fixed_one', 'clear_only')
    return [name for name in names if all(candidate_solve(p['input'], name, intended) == p['output'] for p in demos)]


def self_check(grid: Grid, **_: object) -> list[str]:
    findings: list[str] = []
    try:
        info = derive(grid)
        if not info['ships']:
            findings.append('at least one mixed-color ship required')
        if solve(grid, 'particle_count') == solve(grid, 'to_edge'):
            findings.append('extension settings must differ')
        if any(ship['particle_count'] >= 7 for ship in info['ships']):
            findings.append('unexpected particle count')
    except Exception as exc:  # pragma: no cover - generator boundary
        findings.append(str(exc))
    return findings


def generate(seed: int, sample_index: int, difficulty: str = 'medium') -> dict[str, Grid]:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('seed outside exact bounds')
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError('sample_index must be nonnegative')
    return {'input': _scene(seed, sample_index % 4, query=True)}
