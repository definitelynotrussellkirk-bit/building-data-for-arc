"""Input curriculum for the union of ALL unit-cost shortest maze paths.

Even default draws are varied route-cost tradeoffs; odd draws are irregular
mazes. Four demonstrations plus one query contain at least two tradeoffs
before sampler rejections. Each tradeoff refutes every declared competitor,
including anisotropic step costs which fit all five canonical labels.
The selected Racket rule remains the only label authority.
"""
from __future__ import annotations

from collections import Counter, deque
from heapq import heappop, heappush

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "675dcb932594"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "1e4fa5a56660"
SUMMARY = (
    "Color-5 walls, color-2 start and color-3 goal. Recolor precisely the "
    "zero cells on any shortest cardinal path to 8; preserve other cells. "
    "Alternate equal-length routes with different horizontal/vertical step "
    "counts and irregular mazes, with varied endpoints and canonical-size support."
)
INVARIANTS = [
    "rectangular 5..24 by 5..24 integer grids with a complete color-5 perimeter",
    "input palette is exactly 0,2,3,5; the symbolic colors are fixed by the rule",
    "exactly one start and goal, connected at cardinal distance at least two",
    "disconnected zero distractors are lawful and remain unchanged",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profile or 5..24", "valid": "5..24"},
    "grid_w": {"type": "int", "default": "canonical profile or 5..24", "valid": "5..24"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("tradeoff", "maze")
MIN_STRICT_FRAC = 0.05
_DIRS = ((-1, 0), (0, 1), (1, 0), (0, -1))
_CANONICAL_SHAPES = ((5, 11), (6, 12), (7, 11), (8, 13), (7, 13))


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic period for ordinary draws; explicit 5-cell axes may fall back."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _endpoints(grid):
    return tuple(next((r, c) for r, row in enumerate(grid)
                      for c, value in enumerate(row) if value == marker)
                 for marker in (2, 3))


def _distances(grid, start, *, directions=_DIRS, vertical=1, horizontal=1):
    """Local graph measurements for construction/diagnostics, never labels."""
    h, w = len(grid), len(grid[0])
    if not (0 <= start[0] < h and 0 <= start[1] < w) or grid[start[0]][start[1]] == 5:
        return {}
    distances = {start: 0}
    queue = [(0, start)]
    while queue:
        distance, (r, c) = heappop(queue)
        if distance != distances[r, c]:
            continue
        for dr, dc in directions:
            point = r + dr, c + dc
            if not (0 <= point[0] < h and 0 <= point[1] < w):
                continue
            if grid[point[0]][point[1]] == 5:
                continue
            candidate = distance + (vertical if dr else horizontal)
            if candidate < distances.get(point, float("inf")):
                distances[point] = candidate
                heappush(queue, (candidate, point))
    return distances


def _draw_dimension(ctx, name, overrides, options):
    # Exact public bounds do not depend on the difficulty/default mixture.
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, 5, 24)
    return ctx.draw_choice(name, options)


def _tradeoff_grid(h, w, rng):
    """Two tied routes with opposite H/V cost preferences and a longer corner.

    Start k cells inward from a rectangle's northwest corner; connect north
    and west to its perimeter. For rectangle spans H,W, routes have move
    counts (H+k,W-k) and (H-k,W+k), both total H+W. The corner arc is longer.
    """
    rh, rw = rng.randint(4, h - 2), rng.randint(4, w - 2)
    top, left = rng.randint(1, h - rh - 1), rng.randint(1, w - rw - 1)
    bottom, right = top + rh - 1, left + rw - 1
    k = rng.randint(1, min(rh - 3, rw - 3))
    sr, sc = top + k, left + k
    grid = full_grid(h, w, 5)
    for c in range(left, right + 1):
        grid[top][c] = grid[bottom][c] = 0
    for r in range(top, bottom + 1):
        grid[r][left] = grid[r][right] = 0
    for r in range(top, sr + 1):
        grid[r][sc] = 0
    for c in range(left, sc + 1):
        grid[sr][c] = 0
    grid[sr][sc], grid[bottom][right] = 2, 3
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    first, second = _endpoints(grid)
    # Each rich draw teaches both canonical endpoint shortcuts. Generic draws
    # still allow starts at (1,1) and goals in the right interior column.
    orders = [(a, b) for a, b in ((first, second), (second, first))
              if a != (1, 1) and b[1] != w - 2]
    start, goal = rng.choice(orders)
    grid[first[0]][first[1]] = grid[second[0]][second[1]] = 0
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 2, 3
    return grid


def _maze_grid(h, w, rng, difficulty):
    """Irregular occupancy plus a guaranteed three-cell connected component."""
    openness = rng.uniform(0.50, 0.82) if difficulty == "hard" else rng.uniform(0.60, 0.90)
    grid = full_grid(h, w, 5)
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if rng.random() < openness:
                grid[r][c] = 0
    # Makes even a 5x5 draw constructive, without rejection or resized overrides.
    # Other components remain as lawful disconnected distractors.
    row, col = rng.randint(1, h - 2), rng.randint(1, w - 4)
    for c in range(col, col + 3):
        grid[row][c] = 0
    component = sorted(_distances(grid, (row, col)))
    start = rng.choice(component)
    distances = _distances(grid, start)
    goals = sorted(point for point, distance in distances.items() if distance >= 2)
    if not goals:
        # A three-cell component can put the initial start at its center.
        # A neighbor then has a nonadjacent peer: cardinal grids have no triangles.
        start = rng.choice(sorted(point for point in distances if point != start))
        distances = _distances(grid, start)
        goals = sorted(point for point, distance in distances.items() if distance >= 2)
    goal = rng.choice(goals)
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 2, 3
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be a Python integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    shapes = _CANONICAL_SHAPES[1:] if profile == "tradeoff" else _CANONICAL_SHAPES
    anchor_h, anchor_w = ctx.draw_rng("canonical_shape").choice(shapes)
    # Half the defaults use a canonical shape in EVERY band. Other draws explore
    # the full supported size range. This recreates no canonical input.
    core = sample_index % 4 < 2
    lower = 6 if profile == "tradeoff" else 5
    h_options = (anchor_h,) if core else tuple(range(lower, 25))
    w_options = (anchor_w,) if core else tuple(range(lower, 25))
    h = _draw_dimension(ctx, "grid_h", overrides, h_options)
    w = _draw_dimension(ctx, "grid_w", overrides, w_options)
    rng = ctx.draw_rng("maze_geometry")
    if profile == "tradeoff" and min(h, w) >= 6:
        return _tradeoff_grid(h, w, rng)
    return _maze_grid(h, w, rng, difficulty)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    """Validate returned pixels; old texture metadata grants no bypass."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty grid rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged or malformed grid"]
    if any(type(value) is not int or value not in (0, 2, 3, 5) for row in grid for value in row):
        return ["input cells must be integer colors 0,2,3,5"]
    errors = []
    if not (5 <= h <= 24 and 5 <= w <= 24):
        errors.append("grid dimensions outside 5..24")
    counts = Counter(value for row in grid for value in row)
    if counts[2] != 1 or counts[3] != 1:
        errors.append("expected exactly one color-2 start and one color-3 goal")
    if counts[0] == 0:
        errors.append("expected at least one open color-0 cell")
    frame = list(grid[0]) + list(grid[-1]) + [row[0] for row in grid] + [row[-1] for row in grid]
    if any(value != 5 for value in frame):
        errors.append("the complete perimeter must be color-5 walls")
    if errors:
        return errors
    start, goal = _endpoints(grid)
    distance = _distances(grid, start).get(goal)
    if distance is None:
        return ["start and goal are disconnected"]
    if distance < 2:
        return ["a shortest path must contain at least one open cell"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    start, _ = _endpoints(grid)
    reachable = _distances(grid, start)
    if any(value != 5 and (r, c) not in reachable
           for r, row in enumerate(grid) for c, value in enumerate(row)):
        return ["canonical inputs have one nonwall component"]
    output = _union_probe(grid)
    if not any(value == 0 for row in output for value in row):
        return ["canonical inputs include an unused open cell"]
    return []


def _union_probe(grid, *, directions=_DIRS, vertical=1, horizontal=1,
                 fixed_start=False, fixed_goal_right=False):
    """Authoring mirror/rival primitive. Generation never calls it for labels."""
    start, goal = _endpoints(grid)
    if fixed_start:
        start = (1, 1)
    if fixed_goal_right:
        goal = (goal[0], len(grid[0]) - 2)
    ds = _distances(grid, start, directions=directions, vertical=vertical, horizontal=horizontal)
    backwards = tuple((-dr, -dc) for dr, dc in directions)
    dg = _distances(grid, goal, directions=backwards, vertical=vertical, horizontal=horizontal)
    distance = ds.get(goal)
    output = [list(row) for row in grid]
    if distance is not None:
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0 and (r, c) in ds and (r, c) in dg and ds[r, c] + dg[r, c] == distance:
                    output[r][c] = 8
    return output


def _single_path(grid):
    start, goal = _endpoints(grid)
    parents = {start: None}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIRS:
            point = r + dr, c + dc
            if (0 <= point[0] < len(grid) and 0 <= point[1] < len(grid[0])
                    and grid[point[0]][point[1]] != 5 and point not in parents):
                parents[point] = (r, c)
                queue.append(point)
    output = [list(row) for row in grid]
    point = goal if goal in parents else None
    while point is not None:
        if grid[point[0]][point[1]] == 0:
            output[point[0]][point[1]] = 8
        point = parents[point]
    return output


def _intersection_path(grid):
    start, goal = _endpoints(grid)
    ds, dg = _distances(grid, start), _distances(grid, goal)
    distance = ds.get(goal)
    output = [list(row) for row in grid]
    if distance is None:
        return output
    layers = Counter(ds[p] for p in ds if p in dg and ds[p] + dg[p] == distance)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            point = r, c
            if (value == 0 and point in ds and point in dg
                    and ds[point] + dg[point] == distance and layers[ds[point]] == 1):
                output[r][c] = 8
    return output


def _reachable_component(grid):
    reachable = _distances(grid, _endpoints(grid)[0])
    return [[8 if value == 0 and (r, c) in reachable else value
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


def _wall_blind_rectangle(grid):
    start, goal = _endpoints(grid)
    r0, r1 = sorted((start[0], goal[0]))
    c0, c1 = sorted((start[1], goal[1]))
    return [[8 if value == 0 and r0 <= r <= r1 and c0 <= c <= c1 else value
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


def _paint_endpoints(grid):
    output = _union_probe(grid)
    for r, c in _endpoints(grid):
        output[r][c] = 8
    return output


SEMANTIC_RIVALS = {
    "vertical_cost_2": lambda g: _union_probe(g, vertical=2),
    "horizontal_cost_2": lambda g: _union_probe(g, horizontal=2),
    "fixed_start_1_1": lambda g: _union_probe(g, fixed_start=True),
    "fixed_goal_right_column": lambda g: _union_probe(g, fixed_goal_right=True),
    "single_shortest_path": _single_path,
    "intersection_of_shortest_paths": _intersection_path,
    "eight_connected_paths": lambda g: _union_probe(g, directions=_DIRS + ((-1, -1), (-1, 1), (1, -1), (1, 1))),
    "paint_endpoints": _paint_endpoints,
    "paint_all_open": lambda g: [[8 if value == 0 else value for value in row] for row in g],
    "reachable_component": _reachable_component,
    "identity": lambda g: [list(row) for row in g],
    "wall_blind_rectangle": _wall_blind_rectangle,
    **{f"forbid_{name}": (lambda g, d=direction: _union_probe(g, directions=tuple(x for x in _DIRS if x != d)))
       for name, direction in zip(("north", "east", "south", "west"), _DIRS)},
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("vertical_cost_2", "horizontal_cost_2", "fixed_start_1_1",
                        "fixed_goal_right_column", "forbid_west")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, name):
    return SEMANTIC_RIVALS[name](grid) != _union_probe(grid)


SEMANTIC_WITNESSES = {name: (lambda grid, n=name: _refutes(grid, n))
                      for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def lesson_identifiable(demos, query):
    """Finite declared-rival diagnostic, not a claim of universal induction."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
