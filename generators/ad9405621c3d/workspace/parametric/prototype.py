"""Separate native family: direct routing or routing via a derived farthest cell.

The production sampler and canonical program remain unchanged. Inputs are
matched across settings. Python labels are claims; native qualification executes
the returned Racket on every pair independently.
"""
from collections import deque
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random
import sys

HOME = Path(__file__).resolve().parent
SETTINGS = ({'route_mode': 'direct'}, {'route_mode': 'via_farthest'})
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
COLORS = (2, 3, 4, 6, 7, 8, 9)


def _setting(settings):
    if not isinstance(settings, dict) or set(settings) != {'route_mode'}:
        raise ValueError('settings must contain exactly route_mode')
    if type(settings['route_mode']) is not str or settings['route_mode'] not in ('direct', 'via_farthest'):
        raise ValueError('route_mode must be direct or via_farthest')
    return settings['route_mode']


def program(settings):
    mode = _setting(settings)
    return (HOME / ('canonical.rkt' if mode == 'direct' else 'via_farthest.rkt')).read_text()


def _parse(g):
    if type(g) is not list or not 2 <= len(g) <= 30 or any(type(row) is not list for row in g):
        raise ValueError('grid must have 2..30 list rows')
    w = len(g[0])
    if not 2 <= w <= 30 or any(len(row) != w for row in g):
        raise ValueError('grid must be rectangular, width 2..30')
    if any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row):
        raise ValueError('grid cells must be exact ARC integers')
    colors = {v for row in g for v in row if v not in (0, 5)}
    if len(colors) != 1 or not colors.issubset(COLORS):
        raise ValueError('one endpoint color outside 0,1,5 is required')
    color = next(iter(colors))
    points = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == color]
    if len(points) != 2 or sum(v == 5 for row in g for v in row) < 3:
        raise ValueError('two endpoints and at least three wall cells are required')
    return points[0], points[1], color


def _bfs(g, start, dirs=DIRS):
    h, w = len(g), len(g[0])
    distance, parent = {start: 0}, {start: None}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in dirs:
            q = (r + dr, c + dc)
            if 0 <= q[0] < h and 0 <= q[1] < w and g[q[0]][q[1]] != 5 and q not in distance:
                distance[q] = distance[(r, c)] + 1
                parent[q] = (r, c)
                queue.append(q)
    return distance, parent


def _path(parent, goal):
    if goal not in parent:
        return []
    result = []
    while goal is not None:
        result.append(goal)
        goal = parent[goal]
    return result[::-1]


def analyze(grid):
    start, goal, color = _parse(grid)
    dist, parents = _bfs(grid, start)
    traversable = sum(v != 5 for row in grid for v in row)
    if len(dist) != traversable:
        raise ValueError('all traversable cells must be connected')
    maximum = max(dist.values())
    tied = sorted(p for p, d in dist.items() if d == maximum)
    waypoint = tied[0]
    _, second_parents = _bfs(grid, waypoint)
    return {'start': list(start), 'goal': list(goal), 'color': color,
            'waypoint': list(waypoint), 'waypoint_distance': maximum,
            'farthest_ties': [list(p) for p in tied],
            'direct_path': [list(p) for p in _path(parents, goal)],
            'first_leg': [list(p) for p in _path(parents, waypoint)],
            'second_leg': [list(p) for p in _path(second_parents, goal)],
            'open_cells': traversable}


def mirror(grid, settings):
    mode = _setting(settings)
    info = analyze(grid)
    path = info['direct_path'] if mode == 'direct' else info['first_leg'] + info['second_leg']
    out = [row[:] for row in grid]
    for r, c in path:
        out[r][c] = info['color']
    return out


