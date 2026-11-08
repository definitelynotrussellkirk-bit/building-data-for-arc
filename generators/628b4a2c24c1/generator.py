"""Generator for bank task 56b8d7075625:M157 / 628b4a2c24c1.

Treat every 8 as a wall.  In each row containing a nonzero, non-wall seed,
extend that seed color rightward through blank cells until the next 8 in that
row, or through the last column when the row has no wall.  Existing walls and
seed cells are preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "628b4a2c24c1"
VERSION = "2.0.0"
TASK_ID = "628b4a2c24c1"
RULE_HASH = "5ac6fbbb3b3d"

SUMMARY = (
    "Place one monochrome set of row seeds and color-8 wall markers. Each "
    "seed row has a blank corridor to its next wall or to the right edge; "
    "the oracle sweeps the seed color rightward through that corridor."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0; 8s are fixed wall markers",
    "one non-wall color appears in two to four active rows",
    "each active row contains one contiguous seed run",
    "each seed row has at most one wall, strictly to its right with a blank gap",
    "rows without a wall sweep to the right edge, and at least one wall exists",
    "the seed layout is either one connected shape or separated row segments",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted rng",
        "valid": "5..10",
        "doc": "Input/output grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted rng",
        "valid": "8..14",
        "doc": "Input/output grid width.",
    },
    "active_rows": {
        "type": "int",
        "default": "difficulty-weighted rng",
        "valid": "2..4",
        "doc": "Number of rows containing colored seed cells.",
    },
    "seed_color": {
        "type": "color",
        "default": "rng excluding background and wall colors",
        "valid": "1..9 (!=8)",
        "doc": "The single non-wall seed color.",
    },
    "seed_mode": {
        "type": "enum",
        "default": "rng connected|separated",
        "valid": "connected|separated",
        "doc": "Whether all seed runs form one 4-connected shape.",
    },
    "wall_mode": {
        "type": "enum",
        "default": "rng shared|staggered|mixed_edge",
        "valid": "shared|staggered|mixed_edge",
        "doc": "Shared wall column, row-specific columns, or at least one edge sweep.",
    },
    "wide_seed_row": {
        "type": "bool",
        "default": "rng false|true",
        "valid": "false|true",
        "doc": "Whether at least one active row starts with a two-cell seed run.",
    },
    "extra_walls": {
        "type": "bool",
        "default": "rng false|true",
        "valid": "false|true",
        "doc": "Whether at least one inactive row also contains a wall marker.",
    },
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Official inputs, represented without the nuisance seed color.
# Each profile is (height, width, seed cells, wall cells, axis values).
_CANONICAL_PROFILES = (
    (
        6,
        10,
        ((1, 1), (2, 1), (2, 2), (3, 1)),
        ((0, 6), (1, 6), (2, 6), (3, 6), (4, 6)),
        {
            "active_rows": 3,
            "seed_mode": "connected",
            "wall_mode": "shared",
            "wide_seed_row": True,
            "extra_walls": True,
        },
    ),
    (
        6,
        10,
        ((1, 1), (2, 2), (3, 1)),
        ((1, 4), (2, 6), (3, 8)),
        {
            "active_rows": 3,
            "seed_mode": "separated",
            "wall_mode": "staggered",
            "wide_seed_row": False,
            "extra_walls": False,
        },
    ),
    (
        6,
        10,
        ((1, 1), (2, 2), (3, 1)),
        ((1, 6), (2, 7), (3, 8)),
        {
            "active_rows": 3,
            "seed_mode": "separated",
            "wall_mode": "staggered",
            "wide_seed_row": False,
            "extra_walls": False,
        },
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "active_rows", "seed_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name in ("wide_seed_row", "extra_walls"):
        value = overrides.get(name)
        if value is not None and type(value) is not bool:
            raise ValueError(f"{name} must be a boolean")
    for name in ("seed_mode", "wall_mode"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise ValueError(f"{name} must be a string")


def _weighted_values(axis, difficulty):
    if axis == "grid_h":
        return {
            "easy": (5, 5, 6, 6, 7, 8, 9, 10),
            "medium": (5, 6, 6, 7, 7, 8, 9, 10),
            "hard": (5, 6, 7, 8, 8, 9, 9, 10),
        }.get(difficulty, (5, 6, 7, 8, 9, 10))
    if axis == "grid_w":
        return {
            "easy": (8, 8, 9, 9, 10, 11, 12, 13, 14),
            "medium": (8, 9, 10, 10, 11, 12, 13, 14),
            "hard": (8, 9, 10, 11, 12, 13, 13, 14, 14),
        }.get(difficulty, (8, 9, 10, 11, 12, 13, 14))
    if axis == "active_rows":
        return {
            "easy": (2, 2, 2, 3, 4),
            "medium": (2, 2, 3, 3, 4),
            "hard": (2, 3, 3, 4, 4),
        }.get(difficulty, (2, 3, 4))
    raise KeyError(axis)


def _seed_components(cells):
    remaining = set(cells)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINALS:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(tuple(sorted(component)))
    return tuple(components)


def _analyze(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    seed_cells = tuple(
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 8)
    )
    seed_colors = tuple(sorted({grid[r][c] for r, c in seed_cells}))
    active_rows = tuple(sorted({r for r, _ in seed_cells}))
    seeds_by_row = {
        r: tuple(c for rr, c in seed_cells if rr == r) for r in active_rows
    }
    walls_by_row = {
        r: tuple(c for c in range(w) if grid[r][c] == 8) for r in range(h)
    }
    components = _seed_components(seed_cells) if seed_cells else ()
    if len(components) == 1:
        seed_mode = "connected"
    elif len(components) == len(active_rows) and active_rows:
        seed_mode = "separated"
    else:
        seed_mode = "mixed"

    active_wall_columns = [
        walls_by_row[r][0] if len(walls_by_row[r]) == 1 else None
        for r in active_rows
    ]
    if active_rows and any(column is None for column in active_wall_columns):
        wall_mode = "mixed_edge"
    elif active_rows and len(set(active_wall_columns)) == 1:
        wall_mode = "shared"
    elif active_rows:
        wall_mode = "staggered"
    else:
        wall_mode = None

    return {
        "h": h,
        "w": w,
        "seed_cells": seed_cells,
        "seed_colors": seed_colors,
        "active_rows": active_rows,
        "seeds_by_row": seeds_by_row,
        "walls_by_row": walls_by_row,
        "components": components,
        "seed_mode": seed_mode,
        "wall_mode": wall_mode,
        "wide_seed_row": any(len(cols) > 1 for cols in seeds_by_row.values()),
        "extra_walls": any(
            walls_by_row[r] for r in range(h) if r not in set(active_rows)
        ),
    }


def _canonical_board(ctx, profile):
    h, w, seed_cells, wall_cells, axes = profile
    ctx.draw_choice("grid_h", (h,))
    ctx.draw_choice("grid_w", (w,))
    ctx.draw_choice("active_rows", (axes["active_rows"],))
    seed_color = ctx.draw_color("seed_color", exclude={0, 8})
    ctx.draw_choice("seed_mode", (axes["seed_mode"],))
    ctx.draw_choice("wall_mode", (axes["wall_mode"],))
    ctx.draw_choice("wide_seed_row", (axes["wide_seed_row"],))
    ctx.draw_choice("extra_walls", (axes["extra_walls"],))
    grid = full_grid(h, w, 0)
    for r, c in seed_cells:
        grid[r][c] = seed_color
    for r, c in wall_cells:
        grid[r][c] = 8
    return grid


def _active_row_positions(h, active_rows, seed_mode, rng):
    if seed_mode == "connected":
        start = rng.randint(0, h - active_rows)
        return tuple(range(start, start + active_rows))
    return tuple(sorted(rng.sample(range(h), active_rows)))


def _wall_stops(rows, w, wall_mode, rng):
    if wall_mode == "shared":
        wall = rng.choice(tuple(range(4, w)))
        return {r: wall for r in rows}
    if wall_mode == "staggered":
        candidates = list(range(4, w))
        rng.shuffle(candidates)
        return {r: candidates[index] for index, r in enumerate(rows)}
    edge_count = rng.randint(1, len(rows) - 1)
    edge_rows = set(rng.sample(list(rows), edge_count))
    wall_candidates = tuple(range(4, w))
    return {
        r: w if r in edge_rows else rng.choice(wall_candidates) for r in rows
    }


def _separated_starts(rows, widths, stops, rng):
    choices = {}
    for r in rows:
        maximum = stops[r] - widths[r] - 1
        if maximum < 0:
            raise ValueError("requested scene leaves no blank sweep corridor")
        values = list(range(maximum + 1))
        rng.shuffle(values)
        choices[r] = values

    assigned = {}

    def place(index):
        if index == len(rows):
            return True
        row = rows[index]
        width = widths[row]
        for start in choices[row]:
            previous = row - 1
            if previous in assigned:
                prev_start = assigned[previous]
                prev_end = prev_start + widths[previous] - 1
                end = start + width - 1
                if not (end < prev_start or prev_end < start):
                    continue
            assigned[row] = start
            if place(index + 1):
                return True
            del assigned[row]
        return False

    if not place(0):
        raise ValueError("could not separate requested row seed runs")
    return assigned


def _general_board(ctx, difficulty, schedule_slot=None):
    h = ctx.draw_choice("grid_h", _weighted_values("grid_h", difficulty))
    w = ctx.draw_choice("grid_w", _weighted_values("grid_w", difficulty))
    active_count = ctx.draw_choice(
        "active_rows", _weighted_values("active_rows", difficulty)
    )
    seed_color = ctx.draw_color("seed_color", exclude={0, 8})
    if schedule_slot == 1:
        seed_mode = ctx.draw_choice("seed_mode", ("connected",))
        wall_mode = ctx.draw_choice("wall_mode", ("shared",))
    elif schedule_slot == 2:
        seed_mode = ctx.draw_choice("seed_mode", ("separated",))
        wall_mode = ctx.draw_choice("wall_mode", ("mixed_edge",))
    elif schedule_slot == 3:
        seed_mode = ctx.draw_choice(
            "seed_mode", ("connected", "separated")
        )
        wall_mode = ctx.draw_choice("wall_mode", ("staggered",))
    else:
        seed_mode = ctx.draw_choice("seed_mode", ("connected", "separated"))
        wall_mode = ctx.draw_choice(
            "wall_mode", ("shared", "staggered", "mixed_edge")
        )
    wide_seed_row = ctx.draw_choice("wide_seed_row", (False, True))
    extra_walls = ctx.draw_choice("extra_walls", (False, True))

    rng = ctx.draw_rng("layout")
    rows = _active_row_positions(h, active_count, seed_mode, rng)
    stops = _wall_stops(rows, w, wall_mode, rng)
    widths = {r: 1 for r in rows}
    if wide_seed_row:
        widths[rng.choice(rows)] = 2

    if seed_mode == "connected":
        maximum = min(stops[r] - widths[r] - 1 for r in rows)
        if maximum < 0:
            raise ValueError("requested scene leaves no blank sweep corridor")
        start = rng.randint(0, maximum)
        starts = {r: start for r in rows}
    else:
        starts = _separated_starts(rows, widths, stops, rng)

    grid = full_grid(h, w, 0)
    for r in rows:
        for c in range(starts[r], starts[r] + widths[r]):
            grid[r][c] = seed_color
        if stops[r] < w:
            grid[r][stops[r]] = 8

    inactive_rows = [r for r in range(h) if r not in set(rows)]
    if extra_walls:
        count = rng.randint(1, len(inactive_rows))
        for r in rng.sample(inactive_rows, count):
            grid[r][rng.randrange(w)] = 8
    return grid


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
    schedule_slot = sample_index % 4 if not overrides else None
    if schedule_slot == 0:
        profile_index = (sample_index // 4) % len(_CANONICAL_PROFILES)
        grid = _canonical_board(ctx, _CANONICAL_PROFILES[profile_index])
    else:
        grid = _general_board(ctx, difficulty, schedule_slot=schedule_slot)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not all(
        isinstance(row, list) for row in grid
    ):
        return ["grid must be a nonempty list of rows"]
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]

    scene = _analyze(grid)
    errors = []
    if not 5 <= scene["h"] <= 10:
        errors.append("grid height must be 5..10")
    if not 8 <= scene["w"] <= 14:
        errors.append("grid width must be 8..14")
    if len(scene["seed_colors"]) != 1:
        errors.append("scene must contain exactly one non-wall seed color")
    if not 2 <= len(scene["active_rows"]) <= 4:
        errors.append("scene must contain colored seeds in two to four rows")
    if scene["seed_mode"] not in ("connected", "separated"):
        errors.append("seed rows must form one connected shape or separate row segments")

    wall_count = sum(bool(columns) for columns in scene["walls_by_row"].values())
    if wall_count == 0:
        errors.append("scene must contain at least one color-8 wall")
    for r, columns in scene["walls_by_row"].items():
        if len(columns) > 1:
            errors.append(f"row {r} may contain at most one wall marker")

    for r in scene["active_rows"]:
        seed_columns = scene["seeds_by_row"][r]
        if tuple(range(seed_columns[0], seed_columns[-1] + 1)) != seed_columns:
            errors.append(f"row {r} seed cells must form one contiguous run")
        if len(seed_columns) > 2:
            errors.append(f"row {r} seed run may contain at most two cells")
        wall_columns = scene["walls_by_row"][r]
        stop = wall_columns[0] if wall_columns else scene["w"]
        if stop <= seed_columns[-1] + 1:
            errors.append(
                f"row {r} must leave at least one blank corridor cell before its wall or edge"
            )
        if wall_columns and wall_columns[0] <= seed_columns[-1]:
            errors.append(f"row {r} wall must be strictly right of its seed run")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze(grid)
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "active_rows": len(scene["active_rows"]),
        "seed_color": scene["seed_colors"][0],
        "seed_mode": scene["seed_mode"],
        "wall_mode": scene["wall_mode"],
        "wide_seed_row": scene["wide_seed_row"],
        "extra_walls": scene["extra_walls"],
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0])
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 8):
                continue
            walls = [x for x in range(c + 1, w) if grid[r][x] == 8]
            stop = walls[0] if walls else w
            for x in range(c, stop):
                if output[r][x] == 0:
                    output[r][x] = value
    return output


def profile_signature(grid):
    if self_check(grid):
        return None
    normalized = tuple(
        tuple(0 if value == 0 else 8 if value == 8 else 1 for value in row)
        for row in grid
    )
    return len(grid), len(grid[0]), normalized


def _profile_signature_from_spec(profile):
    h, w, seed_cells, wall_cells, _ = profile
    grid = full_grid(h, w, 0)
    for r, c in seed_cells:
        grid[r][c] = 1
    for r, c in wall_cells:
        grid[r][c] = 8
    return profile_signature(grid)


CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature_from_spec(profile) for profile in _CANONICAL_PROFILES
)


def is_canonical_profile(grid):
    return profile_signature(grid) in CANONICAL_PROFILE_SIGNATURES
