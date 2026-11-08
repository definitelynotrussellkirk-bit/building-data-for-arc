"""Input sampler for blocked geodesic Voronoi, task d3633a9fb1cd.

The unchanged Racket authority treats color 5 as an impassable wall and every
other non-zero cell as a seed.  A zero cell is painted by its unique nearest
seed under four-neighbour shortest-path distance through non-wall cells; ties
and seedless components remain zero.

This sampler mirrors the canonical two-room grammar, then adds controlled
vertical orientation and a wall-detour branch.  Every public axis is visible in
the returned pixels and every advertised override is constructive in every
difficulty band.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "d3633a9fb1cd"
TASK_ID = GENERATOR_ID
RULE_HASH = "2c2e8f36a1dd"
VERSION = "2.1.0"
SUMMARY = (
    "Two separated color-5 framed rooms contain one or two distinct-colored "
    "seeds each. Zero cells take the color of their unique nearest seed by "
    "four-neighbour shortest-path distance through non-wall cells; ties stay "
    "zero. Some lessons include an attached interior wall that makes geodesic "
    "distance disagree with a Manhattan shortcut."
)

INVARIANTS = [
    "exactly two separated rectangular color-5 wall components on a zero background",
    "each room has one or two seed cells; all seed colors are globally distinct and exclude 0 and 5",
    "every non-wall interior component contains a seed",
    "two-seed rooms contain a genuine equal-distance tie",
    "when an interior barrier accompanies two seeds, it creates a geodesic-vs-Manhattan counterexample",
]

AXES = {
    "room_depth": {"type": "int", "default": "weighted 4..6", "valid": "4..6"},
    "room_span_a": {"type": "int", "default": "weighted 2..5", "valid": "2..5"},
    "room_span_b": {"type": "int", "default": "weighted 2..5", "valid": "2..5"},
    "gap": {"type": "int", "default": "weighted 1..2", "valid": "1..2"},
    "orientation": {
        "type": "str",
        "default": "weighted horizontal|vertical",
        "valid": "horizontal|vertical",
    },
    "seed_mode": {
        "type": "str",
        "default": "three-slot detour/single/broad lesson schedule",
        "valid": "single|mixed|double",
    },
    "barrier": {
        "type": "bool",
        "default": "three-slot detour/single/broad lesson schedule",
        "valid": "true|false",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("detour", "canonical_single", "broad")

_INT_DOMAINS = {
    "room_depth": range(4, 7),
    "room_span_a": range(2, 6),
    "room_span_b": range(2, 6),
    "gap": range(1, 3),
}
_STR_DOMAINS = {
    "orientation": ("horizontal", "vertical"),
    "seed_mode": ("single", "mixed", "double"),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_DOMAINS:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            if value not in _INT_DOMAINS[name]:
                lo, hi = min(_INT_DOMAINS[name]), max(_INT_DOMAINS[name])
                raise ValueError(f"{name}={value!r} is outside [{lo}, {hi}]")
        elif name in _STR_DOMAINS:
            if type(value) is not str or value not in _STR_DOMAINS[name]:
                raise ValueError(f"{name} must be one of {_STR_DOMAINS[name]}, got {value!r}")
        elif name == "barrier":
            if type(value) is not bool:
                raise ValueError(f"barrier must be bool, not {type(value).__name__}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive defaults always include a rival-refuting detour."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _weighted(ctx, name, legal, favored=()):
    """Draw from the whole legal domain while allowing band-specific emphasis."""
    options = list(legal) + list(favored) * 4
    return ctx.draw_choice(name, options)


def _scheduled_choice(ctx, name, legal, value):
    """Pin a default schedule slot while preserving the exact override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, legal)
    return ctx.draw_choice(name, (value,))


