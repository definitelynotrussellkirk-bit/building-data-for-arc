"""Inputs for the unchanged Racket shortest-corridor rule.

Even indices supply a stretched two-loop teaching witness. Odd indices supply
random lattice mazes. Racket owns labels; Python searches select inputs and
define explicitly named rival hypotheses.
"""
from __future__ import annotations

from collections import deque
from functools import partial
import heapq
from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "2006f915df8b"
VERSION = "3.0.0"
RULE_HASH = "24791e9d8fc8"
SUMMARY = (
    "Trace a shortest four-neighbor route from red 2 to green 3 through cells "
    "other than gray walls 5. The unchanged Racket rule colors only the route's "
    "zero-valued interior cells cyan 8. Three demonstrations mix competing-route "
    "witnesses with varied lattice mazes, branches and loops."
)
EXAMPLES_NEEDED = 3
EXPECTED_OUTPUT_CODOMAIN = {0, 2, 3, 5, 8}
# Fixed input roles 0/2/3/5 are preserved; the rule introduces only color 8.
INVARIANTS = [
    "exactly one red 2 start and one green 3 goal; input roles are 0/2/3/5",
    "the marked endpoints are connected and there are at least two zero cells",
    "production selects unique shortest paths; canonical ties remain valid inputs",
    "even-index witnesses distinguish distance from DFS order, turns and goal proximity",
    "off-path zeros, walls and endpoints must be preserved by the reference output",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..12; indexed canonical-size anchors", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "8..14; indexed canonical-size anchors", "valid": "8..14"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("witness", "maze")
_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def schedule_profile(seed, sample_index, difficulty=None):
    return "witness" if sample_index % 2 == 0 else "maze"


def _endpoints(grid):
    positions = {value: [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == value]
                 for value in (2, 3)}
    return positions[2][0], positions[3][0]


def _neighbors(grid, point, directions=_DIRECTIONS):
    r, c = point
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != 5:
            yield nr, nc


def _search(grid):
    """Input-selection statistics, including shortest-path multiplicity."""
    start, goal = _endpoints(grid)
    queue, distance, count, parent = deque([start]), {start: 0}, {start: 1}, {}
    while queue:
        point = queue.popleft()
        for nxt in _neighbors(grid, point):
            depth = distance[point] + 1
            if nxt not in distance:
                distance[nxt], count[nxt], parent[nxt] = depth, count[point], point
                queue.append(nxt)
            elif distance[nxt] == depth:
                count[nxt] = min(2, count[nxt] + count[point])
    if goal not in distance:
        return [], 0
    path, point = [goal], goal
    while point != start:
        point = parent[point]
        path.append(point)
    return path[::-1], count[goal]


def _paint(grid, path):
    out = [list(row) for row in grid]
    for r, c in path:
        if grid[r][c] == 0:
            out[r][c] = 8
    return out


def _carve(grid, points):
    for (r, c), (nr, nc) in zip(points, points[1:]):
        dr, dc = (nr > r) - (nr < r), (nc > c) - (nc < c)
        assert dr == 0 or dc == 0
        grid[r][c] = 0
        while (r, c) != (nr, nc):
            r, c = r + dr, c + dc
            grid[r][c] = 0


def _witness(h, w, rng, difficulty):
    transpose = rng.randrange(2)
    rh, rw = (w, h) if transpose else (h, w)
    # Row levels are y0,y1,y2,y3,y5. Keep y5-y3 > y2-y1.
    gaps = [1, 1, 1, 2]
    for _ in range(rng.randint(0, rh - 6)):
        gaps[rng.choice((0, 2, 3))] += 1
    ys = [0]
    for gap in gaps:
        ys.append(ys[-1] + gap)
    xs = [0, 2, 4]
    for _ in range(rng.randint(0, rw - 5)):
        split = rng.choice((1, 2))
        for j in range(split, 3):
            xs[j] += 1
    y0, y1, y2, y3, y5 = ys
    x1, x3, x5 = xs
    core = full_grid(y5 + 1, x5 + 1, 5)
    _carve(core, [(y2, x1), (y1, x1), (y1, x3), (y2, x3), (y2, x5), (y3, x5)])
    _carve(core, [(y2, x1), (y5, x1), (y5, x5), (y3, x5)])
    _carve(core, [(y1, x3), (y0, x3), (y0, x5), (y2, x5)])
    core[y2][x1], core[y3][x5] = 2, 3
    if transpose:
        core = [list(row) for row in zip(*core)]
    if rng.randrange(2):
        core.reverse()
    if rng.randrange(2):
        core = [row[::-1] for row in core]
    grid = full_grid(h, w, 5)
    top, left = rng.randint(0, h - len(core)), rng.randint(0, w - len(core[0]))
    for r, row in enumerate(core, top):
        grid[r][left:left + len(row)] = row
    # Each added cell has at most one open neighbor, so it cannot add a route.
    walls = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    rng.shuffle(walls)
    remaining = rng.randint(0, {"easy": 2, "hard": 8}.get(difficulty, 5))
    for point in walls:
        if not remaining:
            break
        if sum(1 for _ in _neighbors(grid, point)) <= 1:
            grid[point[0]][point[1]] = 0
            remaining -= 1
    return grid


def _maze(h, w, rng):
    nodes = [(r, c) for r in range(1, h - 1, 2) for c in range(1, w - 1, 2)]
    node_set = set(nodes)
    start = rng.choice(nodes)
    seen, stack, edges = {start}, [start], []
    while stack:
        r, c = stack[-1]
        choices = [(r + 2 * dr, c + 2 * dc) for dr, dc in _DIRECTIONS
                   if (r + 2 * dr, c + 2 * dc) in node_set and (r + 2 * dr, c + 2 * dc) not in seen]
        if not choices:
            stack.pop()
            continue
        nxt = rng.choice(choices)
        edges.append((stack[-1], nxt))
        seen.add(nxt)
        stack.append(nxt)
    grid = full_grid(h, w, 5)
    for edge in edges:
        _carve(grid, edge)
    candidates = [((r, c), (r + dr, c + dc)) for r, c in nodes for dr, dc in ((2, 0), (0, 2))
                  if (r + dr, c + dc) in node_set and grid[r + dr // 2][c + dc // 2] == 5]
    rng.shuffle(candidates)
    for edge in candidates[:rng.randrange(3)]:
        _carve(grid, edge)
    pairs = [(a, b) for a in nodes for b in nodes if a != b]
    rng.shuffle(pairs)
    for a, b in pairs:
        grid[a[0]][a[1]], grid[b[0]][b[1]] = 2, 3
        path, count = _search(grid)
        if count == 1 and len(path) >= 4:
            return grid
        grid[a[0]][a[1]], grid[b[0]][b[1]] = 0, 0
    return None


def _dimension(ctx, label, lo, hi, anchor, sample_index, difficulty):
    if label in ctx.overrides:
        return ctx.draw_int_strict(label, lo, hi)
    if sample_index % 4 == 0:
        return ctx.draw_choice(label, [anchor])
    choices = list(range(lo, hi + 1))
    favored = choices[:2] if difficulty == "easy" else choices[-2:] if difficulty == "hard" else choices
    return ctx.draw_choice(label, choices + favored * 2)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unsupported override(s): {', '.join(sorted(unknown))}; supported: grid_h, grid_w")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = _dimension(ctx, "grid_h", 7, 12, 11, sample_index, difficulty)
    w = _dimension(ctx, "grid_w", 8, 14, 12, sample_index, difficulty)
    rng = ctx.draw_rng("maze_geometry")
    if sample_index % 2 == 0:
        return _witness(h, w, rng, difficulty)
    grid = _maze(h, w, rng)
    return grid if grid is not None else _witness(h, w, rng, difficulty)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) or not row for row in grid):
        return ["grid must be a nonempty list of nonempty rows"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or value not in (0, 2, 3, 5) for row in grid for value in row):
        return ["maze cells must be integer colors 0, 2, 3 or 5"]
    counts = {color: sum(row.count(color) for row in grid) for color in (0, 2, 3)}
    if counts[2] != 1 or counts[3] != 1:
        return ["expected exactly one start 2 and one goal 3"]
    errors = []
    if not _search(grid)[0]:
        errors.append("start and goal must be connected through non-wall cells")
    if counts[0] < 2:
        errors.append("corridor needs at least two open zero cells")
    return errors


def strict_canonical_like(grid):
    # In particular, do not reject the canonical examples' shortest-path ties.
    return self_check(grid)


def _dfs_rival(grid, directions=_DIRECTIONS, greedy=False):
    start, goal = _endpoints(grid)
    visited = {start}

    def adjacent(point):
        neighbors = list(_neighbors(grid, point, directions))
        if greedy:
            neighbors.sort(key=lambda p: abs(p[0] - goal[0]) + abs(p[1] - goal[1]))
        return iter(neighbors)

    stack, path = [(start, adjacent(start))], [start]
    while stack:
        point, neighbors = stack[-1]
        if point == goal:
            return _paint(grid, path)
        nxt = next(neighbors, None)
        if nxt is None:
            stack.pop()
            path.pop()
        elif nxt not in visited:
            visited.add(nxt)
            stack.append((nxt, adjacent(nxt)))
            path.append(nxt)
    return [list(row) for row in grid]


def _fewest_turns(grid):
    start, goal = _endpoints(grid)
    initial = (start, -1)
    heap, best, parent = [(0, 0, start, -1)], {initial: (0, 0)}, {}
    while heap:
        turns, length, point, previous = heapq.heappop(heap)
        state = point, previous
        if best.get(state) != (turns, length):
            continue
        if point == goal:
            path = [point]
            while state != initial:
                state = parent[state]
                path.append(state[0])
            return _paint(grid, path)
        for direction, delta in enumerate(_DIRECTIONS):
            for nxt in _neighbors(grid, point, (delta,)):
                cost = turns + int(previous != -1 and previous != direction), length + 1
                new_state = nxt, direction
                if cost < best.get(new_state, (float("inf"), float("inf"))):
                    best[new_state], parent[new_state] = cost, state
                    heapq.heappush(heap, (*cost, nxt, direction))
    return [list(row) for row in grid]


def _flood_open(grid):
    return [[8 if value == 0 else value for value in row] for row in grid]


LESSON_COMPETITORS = {f"dfs_{i:02d}": partial(_dfs_rival, directions=order)
                      for i, order in enumerate(permutations(_DIRECTIONS))}
LESSON_COMPETITORS.update(flood_open=_flood_open, fewest_turns=_fewest_turns,
                          goal_greedy=partial(_dfs_rival, greedy=True))
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = {}


def _refutes_all_rivals(grid):
    path, count = _search(grid)
    if count != 1:
        return False
    expected = _paint(grid, path)
    return all(rival(grid) != expected for rival in LESSON_COMPETITORS.values())


SEMANTIC_WITNESSES = {"shortest_over_search_order_turns_and_proximity": _refutes_all_rivals}
WITNESS_RIVALS = {"shortest_over_search_order_turns_and_proximity": list(SEMANTIC_RIVALS)}

