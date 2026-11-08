"""Generator for ``arc_additional_puzzles_21_set16_bundle:M109``.

The nonzero token at ``(0, 0)`` is a command.  Remove that token, crop the
single interior object, then apply the command-selected dihedral transform:

``1`` identity, ``2`` clockwise rotation, ``3`` 180-degree rotation,
``4`` transpose, ``5`` left/right flip, ``6`` up/down flip, ``7`` transpose,
and ``8`` anti-transpose.

The generator deliberately schedules commands by ``sample_index`` so every
8-demo lesson contains every command.  Ordinary draws include a substantial
canonical-scale, one-color prior, while broader draws vary canvas size and
object palette without changing the task grammar.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e69a3b575440"
VERSION = "2.0.0"
TASK_ID = "e69a3b575440"
RULE_HASH = "8710239f76c6"
EXAMPLES_NEEDED = 8

SUMMARY = (
    "A command token at (0,0) selects a transform. Remove the token, crop the "
    "single connected interior object, and apply command 1=id, 2=cw, 3=180, "
    "4=transpose, 5=flip-lr, 6=flip-ud, 7=transpose, or 8=anti-transpose."
)

INVARIANTS = [
    "the background is black 0 and the command at (0,0) is an integer 1..8",
    "after removing the command there is exactly one 4-connected interior object",
    "the object has a full bounding box at least 2x2 and uses 1..3 colors",
    "the object exposes at least four distinct dihedral views",
    "the selected non-identity command changes the cropped object",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 7..8 prior or difficulty-aware 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 7..8 prior or difficulty-aware 7..14",
        "valid": "7..14",
    },
    "cmd": {
        "type": "int",
        "default": "1 + sample_index mod 8",
        "valid": "1..8",
    },
    "object_color_count": {
        "type": "int",
        "default": "1 on canonical prior; otherwise keyed 1..3",
        "valid": "1..3",
    },
}

_CANONICAL_PROFILES = (
    (7, 7, 2),
    (7, 8, 2),
    (8, 8, 2),
    (8, 8, 3),
)
_CANONICAL_PRIOR = {"easy": 0.70, "medium": 0.55, "hard": 0.40}
_COMMANDS = tuple(range(1, 9))
_AXIS_BOUNDS = {
    "grid_h": (7, 14),
    "grid_w": (7, 14),
    "cmd": (1, 8),
    "object_color_count": (1, 3),
}


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    """Reject scalar coercions before they can alter keyed generation."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for axis, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{axis} override must be an integer (not bool)")
        low, high = _AXIS_BOUNDS[axis]
        if not low <= value <= high:
            raise ValueError(f"{axis} override {value} outside [{low}, {high}]")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket rule is authority."""
    _validate_call(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _CANONICAL_PRIOR else "medium"

    if "cmd" in overrides and overrides["cmd"] is not None:
        cmd = ctx.draw_int("cmd", 1, 8)
    else:
        # Sequential sample indexes now cover all command branches exactly once
        # per 8-demo lesson, while still recording keyed draw provenance.
        cmd = ctx.draw_choice("cmd", [1 + (int(sample_index) % 8)])

    canonical_prior = (
        not overrides
        and cmd <= 4
        and ctx.draw_rng("scene_family").random() < _CANONICAL_PRIOR[band]
    )

    if canonical_prior:
        h, w, total_palette_size = ctx.draw_rng("canonical_profile").choice(
            _CANONICAL_PROFILES
        )
        h = ctx.draw_choice("grid_h", [h])
        w = ctx.draw_choice("grid_w", [w])
        object_color_count = ctx.draw_choice("object_color_count", [1])
    else:
        h = ctx.draw_int_diff("grid_h", 7, 14)
        w = ctx.draw_int_diff("grid_w", 7, 14)
        object_color_count = ctx.draw_int("object_color_count", 1, 3)
        total_palette_size = None

    layout_rng = ctx.draw_rng("layout")
    if canonical_prior:
        size_options = [
            (oh, ow)
            for oh, ow in ((2, 2), (2, 3), (3, 2), (3, 3))
            if oh <= h - 3 and ow <= w - 3
        ]
        object_h, object_w = layout_rng.choice(size_options)
    else:
        cap = {"easy": 4, "medium": 5, "hard": 6}[band]
        object_h = layout_rng.randint(2, min(cap, h - 3))
        object_w = layout_rng.randint(2, min(cap, w - 3))
        # A monochrome 2x2 connected full-bbox object cannot refute the
        # anti-transpose shortcut for command 8.  The canvas always has room
        # for one extra column, so choose a genuinely observable rectangle.
        if cmd == 8 and object_h == object_w == 2:
            object_w = 3

    palette_rng = ctx.draw_rng("object_palette")
    if canonical_prior and total_palette_size == 2:
        palette = [cmd]
    elif canonical_prior:
        palette = [palette_rng.choice([color for color in range(1, 10) if color != cmd])]
    else:
        candidates = list(range(1, 10))
        palette_rng.shuffle(candidates)
        palette = candidates[:object_color_count]
        if palette_rng.random() < 0.35 and cmd not in palette:
            palette[-1] = cmd
        palette = list(dict.fromkeys(palette))
        if len(palette) < object_color_count:
            palette.extend(
                color
                for color in candidates
                if color not in palette
            )
            palette = palette[:object_color_count]

    obj = _make_object(
        object_h,
        object_w,
        palette,
        cmd,
        ctx.draw_rng("object_shape"),
    )
    r0 = layout_rng.randint(2, h - object_h - 1)
    c0 = layout_rng.randint(2, w - object_w - 1)

    grid = full_grid(h, w, 0)
    grid[0][0] = cmd
    for row in range(object_h):
        for col in range(object_w):
            if obj[row][col] != 0:
                grid[r0 + row][c0 + col] = obj[row][col]
    return grid


def _make_object(
    height: int,
    width: int,
    palette: list[int],
    cmd: int,
    rng,
) -> list[list[int]]:
    """Build a connected, full-bbox object that reveals the selected transform."""
    for _attempt in range(256):
        steps = ["d"] * (height - 1) + ["r"] * (width - 1)
        rng.shuffle(steps)
        row = col = 0
        cells = {(row, col)}
        for step in steps:
            if step == "d":
                row += 1
            else:
                col += 1
            cells.add((row, col))
        # Add texture only along the existing component boundary.  Arbitrary
        # Bernoulli cells can create disconnected islands that the structural
        # checker must (correctly) reject.
        for _growth_pass in range(2):
            candidates = [
                (row, col)
                for row in range(height)
                for col in range(width)
                if (row, col) not in cells
                and any(
                    neighbor in cells
                    for neighbor in (
                        (row - 1, col),
                        (row + 1, col),
                        (row, col - 1),
                        (row, col + 1),
                    )
                )
            ]
            rng.shuffle(candidates)
            for cell in candidates:
                if rng.random() < 0.34:
                    cells.add(cell)

        positions = sorted(cells)
        if len(positions) < len(palette):
            continue
        rng.shuffle(positions)
        object_grid = full_grid(height, width, 0)
        for index, (row, col) in enumerate(positions):
            color = palette[index] if index < len(palette) else rng.choice(palette)
            object_grid[row][col] = color

        views = _distinct_views(object_grid)
        selected = _transform(object_grid, cmd)
        discriminates = (
            _rotate_cw(object_grid) != object_grid
            if cmd == 1
            else selected != object_grid
        )
        if len(views) >= 4 and discriminates:
            return object_grid
    raise RuntimeError(
        f"could not construct a transform-revealing {height}x{width} object "
        f"for command {cmd}"
    )


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _anti_transpose(grid: list[list[int]]) -> list[list[int]]:
    return _rotate_180(_transpose(grid))


def _transform(grid: list[list[int]], cmd: int) -> list[list[int]]:
    transforms: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
        1: lambda value: [list(row) for row in value],
        2: _rotate_cw,
        3: _rotate_180,
        4: _transpose,
        5: _flip_lr,
        6: _flip_ud,
        7: _transpose,
        8: _anti_transpose,
    }
    if cmd not in transforms:
        raise ValueError(f"command must be in 1..8, got {cmd!r}")
    return transforms[cmd](grid)


def _distinct_views(grid: list[list[int]]) -> set[tuple[tuple[int, ...], ...]]:
    return {
        tuple(tuple(row) for row in view)
        for view in (
            grid,
            _rotate_cw(grid),
            _rotate_180(grid),
            _transpose(grid),
            _flip_lr(grid),
            _flip_ud(grid),
            _anti_transpose(grid),
        )
    }


def _crop_object(grid: list[list[int]]) -> list[list[int]]:
    cleaned = [list(row) for row in grid]
    cleaned[0][0] = 0
    cells = [
        (row, col)
        for row, values in enumerate(cleaned)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("no object after removing command")
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [values[left : right + 1] for values in cleaned[top : bottom + 1]]


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular and nonempty"]

    height = len(grid)
    if not 7 <= height <= 14:
        errors.append(f"height must be in 7..14, got {height}")
    if not 7 <= width <= 14:
        errors.append(f"width must be in 7..14, got {width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return {}, errors

    cmd = grid[0][0]
    if cmd not in _COMMANDS:
        errors.append(f"command at (0,0) must be in 1..8, got {cmd}")

    object_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    ]
    if not object_cells:
        errors.append("expected one nonempty object after removing the command")
        return {
            "grid_h": height,
            "grid_w": width,
            "cmd": cmd,
            "object_color_count": 0,
        }, errors

    top = min(row for row, _ in object_cells)
    bottom = max(row for row, _ in object_cells)
    left = min(col for _, col in object_cells)
    right = max(col for _, col in object_cells)
    if top < 2 or left < 2:
        errors.append("object must be separated from the command by a blank row and column")
    if bottom > height - 2 or right > width - 2:
        errors.append("object must leave a one-cell bottom and right margin")

    occupied = set(object_cells)
    seen = set()
    queue = deque([next(iter(occupied))])
    while queue:
        cell = queue.popleft()
        if cell in seen:
            continue
        seen.add(cell)
        row, col = cell
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in occupied and neighbor not in seen:
                queue.append(neighbor)
    if seen != occupied:
        errors.append("object cells must form exactly one 4-connected component")

    crop = [values[left : right + 1] for values in grid[top : bottom + 1]]
    object_h = len(crop)
    object_w = len(crop[0])
    if object_h < 2 or object_w < 2:
        errors.append(f"object bounding box must be at least 2x2, got {object_h}x{object_w}")

    object_colors = {grid[row][col] for row, col in object_cells}
    if not 1 <= len(object_colors) <= 3:
        errors.append(f"object must use 1..3 colors, got {len(object_colors)}")

    view_count = len(_distinct_views(crop))
    if view_count < 4:
        errors.append(
            f"object exposes only {view_count} distinct dihedral views; at least 4 required"
        )
    if cmd in _COMMANDS:
        if cmd == 1 and _rotate_cw(crop) == crop:
            errors.append("identity-command scene must still refute an always-rotate shortcut")
        elif cmd != 1 and _transform(crop, cmd) == crop:
            errors.append("selected non-identity transform must visibly change the object")

    facts = {
        "grid_h": height,
        "grid_w": width,
        "cmd": cmd,
        "object_color_count": len(object_colors),
        "object_h": object_h,
        "object_w": object_w,
        "object_cell_count": len(object_cells),
        "total_palette_size": len({value for row in grid for value in row}),
        "distinct_views": view_count,
        "crop": crop,
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "cmd": int(facts["cmd"]),
        "object_color_count": int(facts["object_color_count"]),
    }


def profile_signature(grid) -> dict[str, Any]:
    """Task-linked observable summary used by focused tests and review censuses."""
    facts, errors = _analyze(grid)
    return {"valid": not errors, "errors": errors, **facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes and verify exact overrides."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if facts and requested:
        observed = observe_overrides(grid)
        for axis in AXES:
            if axis in requested and observed.get(axis) != requested[axis]:
                errors.append(
                    f"override {axis} requested {requested[axis]!r}, "
                    f"observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact canonical canvas/palette envelope, not just validity."""
    facts, errors = _analyze(grid)
    if errors:
        return errors
    profile = (
        facts["grid_h"],
        facts["grid_w"],
        facts["total_palette_size"],
    )
    reasons: list[str] = []
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile!r} is outside canonical profiles")
    if facts["cmd"] not in (1, 2, 3, 4):
        reasons.append("canonical examples use command 1..4")
    if facts["object_color_count"] != 1:
        reasons.append("canonical object is monochrome")
    return reasons


