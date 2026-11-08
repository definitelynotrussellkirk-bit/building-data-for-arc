"""Generator for 6b694a414d96 — fill rooms directly adjacent to the seed.

The unchanged Racket rule treats colors 1, 7, and 9 as walls. Non-wall cells
form 4-connected rooms; a color-7 wall cell is a door connecting the two rooms
on opposite sides. The room containing the sole color-2 marker is the seed.
The output preserves walls and doors, clears every room, and paints only the
seed's direct graph neighbors color 8.

Version 3 replaces the previous one-row strip sampler with bounded 2-D room
lattices that accept the canonical examples. A three-slot schedule alternates
horizontal doors, vertical doors, and a second-hop witness. Thus every complete
three-example default lesson refutes the canonical-fitting shortcut "paint all
rooms reachable from the seed" as well as orientation-only and fill-all rivals.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b694a414d96"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bf24da6609f2"

SUMMARY = (
    "A closed 2-D lattice of rectangular rooms is separated by color-1/9 "
    "walls. Color-7 doors define room-graph edges and one room contains a "
    "color-2 seed. Preserve the walls, clear all rooms, and fill exactly the "
    "rooms one door away from the seed with color 8."
)

INVARIANTS = [
    "colors 1 and 9 are walls; each color-7 door links two opposite rooms",
    "non-wall cells form a rectangular lattice of rectangular rooms",
    "exactly one room contains exactly one color-2 seed marker",
    "the seed room has at least one direct door neighbor",
    "only direct neighbors are filled; second-hop and disconnected rooms remain empty",
]

AXES = {
    "rooms_r": {"type": "int", "default": "profile/difficulty draw", "valid": "2..4"},
    "rooms_c": {"type": "int", "default": "profile/difficulty draw", "valid": "2..5"},
    "room_h": {"type": "int", "default": "difficulty draw", "valid": "2..5"},
    "room_w": {"type": "int", "default": "difficulty draw", "valid": "2..4"},
    "wall_color": {"type": "int", "default": "1 favored; 9 supported", "valid": "1|9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

SCHEDULE_PROFILES = ("horizontal", "vertical", "second_hop")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_WALLS = frozenset((1, 7, 9))
_DELTAS = ((-1, 0), (0, -1), (0, 1), (1, 0))
_LEGAL_AXES = {
    "rooms_r": tuple(range(2, 5)),
    "rooms_c": tuple(range(2, 6)),
    "room_h": tuple(range(2, 6)),
    "room_w": tuple(range(2, 5)),
    "wall_color": (1, 9),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Seed-rotated period; any three consecutive draws cover all roles."""
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(sorted(unknown)))
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int or value not in _LEGAL_AXES[name]:
            raise ValueError(
                f"invalid {name}={value!r}; expected one of {_LEGAL_AXES[name]}"
            )
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")


def _axis(ctx, name, defaults):
    options = _LEGAL_AXES[name] if ctx.overrides.get(name) is not None else tuple(defaults)
    return ctx.draw_choice(name, options)


def _room_data(grid):
    """Return non-wall rooms, cell ownership, room adjacency, and doors."""
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
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and grid[rr][cc] not in _WALLS
                        and (rr, cc) not in owner
                    ):
                        owner[rr, cc] = rid
                        queue.append((rr, cc))
            rooms.append(cells)

    adjacency, doors = [set() for _ in rooms], []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 7:
                continue
            ids = {
                owner[r + dr, c + dc]
                for dr, dc in _DELTAS
                if (r + dr, c + dc) in owner
            }
            doors.append(((r, c), ids))
            for a in ids:
                adjacency[a].update(ids - {a})
    return rooms, owner, [sorted(ids) for ids in adjacency], doors


def _geometry(rooms):
    rectangles = [
        (
            min(r for r, _ in cells),
            max(r for r, _ in cells),
            min(c for _, c in cells),
            max(c for _, c in cells),
        )
        for cells in rooms
    ]
    return (
        rectangles,
        {(r0, r1) for r0, r1, _, _ in rectangles},
        {(c0, c1) for _, _, c0, c1 in rectangles},
    )


def _analysis(grid):
    rooms, owner, adjacency, doors = _room_data(grid)
    seed_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(seed_cells) != 1 or seed_cells[0] not in owner:
        raise ValueError("exactly one seed cell inside a room is required")
    return rooms, owner, adjacency, doors, owner[seed_cells[0]]


def _paint_rooms(grid, rooms, room_ids):
    out = [[value if value in _WALLS else 0 for value in row] for row in grid]
    for rid in room_ids:
        for r, c in rooms[rid]:
            out[r][c] = 8
    return out


def rule_mirror(grid):
    """Diagnostic Python mirror of the unchanged canonical Racket rule."""
    rooms, _, adjacency, _, seed = _analysis(grid)
    return _paint_rooms(grid, rooms, adjacency[seed])


def _all_lattice_edges(rows, cols):
    return [
        (r * cols + c, rr * cols + cc)
        for r in range(rows)
        for c in range(cols)
        for rr, cc in ((r, c + 1), (r + 1, c))
        if rr < rows and cc < cols
    ]


