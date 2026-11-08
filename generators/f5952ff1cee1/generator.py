"""Generator for bank task H124 / f5952ff1cee1.

A red source on one edge emits a cyan ray inward. The ray paints each visited
cell, turns on slash/backslash mirrors, and stops before a gray stopper or
after reaching the opposite grid boundary.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f5952ff1cee1"
VERSION = "3.0.0"
TASK_ID = "f5952ff1cee1"
RULE_HASH = "eb0f3f3b55d2"

SUMMARY = (
    "Construct one simple orthogonal beam route from a non-corner edge "
    "source through one to three active 6/7 mirrors. The ray ends at the "
    "boundary or, less often, immediately before an active 5 stopper. Up to "
    "three off-route mirrors or stoppers may act as genuine decoys."
)

INVARIANTS = [
    "zero is background and exactly one color-2 source is on a non-corner edge",
    "the source emits inward and the visited route is nonempty and simple",
    "every lesson has one through three active color-6 or color-7 mirrors",
    "the ray terminates at the boundary or immediately before a color-5 stopper",
    "zero through three additional 5/6/7 cells may be off-route decoys",
    "the output is zero except for color 8 on every visited ray cell",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_EDGES = ("top", "bottom", "left", "right")
_TERMINATIONS = ("boundary", "stopper")
_PROFILE_PRIOR = 0.10
_MAX_FUEL = 500

AXES = {
    "edge": {
        "type": "str",
        "default": "difficulty-independent choice",
        "valid": "top|bottom|left|right",
    },
    "turn_count": {
        "type": "int",
        "default": "difficulty-aware 1..3",
        "valid": "1..3",
    },
    "termination": {
        "type": "str",
        "default": "mostly boundary",
        "valid": "boundary|stopper",
    },
}

# Complete public input scenes represented sparsely. These five scenes cover
# all four source edges, one through three active turns, and zero through two
# off-route objects. A lawful D4 transform must also transform mirror slope,
# so 6 and 7 swap after each quarter-turn or horizontal reflection.
_PROFILE_SCENES = (
    (
        8,
        10,
        (
            (0, 2, 2),
            (3, 2, 6),
            (3, 7, 7),
        ),
    ),
    (
        9,
        11,
        (
            (1, 3, 5),
            (5, 3, 7),
            (5, 8, 6),
            (8, 8, 2),
        ),
    ),
    (
        10,
        12,
        (
            (4, 0, 2),
            (4, 4, 6),
            (7, 4, 6),
            (7, 9, 7),
        ),
    ),
    (
        9,
        10,
        (
            (2, 9, 2),
            (2, 6, 7),
            (6, 0, 5),
            (6, 2, 6),
            (6, 6, 7),
        ),
    ),
    (
        10,
        12,
        (
            (2, 8, 7),
            (6, 3, 6),
            (6, 8, 6),
            (9, 3, 2),
        ),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    turn_count = overrides.get("turn_count")
    if turn_count is not None and (
        type(turn_count) is not int or not 1 <= turn_count <= 3
    ):
        raise ValueError("turn_count must be an integer in [1, 3]")
    edge = overrides.get("edge")
    if edge is not None and (
        type(edge) is not str or edge not in _EDGES
    ):
        raise ValueError("edge must be top, bottom, left, or right")
    termination = overrides.get("termination")
    if termination is not None and (
        type(termination) is not str
        or termination not in _TERMINATIONS
    ):
        raise ValueError("termination must be boundary or stopper")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _edge_and_direction(source, height, width):
    row, col = source
    if row == 0 and 0 < col < width - 1:
        return "top", (1, 0)
    if row == height - 1 and 0 < col < width - 1:
        return "bottom", (-1, 0)
    if col == 0 and 0 < row < height - 1:
        return "left", (0, 1)
    if col == width - 1 and 0 < row < height - 1:
        return "right", (0, -1)
    return None, None


def _turned_direction(direction, mirror):
    dr, dc = direction
    if mirror == 7:
        return -dc, -dr
    if mirror == 6:
        return dc, dr
    return direction


def _trace(grid):
    height = len(grid)
    width = len(grid[0])
    sources = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    if len(sources) != 1:
        return None, ["exactly one color-2 source is required"]
    source = sources[0]
    edge, direction = _edge_and_direction(source, height, width)
    if edge is None:
        return None, ["the source must occupy one non-corner edge cell"]

    row, col = source
    dr, dc = direction
    path = []
    active_mirrors = []
    states = set()
    repeated_state = False
    termination = "fuel"
    stopper = None
    for _step in range(_MAX_FUEL):
        state = row, col, dr, dc
        if state in states:
            repeated_state = True
        states.add(state)
        next_row = row + dr
        next_col = col + dc
        if not (
            0 <= next_row < height and 0 <= next_col < width
        ):
            termination = "boundary"
            break
        if grid[next_row][next_col] == 5:
            termination = "stopper"
            stopper = next_row, next_col
            break
        row, col = next_row, next_col
        path.append((row, col))
        value = grid[row][col]
        if value in (6, 7):
            active_mirrors.append((row, col, value))
            dr, dc = _turned_direction((dr, dc), value)

    active_positions = {
        (row, col) for row, col, _value in active_mirrors
    }
    decoys = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if (
            grid[row][col] in (5, 6, 7)
            and (row, col) not in active_positions
            and (row, col) != stopper
        )
    ]
    output = full_grid(height, width, 0)
    for path_row, path_col in path:
        output[path_row][path_col] = 8
    return {
        "source": source,
        "edge": edge,
        "initial_direction": direction,
        "path": tuple(path),
        "active_mirrors": tuple(active_mirrors),
        "turn_count": len(active_mirrors),
        "termination": termination,
        "stopper": stopper,
        "decoys": tuple(decoys),
        "repeated_state": repeated_state,
        "self_intersection": len(path) != len(set(path)),
        "output": output,
    }, []


def _scene_analysis(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, None, ["grid must be a non-empty list or tuple"]
    if not all(
        isinstance(row, (list, tuple, str)) and row for row in grid
    ):
        return None, None, [
            "rows must be non-empty lists, tuples, or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]
    height = len(coerced)
    errors = []
    if not 8 <= height <= 20 or not 8 <= width <= 20:
        errors.append("grid dimensions must be between 8 and 20")
    if any(
        type(value) is not int or value not in (0, 2, 5, 6, 7)
        for row in coerced
        for value in row
    ):
        errors.append("cells must use only colors 0, 2, 5, 6, and 7")
        return coerced, None, errors
    trace, trace_errors = _trace(coerced)
    errors.extend(trace_errors)
    if trace is None:
        return coerced, None, errors
    if len(trace["path"]) < 3:
        errors.append("the ray must visit at least three cells")
    if not 1 <= trace["turn_count"] <= 3:
        errors.append("the ray must hit one through three active mirrors")
    if trace["termination"] not in _TERMINATIONS:
        errors.append("the ray must terminate at a boundary or stopper")
    if trace["repeated_state"] or trace["self_intersection"]:
        errors.append("the ray route must be simple and non-looping")
    if not 0 <= len(trace["decoys"]) <= 3:
        errors.append("there must be zero through three off-route decoys")
    if errors:
        return coerced, None, errors
    return coerced, {
        "height": height,
        "width": width,
        "source": trace["source"],
        "edge": trace["edge"],
        "path": trace["path"],
        "path_length": len(trace["path"]),
        "active_mirrors": trace["active_mirrors"],
        "turn_count": trace["turn_count"],
        "termination": trace["termination"],
        "stopper": trace["stopper"],
        "decoys": trace["decoys"],
        "decoy_count": len(trace["decoys"]),
        "output": trace["output"],
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "edge": features["edge"],
        "turn_count": features["turn_count"],
        "termination": features["termination"],
    }


def rule_mirror(grid):
    coerced = _coerce_grid(grid)
    trace, errors = _trace(coerced)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    return [row[:] for row in trace["output"]]


def _sparse_scene(specification):
    height, width, cells = specification
    grid = full_grid(height, width, 0)
    for row, col, value in cells:
        grid[row][col] = value
    return grid


def _swap_mirrors(grid):
    return [
        [
            7 if value == 6 else 6 if value == 7 else value
            for value in row
        ]
        for row in grid
    ]


def _rotate_scene_90(grid):
    rotated = [list(row) for row in zip(*grid[::-1])]
    return _swap_mirrors(rotated)


def _reflect_scene(grid):
    return _swap_mirrors([row[::-1] for row in grid])


def _d4_scenes(grid):
    current = _coerce_grid(grid)
    variants = []
    for _turn in range(4):
        variants.append([row[:] for row in current])
        variants.append(_reflect_scene(current))
        current = _rotate_scene_90(current)
    return tuple(variants)


_PROFILE_GRIDS = tuple(_sparse_scene(spec) for spec in _PROFILE_SCENES)


def _answer_bearing_signature(grid):
    coerced = _coerce_grid(grid)
    trace, errors = _trace(coerced)
    if errors:
        return None
    signature = full_grid(len(coerced), len(coerced[0]), 0)
    source_row, source_col = trace["source"]
    signature[source_row][source_col] = 2
    for row, col, color in trace["active_mirrors"]:
        signature[row][col] = color
    if trace["stopper"] is not None:
        row, col = trace["stopper"]
        signature[row][col] = 5
    return tuple(tuple(row) for row in signature)


_PROFILE_SIGNATURE_TO_INDEX = {
    _answer_bearing_signature(variant): index
    for index, source in enumerate(_PROFILE_GRIDS)
    for variant in _d4_scenes(source)
}


def canonical_profile_index(grid):
    return _PROFILE_SIGNATURE_TO_INDEX.get(
        _answer_bearing_signature(grid)
    )


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _source_position(edge, height, width, rng):
    if edge == "top":
        return 0, rng.randint(1, width - 2)
    if edge == "bottom":
        return height - 1, rng.randint(1, width - 2)
    if edge == "left":
        return rng.randint(1, height - 2), 0
    return rng.randint(1, height - 2), width - 1


def _distance_to_edge(position, direction, height, width):
    row, col = position
    dr, dc = direction
    if dr == 1:
        return height - 1 - row
    if dr == -1:
        return row
    if dc == 1:
        return width - 1 - col
    return col


def _segment(position, direction, distance):
    row, col = position
    dr, dc = direction
    return tuple(
        (row + dr * step, col + dc * step)
        for step in range(1, distance + 1)
    )


def _search_route(
    position,
    direction,
    remaining_turns,
    termination,
    height,
    width,
    used,
    rng,
):
    distance_to_edge = _distance_to_edge(
        position, direction, height, width
    )
    if remaining_turns == 0:
        if termination == "boundary":
            path = _segment(position, direction, distance_to_edge)
            if any(cell in used for cell in path):
                return None
            return path, (), None
        distances = list(range(2, distance_to_edge + 1))
        rng.shuffle(distances)
        for distance in distances:
            cells = _segment(position, direction, distance)
            path = cells[:-1]
            stopper = cells[-1]
            if stopper in used or any(cell in used for cell in path):
                continue
            return path, (), stopper
        return None

    distances = list(range(2, distance_to_edge))
    rng.shuffle(distances)
    for distance in distances:
        segment = _segment(position, direction, distance)
        if any(cell in used for cell in segment):
            continue
        mirror_position = segment[-1]
        mirror_colors = [6, 7]
        rng.shuffle(mirror_colors)
        for mirror_color in mirror_colors:
            next_direction = _turned_direction(
                direction, mirror_color
            )
            if _distance_to_edge(
                mirror_position,
                next_direction,
                height,
                width,
            ) < 2:
                continue
            result = _search_route(
                mirror_position,
                next_direction,
                remaining_turns - 1,
                termination,
                height,
                width,
                used.union(segment),
                rng,
            )
            if result is None:
                continue
            tail, mirrors, stopper = result
            mirror = (
                mirror_position[0],
                mirror_position[1],
                mirror_color,
            )
            return segment + tail, (mirror,) + mirrors, stopper
    return None


def _construct_route(
    height,
    width,
    edge,
    turn_count,
    termination,
    decoy_count,
    rng,
):
    for _attempt in range(120):
        source = _source_position(edge, height, width, rng)
        _edge, direction = _edge_and_direction(
            source, height, width
        )
        result = _search_route(
            source,
            direction,
            turn_count,
            termination,
            height,
            width,
            {source},
            rng,
        )
        if result is None:
            continue
        path, mirrors, stopper = result
        grid = full_grid(height, width, 0)
        grid[source[0]][source[1]] = 2
        for row, col, color in mirrors:
            grid[row][col] = color
        if stopper is not None:
            grid[stopper[0]][stopper[1]] = 5

        excluded = set(path)
        excluded.add(source)
        if stopper is not None:
            excluded.add(stopper)
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if (row, col) not in excluded
        ]
        rng.shuffle(candidates)
        if len(candidates) < decoy_count:
            continue
        decoy_colors = [5, 6, 7]
        rng.shuffle(decoy_colors)
        for index in range(decoy_count):
            row, col = candidates[index]
            grid[row][col] = decoy_colors[index % len(decoy_colors)]
        return grid
    raise RuntimeError(
        "could not construct a simple beam route for the requested axes"
    )


def _draw_profile(index, rng):
    variants = _d4_scenes(_PROFILE_GRIDS[index])
    source = [row[:] for row in rng.choice(variants)]
    trace, errors = _trace(source)
    if errors:
        raise AssertionError(errors)
    grid = full_grid(len(source), len(source[0]), 0)
    source_row, source_col = trace["source"]
    grid[source_row][source_col] = 2
    for row, col, color in trace["active_mirrors"]:
        grid[row][col] = color
    if trace["stopper"] is not None:
        row, col = trace["stopper"]
        grid[row][col] = 5

    excluded = set(trace["path"])
    excluded.add(trace["source"])
    if trace["stopper"] is not None:
        excluded.add(trace["stopper"])
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if (row, col) not in excluded
    ]
    rng.shuffle(candidates)
    decoy_count = rng.choice((0, 1, 1, 2, 2, 3, 3))
    decoy_colors = [5, 6, 7]
    rng.shuffle(decoy_colors)
    for decoy_index in range(decoy_count):
        row, col = candidates[decoy_index]
        grid[row][col] = decoy_colors[
            decoy_index % len(decoy_colors)
        ]
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
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_GRIDS))),
            )

    if profile_index is not None:
        grid = _draw_profile(
            profile_index,
            ctx.draw_rng("profile_transform"),
        )
        _coerced, features, errors = _scene_analysis(grid)
        if errors:
            raise AssertionError(
                "generated invalid profile: " + "; ".join(errors)
            )
        for label in ("edge", "turn_count", "termination"):
            ctx.draw_choice(label, (observe_overrides(grid)[label],))
    else:
        configuration_rng = ctx.draw_rng("configuration")
        dimension_ranges = {
            "easy": (8, 12),
            "medium": (10, 16),
            "hard": (14, 20),
        }
        decoy_ranges = {
            "easy": (0, 1),
            "medium": (1, 2),
            "hard": (2, 3),
        }
        dimension_lo, dimension_hi = dimension_ranges[band]
        height = configuration_rng.randint(
            dimension_lo, dimension_hi
        )
        width = configuration_rng.randint(
            dimension_lo, dimension_hi
        )
        edge = ctx.draw_choice("edge", _EDGES)
        turn_options = {
            "easy": (1, 1, 2),
            "medium": (1, 2, 2, 3),
            "hard": (2, 3, 3),
        }[band]
        if overrides.get("turn_count") is not None:
            turn_options = (1, 2, 3)
        turn_count = ctx.draw_choice("turn_count", turn_options)
        termination = ctx.draw_choice(
            "termination",
            ("boundary",) * 5 + ("stopper",),
        )
        decoy_count = configuration_rng.randint(
            *decoy_ranges[band]
        )
        grid = _construct_route(
            height,
            width,
            edge,
            turn_count,
            termination,
            decoy_count,
            ctx.draw_rng("route"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