def _neighbors(point, h, w):
    r, c = point
    for dr, dc in _CARDINAL:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _distance_map(grid, start):
    h, w = len(grid), len(grid[0])
    queue = deque([start])
    distance = {start: 0}
    while queue:
        point = queue.popleft()
        for nxt in _neighbors(point, h, w):
            if grid[nxt[0]][nxt[1]] != 5 and nxt not in distance:
                distance[nxt] = distance[point] + 1
                queue.append(nxt)
    return distance


def _components(grid, value):
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == value}
    found = []
    while pending:
        start = min(pending)
        pending.remove(start)
        comp = {start}
        queue = deque([start])
        while queue:
            point = queue.popleft()
            for nxt in _neighbors(point, h, w):
                if nxt in pending:
                    pending.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        found.append(comp)
    return found


def _room_boxes(grid):
    """Return (orientation, two ordered frame boxes), or raise ValueError."""
    boxes = []
    for comp in _components(grid, 5):
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        box = (min(rs), min(cs), max(rs), max(cs))
        r0, c0, r1, c1 = box
        if r1 - r0 < 2 or c1 - c0 < 2:
            raise ValueError(f"wall component is too small to frame a room: {box}")
        perimeter = (
            {(r0, c) for c in range(c0, c1 + 1)}
            | {(r1, c) for c in range(c0, c1 + 1)}
            | {(r, c0) for r in range(r0, r1 + 1)}
            | {(r, c1) for r in range(r0, r1 + 1)}
        )
        if not perimeter <= comp:
            raise ValueError(f"wall component lacks a complete rectangular frame: {box}")
        if any(not (r0 <= r <= r1 and c0 <= c <= c1) for r, c in comp):
            raise ValueError(f"wall component extends outside its frame box: {box}")
        boxes.append(box)
    if len(boxes) != 2:
        raise ValueError(f"expected exactly two wall components, found {len(boxes)}")

    a, b = boxes
    if a[3] < b[1] or b[3] < a[1]:
        ordered = sorted(boxes, key=lambda box: box[1])
        if ordered[0][0] != ordered[1][0] or ordered[0][2] != ordered[1][2]:
            raise ValueError("horizontally separated frames must share row bounds")
        return "horizontal", ordered
    if a[2] < b[0] or b[2] < a[0]:
        ordered = sorted(boxes, key=lambda box: box[0])
        if ordered[0][1] != ordered[1][1] or ordered[0][3] != ordered[1][3]:
            raise ValueError("vertically separated frames must share column bounds")
        return "vertical", ordered
    raise ValueError("the two frame boxes overlap")


def _inside(box, point):
    r0, c0, r1, c1 = box
    r, c = point
    return r0 < r < r1 and c0 < c < c1


def _open_inside(grid, box):
    r0, c0, r1, c1 = box
    return [
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] != 5
    ]


def _room_signature(grid, box):
    r0, c0, r1, c1 = box
    depth = r1 - r0 - 1
    span = c1 - c0 - 1
    blocked = tuple(
        (r - r0, c - c0)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] == 5
    )
    return depth, span, blocked


@lru_cache(maxsize=64)
def _seed_pair_candidates(depth, span, blocked, require_detour):
    """Precompute lawful two-seed pairs for one room geometry.

    Override validation explores tens of thousands of draws.  The room geometry
    has only a few dozen possible states, so repeated BFS enumeration belongs in
    a source-bound cache rather than in every generated example.
    """
    local = full_grid(depth + 2, span + 2, 0)
    draw_frame(local, 0, 0, depth + 1, span + 1, 5)
    for r, c in blocked:
        local[r][c] = 5
    cells = [
        (r, c)
        for r in range(1, depth + 1)
        for c in range(1, span + 1)
        if local[r][c] != 5
    ]
    distance_maps = {cell: _distance_map(local, cell) for cell in cells}
    candidates = []
    for a, b in combinations(cells, 2):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 2:
            continue
        map_a, map_b = distance_maps[a], distance_maps[b]
        tie = False
        detour = False
        for point in cells:
            if point in (a, b):
                continue
            da, db = map_a.get(point), map_b.get(point)
            if da is None or db is None:
                continue
            geo = -1 if da == db else (0 if da < db else 1)
            ma = abs(point[0] - a[0]) + abs(point[1] - a[1])
            mb = abs(point[0] - b[0]) + abs(point[1] - b[1])
            man = -1 if ma == mb else (0 if ma < mb else 1)
            tie |= geo == -1
            detour |= geo != man
        if tie and (detour or not require_detour):
            candidates.append((a, b))
    return tuple(candidates)


