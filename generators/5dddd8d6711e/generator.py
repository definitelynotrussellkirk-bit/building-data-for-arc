"""Room-graph shortest paths with variable geometry and explicit teaching cases.

The unchanged Racket rule owns labels. It flood-fills non-{1,7,9} chambers,
connects them through 7-doors, and runs BFS from the red chamber. Neighbors
are visited in row-major chamber-ID order. Walls/doors survive; other cells
are cleared and chambers on the chosen path are painted 8, including endpoints.

The default three-draw schedule contains a cycle/erasure witness, randomized
canonical geometry, and a broader maze. Any three consecutive default draws
refute the five declared rivals. Exact overrides may remove that teaching
property. The Python predictions below are diagnostics, never emitted labels.
"""
from __future__ import annotations

from collections import deque
from heapq import heappop, heappush

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5dddd8d6711e"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "5e8877987e4c"
SUMMARY = (
    "Variable rectangular chambers separated by 1/9 walls and 7-doors. "
    "Red-to-green shortest chamber paths use row-major BFS ties; disconnected "
    "chambers and off-path distractors are cleared. Three-draw lessons "
    "separate BFS from DFS, reverse ties, path union and area costs."
)
INVARIANTS = [
    "a bounded rectangular lattice contains exactly one red and one green marker",
    "rooms are rectangular nonwall components; 7-doors link opposite adjacent rooms",
    "wall color is 1 or 9; 0/4/5/6/8 interiors do not define additional graph edges",
    "room sizes, marker positions, reachability, branches and cycle structure vary",
    "default three-draw windows contain a witness against every declared rival",
]
AXES = {
    "rooms_r": {"type": "int", "default": "profile dependent 1..6", "valid": "1..6"},
    "rooms_c": {"type": "int", "default": "profile dependent 1..6", "valid": "1..6"},
    "wall_color": {"type": "int", "default": "1 favored; 9 supported", "valid": "1|9"},
    "n_noise": {"type": "int", "default": "witness 2; canonical 0; varied 0..2", "valid": "0..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("witness", "canonical", "varied")
_WALLS = frozenset((1, 7, 9))
_NOISE = frozenset((4, 5, 6, 8))
_DELTAS = ((-1, 0), (0, -1), (0, 1), (1, 0))
_LEGAL_AXES = {"rooms_r": tuple(range(1, 7)), "rooms_c": tuple(range(1, 7)),
               "wall_color": (1, 9), "n_noise": (0, 1, 2)}


def schedule_profile(seed, sample_index, difficulty=None):
    """Seed-rotated period; sample order is part of the documented sampler."""
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % 3]


def _axis(ctx, name, defaults):
    options = _LEGAL_AXES[name] if ctx.overrides.get(name) is not None else defaults
    return ctx.draw_choice(name, options)


def _room_data(grid):
    """Read chambers and doors from pixels, independently of drawing coordinates."""
    h, w = len(grid), len(grid[0])
    rooms, owner = [], {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] in _WALLS or (r, c) in owner:
                continue
            rid, cells = len(rooms), []
            queue = deque([(r, c)])
            owner[r, c] = rid
            while queue:
                point = queue.popleft()
                cells.append(point)
                for dr, dc in _DELTAS:
                    rr, cc = point[0] + dr, point[1] + dc
                    if (0 <= rr < h and 0 <= cc < w and grid[rr][cc] not in _WALLS
                            and (rr, cc) not in owner):
                        owner[rr, cc] = rid
                        queue.append((rr, cc))
            rooms.append(cells)
    adjacency, doors = [set() for _ in rooms], []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 7:
                ids = {owner[r + dr, c + dc] for dr, dc in _DELTAS
                       if (r + dr, c + dc) in owner}
                doors.append(((r, c), ids))
                for a in ids:
                    adjacency[a].update(ids - {a})
    return rooms, owner, [sorted(ids) for ids in adjacency], doors


def _path(adjacency, start, goal, *, descending=False):
    previous, queue = {start: None}, deque([start])
    while queue and goal not in previous:
        node = queue.popleft()
        for nxt in sorted(adjacency[node], reverse=descending):
            if nxt not in previous:
                previous[nxt] = node
                queue.append(nxt)
    if goal not in previous:
        return []
    path, node = [], goal
    while node is not None:
        path.append(node)
        node = previous[node]
    return path[::-1]


def _analysis(grid):
    rooms, owner, adjacency, _ = _room_data(grid)
    endpoints = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (2, 3) and value not in endpoints:
                endpoints[value] = owner[r, c]
    if set(endpoints) != {2, 3}:
        raise ValueError("both endpoint colors are required")
    return rooms, adjacency, endpoints[2], endpoints[3]


def _paint(grid, rooms, path, *, preserve_noise=False):
    out = [[v if v in _WALLS or (preserve_noise and v in _NOISE) else 0
            for v in row] for row in grid]
    for rid in path:
        for r, c in rooms[rid]:
            out[r][c] = 8
    return out


def _bfs_prediction(grid):
    """Diagnostic model, never the label authority or an emitted answer."""
    rooms, adjacency, start, goal = _analysis(grid)
    return _paint(grid, rooms, _path(adjacency, start, goal))


def _depth_first_path(grid):
    rooms, adjacency, start, goal = _analysis(grid)
    seen = set()

    def visit(node, path):
        seen.add(node)
        if node == goal:
            return path
        for nxt in adjacency[node]:
            if nxt not in seen:
                found = visit(nxt, path + [nxt])
                if found:
                    return found
        return []

    return _paint(grid, rooms, visit(start, [start]))


def _descending_bfs(grid):
    rooms, adjacency, start, goal = _analysis(grid)
    return _paint(grid, rooms, _path(adjacency, start, goal, descending=True))


def _distances(adjacency, source):
    distances, queue = {source: 0}, deque([source])
    while queue:
        node = queue.popleft()
        for nxt in adjacency[node]:
            if nxt not in distances:
                distances[nxt] = distances[node] + 1
                queue.append(nxt)
    return distances


def _all_shortest_union(grid):
    rooms, adjacency, start, goal = _analysis(grid)
    forward, backward = _distances(adjacency, start), _distances(adjacency, goal)
    path = [] if goal not in forward else [node for node in forward if node in backward
                                          and forward[node] + backward[node] == forward[goal]]
    return _paint(grid, rooms, path)


def _minimum_room_area(grid):
    rooms, adjacency, start, goal = _analysis(grid)
    queue, best, selected = [(len(rooms[start]), (start,), start)], {}, ()
    while queue:
        cost, path, node = heappop(queue)
        if node in best:
            continue
        best[node] = cost
        if node == goal:
            selected = path
            break
        for nxt in adjacency[node]:
            if nxt not in best:
                heappush(queue, (cost + len(rooms[nxt]), path + (nxt,), nxt))
    return _paint(grid, rooms, selected)


def _preserve_offpath_noise(grid):
    rooms, adjacency, start, goal = _analysis(grid)
    return _paint(grid, rooms, _path(adjacency, start, goal), preserve_noise=True)


def _edges(rows, cols):
    return [(r * cols + c, rr * cols + cc) for r in range(rows) for c in range(cols)
            for rr, cc in ((r + 1, c), (r, c + 1)) if rr < rows and cc < cols]


def _forest(rows, cols, rng, *, core=(), chance=0.7):
    edges, parent = set(core), list(range(rows * cols))

    def find(node):
        while node != parent[node]:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for a, b in core:
        parent[find(a)] = find(b)
    candidates = _edges(rows, cols)
    rng.shuffle(candidates)
    for a, b in candidates:
        if find(a) != find(b) and rng.random() < chance:
            edges.add((a, b))
            parent[find(a)] = find(b)
    return edges


def _adjacency(count, edges):
    adjacency = [[] for _ in range(count)]
    for a, b in sorted(edges):
        adjacency[a].append(b)
        adjacency[b].append(a)
    return [sorted(row) for row in adjacency]


def _sizes(count, rng):
    upper = min(5, (29 - count - 1) // count)
    return [rng.randint(2, upper) for _ in range(count)]


def _endpoints(adjacency, rng):
    count = len(adjacency)
    reached = [_distances(adjacency, node) for node in range(count)]
    connected = [(a, b) for a in range(count) for b in reached[a] if a != b]
    separate = [(a, b) for a in range(count) for b in range(count) if b not in reached[a]]
    cases = (["connected"] * 8 if connected else []) + (["separate"] * 2 if separate else []) + ["same"]
    case = rng.choice(cases)
    if case == "connected":
        return rng.choice(connected)
    if case == "separate":
        return rng.choice(separate)
    node = rng.randrange(count)
    return node, node


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(sorted(unknown)))
    for name, value in overrides.items():
        if value is not None and (type(value) is not int or value not in _LEGAL_AXES[name]):
            raise ValueError(f"invalid {name}={value!r}; expected one of {_LEGAL_AXES[name]}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile, rng = schedule_profile(seed, sample_index, difficulty), ctx.draw_rng("layout")
    template = rng.choice((((3, 3), (3, 3, 3)), ((5,), (3, 5, 3, 4)), ((3, 3, 3), (4, 3))))
    if profile == "canonical":
        row_defaults, col_defaults = (len(template[0]),), (len(template[1]),)
    elif profile == "witness":
        row_defaults = (2, 2, 3) if difficulty == "easy" else (2, 3, 4)
        col_defaults = (3, 3, 4) if difficulty == "easy" else (3, 4, 5)
    else:
        favored = (1, 2, 2, 3) if difficulty == "easy" else ((3, 4, 5, 6) if difficulty == "hard" else (2, 3, 4))
        row_defaults = col_defaults = tuple(range(1, 7)) + favored * 2
    rows, cols = _axis(ctx, "rooms_r", row_defaults), _axis(ctx, "rooms_c", col_defaults)
    wall = _axis(ctx, "wall_color", (1,) if profile == "canonical" else (1, 1, 1, 1, 9))
    noise = _axis(ctx, "n_noise", (2,) if profile == "witness" else ((0,) if profile == "canonical" else (0, 1, 2)))
    heights, widths = _sizes(rows, rng), _sizes(cols, rng)
    if profile == "canonical" and (rows, cols) == (len(template[0]), len(template[1])):
        heights, widths = list(template[0]), list(template[1])
    witness = profile == "witness" and rows >= 2 and cols >= 3
    if witness:
        top, left = rng.randrange(rows - 1), rng.randrange(cols - 2)
        heights[top], heights[top + 1] = rng.randint(3, 5), 2
        widths[left], widths[left + 1] = 2, rng.randint(3, 5)
        core_nodes = {r * cols + c for r in (top, top + 1) for c in range(left, left + 3)}
        core = [(a, b) for a, b in _edges(rows, cols) if a in core_nodes and b in core_nodes]
        edges = _forest(rows, cols, rng, core=core)
        start, goal = top * cols + left, (top + 1) * cols + left + 1
    else:
        edges = _forest(rows, cols, rng, chance=0.65)
        extra = 0.07 if difficulty == "easy" else (0.3 if difficulty == "hard" else 0.16)
        for edge in _edges(rows, cols):
            if rng.random() < extra:
                edges.add(edge)
        start, goal = _endpoints(_adjacency(rows * cols, edges), rng)
    row_starts, col_starts = [], []
    cursor = 1
    for value in heights:
        row_starts.append(cursor)
        cursor += value + 1
    cursor = 1
    for value in widths:
        col_starts.append(cursor)
        cursor += value + 1
    grid = full_grid(sum(heights) + rows + 1, sum(widths) + cols + 1, wall)
    cells = []
    for r in range(rows):
        for c in range(cols):
            room = [(rr, cc) for rr in range(row_starts[r], row_starts[r] + heights[r])
                    for cc in range(col_starts[c], col_starts[c] + widths[c])]
            cells.append(room)
            for rr, cc in room:
                grid[rr][cc] = 0
    for a, b in sorted(edges):
        ar, ac = divmod(a, cols)
        br, bc = divmod(b, cols)
        if ar == br:
            point = (rng.choice(range(row_starts[ar], row_starts[ar] + heights[ar])), col_starts[bc] - 1)
        else:
            point = (row_starts[br] - 1, rng.choice(range(col_starts[ac], col_starts[ac] + widths[ac])))
        grid[point[0]][point[1]] = 7
    red = rng.choice(cells[start])
    green = rng.choice([point for point in cells[goal] if point != red])
    grid[red[0]][red[1]], grid[green[0]][green[1]] = 2, 3
    available = [point for room in cells for point in room if point not in (red, green)]
    if witness and noise == 2:
        path = set(_path(_adjacency(rows * cols, edges), start, goal))
        on_path = [point for rid in sorted(path) for point in cells[rid] if point not in (red, green)]
        off_path = [point for rid in range(len(cells)) if rid not in path for point in cells[rid]]
        noise_cells = [rng.choice(on_path), rng.choice(off_path)]
    else:
        noise_cells = rng.sample(available, noise)
    pigment = rng.choice(sorted(_NOISE))
    for rr, cc in noise_cells:
        grid[rr][cc] = pigment
    return grid


def _geometry(rooms):
    rectangles = [(min(r for r, c in cells), max(r for r, c in cells),
                   min(c for r, c in cells), max(c for r, c in cells)) for cells in rooms]
    return rectangles, {(a, b) for a, b, c, d in rectangles}, {(c, d) for a, b, c, d in rectangles}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors; booleans are not colors"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid exceeds 30x30"]
    counts = {color: sum(value == color for row in grid for value in row) for color in (2, 3)}
    if counts != {2: 1, 3: 1}:
        return ["exactly one marker of each endpoint color is required"]
    if any(grid[r][c] not in (1, 9) for r in range(h) for c in range(w)
           if r in (0, h - 1) or c in (0, w - 1)):
        return ["the outer boundary must be closed 1/9 wall"]
    rooms, owner, _, doors = _room_data(grid)
    if not rooms:
        return ["no chambers"]
    rectangles, row_intervals, col_intervals = _geometry(rooms)
    errors = []
    for cells, (r0, r1, c0, c1) in zip(rooms, rectangles):
        if len(cells) != (r1 - r0 + 1) * (c1 - c0 + 1):
            errors.append("chambers must be filled rectangles")
    if len(rooms) != len(row_intervals) * len(col_intervals):
        errors.append("chambers must form a rectangular lattice")
    for (r, c), ids in doors:
        opposite = ((r - 1, c) in owner and (r + 1, c) in owner) or ((r, c - 1) in owner and (r, c + 1) in owner)
        if len(ids) != 2 or not opposite:
            errors.append("each door must link two opposite distinct chambers")
    # Connectivity is not required: canonical examples include isolated rooms.
    return errors


def strict_canonical_like(grid):
    """Declared rectangular-chamber manifold, including lawful edge cases."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rooms, _, _, _ = _room_data(grid)
    _, row_intervals, col_intervals = _geometry(rooms)
    walls = {value for row in grid for value in row if value in (1, 9)}
    if len(walls) != 1:
        raise ValueError("wall_color is observable only for a uniform wall palette")
    return {"rooms_r": len(row_intervals), "rooms_c": len(col_intervals),
            "wall_color": next(iter(walls)),
            "n_noise": sum(value in _NOISE for row in grid for value in row)}


SEMANTIC_RIVALS = {
    "depth_first_path": _depth_first_path,
    "descending_bfs": _descending_bfs,
    "all_shortest_union": _all_shortest_union,
    "minimum_room_area": _minimum_room_area,
    "preserve_offpath_noise": _preserve_offpath_noise,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _cycle_and_erasure(grid):
    expected = _bfs_prediction(grid)
    return all(rival(grid) != expected for rival in SEMANTIC_RIVALS.values())


SEMANTIC_WITNESSES = {"cycle_and_erasure": _cycle_and_erasure}
WITNESS_RIVALS = {"cycle_and_erasure": list(SEMANTIC_RIVALS)}


def lesson_identifiable(demos, query):
    """Finite-rival query agreement only; not a claim of universal induction."""
    if not demos or any("input" not in pair or "output" not in pair for pair in demos):
        return ["labeled demonstration pairs are required"]
    if "input" not in query or "output" not in query:
        return ["a labeled query is required for this diagnostic hook"]
    return [f"{name} fits all demos but changes the query" for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