def _valid_cmd(grid: Any) -> int | None:
    facts, errors = _analyze(grid)
    return None if errors else int(facts["cmd"])


SEMANTIC_WITNESSES = {
    f"command_{cmd}": (lambda grid, expected=cmd: _valid_cmd(grid) == expected)
    for cmd in _COMMANDS
}


def _rival_ignore_command(grid: list[list[int]]) -> list[list[int]]:
    return _crop_object(grid)


def _rival_always_cw(grid: list[list[int]]) -> list[list[int]]:
    return _rotate_cw(_crop_object(grid))


def _rival_marker_only(grid: list[list[int]]) -> list[list[int]]:
    return [[int(grid[0][0])]]


SEMANTIC_RIVALS = {
    "ignore_command": _rival_ignore_command,
    "always_cw": _rival_always_cw,
}
WITNESS_RIVALS = {
    "command_1": ["always_cw"],
    **{f"command_{cmd}": ["ignore_command"] for cmd in range(2, 9)},
}
LESSON_COMPETITORS = {
    "ignore_command": _rival_ignore_command,
    "always_cw": _rival_always_cw,
    "marker_only": _rival_marker_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require one valid, transform-revealing demonstration for every command."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["lesson must contain a demo list and one query pair"]

    seen_commands: set[int] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        facts, errors = _analyze(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        cmd = int(facts["cmd"])
        seen_commands.add(cmd)
        expected = _transform(facts["crop"], cmd)
        if pair["output"] != expected:
            reasons.append(f"demo {index} does not match command {cmd}")

    missing = sorted(set(_COMMANDS) - seen_commands)
    if missing:
        reasons.append(f"demos omit command(s) {missing}")

    if "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
        return reasons
    query_facts, query_errors = _analyze(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
        return reasons
    query_cmd = int(query_facts["cmd"])
    if query_cmd not in seen_commands:
        reasons.append(f"query command {query_cmd} has no demonstration")
    expected_query = _transform(query_facts["crop"], query_cmd)
    if query["output"] != expected_query:
        reasons.append("query output disagrees with the command mapping")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    """Name the command residue used by the sequential lesson schedule."""
    del seed, difficulty
    return 1 + (int(sample_index) % 8)


SCHEDULE_PROFILES = _COMMANDS


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named task-semantic impostors that the structural checker must reject."""
    no_command = full_grid(8, 8, 0)
    no_command[3][3] = 4
    no_command[3][4] = 4
    no_command[4][3] = 4

    no_object = full_grid(8, 8, 0)
    no_object[0][0] = 2

    disconnected = full_grid(8, 8, 0)
    disconnected[0][0] = 3
    disconnected[3][3] = 4
    disconnected[5][5] = 4

    transform_alias = full_grid(8, 8, 0)
    transform_alias[0][0] = 4
    for row in (3, 4):
        for col in (3, 4):
            transform_alias[row][col] = 6

    border_touch = full_grid(8, 8, 0)
    border_touch[0][0] = 2
    border_touch[1][3] = 6
    border_touch[1][4] = 6
    border_touch[2][3] = 6

    return [
        ("missing_command", no_command),
        ("missing_object", no_object),
        ("disconnected_object", disconnected),
        ("transform_alias_square", transform_alias),
        ("object_touches_command_zone", border_touch),
    ]
