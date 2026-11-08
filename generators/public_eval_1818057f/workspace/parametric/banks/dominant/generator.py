"""Public 1818057f: find orthogonal color-4 plus motifs in clutter.

The standalone sampler and Python claim oracle live here so ordinary relocated
runtime preparation never depends on the task workspace. Protected Racket is the
label authority during authoring preflight and later native qualification.
"""
from __future__ import annotations

from collections import deque
import copy
from typing import Any

from puzzle_generators.base import gen_ctx

TASK_ID = GENERATOR_ID = 'public_eval_1818057f'
RULE_TASK_ID = 'ee_1818057f'
VERSION = '1.0.0'
SUMMARY = 'Recolor every orthogonal five-cell color-4 plus embedded in a color-2 scene.'
EXAMPLES_NEEDED = 2
AXES = {}
MARK_SCOPES = ('all', 'dominant_component')

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def check_grid(grid: Any) -> None:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError('grid dimensions must be 1..30')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError('grid must be rectangular with exact integer colors 0..9')


def plus_cells(center: tuple[int, int]) -> set[tuple[int, int]]:
    r, c = center
    return {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}


def cross_centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    check_grid(grid)
    height, width = len(grid), len(grid[0])
    result = []
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if all(grid[rr][cc] == 4 for rr, cc in plus_cells((r, c))):
                result.append((r, c))
    return result


def components4(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    check_grid(grid)
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 4}
    result = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        queue = deque([first])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _CARDINAL:
                p = r + dr, c + dc
                if p in remaining:
                    remaining.remove(p)
                    queue.append(p)
        result.append(sorted(cells))
    return result


def analyse(grid: list[list[int]]) -> dict:
    check_grid(grid)
    centers = cross_centers(grid)
    center_set = set(centers)
    components = []
    center_owner = {}
    for index, cells in enumerate(components4(grid)):
        own = [p for p in cells if p in center_set]
        for p in own:
            center_owner[p] = index
        components.append({'index': index, 'cells': cells, 'size': len(cells),
                           'plus_centers': own, 'plus_count': len(own)})
    candidates = [row for row in components if row['plus_count']]
    dominant = max(candidates, key=lambda row: row['plus_count'])['index'] if candidates else None
    return {'centers': centers, 'components': components, 'center_owner': center_owner,
            'dominant_component': dominant}


def _selected_centers(facts: dict, mark_scope: str, foil: str | None = None) -> list[tuple[int, int]]:
    centers = facts['centers']
    rows = [row for row in facts['components'] if row['plus_count']]
    if foil == 'exact_only':
        raise ValueError('exact_only is evaluated by rival_solve')
    if mark_scope == 'all':
        selected = centers
    elif mark_scope == 'dominant_component':
        selected = [p for p in centers if facts['center_owner'][p] == facts['dominant_component']]
    else:
        raise ValueError('mark_scope must be all or dominant_component')
    if foil == 'first_center':
        selected = centers[:1]
    elif foil == 'last_center':
        selected = centers[-1:]
    elif foil == 'one_per_component':
        selected = [row['plus_centers'][0] for row in rows]
    elif foil == 'first_component':
        selected = rows[0]['plus_centers'] if rows else []
    elif foil == 'last_component':
        selected = rows[-1]['plus_centers'] if rows else []
    elif foil == 'largest_area':
        selected = max(rows, key=lambda row: row['size'])['plus_centers'] if rows else []
    elif foil == 'smallest_area':
        selected = min(rows, key=lambda row: row['size'])['plus_centers'] if rows else []
    elif foil == 'topmost_centers':
        if centers:
            top = min(r for r, _ in centers)
            selected = [p for p in centers if p[0] == top]
        else:
            selected = []
    elif foil not in (None, 'paint_components', 'all_fours'):
        raise ValueError('unknown foil')
    return selected


