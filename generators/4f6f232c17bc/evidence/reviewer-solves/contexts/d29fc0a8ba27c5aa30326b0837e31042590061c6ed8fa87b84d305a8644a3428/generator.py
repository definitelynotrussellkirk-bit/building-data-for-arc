"""Constructive sampler for reflection across a full-height gray divider.

The selected Racket rule finds the first full-height color-5 column, starts a
blank output, and mirrors every blue (1) input cell across that column as cyan
(8).  Mirroring is per cell: out-of-bounds targets are clipped.  Every other
input color is a distractor, including isolated off-axis gray cells.

Ordinary lessons deliberately rotate four semantic states so any three of four
consecutive examples retain both source directions and at least one clipping
counterexample.  Every ordinary draw also includes an ignored distractor.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f6f232c17bc"
TASK_ID = GENERATOR_ID
RULE_HASH = "549dba88300b"
VERSION = "3.0.0"
SUMMARY = (
    "A unique full-height gray (5) column is the reflection axis. A connected "
    "blue (1) object lies wholly on either side; each blue cell is reflected "
    "independently to cyan (8) on an otherwise blank output, with out-of-bounds "
    "targets clipped. Non-blue cells, including off-axis gray cells, are ignored."
)

INVARIANTS = [
    "exactly one full-height color-5 divider column",
    "one nonempty 4-connected blue object lies wholly on one side of the divider",
    "at least one reflected blue target is in bounds; full and partial visibility both occur",
    "0..3 observable distractor cells are ignored by the selected rule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-aware 8..10",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-aware 11..14",
        "valid": "11..14",
    },
    "blue_size": {
        "type": "int",
        "default": "difficulty-aware 3..8",
        "valid": "3..8",
    },
    "source_side": {
        "type": "str",
        "default": "four-state schedule alternates left and right",
        "valid": "left|right",
    },
    "mirror_visibility": {
        "type": "str",
        "default": "four-state schedule includes full and partial clipping",
        "valid": "full|partial",
    },
    "n_distractors": {
        "type": "int",
        "default": "canonical-profile schedule or difficulty-aware 1..3",
        "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

_INT_DOMAINS = {
    "grid_h": (8, 10),
    "grid_w": (11, 14),
    "blue_size": (3, 8),
    "n_distractors": (0, 3),
}
_CHOICE_DOMAINS = {
    "source_side": ("left", "right"),
    "mirror_visibility": ("full", "partial"),
}
_ALLOWED_OVERRIDES = frozenset(_INT_DOMAINS) | frozenset(_CHOICE_DOMAINS)

# (height, width, distractor count, distractor color).  These reproduce every
# distinct canonical (height, width, palette-size) profile without replaying a
# canonical grid.  The fifth profile uses off-axis gray, as the official test
# does, and therefore has palette size three.
_CANONICAL_PROFILES = (
    (8, 11, 1, 4),
    (9, 13, 2, 7),
    (10, 12, 1, 6),
    (8, 14, 3, 9),
    (9, 13, 1, 5),
)

# Each cyclic block of four has both source directions and two clipped examples.
# Thus any query rotation leaves three demos containing both directions and at
# least one clipping witness.
_TEACHING_STATES = (
    ("left", "full"),
    ("right", "partial"),
    ("left", "partial"),
    ("right", "full"),
)
_DISTRACTOR_COLORS = (4, 6, 7, 9)


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    for name, options in _CHOICE_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not str or value not in options:
            raise ValueError(f"{name}={value!r} must be one of {options}")


def _difficulty_ranges(difficulty):
    if difficulty == "easy":
        return {
            "grid_h": (8, 9), "grid_w": (11, 13),
            "blue_size": (3, 4), "n_distractors": (1, 1),
        }
    if difficulty == "medium":
        return {
            "grid_h": (8, 10), "grid_w": (11, 14),
            "blue_size": (4, 6), "n_distractors": (1, 2),
        }
    if difficulty == "hard":
        return {
            "grid_h": (9, 10), "grid_w": (12, 14),
            "blue_size": (6, 8), "n_distractors": (2, 3),
        }
    return {
        "grid_h": (8, 10), "grid_w": (11, 14),
        "blue_size": (3, 8), "n_distractors": (1, 3),
    }


def _draw_int(ctx, name, ordinary_bounds):
    bounds = (_INT_DOMAINS[name]
              if name in ctx.overrides and ctx.overrides[name] is not None
              else ordinary_bounds)
    return ctx.draw_int(name, *bounds)


def _draw_choice(ctx, name, ordinary_options):
    options = (_CHOICE_DOMAINS[name]
               if name in ctx.overrides and ctx.overrides[name] is not None
               else ordinary_options)
    return ctx.draw_choice(name, options)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the exact-profile cadence to semantic coverage tooling."""
    del seed, difficulty
    return "canonical_profile" if sample_index % 5 == 0 else "expanded_profile"