def _rng(seed, label):
    digest = hashlib.sha256(f'ad9405621c3d/native/v1/{seed}/{label}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _maze(rng, h, w, loops):
    """Spanning tree on a full lattice, plus lawful cycles and border mouths."""
    grid = [[5] * w for _ in range(h)]
    sites = {(r, c) for r in range(1, h, 2) for c in range(1, w, 2)}
    start = rng.choice(sorted(sites))
    stack, seen = [start], {start}
    grid[start[0]][start[1]] = 0
    while stack:
        r, c = stack[-1]
        options = [(r + 2*dr, c + 2*dc) for dr, dc in DIRS
                   if (r + 2*dr, c + 2*dc) in sites and (r + 2*dr, c + 2*dc) not in seen]
        if not options:
            stack.pop()
            continue
        nr, nc = rng.choice(options)
        grid[(r + nr)//2][(c + nc)//2] = grid[nr][nc] = 0
        seen.add((nr, nc))
        stack.append((nr, nc))
    connectors = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 5 and ((grid[r-1][c] == grid[r+1][c] == 0) or (grid[r][c-1] == grid[r][c+1] == 0)):
                connectors.append((r, c))
    rng.shuffle(connectors)
    for r, c in connectors[:round(len(connectors)*loops)]:
        grid[r][c] = 0
    # These tunnels retain connection and exercise all four canvas boundaries.
    for side in range(4):
        if side < 2:
            c = rng.choice(list(range(1, w, 2)))
            r = 0 if side == 0 else h-1
            grid[r][c] = 0
            if side == 1 and grid[r-1][c] == 5:
                grid[r-1][c] = 0
        else:
            r = rng.choice(list(range(1, h, 2)))
            c = 0 if side == 2 else w-1
            grid[r][c] = 0
            if side == 3 and grid[r][c-1] == 5:
                grid[r][c-1] = 0
    return grid


def _scene(seed, label, h, w, *, loops=0.08, interior=False, terminal=False):
    rng = _rng(seed, label)
    grid = _maze(rng, h, w, loops)
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0]
    eligible = [p for p in cells if min(p[0], p[1], h-1-p[0], w-1-p[1]) >= 2] if interior else cells
    candidates = []
    for _ in range(36 if interior else 8):
        start, goal = sorted(rng.sample(eligible, 2))
        dist, parents = _bfs(grid, start)
        path = _path(parents, goal)
        maxdist = max(dist.values())
        far = min(p for p, d in dist.items() if d == maxdist)
        _, second = _bfs(grid, far)
        extra = len((set(_path(parents, far)) | set(_path(second, goal))) - set(path))
        detour = len(path)-1-(abs(start[0]-goal[0])+abs(start[1]-goal[1]))
        _, reverse_order = _bfs(grid, start, tuple(reversed(DIRS)))
        tie = _path(reverse_order, goal) != path
        score = (bool(extra), bool(detour), tie, min(extra, 12), min(detour, 12), len(path))
        candidates.append((score, start, goal))
    _, start, goal = max(candidates)
    if terminal:
        dist, _ = _bfs(grid, start)
        far = min(q for q, d in dist.items() if d == max(dist.values()))
        if far < start:
            start = min(cells)
            dist, _ = _bfs(grid, start)
            far = min(q for q, d in dist.items() if d == max(dist.values()))
        goal = far
    color = rng.choice(COLORS)
    grid[start[0]][start[1]] = grid[goal[0]][goal[1]] = color
    return grid


@lru_cache(maxsize=1)
def _rivals():
    path = HOME / 'rivals.py'
    name = '_maze_teaching_rivals_' + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _teaching_candidates(seed):
    """Construct connected mazes and varied endpoint roles; never inspect queries."""
    for i in range(80):
        h, w = ((9, 11), (11, 13), (13, 15), (15, 17))[i % 4]
        rng = _rng(seed, f'core-candidate-{i}')
        base = _maze(rng, h, w, (0.12, 0.35, 0.6, 0.85)[(i // 4) % 4])
        cells = [(r, c) for r in range(h) for c in range(w) if base[r][c] == 0]
        interior = [q for q in cells if min(q[0], q[1], h-1-q[0], w-1-q[1]) >= 2]
        color = COLORS[(seed + i) % len(COLORS)]
        for j in range(5):
            start, goal = sorted(rng.sample(interior if j < 2 else cells, 2))
            if j in (1, 3):
                distances, _ = _bfs(base, start)
                far = min(q for q, value in distances.items() if value == max(distances.values()))
                if far > start:
                    goal = far
            grid = [row[:] for row in base]
            grid[start[0]][start[1]] = grid[goal[0]][goal[1]] = color
            yield grid


@lru_cache(maxsize=32)
def _teaching(seed):
    """Select a joint three-demo cover for both settings from at most 400 inputs.

    This is demonstration construction, not a query-conditioned rejection gate.
    The independently authored executable bank stays source-bound and reusable.
    If the bounded search cannot teach every declared distinction, fail loudly.
    """
    bank = [(s, r) for s in SETTINGS for r in _rivals().bank(s)]
    full = (1 << len(bank)) - 1
    masks, grids, indices = [], [], []
    for attempt, grid in enumerate(_teaching_candidates(seed), 1):
        expected = {s['route_mode']: mirror(grid, s) for s in SETTINGS}
        mask = sum(1 << i for i, (s, rival) in enumerate(bank)
                   if rival.apply(grid) != expected[s['route_mode']])
        if mask in masks:
            continue  # equal coverage cannot improve a pair; keeps all three grids distinct
        for i, prior in enumerate(masks):
            for j in range(i + 1, len(masks)):
                if prior | masks[j] | mask == full:
                    chosen = (grids[i], grids[j], grid)
                    frozen = tuple(tuple(tuple(row) for row in g) for g in chosen)
                    return frozen, attempt, (indices[i], indices[j], attempt), len(bank)
        masks.append(mask)
        grids.append(grid)
        indices.append(attempt)
    raise RuntimeError('bounded 400-candidate demonstration construction found no three-example cover')


def teaching_summary(seed):
    _, attempts, selected, rival_count = _teaching(seed)
    return {'candidate_limit': 400, 'candidates_examined': attempts,
            'selected_candidate_numbers': list(selected), 'rivals_rejected_across_settings': rival_count,
            'queries_consulted': False, 'inputs_conditioned_on_setting': False}


@lru_cache(maxsize=32)
def _inputs(seed):
    # A fixed three-example teaching core is reused at every supported count.
    demos = [[list(row) for row in g] for g in _teaching(seed)[0]]
    for i, (h, w) in enumerate(((18, 22), (23, 19), (27, 25)), 3):
        demos.append(_scene(seed, f'demo{i}', h, w, loops=(i%3)*0.08))
    profiles = [(7, 9), (17, 21), (30, 30), (25, 29)]
    _rng(seed, 'query-order').shuffle(profiles)
    terminal_index = _rng(seed, 'terminal-query').randrange(4)
    queries = [_scene(seed, f'query{h}x{w}', h, w, loops=0.04+0.04*i, terminal=(i == terminal_index))
               for i, (h, w) in enumerate(profiles)]
    values = tuple(tuple(tuple(row) for row in g) for g in demos + queries)
    if len(set(values)) != 10:
        raise RuntimeError('duplicate inputs in deterministic assembly')
    return values


def generate(seed, settings, demos=3, queries=4):
    _setting(settings)
    for name, value, lo, hi in (('seed', seed, 0, 2**63-1), ('demos', demos, 3, 6), ('queries', queries, 1, 4)):
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{name} must be an integer in {lo}..{hi}')
    grids = _inputs(seed)
    def pair(value):
        grid = [list(row) for row in value]
        return {'input': grid, 'output': mirror(grid, settings)}
    return {'train': [pair(g) for g in grids[:demos]],
            'test': [pair(g) for g in grids[6:6+queries]],
            'program_solution': program(settings)}
