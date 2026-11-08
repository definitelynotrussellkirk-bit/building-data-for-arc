"""Input sampler for reflecting a source shape across a color-9 cross.

The selected Racket authority is unchanged: detect the single full 9-row and
9-column, then copy every source color-1 cell across the row, the column, and
both, painting the three reflected copies color 8.  This file generates inputs
only; semantic rivals below are diagnostics, never label authority.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "77871cecd343"
TASK_ID = GENERATOR_ID
RULE_HASH = "1bad9bf6a465"
VERSION = "2.1.0"
SUMMARY = (
    "A connected 3..8-cell blue shape occupies any one quadrant of a full "
    "maroon cross.  The cross can move one cell from the geometric center; "
    "the rule reflects the shape across the detected cross, not the canvas center."
)

INVARIANTS = [
    "exactly one full color-9 row and one full color-9 column",
    "one 4-connected color-1 source shape of 3..8 cells in exactly one quadrant",
    "all three reflections of every source cell are distinct, in bounds, and initially background",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4

_QUADRANTS = ("top_left", "top_right", "bottom_left", "bottom_right")
_AXES_OFFSETS = (
    (0, 0),
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)
_OLD_QUADRANT_OFFSET_SCHEDULE = {
    "top_left": (0, 0),
    "top_right": (-1, 1),
    "bottom_left": (1, 0),
    "bottom_right": (0, -1),
}
_DIFFICULTY_DIMS = {
    None: ((9, 9), (9, 11), (11, 9), (11, 11), (13, 9), (9, 13)),
    "easy": ((9, 9), (9, 11), (11, 9), (11, 11), (13, 9), (9, 13)),
    "medium": ((9, 9), (9, 11), (11, 9), (11, 11), (13, 11), (11, 13)),
    "hard": ((9, 9), (9, 11), (11, 9), (13, 13), (15, 13), (13, 15)),
}
_DIFFICULTY_CELLS = {
    None: (4, 5, 6, 5),
    "easy": (3, 4, 5, 4),
    "medium": (4, 5, 6, 5),
    "hard": (6, 7, 8, 7),
}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9..15; canonical sizes frequent", "valid": "9..15"},
    "grid_w": {"type": "int", "default": "scheduled 9..15; canonical sizes frequent", "valid": "9..15"},
    "row_offset": {"type": "int", "default": "joint cycle covers all -1..1 offsets", "valid": "-1..1"},
    "col_offset": {"type": "int", "default": "joint cycle covers all -1..1 offsets", "valid": "-1..1"},
    "source_quadrant": {
        "type": "str",
        "default": "cycle all four quadrants",
        "valid": "|".join(_QUADRANTS),
    },
    "shape_cells": {"type": "int", "default": "difficulty schedule 3..8", "valid": "3..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    int_ranges = {
        "grid_h": (9, 15),
        "grid_w": (9, 15),
        "row_offset": (-1, 1),
        "col_offset": (-1, 1),
        "shape_cells": (3, 8),
    }
    for name, (lo, hi) in int_ranges.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    value = overrides.get("source_quadrant")
    if value is not None and value not in _QUADRANTS:
        raise ValueError(f"source_quadrant must be one of {_QUADRANTS}, not {value!r}")


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _connected_shape(rng, height: int, width: int, count: int) -> tuple[tuple[int, int], ...]:
    """Grow an exact-size 4-connected set inside the available source quadrant."""
    if count > height * width:
        raise ValueError(f"shape_cells={count} does not fit {height}x{width} source region")
    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < count:
        frontier = set()
        for r, c in cells:
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in cells:
                    frontier.add((nr, nc))
        if not frontier:
            raise RuntimeError("connected-shape frontier unexpectedly exhausted")
        cells.add(rng.choice(sorted(frontier)))
    return tuple(sorted(cells))


def _place_shape(
    grid: list[list[int]],
    axis_r: int,
    axis_c: int,
    quadrant: str,
    shape: Iterable[tuple[int, int]],
) -> None:
    top = quadrant.startswith("top")
    left = quadrant.endswith("left")
    for local_r, local_c in shape:
        distance_r, distance_c = local_r + 1, local_c + 1
        r = axis_r - distance_r if top else axis_r + distance_r
        c = axis_c - distance_c if left else axis_c + distance_c
        if grid[r][c] != 0:
            raise RuntimeError("constructive source placement collided")
        grid[r][c] = 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in _DIFFICULTY_DIMS:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    if type(sample_index) is not int or isinstance(sample_index, bool):
        raise ValueError("sample_index must be an integer")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _DIFFICULTY_DIMS[difficulty][sample_index % len(_DIFFICULTY_DIMS[difficulty])]
    h = _draw_scheduled_int(ctx, "grid_h", profile[0], 9, 15)
    w = _draw_scheduled_int(ctx, "grid_w", profile[1], 9, 15)
    scheduled_row, scheduled_col = _AXES_OFFSETS[sample_index % len(_AXES_OFFSETS)]
    row_offset = _draw_scheduled_int(ctx, "row_offset", scheduled_row, -1, 1)
    col_offset = _draw_scheduled_int(ctx, "col_offset", scheduled_col, -1, 1)
    quadrant = _draw_scheduled_choice(
        ctx,
        "source_quadrant",
        _QUADRANTS[sample_index % len(_QUADRANTS)],
        _QUADRANTS,
    )
    scheduled_cells = _DIFFICULTY_CELLS[difficulty][sample_index % len(_DIFFICULTY_CELLS[difficulty])]
    shape_cells = _draw_scheduled_int(ctx, "shape_cells", scheduled_cells, 3, 8)

    axis_r = h // 2 + row_offset
    axis_c = w // 2 + col_offset
    radius_r = min(axis_r, h - 1 - axis_r)
    radius_c = min(axis_c, w - 1 - axis_c)
    if radius_r < 3 or radius_c < 3:
        raise RuntimeError("declared dimensions/offsets must leave at least a 3x3 source region")

    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[axis_r][c] = 9
    for r in range(h):
        grid[r][axis_c] = 9
    shape = _connected_shape(ctx.draw_rng("source_shape"), radius_r, radius_c, shape_cells)
    _place_shape(grid, axis_r, axis_c, quadrant, shape)
    return grid


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, (list, tuple))
        and grid
        and isinstance(grid[0], (list, tuple))
        and grid[0]
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    pending = set(cells)
    if not pending:
        return False
    seen = {next(iter(pending))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in pending and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == pending


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts.update(grid_h=h, grid_w=w)
    if not 9 <= h <= 15 or not 9 <= w <= 15:
        errors.append(f"grid dimensions {h}x{w} outside 9..15 x 9..15")

    colors = {value for row in grid for value in row}
    if not colors <= {0, 1, 9}:
        errors.append(f"input colors must be a subset of {{0,1,9}}, found {sorted(colors)}")

    full_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(full_rows) != 1 or len(full_cols) != 1:
        errors.append(f"expected one full color-9 row/column, found rows={full_rows}, cols={full_cols}")
        return facts
    axis_r, axis_c = full_rows[0], full_cols[0]
    facts.update(axis_r=axis_r, axis_c=axis_c)
    row_offset, col_offset = axis_r - h // 2, axis_c - w // 2
    facts.update(row_offset=row_offset, col_offset=col_offset)
    if not -1 <= row_offset <= 1 or not -1 <= col_offset <= 1:
        errors.append(f"cross offsets {(row_offset, col_offset)} outside [-1,1]^2")

    stray_nines = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9 and r != axis_r and c != axis_c
    ]
    if stray_nines:
        errors.append(f"stray color-9 cells outside the cross: {stray_nines[:5]}")

    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    facts["shape_cells"] = len(ones)
    if not 3 <= len(ones) <= 8:
        errors.append(f"source shape has {len(ones)} cells; expected 3..8")
    if any(r == axis_r or c == axis_c for r, c in ones):
        errors.append("source cells must be strictly off both cross axes")

    quadrants = {
        ("top" if r < axis_r else "bottom") + "_" + ("left" if c < axis_c else "right")
        for r, c in ones
        if r != axis_r and c != axis_c
    }
    if len(quadrants) != 1:
        errors.append(f"source cells must occupy exactly one quadrant, found {sorted(quadrants)}")
    else:
        facts["source_quadrant"] = next(iter(quadrants))
    if ones and not _connected(ones):
        errors.append("source shape must be 4-connected")

    blocked_targets = []
    for r, c in ones:
        for rr, cc in ((r, 2 * axis_c - c), (2 * axis_r - r, c), (2 * axis_r - r, 2 * axis_c - c)):
            if not (0 <= rr < h and 0 <= cc < w):
                blocked_targets.append((rr, cc, "out_of_bounds"))
            elif grid[rr][cc] != 0:
                blocked_targets.append((rr, cc, f"occupied_by_{grid[rr][cc]}"))
    if blocked_targets:
        errors.append(f"reflected targets must be distinct in-bounds background: {blocked_targets[:5]}")
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar advertised by this sampler."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """All lawful cross-reflection instances are task-canonical in semantics."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every advertised exact control from returned pixels."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError(f"cannot observe invalid grid: {facts['errors']}")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "row_offset": facts["row_offset"],
        "col_offset": facts["col_offset"],
        "source_quadrant": facts["source_quadrant"],
        "shape_cells": facts["shape_cells"],
    }