SCHEDULE_PROFILES = ("canonical_profile", "expanded_profile")


def _visible_columns(width, divider, side):
    if side == "left":
        return tuple(range(max(0, 2 * divider - (width - 1)), divider))
    return tuple(range(divider + 1, min(width - 1, 2 * divider) + 1))


def _choose_divider(rng, height, width, size, side, visibility, sample_index):
    if visibility == "partial":
        # For a right-side source, columns <= 2*d reflect in bounds and columns
        # > 2*d clip.  The left-side case is its horizontal reflection.
        near_left = tuple(range(2, (width - 2) // 2 + 1))
        if not near_left:
            raise ValueError(f"width {width} cannot support partial clipping")
        base = rng.choice(near_left)
        return base if side == "right" else width - 1 - base

    candidates = []
    for divider in range(2, width - 2):
        columns = _visible_columns(width, divider, side)
        if len(columns) * height >= size:
            candidates.append(divider)
    if not candidates:
        raise ValueError("no constructive full-visibility divider")

    # Retain some true center axes, but most draws are off-center. Partial
    # states are always off-center and already guarantee the center-axis rival
    # is exercised in each teaching window.
    if sample_index % 4 == 0:
        preferred = width // 2
        if preferred in candidates:
            return preferred
    geometric_center = (width - 1) / 2
    off_center = [divider for divider in candidates if divider != geometric_center]
    return rng.choice(off_center or candidates)


def _neighbors(point):
    r, c = point
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _grow_connected(rng, allowed, size, required=()):
    allowed = set(allowed)
    cells = set(required)
    if not cells <= allowed:
        raise ValueError("required blob cells are outside the allowed region")
    if len(cells) > size:
        raise ValueError("required blob is larger than requested blue_size")
    if not cells:
        cells.add(rng.choice(sorted(allowed)))
    while len(cells) < size:
        frontier = sorted({nxt for cell in cells for nxt in _neighbors(cell)
                           if nxt in allowed and nxt not in cells})
        if not frontier:
            raise ValueError(
                f"cannot grow a connected {size}-cell blob in {len(allowed)} cells"
            )
        cells.add(rng.choice(frontier))
    return cells


def _blue_blob(rng, height, width, divider, side, visibility, size):
    side_columns = (range(0, divider) if side == "left"
                    else range(divider + 1, width))
    if visibility == "full":
        columns = _visible_columns(width, divider, side)
        allowed = {(r, c) for r in range(height) for c in columns}
        return _grow_connected(rng, allowed, size)

    allowed = {(r, c) for r in range(height) for c in side_columns}
    row = rng.randrange(height)
    if side == "right":
        visible_col, clipped_col = 2 * divider, 2 * divider + 1
    else:
        visible_col = 2 * divider - (width - 1)
        clipped_col = visible_col - 1
    required = ((row, visible_col), (row, clipped_col))
    return _grow_connected(rng, allowed, size, required=required)


def _blue_output_positions(blue, divider, width):
    return {(r, 2 * divider - c) for r, c in blue
            if 0 <= 2 * divider - c < width}


def _place_distractors(grid, count, color, divider, blue, rng):
    if count == 0:
        return
    height, width = len(grid), len(grid[0])
    blue_output = _blue_output_positions(blue, divider, width)
    free = [(r, c) for r in range(height) for c in range(width)
            if c != divider and grid[r][c] == 0]
    witness_candidates = [
        (r, c) for r, c in free
        if 0 <= 2 * divider - c < width
        and (r, 2 * divider - c) not in blue_output
    ]
    if not witness_candidates:
        raise ValueError("no in-bounds distractor counterexample position")
    chosen = [rng.choice(witness_candidates)]
    remaining = [point for point in free if point not in chosen]
    chosen.extend(rng.sample(remaining, count - 1))
    for r, c in chosen:
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    ranges = _difficulty_ranges(difficulty)

    profile_locked = (
        sample_index % 5 == 0
        and all(overrides.get(name) is None
                for name in ("grid_h", "grid_w", "n_distractors"))
    )
    if profile_locked:
        h0, w0, noise0, color0 = _CANONICAL_PROFILES[
            (sample_index // 5) % len(_CANONICAL_PROFILES)
        ]
        height = ctx.draw_choice("grid_h", (h0,))
        width = ctx.draw_choice("grid_w", (w0,))
        n_distractors = ctx.draw_choice("n_distractors", (noise0,))
        distractor_color = ctx.draw_choice("distractor_color", (color0,))
    else:
        height = _draw_int(ctx, "grid_h", ranges["grid_h"])
        width = _draw_int(ctx, "grid_w", ranges["grid_w"])
        n_distractors = _draw_int(
            ctx, "n_distractors", ranges["n_distractors"]
        )
        distractor_color = ctx.draw_choice(
            "distractor_color", _DISTRACTOR_COLORS
        )

    blue_size = _draw_int(ctx, "blue_size", ranges["blue_size"])
    scheduled_side, scheduled_visibility = _TEACHING_STATES[sample_index % 4]
    source_side = _draw_choice(ctx, "source_side", (scheduled_side,))
    mirror_visibility = _draw_choice(
        ctx, "mirror_visibility", (scheduled_visibility,)
    )

    layout_rng = ctx.draw_rng("layout")
    divider = _choose_divider(
        layout_rng, height, width, blue_size, source_side,
        mirror_visibility, sample_index,
    )
    blue = _blue_blob(
        ctx.draw_rng("blue_blob"), height, width, divider, source_side,
        mirror_visibility, blue_size,
    )

    grid = full_grid(height, width, 0)
    for row in grid:
        row[divider] = 5
    for r, c in blue:
        grid[r][c] = 1
    _place_distractors(
        grid, n_distractors, distractor_color, divider, blue,
        ctx.draw_rng("distractors"),
    )
    return grid


def _rectangular_arc_grid(grid):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9"]
    return (len(grid), width), []


def _divider(grid):
    height, width = len(grid), len(grid[0])
    columns = [c for c in range(width)
               if all(grid[r][c] == 5 for r in range(height))]
    if len(columns) != 1:
        raise ValueError(
            f"expected exactly one full-height 5 divider, found {len(columns)}"
        )
    return columns[0]


def _blue_cells(grid):
    return {(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 1}


def _connected4(cells):
    if not cells:
        return False
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        cell = frontier.pop()
        for nxt in _neighbors(cell):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen == cells


def observe_overrides(grid):
    """Recover every public exact axis from returned pixels."""
    divider = _divider(grid)
    blue = _blue_cells(grid)
    sides = {"left" if c < divider else "right" for _, c in blue}
    source_side = next(iter(sides)) if len(sides) == 1 else "both"
    mirrors = [2 * divider - c for _, c in blue]
    visible = sum(0 <= c < len(grid[0]) for c in mirrors)
    mirror_visibility = (
        "full" if visible == len(blue)
        else "partial" if visible
        else "none"
    )
    n_distractors = sum(
        1
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1) and not (c == divider and value == 5)
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "blue_size": len(blue),
        "source_side": source_side,
        "mirror_visibility": mirror_visibility,
        "n_distractors": n_distractors,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    shape, errors = _rectangular_arc_grid(grid)
    if errors:
        return errors
    height, width = shape
    try:
        divider = _divider(grid)
    except ValueError as exc:
        return [str(exc)]

    blue = _blue_cells(grid)
    findings = []
    if not blue:
        findings.append("expected at least one blue (1) cell")
        return findings
    if not _connected4(blue):
        findings.append("blue cells must form one 4-connected object")
    left = any(c < divider for _, c in blue)
    right = any(c > divider for _, c in blue)
    if left and right:
        findings.append("blue object crosses the divider")
    elif not left and not right:
        findings.append("blue object does not lie on either side of the divider")
    visible = sum(0 <= 2 * divider - c < width for _, c in blue)
    if visible == 0:
        findings.append("all blue reflections are out of bounds")
    return findings


def strict_canonical_like(grid):
    """Lawful instances of the selected task, including per-cell clipping."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python transcription used only by tests and rival hooks."""
    height, width = len(grid), len(grid[0])
    divider = _divider(grid)
    out = full_grid(height, width, 0)
    for r, c in _blue_cells(grid):
        mirror = 2 * divider - c
        if 0 <= mirror < width:
            out[r][mirror] = 8
    return out


def _one_direction(grid, side):
    height, width = len(grid), len(grid[0])
    divider = _divider(grid)
    out = full_grid(height, width, 0)
    for r, c in _blue_cells(grid):
        if (side == "left" and c >= divider) or (side == "right" and c <= divider):
            continue
        mirror = 2 * divider - c
        if 0 <= mirror < width:
            out[r][mirror] = 8
    return out


def _left_source_only(grid):
    return _one_direction(grid, "left")


def _right_source_only(grid):
    return _one_direction(grid, "right")


def _grid_center_axis(grid):
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    for r, c in _blue_cells(grid):
        out[r][width - 1 - c] = 8
    return out


def _all_or_nothing_clipping(grid):
    divider = _divider(grid)
    width = len(grid[0])
    if any(not 0 <= 2 * divider - c < width for _, c in _blue_cells(grid)):
        return full_grid(len(grid), width, 0)
    return rule_mirror(grid)


def _mirror_all_nonbackground(grid):
    height, width = len(grid), len(grid[0])
    divider = _divider(grid)
    out = full_grid(height, width, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 or c == divider:
                continue
            mirror = 2 * divider - c
            if 0 <= mirror < width:
                out[r][mirror] = 8
    return out


def _source_is(grid, side):
    try:
        return observe_overrides(grid)["source_side"] == side
    except (TypeError, IndexError, ValueError):
        return False


def _is_partial(grid):
    try:
        return observe_overrides(grid)["mirror_visibility"] == "partial"
    except (TypeError, IndexError, ValueError):
        return False


def _center_rival_differs(grid):
    try:
        return _grid_center_axis(grid) != rule_mirror(grid)
    except (TypeError, IndexError, ValueError):
        return False


def _distractor_rival_differs(grid):
    try:
        return _mirror_all_nonbackground(grid) != rule_mirror(grid)
    except (TypeError, IndexError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "source_on_left": lambda grid: _source_is(grid, "left"),
    "source_on_right": lambda grid: _source_is(grid, "right"),
    "partial_clipping": _is_partial,
    "divider_not_grid_center": _center_rival_differs,
    "distractors_ignored": _distractor_rival_differs,
}
SEMANTIC_RIVALS = {
    "left_source_only": _left_source_only,
    "right_source_only": _right_source_only,
    "grid_center_axis": _grid_center_axis,
    "all_or_nothing_clipping": _all_or_nothing_clipping,
    "mirror_all_nonbackground": _mirror_all_nonbackground,
}
WITNESS_RIVALS = {
    "source_on_left": ["right_source_only"],
    "source_on_right": ["left_source_only"],
    "partial_clipping": ["all_or_nothing_clipping"],
    "divider_not_grid_center": ["grid_center_axis"],
    "distractors_ignored": ["mirror_all_nonbackground"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {}


def lesson_identifiable(demos, query):
    """Reject a lesson when a declared plausible rival survives its demos."""
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"]
                for pair in demos
            )
            changes_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} evaluation failed: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