def _profile_graph(profile, rows, cols, rng):
    """Return (seed room id, undirected door edges) for one schedule role."""
    if profile == "horizontal":
        sr = rng.randrange(rows)
        sc = rng.randrange(1, cols - 1) if cols >= 3 else rng.randrange(cols)
        seed = sr * cols + sc
        neighbors = []
        if sc > 0:
            neighbors.append(seed - 1)
        if sc + 1 < cols:
            neighbors.append(seed + 1)
        edges = {(min(seed, nb), max(seed, nb)) for nb in neighbors}
        return seed, edges

    if profile == "vertical":
        sr = rng.randrange(1, rows - 1) if rows >= 3 else rng.randrange(rows)
        sc = rng.randrange(cols)
        seed = sr * cols + sc
        neighbors = []
        if sr > 0:
            neighbors.append(seed - cols)
        if sr + 1 < rows:
            neighbors.append(seed + cols)
        edges = {(min(seed, nb), max(seed, nb)) for nb in neighbors}
        return seed, edges

    # A corner seed has two direct neighbors. One of those opens into the
    # diagonally adjacent room, creating a guaranteed graph-distance-2 room.
    corner = rng.choice(((0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)))
    sr, sc = corner
    seed = sr * cols + sc
    horizontal = sr * cols + (1 if sc == 0 else cols - 2)
    vertical = (1 if sr == 0 else rows - 2) * cols + sc
    diagonal = (1 if sr == 0 else rows - 2) * cols + (1 if sc == 0 else cols - 2)
    bridge = rng.choice((horizontal, vertical))
    edges = {
        (min(seed, horizontal), max(seed, horizontal)),
        (min(seed, vertical), max(seed, vertical)),
        (min(bridge, diagonal), max(bridge, diagonal)),
    }
    return seed, edges