def solve(grid: list[list[int]], mark_scope: str = 'all', foil: str | None = None) -> list[list[int]]:
    facts = analyse(grid)
    if foil == 'all_fours':
        return [[8 if v == 4 else v for v in row] for row in grid]
    selected = _selected_centers(facts, mark_scope, foil)
    cells = set().union(*(plus_cells(p) for p in selected)) if selected else set()
    if foil == 'paint_components':
        owners = {facts['center_owner'][p] for p in selected}
        cells = {p for row in facts['components'] if row['index'] in owners for p in row['cells']}
    out = copy.deepcopy(grid)
    for r, c in cells:
        out[r][c] = 8
    return out


def rival_solve(grid: list[list[int]], mark_scope: str, foil: str) -> list[list[int]]:
    if foil != 'exact_only':
        return solve(grid, mark_scope, foil)
    centers = []
    height, width = len(grid), len(grid[0])
    for r, c in cross_centers(grid):
        if all(grid[rr][cc] == 2 for rr, cc in
               ((r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1))
               if 0 <= rr < height and 0 <= cc < width):
            centers.append((r, c))
    facts = analyse(grid)
    if mark_scope == 'dominant_component':
        counts = {}
        for p in centers:
            owner = facts['center_owner'][p]
            counts[owner] = counts.get(owner, 0) + 1
        chosen = max(counts, key=lambda i: counts[i]) if counts else None
        centers = [p for p in centers if facts['center_owner'][p] == chosen]
    out = copy.deepcopy(grid)
    for p in centers:
        for r, c in plus_cells(p):
            out[r][c] = 8
    return out


def intermediate(grid: list[list[int]]) -> dict:
    facts = analyse(grid)
    return {'centers': [list(p) for p in facts['centers']],
            'components': [{'index': row['index'], 'size': row['size'],
                            'plus_centers': [list(p) for p in row['plus_centers']],
                            'plus_count': row['plus_count']}
                           for row in facts['components']],
            'dominant_component': facts['dominant_component']}


def _add_plus_chain(grid: list[list[int]], centers: list[tuple[int, int]], *, diagonals: int = 0) -> None:
    for center in centers:
        for r, c in plus_cells(center):
            if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
                raise ValueError('plus placement outside grid')
            grid[r][c] = 4
    for (r1, c1), (r2, c2) in zip(centers, centers[1:]):
        if r1 == r2:
            for c in range(min(c1, c2) + 2, max(c1, c2) - 1):
                grid[r1][c] = 4
        elif c1 == c2:
            for r in range(min(r1, r2) + 2, max(r1, r2) - 1):
                grid[r][c1] = 4
        else:
            raise ValueError('plus chains must be axis aligned')
    for i, (r, c) in enumerate(centers):
        if (diagonals >> i) & 1:
            rr, cc = r - 1, c - 1
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                grid[rr][cc] = 4


def _line(grid: list[list[int]], a: tuple[int, int], b: tuple[int, int]) -> None:
    r1, c1 = a; r2, c2 = b
    if r1 != r2 and c1 != c2:
        raise ValueError('line must be axis aligned')
    if r1 == r2:
        for c in range(min(c1, c2), max(c1, c2) + 1):
            grid[r1][c] = 4
    else:
        for r in range(min(r1, r2), max(r1, r2) + 1):
            grid[r][c1] = 4