def _choose_seed_cells(grid, box, count, rng, *, require_detour=False):
    cells = _open_inside(grid, box)
    if count == 1:
        if not cells:
            raise RuntimeError("room contains no open cell for its seed")
        return [rng.choice(cells)]

    r0, c0, _, _ = box
    depth, span, blocked = _room_signature(grid, box)
    candidates = _seed_pair_candidates(depth, span, blocked, require_detour)
    if not candidates:
        requirement = "tie plus wall detour" if require_detour else "equal-distance tie"
        raise RuntimeError(f"constructive room has no seed pair realizing {requirement}")
    chosen = rng.choice(candidates)
    return [(r0 + r, c0 + c) for r, c in chosen]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _horizontal_canvas(depth, span_a, span_b, gap):
    h = depth + 4
    w = span_a + span_b + gap + 6
    grid = full_grid(h, w, 0)
    room_a = (1, 1, depth + 2, span_a + 2)
    b_left = room_a[3] + gap + 1
    room_b = (1, b_left, depth + 2, b_left + span_b + 1)
    draw_frame(grid, *room_a, 5)
    draw_frame(grid, *room_b, 5)
    return grid, [room_a, room_b]


def _add_barrier(grid, box):
    """Attach a wall finger while preserving one connected open component."""
    r0, c0, r1, c1 = box
    interior_span = c1 - c0 - 1
    if interior_span >= 3:
        column = c0 + 1 + interior_span // 2
        for row in range(r0 + 1, r1 - 1):
            grid[row][column] = 5
    else:
        # A vertical finger in a two-column room leaves only a dead-end nub and
        # cannot teach geodesic-vs-Manhattan distance.  Turn the finger ninety
        # degrees: attach it to the left frame and leave the right column open.
        interior_depth = r1 - r0 - 1
        row = r0 + 1 + interior_depth // 2
        for column in range(c0 + 1, c1 - 1):
            grid[row][column] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        favored = {
            "room_depth": (5,), "room_span_a": (3,), "room_span_b": (3,),
            "gap": (1,), "orientation": ("horizontal",),
            "seed_mode": ("single",), "barrier": (False,),
        }
    elif difficulty == "hard":
        favored = {
            "room_depth": (6,), "room_span_a": (4,), "room_span_b": (4,),
            "gap": (1,), "orientation": ("horizontal",),
            "seed_mode": ("double",), "barrier": (True,),
        }
    else:
        favored = {
            "room_depth": (5,), "room_span_a": (3,), "room_span_b": (3,),
            "gap": (1,), "orientation": ("horizontal",),
            "seed_mode": ("single",), "barrier": (False, True),
        }

    depth = _weighted(ctx, "room_depth", tuple(_INT_DOMAINS["room_depth"]), favored["room_depth"])
    span_a = _weighted(ctx, "room_span_a", tuple(_INT_DOMAINS["room_span_a"]), favored["room_span_a"])
    span_b = _weighted(ctx, "room_span_b", tuple(_INT_DOMAINS["room_span_b"]), favored["room_span_b"])
    gap = _weighted(ctx, "gap", tuple(_INT_DOMAINS["gap"]), favored["gap"])
    orientation = _weighted(ctx, "orientation", _STR_DOMAINS["orientation"], favored["orientation"])
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "detour":
        seed_mode = _scheduled_choice(ctx, "seed_mode", _STR_DOMAINS["seed_mode"], "double")
        barrier = _scheduled_choice(ctx, "barrier", (False, True), True)
    elif profile == "canonical_single":
        seed_mode = _scheduled_choice(ctx, "seed_mode", _STR_DOMAINS["seed_mode"], "single")
        barrier = _scheduled_choice(ctx, "barrier", (False, True), False)
    else:
        seed_mode = _weighted(ctx, "seed_mode", _STR_DOMAINS["seed_mode"], favored["seed_mode"])
        barrier = _weighted(ctx, "barrier", (False, True), favored["barrier"])

    grid, boxes = _horizontal_canvas(depth, span_a, span_b, gap)
    if seed_mode == "single":
        seed_counts = [1, 1]
    elif seed_mode == "double":
        seed_counts = [2, 2]
    else:
        double_room = ctx.draw_rng("mixed_double_room").choice((0, 1))
        seed_counts = [2 if i == double_room else 1 for i in range(2)]

    barrier_room = None
    if barrier:
        two_seed_rooms = [i for i, count in enumerate(seed_counts) if count == 2]
        eligible = two_seed_rooms or [0, 1]
        barrier_room = ctx.draw_rng("barrier_room").choice(eligible)
        _add_barrier(grid, boxes[barrier_room])

    total_seeds = sum(seed_counts)
    colors = ctx.draw_rng("seed_colors").sample(list(_SEED_COLORS), total_seeds)
    offset = 0
    for index, (box, count) in enumerate(zip(boxes, seed_counts)):
        points = _choose_seed_cells(
            grid,
            box,
            count,
            ctx.draw_rng(f"room_{index}_seed_positions"),
            require_detour=(barrier_room == index and count == 2),
        )
        for point, color in zip(points, colors[offset:offset + count]):
            grid[point[0]][point[1]] = color
        offset += count

    return _transpose(grid) if orientation == "vertical" else grid