def _door_point(a, b, rows, cols, room_h, room_w, row_starts, col_starts, rng):
    ar, ac = divmod(a, cols)
    br, bc = divmod(b, cols)
    if ar == br:
        right_col = max(ac, bc)
        return (
            rng.choice(range(row_starts[ar], row_starts[ar] + room_h)),
            col_starts[right_col] - 1,
        )
    lower_row = max(ar, br)
    return (
        row_starts[lower_row] - 1,
        rng.choice(range(col_starts[ac], col_starts[ac] + room_w)),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        room_h_defaults, room_w_defaults = (2, 3), (2, 3)
    elif difficulty == "hard":
        room_h_defaults, room_w_defaults = (3, 4, 5), (3, 4)
    else:
        room_h_defaults, room_w_defaults = (2, 3, 4), (2, 3, 4)

    if profile == "horizontal":
        rooms_r_defaults = (2, 2, 3) if difficulty != "hard" else (2, 3, 4)
        rooms_c_defaults = (3, 3, 4) if difficulty == "easy" else (3, 4, 5)
    elif profile == "vertical":
        rooms_r_defaults = (3, 3, 4) if difficulty != "easy" else (3,)
        rooms_c_defaults = (2, 2, 3) if difficulty != "hard" else (2, 3, 4)
    else:
        rooms_r_defaults = (2, 3) if difficulty == "easy" else (2, 3, 4)
        rooms_c_defaults = (2, 3) if difficulty == "easy" else (2, 3, 4, 5)

    rooms_r = _axis(ctx, "rooms_r", rooms_r_defaults)
    rooms_c = _axis(ctx, "rooms_c", rooms_c_defaults)
    room_h = _axis(ctx, "room_h", room_h_defaults)
    room_w = _axis(ctx, "room_w", room_w_defaults)
    wall_color = _axis(ctx, "wall_color", (1, 1, 1, 1, 9))

    height = rooms_r * room_h + rooms_r + 1
    width = rooms_c * room_w + rooms_c + 1
    grid = full_grid(height, width, wall_color)
    row_starts = [1 + index * (room_h + 1) for index in range(rooms_r)]
    col_starts = [1 + index * (room_w + 1) for index in range(rooms_c)]
    room_cells = []
    for rr in range(rooms_r):
        for cc in range(rooms_c):
            cells = [
                (r, c)
                for r in range(row_starts[rr], row_starts[rr] + room_h)
                for c in range(col_starts[cc], col_starts[cc] + room_w)
            ]
            room_cells.append(cells)
            for r, c in cells:
                grid[r][c] = 0

    seed_room, edges = _profile_graph(profile, rooms_r, rooms_c, rng)
    for a, b in sorted(edges):
        r, c = _door_point(
            a,
            b,
            rooms_r,
            rooms_c,
            room_h,
            room_w,
            row_starts,
            col_starts,
            rng,
        )
        grid[r][c] = 7
    seed_cell = rng.choice(room_cells[seed_room])
    grid[seed_cell[0]][seed_cell[1]] = 2
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    if any(
        not isinstance(row, (list, tuple)) or len(row) != len(grid[0])
        for row in grid
    ):
        return ["ragged grid"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors; booleans are not colors"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid exceeds 30x30"]
    unsupported = sorted(
        {value for row in grid for value in row} - {0, 1, 2, 7, 9}
    )
    if unsupported:
        return [f"unsupported input colors: {unsupported}"]
    if sum(value == 2 for row in grid for value in row) != 1:
        return ["exactly one color-2 seed cell is required"]
    if any(
        grid[r][c] not in (1, 9)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    ):
        return ["the outer boundary must be closed color-1/9 wall"]

    rooms, owner, adjacency, doors = _room_data(grid)
    if not rooms:
        return ["no rooms"]
    rectangles, row_intervals, col_intervals = _geometry(rooms)
    errors = []
    for cells, (r0, r1, c0, c1) in zip(rooms, rectangles):
        if len(cells) != (r1 - r0 + 1) * (c1 - c0 + 1):
            errors.append("rooms must be filled rectangles")
    if len(rooms) != len(row_intervals) * len(col_intervals):
        errors.append("rooms must form a rectangular lattice")
    for (r, c), ids in doors:
        opposite = (
            ((r - 1, c) in owner and (r + 1, c) in owner)
            or ((r, c - 1) in owner and (r, c + 1) in owner)
        )
        if len(ids) != 2 or not opposite:
            errors.append("each color-7 door must link two opposite rooms")
    if not errors:
        try:
            _, _, _, _, seed = _analysis(grid)
            if not adjacency[seed]:
                errors.append("seed room must have at least one adjacent door")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def strict_canonical_like(grid):
    """Declared rectangular-room manifold, including canonical geometries."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rooms, _, _, _ = _room_data(grid)
    rectangles, row_intervals, col_intervals = _geometry(rooms)
    room_heights = {r1 - r0 + 1 for r0, r1 in row_intervals}
    room_widths = {c1 - c0 + 1 for c0, c1 in col_intervals}
    wall_colors = {value for row in grid for value in row if value in (1, 9)}
    if len(room_heights) != 1 or len(room_widths) != 1 or len(wall_colors) != 1:
        raise ValueError("grid does not expose uniform room size and wall color")
    return {
        "rooms_r": len(row_intervals),
        "rooms_c": len(col_intervals),
        "room_h": next(iter(room_heights)),
        "room_w": next(iter(room_widths)),
        "wall_color": next(iter(wall_colors)),
    }


def _transitive_closure(grid):
    rooms, _, adjacency, _, seed = _analysis(grid)
    reached, queue = {seed}, deque([seed])
    while queue:
        node = queue.popleft()
        for nxt in adjacency[node]:
            if nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
    return _paint_rooms(grid, rooms, sorted(reached - {seed}))


def _fill_all_nonseed(grid):
    rooms, _, _, _, seed = _analysis(grid)
    return _paint_rooms(grid, rooms, [rid for rid in range(len(rooms)) if rid != seed])


def _orientation_neighbors(grid, *, horizontal):
    rooms, _, adjacency, _, seed = _analysis(grid)
    rectangles, _, _ = _geometry(rooms)
    sr0, sr1, sc0, sc1 = rectangles[seed]
    selected = []
    for rid in adjacency[seed]:
        r0, r1, c0, c1 = rectangles[rid]
        if horizontal and (r0, r1) == (sr0, sr1):
            selected.append(rid)
        if not horizontal and (c0, c1) == (sc0, sc1):
            selected.append(rid)
    return _paint_rooms(grid, rooms, selected)


def _horizontal_only(grid):
    return _orientation_neighbors(grid, horizontal=True)


def _vertical_only(grid):
    return _orientation_neighbors(grid, horizontal=False)


def _seed_and_neighbors(grid):
    rooms, _, adjacency, _, seed = _analysis(grid)
    return _paint_rooms(grid, rooms, [seed, *adjacency[seed]])


SEMANTIC_RIVALS = {
    "transitive_closure": _transitive_closure,
    "fill_all_nonseed": _fill_all_nonseed,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "seed_and_neighbors": _seed_and_neighbors,
}
CANONICAL_SHORTCUTS = {"transitive_closure": _transitive_closure}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _one_hop_only(grid):
    return _transitive_closure(grid) != rule_mirror(grid)


def _has_horizontal_and_vertical_neighbors(grid):
    return (
        _horizontal_only(grid) != _paint_rooms(grid, _analysis(grid)[0], [])
        and _vertical_only(grid) != _paint_rooms(grid, _analysis(grid)[0], [])
    )


SEMANTIC_WITNESSES = {
    "one_hop_only": _one_hop_only,
    "mixed_orientation_neighbors": _has_horizontal_and_vertical_neighbors,
}
WITNESS_RIVALS = {
    "one_hop_only": ["transitive_closure", "fill_all_nonseed"],
    "mixed_orientation_neighbors": ["horizontal_only", "vertical_only"],
}


def lesson_identifiable(demos, query):
    """Finite-rival query agreement only; not a universal induction proof."""
    if not demos or any("input" not in pair or "output" not in pair for pair in demos):
        return ["labeled demonstration pairs are required"]
    if "input" not in query or "output" not in query:
        return ["a labeled query is required for this diagnostic hook"]
    return [
        f"{name} fits all demos but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
