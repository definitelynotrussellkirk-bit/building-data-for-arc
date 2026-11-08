"""Inputs for nearest seed colors on a doorway-connected room graph.

The unchanged selected Racket rule remains the label authority. A room uses
its smallest seed color. Distances count doors, not pixels. Equal nearest
COLORS yield 8; repeated seeds of one color do not. Unreachable rooms use the
authority's distance-999 convention: all global seed colors compete.

Default four-draw windows contain two compound witnesses, one exact canonical
profile anchor and one exploratory layout. Three demonstrations plus one query
retain a compound witness after any query rotation. Explicit controls select
other authoring distributions and do not inherit that lesson guarantee.
Python predictions below are diagnostic rivals/witnesses, never exported labels.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from itertools import combinations, product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b2b9283b4ab"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "3e13418e96c9"
SUMMARY = (
    "Rectangular rooms are joined only by 7-doorways through 1/9 walls. Fill "
    "rooms with the nearest seed-room color in graph distance; use 8 for "
    "equal nearest distinct colors. Multi-color seed rooms use their smallest "
    "color. Includes detours, disconnected rooms, repeated seed colors, "
    "and contrastive lessons with three demonstrations."
)
INVARIANTS = [
    "integer grids at most 30 by 30 with a closed 1/9 border",
    "non-wall 4-components are rectangular rooms; each 7 joins exactly two rooms",
    "at least one room is seeded from 2..6; input 8 is excluded",
    "seed count means seeded rooms, not distinct colors or colored cells",
    "accepted exact controls are observable in the returned grid; no clamping",
    "explicit controls do not inherit the default lesson guarantee",
]
SEED_POOL = (2, 3, 4, 5, 6)
WALL_COLORS = frozenset({1, 7, 9})
HELPFUL_TEXTURES = ("chain", "grid", "tree", "sparse", "witness", "canonical", "explore")
DEGENERATE_TEXTURES = ("single_room", "no_doors", "two_seeds_same_color")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
TEXTURES = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
_DOMAINS = {
    "n_room_rows": (1, 3), "n_room_cols": (1, 6),
    "room_h": (2, 6), "room_w": (2, 6), "n_seeds": (1, 5),
}
AXES = {
    "n_room_rows": {"type": "int", "default": "scheduled; otherwise 1..3", "valid": "1..3"},
    "n_room_cols": {"type": "int", "default": "scheduled; otherwise 1..6", "valid": "1..6"},
    "room_h": {"type": "int", "default": "difficulty-weighted 2..6", "valid": "2..6"},
    "room_w": {"type": "int", "default": "difficulty-weighted 2..6", "valid": "2..6"},
    "n_seeds": {"type": "int", "default": "seeded rooms; scheduled or 1..5", "valid": "1..5"},
    "seed_colors": {"type": "list", "default": "one per seeded room; repeats allowed",
                    "valid": "list of 1..5 integers in 2..6", "probe": "diagnostic"},
    "door_positions": {"type": "str", "default": "random", "valid": "random", "probe": "diagnostic"},
    "seed_positions": {"type": "str", "default": "random", "valid": "random", "probe": "diagnostic"},
    "texture": {"type": "str", "default": "four-draw teaching schedule", "valid": "|".join(TEXTURES)},
}
# Dynamic feasibility errors also carry the exact requested axis names.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("n_room_cols", "room_w"), ("n_room_rows", "n_room_cols", "n_seeds"),
    {"texture": ("single_room", "witness", "canonical", "two_seeds_same_color"), "n_seeds": None},
    {"texture": ("single_room", "witness", "canonical"), "n_room_rows": None},
    {"texture": ("single_room", "witness", "canonical"), "n_room_cols": None},
    {"texture": "canonical", "room_h": None}, {"texture": "canonical", "room_w": None},
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("witness", "canonical", "explore")


def schedule_profile(seed, sample_index, difficulty=None):
    return ("witness", "canonical", "witness", "explore")[sample_index % 4]


def _incompatible(overrides, reason):
    exc = ValueError(f"Incompatible overrides {sorted(overrides)}: {reason}")
    exc.incompatible_axes = tuple(sorted(overrides))
    raise exc


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unknown override keys: {sorted(unknown)}")
    active = {key: value for key, value in overrides.items() if value is not None}
    for key, (lo, hi) in _DOMAINS.items():
        if key in active:
            if type(active[key]) is not int:
                raise TypeError(f"{key} must be an integer, not a coerced scalar")
            if not lo <= active[key] <= hi:
                raise ValueError(f"{key} must be in {lo}..{hi}")
    if "texture" in active and active["texture"] not in TEXTURES:
        raise ValueError(f"texture must be one of {TEXTURES}")
    for key in ("door_positions", "seed_positions"):
        if key in active and active[key] != "random":
            raise ValueError(f"{key} supports only 'random'")
    if "seed_colors" in active:
        colors = active["seed_colors"]
        if not isinstance(colors, (list, tuple)) or not 1 <= len(colors) <= 5:
            raise ValueError("seed_colors must contain 1..5 colors, one per seeded room")
        if any(type(color) is not int or color not in SEED_POOL for color in colors):
            raise ValueError("seed_colors must contain only integer colors 2..6")
        if "n_seeds" in active and active["n_seeds"] != len(colors):
            _incompatible(active, "n_seeds must equal len(seed_colors)")
    return active


@lru_cache(maxsize=1)
def _feasible_shapes():
    """Immutable lawful dimensions shared by all bands and exact controls."""
    return tuple(values for values in product(*(range(lo, hi + 1) for lo, hi in _DOMAINS.values()))
                 if 1 + values[0] * (values[2] + 1) <= 30
                 and 1 + values[1] * (values[3] + 1) <= 30
                 and values[4] <= values[0] * values[1])


def _dimensions(ctx, texture, active):
    pins = {key: active[key] for key in _DOMAINS if key in active}
    if "seed_colors" in active:
        pins["n_seeds"] = len(active["seed_colors"])
    fixed = {}
    if texture == "single_room":
        fixed = {"n_room_rows": 1, "n_room_cols": 1, "n_seeds": 1}
    elif texture == "two_seeds_same_color":
        fixed = {"n_seeds": 2}
    elif texture == "witness":
        fixed = {"n_room_rows": 3, "n_room_cols": 3, "n_seeds": 3}
    elif texture == "canonical":
        fixed = dict(zip(_DOMAINS, (2, 3, 3, 3, 3)))
    if any(key in pins and pins[key] != value for key, value in fixed.items()):
        _incompatible(active, f"{texture} requires {fixed}")
    pins.update(fixed)
    names = tuple(_DOMAINS)
    candidates = [values for values in _feasible_shapes()
                  if all(values[names.index(key)] == value for key, value in pins.items())]
    if not candidates:
        _incompatible(active, "requested dimensions exceed the 30-cell canvas or seed capacity")
    band = ctx.difficulty if ctx.difficulty in ("easy", "medium", "hard") else "medium"
    favorites = {"easy": (1, 3, 2, 2, 2), "medium": (2, 3, 3, 3, 3),
                 "hard": (3, 4, 4, 4, 4)}[band]
    chosen = {}
    for index, name in enumerate(names):
        options = sorted({values[index] for values in candidates})
        # Weight BEFORE drawing. Never resize a sampled/recorded value.
        weighted = options + ([favorites[index]] * 8 if favorites[index] in options else [])
        value = ctx.draw_choice(name, weighted)
        chosen[name] = value
        candidates = [values for values in candidates if values[index] == value]
    return chosen


def _possible_edges(nr, nc):
    return [(r * nc + c, rr * nc + cc)
            for r in range(nr) for c in range(nc)
            for rr, cc in ((r + 1, c), (r, c + 1)) if rr < nr and cc < nc]


def _path(nr, nc):
    return [r * nc + c for r in range(nr)
            for c in (range(nc) if r % 2 == 0 else range(nc - 1, -1, -1))]


def _edges(ctx, texture, nr, nc):
    options = _possible_edges(nr, nc)
    rng = ctx.draw_rng("door_graph")
    if texture in ("single_room", "no_doors"):
        return []
    if texture in ("chain", "two_seeds_same_color"):
        route = _path(nr, nc)
        return list(zip(route, route[1:]))
    if texture == "grid":
        return options
    if texture == "sparse":
        return [edge for edge in options if rng.random() < 0.45]
    # Randomized Kruskal: a connected tree of nr*nc-1 edges.
    parent = list(range(nr * nc))

    def root(node):
        while parent[node] != node:
            node = parent[node]
        return node

    rng.shuffle(options)
    result = []
    for a, b in options:
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[ra] = rb
            result.append((a, b))
    return result


def _transform_room(room, orientation):
    r, c = divmod(room, 3)
    if orientation >= 4:
        c = 2 - c
    for _ in range(orientation % 4):
        r, c = c, 2 - r
    return 3 * r + c


def _render(ctx, dims, edges, seeds, extras=(), *, wall=1):
    nr, nc, ch, cw = (dims[key] for key in tuple(_DOMAINS)[:4])
    grid = full_grid(1 + nr * (ch + 1), 1 + nc * (cw + 1), wall)

    def origin(room):
        r, c = divmod(room, nc)
        return 1 + r * (ch + 1), 1 + c * (cw + 1)

    for room in range(nr * nc):
        r0, c0 = origin(room)
        for r in range(r0, r0 + ch):
            for c in range(c0, c0 + cw):
                grid[r][c] = 0
    door_rng = ctx.draw_rng("door_locations")
    for a, b in edges:
        a, b = sorted((a, b))
        r0, c0 = origin(a)
        if b == a + 1 and a // nc == b // nc:
            grid[r0 + door_rng.randrange(ch)][c0 + cw] = 7
        elif b == a + nc:
            grid[r0 + ch][c0 + door_rng.randrange(cw)] = 7
        else:
            raise ValueError("Graph edge must join cardinally adjacent rooms")
    seed_rng = ctx.draw_rng("seed_locations")
    for room, color in list(seeds) + list(extras):
        r0, c0 = origin(room)
        free = [(r, c) for r in range(r0, r0 + ch) for c in range(c0, c0 + cw)
                if grid[r][c] == 0]
        r, c = seed_rng.choice(free)
        grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not a coerced scalar")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer, not a coerced scalar")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    active = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=active)
    if "texture" in active:
        texture = ctx.draw_choice("texture", TEXTURES)
    else:
        profile = "explore" if active else schedule_profile(seed, sample_index, difficulty)
        texture = ctx.draw_choice("texture", (profile,))
    ctx.draw_choice("door_positions", ("random",))
    ctx.draw_choice("seed_positions", ("random",))
    dims = _dimensions(ctx, texture, active)
    nr, nc, _, _, ns = (dims[key] for key in _DOMAINS)
    palette_rng = ctx.draw_rng("palette")
    if texture == "witness":
        if "seed_colors" in active:
            _incompatible(active, "witness chooses repeated seed colors and a larger in-room color")
        first, second, b = palette_rng.sample(SEED_POOL, 3)
        a, extra = sorted((first, second))
        colors = ctx.draw_choice("seed_colors", ([a, a, b],))
        orientation = ctx.draw_choice("witness_orientation", tuple(range(8)))
        transform = lambda room: _transform_room(room, orientation)
        route = [transform(room) for room in (0, 1, 2, 5, 4, 3, 6, 7)]
        edges = list(zip(route, route[1:]))
        seeds = list(zip((route[0], route[2], route[6]), colors))
        return _render(ctx, dims, edges, seeds, [(route[0], extra)])
    topology = texture
    if texture in ("canonical", "explore"):
        choices = ("grid", "tree", "chain") if texture == "canonical" else (
            "chain", "grid", "tree", "sparse", "no_doors")
        topology = ctx.draw_choice("sampled_topology", choices)
    edges = _edges(ctx, topology, nr, nc)
    proposed = ([palette_rng.choice(SEED_POOL)] * 2 if texture == "two_seeds_same_color"
                else palette_rng.sample(SEED_POOL, ns))
    colors = ctx.draw_choice("seed_colors", (active.get("seed_colors", proposed),))
    if texture == "two_seeds_same_color" and len(set(colors)) != 1:
        _incompatible(active, "two_seeds_same_color requires two identical seed colors")
    if texture == "canonical" and len(set(colors)) != 3:
        _incompatible(active, "canonical profile requires three distinct seed colors")
    room_rng = ctx.draw_rng("seed_rooms")
    if texture == "two_seeds_same_color":
        route = _path(nr, nc)
        rooms = [route[0], route[-1]]
    else:
        rooms = room_rng.sample(range(nr * nc), ns)
    wall = 1 if texture == "canonical" else ctx.draw_choice("wall_tint", (1, 1, 1, 9))
    return _render(ctx, dims, edges, zip(rooms, colors), wall=wall)


def _room_graph(grid):
    h, w = len(grid), len(grid[0])
    rooms, owner = [], {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] in WALL_COLORS or (r, c) in owner:
                continue
            index, cells, queue = len(rooms), [], deque([(r, c)])
            owner[r, c] = index
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for row, col in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= row < h and 0 <= col < w and (row, col) not in owner and grid[row][col] not in WALL_COLORS:
                        owner[row, col] = index
                        queue.append((row, col))
            rooms.append(cells)
    adj = [set() for _ in rooms]
    doors = {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 7:
                ids = {owner[p] for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if p in owner}
                doors[r, c] = ids
                for a, b in combinations(sorted(ids), 2):
                    adj[a].add(b)
                    adj[b].add(a)
    return rooms, adj, doors


def _bounds(cells):
    rs, cs = zip(*cells)
    return min(rs), min(cs), max(rs), max(cs)


def observe_overrides(grid):
    rooms, _, _ = _room_graph(grid)
    bounds = [_bounds(cells) for cells in rooms]
    heights = sorted({r1 - r0 + 1 for r0, _, r1, _ in bounds})
    widths = sorted({c1 - c0 + 1 for _, c0, _, c1 in bounds})
    return {
        "n_room_rows": len({box[0] for box in bounds}),
        "n_room_cols": len({box[1] for box in bounds}),
        "room_h": heights[0] if len(heights) == 1 else tuple(heights),
        "room_w": widths[0] if len(widths) == 1 else tuple(widths),
        "n_seeds": sum(any(grid[r][c] in SEED_POOL for r, c in cells) for cells in rooms),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid exceeds the 30 by 30 canvas"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["colors must be integers in 0..9, excluding booleans"]
    if any(8 in row for row in grid):
        return ["input 8 is excluded; it is the output tie marker"]
    errors = []
    border = grid[0] + grid[-1] + [row[0] for row in grid] + [row[-1] for row in grid]
    if any(value not in (1, 9) for value in border):
        errors.append("outer border must be closed color-1/9 walls")
    rooms, _, doors = _room_graph(grid)
    if not any(value in SEED_POOL for row in grid for value in row):
        errors.append("at least one seeded room is required")
    for cells in rooms:
        r0, c0, r1, c1 = _bounds(cells)
        if len(cells) != (r1 - r0 + 1) * (c1 - c0 + 1):
            errors.append("each non-wall component must be a rectangular room")
            break
    if any(len(ids) != 2 for ids in doors.values()):
        errors.append("each color-7 doorway must join exactly two distinct rooms")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _distances(adj, start):
    distances, queue = {start: 0}, deque([start])
    while queue:
        room = queue.popleft()
        for other in adj[room]:
            if other not in distances:
                distances[other] = distances[room] + 1
                queue.append(other)
    return distances


def diagnostic_prediction(grid, mode="room_graph"):
    """Authoring model and deliberately wrong rivals; never a label authority."""
    rooms, adj, _ = _room_graph(grid)
    entries = []
    for room_id, cells in enumerate(rooms):
        colors = [grid[r][c] for r, c in cells if grid[r][c] not in WALL_COLORS and grid[r][c] != 0]
        if colors:
            color = max(colors) if mode == "largest_seed_in_room" else min(colors)
            entries.append((room_id, color))
    if not entries:
        raise ValueError("at least one seeded room is required")
    dists = [_distances(adj, room_id) for room_id, _ in entries]
    bounds = [_bounds(cells) for cells in rooms]
    row_starts, col_starts = sorted({box[0] for box in bounds}), sorted({box[1] for box in bounds})
    positions = [(row_starts.index(box[0]), col_starts.index(box[1])) for box in bounds]
    output = [list(row) for row in grid]
    for room_id, cells in enumerate(rooms):
        candidates = []
        for index, (seed_room, color) in enumerate(entries):
            distance = dists[index].get(room_id, 999)
            if mode == "ignore_doors":
                a, b = positions[room_id], positions[seed_room]
                distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
            candidates.append((distance, color))
        best = min(distance for distance, _ in candidates)
        nearest = [color for distance, color in candidates if distance == best]
        distinct = set(nearest)
        fill = next(iter(distinct)) if len(distinct) == 1 else 8
        if mode == "seed_room_tie" and len(nearest) > 1:
            fill = 8
        elif mode == "minimum_color_tie":
            fill = min(distinct)
        elif mode == "unreachable_zero" and best == 999:
            fill = 0
        for r, c in cells:
            output[r][c] = fill
    return output


def _seed_room_tie(grid):
    return diagnostic_prediction(grid, "seed_room_tie")


def _largest_seed_in_room(grid):
    return diagnostic_prediction(grid, "largest_seed_in_room")


def _ignore_doors(grid):
    return diagnostic_prediction(grid, "ignore_doors")


def _minimum_color_tie(grid):
    return diagnostic_prediction(grid, "minimum_color_tie")


def _unreachable_zero(grid):
    return diagnostic_prediction(grid, "unreachable_zero")


def _has_same_color_tie(grid):
    return diagnostic_prediction(grid) != _seed_room_tie(grid)


def _has_multi_color_seed_room(grid):
    return diagnostic_prediction(grid) != _largest_seed_in_room(grid)


def _has_doorway_detour(grid):
    return diagnostic_prediction(grid) != _ignore_doors(grid)


def _has_distinct_color_tie(grid):
    return diagnostic_prediction(grid) != _minimum_color_tie(grid)


def _has_unreachable_room(grid):
    return diagnostic_prediction(grid) != _unreachable_zero(grid)


SEMANTIC_RIVALS = {
    "seed_room_tie": _seed_room_tie, "largest_seed_in_room": _largest_seed_in_room,
    "ignore_doors": _ignore_doors, "minimum_color_tie": _minimum_color_tie,
    "unreachable_zero": _unreachable_zero,
}
SEMANTIC_WITNESSES = {
    "same_color_tie": _has_same_color_tie, "multi_color_seed_room": _has_multi_color_seed_room,
    "doorway_detour": _has_doorway_detour, "distinct_color_tie": _has_distinct_color_tie,
    "unreachable_room": _has_unreachable_room,
}
WITNESS_RIVALS = {
    "same_color_tie": ["seed_room_tie"], "multi_color_seed_room": ["largest_seed_in_room"],
    "doorway_detour": ["ignore_doors"], "distinct_color_tie": ["minimum_color_tie"],
    "unreachable_room": ["unreachable_zero"],
}
CANONICAL_SHORTCUTS = {
    "seed_room_tie": _seed_room_tie, "largest_seed_in_room": _largest_seed_in_room,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival test, not a claim of universal identifiability."""
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
