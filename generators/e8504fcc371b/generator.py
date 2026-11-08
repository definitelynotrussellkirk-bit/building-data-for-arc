"""Semantic generator for ARC task e8504fcc371b (Commanded Trail).

A grid contains one command cell and one differently colored seed.  Command
values 1, 2, 3, and 4 mean up, down, left, and right respectively.  Starting
one cell beyond the seed in that direction, paint every zero cell through the
border with the seed color.  The command and seed remain unchanged.

Every generated four-demo lesson covers all four command values and both
command-placement relations; an eight-slot cycle covers their full Cartesian
product.  The query repeats a command on a new layout.  Command placement varies
between the same axis behind the seed and a position off the movement axis, so
marker location cannot stand in for marker value.
"""
from __future__ import annotations

from itertools import permutations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e8504fcc371b"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "72176e994d8a"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A zero-background grid contains exactly one command cell (1=up, 2=down, "
    "3=left, 4=right) and one seed cell colored 5..9. Paint every zero cell "
    "from the seed to the border in the commanded direction with the seed "
    "color, preserving both original cells. Four scheduled demonstrations "
    "cover all command meanings before the query repeats one on a new layout."
)

INVARIANTS = [
    "rectangular 4..10 by 6..14 ARC grid with only colors 0..9",
    "exactly one command cell with value 1, 2, 3, or 4",
    "exactly one seed cell with value 5, 6, 7, 8, or 9",
    "the commanded ray contains at least one cell and is all zero in the input",
    "the command is either behind the seed on the movement axis or off that axis",
    "ordinary four-demo lessons cover all four command-to-direction branches",
]

TRAIL_PROFILES = ("short", "medium", "long")
COMMAND_RELATIONS = ("behind_seed", "off_axis")
_RELATION_SCHEDULE = (
    "behind_seed", "off_axis", "off_axis", "behind_seed",
    "off_axis", "behind_seed", "behind_seed", "off_axis",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = (
    "no_cmd",
    "no_seed",
    "seed_at_edge",
    "cmd_on_ray",
    "extra_seed",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased keyed draw",
        "valid": "4..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased keyed draw",
        "valid": "6..14",
    },
    "code": {
        "type": "int",
        "default": "four-slot lesson schedule",
        "valid": "1..4",
    },
    "seed_color": {
        "type": "color",
        "default": "keyed draw",
        "valid": "5..9",
    },
    "trail_profile": {
        "type": "enum",
        "default": "scheduled feasible profile",
        "valid": "short|medium|long",
    },
    "command_relation": {
        "type": "enum",
        "default": "scheduled relation",
        "valid": "behind_seed|off_axis",
    },
}

_DIR = {
    1: (-1, 0),
    2: (1, 0),
    3: (0, -1),
    4: (0, 1),
}
_CANONICAL_DIRECTIONS = (1, 2, 3, 4)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_BAND_DIMENSIONS = {
    None: ((5, 10), (7, 14)),
    "easy": ((5, 7), (7, 9)),
    "medium": ((6, 9), (8, 11)),
    "hard": ((8, 10), (10, 14)),
}


def _valid_cell(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= 9
    )


def _ray_cells(height: int, width: int, seed_row: int, seed_col: int, code: int):
    drow, dcol = _DIR[code]
    row, col = seed_row + drow, seed_col + dcol
    cells: list[tuple[int, int]] = []
    while 0 <= row < height and 0 <= col < width:
        cells.append((row, col))
        row += drow
        col += dcol
    return cells


def _axis_length(height: int, width: int, code: int) -> int:
    return height if code in (1, 2) else width


def _classify_trail(length: int, axis_length: int) -> str:
    if length == 1:
        return "short"
    if length >= axis_length - 2:
        return "long"
    return "medium"


def _command_relation(
    command_row: int,
    command_col: int,
    seed_row: int,
    seed_col: int,
    code: int,
) -> str | None:
    drow, dcol = _DIR[code]
    if drow:
        if command_col == seed_col and (command_row - seed_row) * drow < 0:
            return "behind_seed"
        if command_col != seed_col:
            return "off_axis"
    else:
        if command_row == seed_row and (command_col - seed_col) * dcol < 0:
            return "behind_seed"
        if command_row != seed_row:
            return "off_axis"
    return None