def _axes(grid: list[list[int]]) -> tuple[int, int]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError(f"invalid cross-reflection input: {facts['errors']}")
    return facts["axis_r"], facts["axis_c"]


def _reflect_about(grid, guessed_r: int, guessed_c: int):
    """Diagnostic reflection helper; the Racket program remains label authority."""
    axis_r, axis_c = _axes(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            for rr, cc in (
                (r, 2 * guessed_c - c),
                (2 * guessed_r - r, c),
                (2 * guessed_r - r, 2 * guessed_c - c),
            ):
                if 0 <= rr < h and 0 <= cc < w and rr != axis_r and cc != axis_c:
                    out[rr][cc] = 8
    return out


def _assume_centered_cross(grid):
    """RIVAL, not authority: reflect around the canvas center, ignoring the 9-cross."""
    return _reflect_about(grid, len(grid) // 2, len(grid[0]) // 2)


def _quadrant_offset_guess(facts: dict[str, Any]) -> tuple[int, int]:
    # Canonical boards are centered, so this shortcut first special-cases them.
    if facts["row_offset"] == 0 and facts["col_offset"] == 0:
        return 0, 0
    return _OLD_QUADRANT_OFFSET_SCHEDULE[facts["source_quadrant"]]


def _assume_quadrant_offset_schedule(grid):
    """RIVAL: infer off-center axes from source quadrant, not from the 9-cross."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError(f"invalid cross-reflection input: {facts['errors']}")
    row_offset, col_offset = _quadrant_offset_guess(facts)
    return _reflect_about(
        grid,
        len(grid) // 2 + row_offset,
        len(grid[0]) // 2 + col_offset,
    )


def _off_center_cross(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and (facts["row_offset"] != 0 or facts["col_offset"] != 0)


def _off_quadrant_schedule(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and (
        (facts["row_offset"], facts["col_offset"]) != _quadrant_offset_guess(facts)
    )


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when any declared canonical rival survives demos but changes query."""
    errors = []
    for name, rival in LESSON_COMPETITORS.items():
        survives_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        changes_query = rival(query["input"]) != query["output"]
        if survives_demos and changes_query:
            errors.append(f"all demos leave {name!r} alive, but it changes the query answer")
    return errors


SEMANTIC_WITNESSES = {
    "off_center_cross": _off_center_cross,
    "off_quadrant_schedule": _off_quadrant_schedule,
}
SEMANTIC_RIVALS = {
    "assume_centered_cross": _assume_centered_cross,
    "assume_quadrant_offset_schedule": _assume_quadrant_offset_schedule,
}
WITNESS_RIVALS = {
    "off_center_cross": ["assume_centered_cross"],
    "off_quadrant_schedule": ["assume_quadrant_offset_schedule"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