def _add_isolated_noise(grid: list[list[int]], rng, count: int) -> None:
    for _ in range(count):
        candidates = []
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] != 2:
                    continue
                if all(not (0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0]))
                           or grid[r + dr][c + dc] != 4 for dr, dc in _CARDINAL):
                    candidates.append((r, c))
        if not candidates:
            raise ValueError('insufficient isolated-noise capacity')
        r, c = rng.choice(candidates)
        grid[r][c] = 4


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    code = integer(code, 0, 7, 'transform')
    out = [row[:] for row in grid]
    if code >= 4:
        out = [row[::-1] for row in out]
    for _ in range(code % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _scene(seed: int, index: int) -> list[list[int]]:
    rng = gen_ctx(seed=seed, sample_index=index, version=VERSION, task_id=TASK_ID).draw_rng('plus-components')
    profile = index % 4
    if profile == 0:
        g = [[2] * 18 for _ in range(14)]
        _add_plus_chain(g, [(2, 2)], diagonals=1)
        _line(g, (1, 2), (0, 2)); _line(g, (0, 0), (0, 8))
        _add_plus_chain(g, [(3, 11), (3, 15)], diagonals=3)
        _add_plus_chain(g, [(10, 12)], diagonals=1)
        expected = [1, 2, 1]
    elif profile == 1:
        g = [[2] * 20 for _ in range(18)]
        _add_plus_chain(g, [(2, 3), (2, 7), (2, 11)], diagonals=5)
        _add_plus_chain(g, [(9, 17)], diagonals=1)
        _line(g, (9, 18), (9, 19)); _line(g, (5, 19), (17, 19)); _line(g, (5, 13), (5, 19))
        _add_plus_chain(g, [(14, 3), (14, 7)], diagonals=2)
        expected = [3, 1, 2]
    elif profile == 2:
        g = [[2] * 24 for _ in range(24)]
        _add_plus_chain(g, [(2, 3), (2, 7)], diagonals=1)
        _add_plus_chain(g, [(6, 21)], diagonals=1)
        _line(g, (6, 22), (6, 23)); _line(g, (0, 14), (0, 23)); _line(g, (0, 23), (10, 23))
        _add_plus_chain(g, [(11, 4), (11, 8), (11, 12), (11, 16)], diagonals=10)
        _add_plus_chain(g, [(20, 3), (20, 7), (20, 11)], diagonals=7)
        expected = [2, 1, 4, 3]
    else:
        g = [[2] * 30 for _ in range(30)]
        _add_plus_chain(g, [(3, 1), (3, 5), (3, 9)], diagonals=5)
        _add_plus_chain(g, [(4, 27)], diagonals=1)
        _line(g, (4, 28), (4, 29)); _line(g, (0, 18), (0, 29)); _line(g, (0, 29), (29, 29)); _line(g, (29, 18), (29, 29))
        _add_plus_chain(g, [(10, 3), (10, 7)], diagonals=2)
        _add_plus_chain(g, [(15, 4), (15, 8), (15, 12), (15, 16), (15, 20)], diagonals=21)
        _add_plus_chain(g, [(28, 1), (28, 5), (28, 9), (28, 13)], diagonals=10)
        expected = [3, 1, 2, 5, 4]
    _add_isolated_noise(g, rng, 2 + index % 11)
    # The first teaching profile keeps its vertical order under identity/LR
    # reflection, so first/last/topmost-component shortcuts are refuted for
    # every seed rather than accidentally rescued by a quarter-turn.
    transform = rng.choice((0, 4)) if profile == 0 else rng.randrange(8)
    g = _transform(g, transform)
    facts = analyse(g)
    got = [row['plus_count'] for row in facts['components'] if row['plus_count']]
    if sorted(got) != sorted(expected) or max(got, default=0) != max(expected):
        raise ValueError(f'constructed plus counts changed: {got} != {expected}')
    if got.count(max(got)) != 1:
        raise ValueError('dominant plus component must be unique')
    if solve(g, 'all') == solve(g, 'dominant_component'):
        raise ValueError('settings must disagree on every admitted input')
    return g


def sample(seed: int, index: int) -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, 'seed')
    integer(index, 0, 2**31 - 1, 'sample_index')
    return _scene(seed, index)


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    integer(seed, 0, 2**63 - 1, 'seed')
    integer(sample_index, 0, 2**31 - 1, 'sample_index')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('unknown difficulty')
    if overrides:
        raise ValueError('unsupported override')
    return sample(seed, sample_index)


def check_invariants(grid, *, difficulty=None, meta=None):
    try:
        facts = analyse(grid)
        counts = [row['plus_count'] for row in facts['components'] if row['plus_count']]
        if len(counts) < 2 or counts.count(max(counts)) != 1:
            return ['at least two plus-bearing components and one unique dominant count required']
        if solve(grid, 'all') == solve(grid, 'dominant_component'):
            return ['settings must disagree']
    except (ValueError, TypeError) as error:
        return [str(error)]
    return []


def rule_mirror(grid):
    return solve(grid, 'all')