def _analyse(grid) -> dict:
    errors: list[str] = []
    facts: dict[str, object] = {}
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty list of rows"], "facts": facts}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["every row must be a nonempty list"], "facts": facts}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": facts}
    if any(not _valid_cell(value) for row in grid for value in row):
        errors.append("every cell must be a literal ARC color integer from 0 through 9")

    height = len(grid)
    if not 4 <= height <= 10 or not 6 <= width <= 14:
        errors.append(f"expected dimensions 4..10 by 6..14; got {height}x{width}")

    commands = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in _DIR
    ]
    seeds = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in (5, 6, 7, 8, 9)
    ]
    if len(commands) != 1:
        errors.append(f"expected exactly one command cell, got {len(commands)}")
    if len(seeds) != 1:
        errors.append(f"expected exactly one seed cell, got {len(seeds)}")
    if len(commands) != 1 or len(seeds) != 1:
        return {"errors": errors, "facts": facts}

    command_row, command_col, code = commands[0]
    seed_row, seed_col, seed_color = seeds[0]
    ray = _ray_cells(height, width, seed_row, seed_col, code)
    if not ray:
        errors.append("seed has zero trail length in the command direction")
    if (command_row, command_col) in ray:
        errors.append("command cell lies on the future trail")
    blocked = [
        (row, col, grid[row][col])
        for row, col in ray
        if grid[row][col] != 0
    ]
    if blocked:
        errors.append(f"future trail must be all zero; blocked at {blocked[:3]}")

    relation = _command_relation(
        command_row, command_col, seed_row, seed_col, code
    )
    if relation is None:
        errors.append(
            "command must be behind the seed on the movement axis or off that axis"
        )

    axis_length = _axis_length(height, width, code)
    facts.update(
        {
            "grid_h": height,
            "grid_w": width,
            "code": code,
            "seed_color": seed_color,
            "seed": (seed_row, seed_col),
            "command": (command_row, command_col),
            "ray": tuple(ray),
            "trail_length": len(ray),
            "trail_profile": _classify_trail(len(ray), axis_length) if ray else None,
            "command_relation": relation,
        }
    )
    return {"errors": errors, "facts": facts}


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a lawful returned grid."""
    analysis = _analyse(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "code": int(facts["code"]),
        "seed_color": int(facts["seed_color"]),
        "trail_profile": str(facts["trail_profile"]),
        "command_relation": str(facts["command_relation"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding input scenes."""
    del difficulty
    analysis = _analyse(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    requested = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and observed[axis] != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold: exact cues plus official scale envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 9:
        errors.append(f"canonical height envelope is 6..9, got {height}")
    if not 7 <= width <= 10:
        errors.append(f"canonical width envelope is 7..10, got {width}")
    return errors


def _rule_mirror(grid):
    """Input-pure Python mirror used only by tests and semantic competitors."""
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    output = [list(row) for row in grid]
    for row, col in facts["ray"]:
        if output[row][col] == 0:
            output[row][col] = facts["seed_color"]
    return output


def _locate(grid):
    height, width = len(grid), len(grid[0])
    command = next(
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in _DIR
    )
    seed = next(
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in (5, 6, 7, 8, 9)
    )
    return command, seed


def _paint_direction(
    grid,
    direction: int,
    *,
    paint: int | None = None,
    limit: int | None = None,
):
    output = [list(row) for row in grid]
    _, seed = _locate(grid)
    seed_row, seed_col, seed_color = seed
    color = seed_color if paint is None else paint
    ray = _ray_cells(len(grid), len(grid[0]), seed_row, seed_col, direction)
    if limit is not None:
        ray = ray[:limit]
    for row, col in ray:
        if output[row][col] == 0:
            output[row][col] = color
    return output


def _mapped_rule(grid, mapping: dict[int, int]):
    command, _ = _locate(grid)
    return _paint_direction(grid, mapping[command[2]])


def _nearest_edge_rule(grid):
    _, seed = _locate(grid)
    row, col, _ = seed
    distances = {
        1: row,
        2: len(grid) - 1 - row,
        3: col,
        4: len(grid[0]) - 1 - col,
    }
    direction = min(distances, key=lambda key: (distances[key], key))
    return _paint_direction(grid, direction)


def _both_axis_rule(grid):
    command, _ = _locate(grid)
    first, second = ((1, 2) if command[2] in (1, 2) else (3, 4))
    output = _paint_direction(grid, first)
    # Re-run on the original cue locations while retaining the first ray.
    second_output = _paint_direction(grid, second)
    for row in range(len(output)):
        for col in range(len(output[0])):
            if output[row][col] == 0 and second_output[row][col] != 0:
                output[row][col] = second_output[row][col]
    return output


def _cross_rule(grid):
    output = [list(row) for row in grid]
    _, seed = _locate(grid)
    row, col, color = seed
    for direction in _CANONICAL_DIRECTIONS:
        for rr, cc in _ray_cells(len(grid), len(grid[0]), row, col, direction):
            if output[rr][cc] == 0:
                output[rr][cc] = color
    return output


def _paint_command_color_rule(grid):
    command, _ = _locate(grid)
    return _paint_direction(grid, command[2], paint=command[2])


def _one_step_rule(grid):
    command, _ = _locate(grid)
    return _paint_direction(grid, command[2], limit=1)


def _two_step_rule(grid):
    command, _ = _locate(grid)
    return _paint_direction(grid, command[2], limit=2)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons compatible with plausible rules that change the query."""
    reasons: list[str] = []
    try:
        query_input = query["input"]
        query_answer = query["output"]
    except (KeyError, TypeError):
        return ["query must contain input and output grids"]
    if _rule_mirror(query_input) != query_answer:
        reasons.append("query output disagrees with the commanded-trail rule")

    competitors: list[tuple[str, Callable]] = []
    for mapped in permutations(_CANONICAL_DIRECTIONS):
        if mapped == _CANONICAL_DIRECTIONS:
            continue
        mapping = dict(zip(_CANONICAL_DIRECTIONS, mapped))
        competitors.append(
            (
                "alternative code mapping " + "".join(map(str, mapped)),
                lambda grid, mapping=mapping: _mapped_rule(grid, mapping),
            )
        )
    competitors.extend(
        [
            ("nearest-edge direction", _nearest_edge_rule),
            ("paint both directions on the selected axis", _both_axis_rule),
            ("paint a four-way cross", _cross_rule),
            ("paint with the command value", _paint_command_color_rule),
            ("paint only one step", _one_step_rule),
            ("paint only two steps", _two_step_rule),
        ]
    )

    for name, competitor in competitors:
        try:
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            competing_answer = competitor(query_input)
        except (KeyError, TypeError, StopIteration, ValueError) as exc:
            return [f"competitor audit failed for {name!r}: {type(exc).__name__}: {exc}"]
        if survives and competing_answer != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query"
            )
    return reasons


def _witness_code(expected: int):
    return lambda grid: observe_overrides(grid).get("code") == expected


def _witness_profile(expected: str):
    return lambda grid: observe_overrides(grid).get("trail_profile") == expected


def _witness_relation(expected: str):
    return lambda grid: observe_overrides(grid).get("command_relation") == expected


SEMANTIC_WITNESSES = {
    "code_up": _witness_code(1),
    "code_down": _witness_code(2),
    "code_left": _witness_code(3),
    "code_right": _witness_code(4),
    "short_trail": _witness_profile("short"),
    "medium_trail": _witness_profile("medium"),
    "long_trail": _witness_profile("long"),
    "command_behind_seed": _witness_relation("behind_seed"),
    "command_off_axis": _witness_relation("off_axis"),
}


def _draw_dimension(ctx, overrides, name: str, full_bounds, default_bounds) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, *full_bounds)
    return ctx.draw_int(name, *default_bounds)


def _feasible_lengths(axis_length: int, relation: str, profile: str) -> list[int]:
    maximum = axis_length - (2 if relation == "behind_seed" else 1)
    return [
        length
        for length in range(1, maximum + 1)
        if _classify_trail(length, axis_length) == profile
    ]


def _draw_from_degenerate(name: str):
    height, width = 6, 9
    grid = full_grid(height, width, 0)
    if name == "no_cmd":
        grid[2][3] = 6
    elif name == "no_seed":
        grid[3][5] = 2
    elif name == "seed_at_edge":
        grid[3][0] = 1
        grid[0][4] = 6
    elif name == "cmd_on_ray":
        grid[3][4] = 6
        grid[2][4] = 1
    elif name == "extra_seed":
        grid[0][0] = 4
        grid[3][2] = 6
        grid[5][8] = 9
    else:
        raise ValueError(f"unknown degenerate texture: {name!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(
                f"unknown texture {texture!r}; valid diagnostics: {DEGENERATE_TEXTURES}"
            )
        extra = sorted(
            name for name, value in overrides.items() if name != "texture" and value is not None
        )
        if extra:
            raise ValueError(
                f"degenerate texture {texture!r} cannot be combined with {extra}"
            )
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height_bounds, width_bounds = _BAND_DIMENSIONS[difficulty]
    height = _draw_dimension(ctx, overrides, "grid_h", (4, 10), height_bounds)
    width = _draw_dimension(ctx, overrides, "grid_w", (6, 14), width_bounds)

    if overrides.get("code") is not None:
        code = ctx.draw_int("code", 1, 4)
    else:
        scheduled_code = ((int(seed) + int(sample_index)) % 4) + 1
        code = ctx.draw_int("code", scheduled_code, scheduled_code)

    seed_color = ctx.draw_color("seed_color", exclude=(0, 1, 2, 3, 4))

    if overrides.get("command_relation") is not None:
        relation = ctx.draw_choice("command_relation", COMMAND_RELATIONS)
    else:
        scheduled_relation = _RELATION_SCHEDULE[int(sample_index) % len(_RELATION_SCHEDULE)]
        relation = ctx.draw_choice("command_relation", (scheduled_relation,))

    axis_length = _axis_length(height, width, code)
    feasible_profiles = [
        profile
        for profile in TRAIL_PROFILES
        if _feasible_lengths(axis_length, relation, profile)
    ]
    if overrides.get("trail_profile") is not None:
        profile = ctx.draw_choice("trail_profile", TRAIL_PROFILES)
        if profile not in feasible_profiles:
            raise ValueError(
                f"trail_profile={profile!r} is infeasible for axis_length={axis_length} "
                f"and command_relation={relation!r}"
            )
    else:
        wanted_index = (int(seed) // 4 + int(sample_index)) % len(TRAIL_PROFILES)
        ordered = TRAIL_PROFILES[wanted_index:] + TRAIL_PROFILES[:wanted_index]
        profile = next(candidate for candidate in ordered if candidate in feasible_profiles)
        profile = ctx.draw_choice("trail_profile", (profile,))

    lengths = _feasible_lengths(axis_length, relation, profile)
    ray_length = ctx.draw_rng("trail_length").choice(lengths)
    layout_rng = ctx.draw_rng("layout")
    if code == 1:
        seed_row = ray_length
        seed_col = layout_rng.randrange(width)
    elif code == 2:
        seed_row = height - 1 - ray_length
        seed_col = layout_rng.randrange(width)
    elif code == 3:
        seed_row = layout_rng.randrange(height)
        seed_col = ray_length
    else:
        seed_row = layout_rng.randrange(height)
        seed_col = width - 1 - ray_length

    if relation == "behind_seed":
        drow, dcol = _DIR[code]
        candidates = []
        row, col = seed_row - drow, seed_col - dcol
        while 0 <= row < height and 0 <= col < width:
            candidates.append((row, col))
            row -= drow
            col -= dcol
    elif code in (1, 2):
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if col != seed_col
        ]
    else:
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if row != seed_row
        ]
    if not candidates:
        raise ValueError(
            f"no command placement for {height}x{width}, code={code}, relation={relation}"
        )
    command_row, command_col = layout_rng.choice(candidates)

    grid = full_grid(height, width, 0)
    grid[seed_row][seed_col] = seed_color
    grid[command_row][command_col] = code
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid commanded-trail scene: " + "; ".join(errors))
    return grid