def observe_overrides(grid):
    """Recover every public axis from pixels rather than draw bookkeeping."""
    orientation, boxes = _room_boxes(grid)
    seed_counts = []
    barrier = False
    for box in boxes:
        r0, c0, r1, c1 = box
        seeds = [
            grid[r][c]
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 5)
        ]
        seed_counts.append(len(seeds))
        barrier |= any(
            grid[r][c] == 5
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        )
    mode = {(1, 1): "single", (1, 2): "mixed", (2, 2): "double"}.get(tuple(sorted(seed_counts)))
    if mode is None:
        raise ValueError(f"unsupported room seed counts: {seed_counts}")
    if orientation == "horizontal":
        depth = boxes[0][2] - boxes[0][0] - 1
        spans = [box[3] - box[1] - 1 for box in boxes]
        gap = boxes[1][1] - boxes[0][3] - 1
    else:
        depth = boxes[0][3] - boxes[0][1] - 1
        spans = [box[2] - box[0] - 1 for box in boxes]
        gap = boxes[1][0] - boxes[0][2] - 1
    return {
        "room_depth": depth,
        "room_span_a": spans[0],
        "room_span_b": spans[1],
        "gap": gap,
        "orientation": orientation,
        "seed_mode": mode,
        "barrier": barrier,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the two-room grammar without consulting generator state."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    errors = []
    try:
        _, boxes = _room_boxes(grid)
    except ValueError as exc:
        return [str(exc)]

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not any(box[0] <= r <= box[2] and box[1] <= c <= box[3] for box in boxes):
                if value != 0:
                    errors.append(f"outside-room cell {(r, c)} must be 0, found {value}")
                    if len(errors) >= 5:
                        return errors

    all_seed_colors = []
    for room_index, box in enumerate(boxes):
        r0, c0, r1, c1 = box
        seeds = [
            (r, c, grid[r][c])
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 5)
        ]
        if len(seeds) not in (1, 2):
            errors.append(f"room {room_index} must contain one or two seeds, found {len(seeds)}")
        all_seed_colors.extend(color for _, _, color in seeds)

        open_cells = set(_open_inside(grid, box))
        unseen = set(open_cells)
        while unseen:
            start = min(unseen)
            unseen.remove(start)
            comp = {start}
            queue = deque([start])
            while queue:
                point = queue.popleft()
                for nxt in _neighbors(point, len(grid), width):
                    if nxt in unseen and _inside(box, nxt):
                        unseen.remove(nxt)
                        comp.add(nxt)
                        queue.append(nxt)
            if not any((r, c) in comp for r, c, _ in seeds):
                errors.append(f"room {room_index} has a seedless open component")

    if len(all_seed_colors) != len(set(all_seed_colors)):
        errors.append("seed colors must be globally distinct")
    if any(color in (0, 5) for color in all_seed_colors):
        errors.append("seed colors must exclude 0 and 5")
    return errors


def strict_canonical_like(grid):
    """Accept the measured canonical manifold, not every lawful broad lesson."""
    errors = self_check(grid)
    if errors:
        return errors
    try:
        axes = observe_overrides(grid)
    except ValueError as exc:
        return [str(exc)]
    strict_errors = []
    if axes["orientation"] != "horizontal":
        strict_errors.append("canonical frames are horizontally paired")
    if axes["room_depth"] not in range(4, 7):
        strict_errors.append("canonical room depth is 4..6")
    if axes["room_span_a"] not in range(2, 5) or axes["room_span_b"] not in range(2, 5):
        strict_errors.append("canonical room spans are 2..4")
    if axes["gap"] not in (1, 2):
        strict_errors.append("canonical frame gap is 1 or 2")
    return strict_errors


def _seed_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]


def _geodesic_output(grid, *, break_ties=False):
    out = deepcopy(grid)
    maps = [(color, _distance_map(grid, (r, c))) for r, c, color in _seed_cells(grid)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            options = [(dist[(r, c)], color) for color, dist in maps if (r, c) in dist]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winners = sorted(color for distance, color in options if distance == best)
            if len(winners) == 1 or break_ties:
                out[r][c] = winners[0]
    return out


def _component_manhattan_output(grid):
    h, w = len(grid), len(grid[0])
    component = {}
    component_id = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in component:
                continue
            component[(r, c)] = component_id
            queue = deque([(r, c)])
            while queue:
                point = queue.popleft()
                for nxt in _neighbors(point, h, w):
                    if grid[nxt[0]][nxt[1]] != 5 and nxt not in component:
                        component[nxt] = component_id
                        queue.append(nxt)
            component_id += 1

    seeds = _seed_cells(grid)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            options = [
                (abs(r - sr) + abs(c - sc), color)
                for sr, sc, color in seeds
                if component.get((sr, sc)) == component.get((r, c))
            ]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winners = [color for distance, color in options if distance == best]
            if len(winners) == 1:
                out[r][c] = winners[0]
    return out


def _tie_break_low_color(grid):
    return _geodesic_output(grid, break_ties=True)


def _has_tie_counterexample(grid):
    return _geodesic_output(grid) != _tie_break_low_color(grid)


def _has_wall_detour(grid):
    return _geodesic_output(grid) != _component_manhattan_output(grid)


SEMANTIC_WITNESSES = {
    "tie_stays_zero": _has_tie_counterexample,
    "wall_detour": _has_wall_detour,
}
SEMANTIC_RIVALS = {
    "tie_break_low_color": _tie_break_low_color,
    "component_manhattan": _component_manhattan_output,
}
WITNESS_RIVALS = {
    "tie_stays_zero": ["tie_break_low_color"],
    "wall_detour": ["component_manhattan"],
}
CANONICAL_SHORTCUTS = {"component_manhattan": _component_manhattan_output}
LESSON_COMPETITORS = {
    "component_manhattan": _component_manhattan_output,
    "tie_break_low_color": _tie_break_low_color,
}
