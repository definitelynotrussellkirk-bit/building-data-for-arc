"""Input sampler for the two-dot horizontal frame task df3c6021b715.

The selected Racket program remains label authority.  This sampler supplies a
small canonical-profile anchor plus counterexamples to the three shortcuts
that fit every canonical pair: fixed dot rows, sorting the two colours, and a
hard-coded row-5 half split.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df3c6021b715"
TASK_ID = GENERATOR_ID
RULE_HASH = "77666531c7cb"
VERSION = "3.0.0"
SUMMARY = (
    "Exactly two distinct nonzero interior dots: one at row < floor(h/2) and "
    "one at row >= floor(h/2).  The selected rule paints the top edge, the upper dot row, and "
    "upper side columns in the upper dot colour; it paints the lower dot row, "
    "bottom edge, and lower side columns in the lower dot colour."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid dimensions are 8..18",
    "background is integer colour 0",
    "exactly two interior nonzero cells with distinct colours 1..9",
    "exactly one dot has row < floor(h/2) and one has row >= floor(h/2)",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8..18 with a 10 anchor", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "scheduled 8..18 with a 10 anchor", "valid": "8..18"},
    "color_pair": {"type": "int", "default": "ordered distinct pair index", "valid": "0..71"},
    "upper_row_slot": {"type": "int", "default": "scheduled", "valid": "0..2"},
    "lower_row_slot": {"type": "int", "default": "scheduled", "valid": "0..2"},
    "upper_col_slot": {"type": "int", "default": "uniform", "valid": "0..4"},
    "lower_col_slot": {"type": "int", "default": "uniform", "valid": "0..4"},
}
# Every joint assignment is constructive for dimensions 8..18.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "reversed_outer_rows",
    "reversed_inner_rows",
    "reversed_cross_rows",
)

_COLOR_PAIRS = tuple(
    (upper, lower)
    for upper in range(1, 10)
    for lower in range(1, 10)
    if upper != lower
)
_PAIR_INDEX = {pair: index for index, pair in enumerate(_COLOR_PAIRS)}
_ASCENDING_PAIRS = tuple(index for index, pair in enumerate(_COLOR_PAIRS) if pair[0] < pair[1])
_REVERSED_PAIRS = tuple(index for index, pair in enumerate(_COLOR_PAIRS) if pair[0] > pair[1])

_BROAD_HEIGHTS = {
    # Default teaching profiles avoid heights 10 and 11 because both have the
    # canonical examples' row-5 split.  Exact overrides still cover every
    # advertised height, including 10 and 11.
    None: (8, 9, 12, 13, 14, 15, 16, 17, 18),
    "easy": (8, 9, 12),
    "medium": (9, 12, 13, 14, 15),
    "hard": (14, 15, 16, 17, 18),
}
_BROAD_WIDTHS = {
    None: tuple(range(8, 19)),
    "easy": (8, 9, 10, 11, 12),
    "medium": (10, 11, 12, 13, 14, 15, 16),
    "hard": (14, 15, 16, 17, 18),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the default four-step teaching schedule; explicit axes still win."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (8, 18),
        "grid_w": (8, 18),
        "color_pair": (0, len(_COLOR_PAIRS) - 1),
        "upper_row_slot": (0, 2),
        "lower_row_slot": (0, 2),
        "upper_col_slot": (0, 4),
        "lower_col_slot": (0, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool, float, or string)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name, lo, hi, defaults):
    """Honor the full exact domain when pinned; otherwise use scheduled choices."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(defaults))


def _upper_rows(h):
    # The packet's Racket DSL uses integer division for (/ h 2).
    hi = h // 2 - 1
    return (1, (1 + hi) // 2, hi)


def _lower_rows(h):
    lo, hi = h // 2, h - 2
    return (lo, (lo + hi + 1) // 2, hi)


def _columns(w):
    lo, hi = 1, w - 2
    span = hi - lo
    return tuple(lo + (slot * span) // 4 for slot in range(5))


def _profile_defaults(profile, difficulty):
    if profile == "canonical_anchor":
        return {
            "grid_h": (10,),
            "grid_w": (10,),
            "color_pair": _ASCENDING_PAIRS,
            "upper_row_slot": (1,),
            "lower_row_slot": (1,),
            "upper_col_slot": range(5),
            "lower_col_slot": range(5),
        }
    row_slots = {
        "reversed_outer_rows": ((0,), (2,)),
        "reversed_inner_rows": ((2,), (0,)),
        "reversed_cross_rows": ((0,), (0, 2)),
    }[profile]
    # A second exact-morphology profile keeps the strict canonical envelope
    # clean while still teaching colour ownership and non-fixed dot rows.
    if profile == "reversed_inner_rows":
        return {
            "grid_h": (10,),
            "grid_w": (10,),
            "color_pair": _REVERSED_PAIRS,
            "upper_row_slot": row_slots[0],
            "lower_row_slot": row_slots[1],
            "upper_col_slot": range(5),
            "lower_col_slot": range(5),
        }
    return {
        "grid_h": _BROAD_HEIGHTS.get(difficulty, _BROAD_HEIGHTS[None]),
        "grid_w": _BROAD_WIDTHS.get(difficulty, _BROAD_WIDTHS[None]),
        "color_pair": _REVERSED_PAIRS,
        "upper_row_slot": row_slots[0],
        "lower_row_slot": row_slots[1],
        "upper_col_slot": range(5),
        "lower_col_slot": range(5),
    }


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
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _profile_defaults(profile, difficulty)
    h = _draw_axis(ctx, "grid_h", 8, 18, defaults["grid_h"])
    w = _draw_axis(ctx, "grid_w", 8, 18, defaults["grid_w"])
    pair_index = _draw_axis(ctx, "color_pair", 0, 71, defaults["color_pair"])
    upper_row_slot = _draw_axis(ctx, "upper_row_slot", 0, 2, defaults["upper_row_slot"])
    lower_row_slot = _draw_axis(ctx, "lower_row_slot", 0, 2, defaults["lower_row_slot"])
    upper_col_slot = _draw_axis(ctx, "upper_col_slot", 0, 4, defaults["upper_col_slot"])
    lower_col_slot = _draw_axis(ctx, "lower_col_slot", 0, 4, defaults["lower_col_slot"])

    upper_color, lower_color = _COLOR_PAIRS[pair_index]
    upper_row = _upper_rows(h)[upper_row_slot]
    lower_row = _lower_rows(h)[lower_row_slot]
    columns = _columns(w)
    grid = full_grid(h, w, 0)
    grid[upper_row][columns[upper_col_slot]] = upper_color
    grid[lower_row][columns[lower_col_slot]] = lower_color
    return grid


def _shape_and_dots(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer colours 0..9 (booleans are not colours)")
    dots = sorted(
        (row_index, col_index, value)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value != 0
    )
    return len(grid), width, dots


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        h, w, dots = _shape_and_dots(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if not 8 <= h <= 18 or not 8 <= w <= 18:
        errors.append("grid dimensions must each be in 8..18")
    if len(dots) != 2:
        errors.append(f"expected exactly two nonzero dots, found {len(dots)}")
        return errors
    if dots[0][2] == dots[1][2]:
        errors.append("the two dots must have distinct nonzero colours")
    split_row = h // 2
    upper = [dot for dot in dots if dot[0] < split_row]
    lower = [dot for dot in dots if dot[0] >= split_row]
    if len(upper) != 1 or len(lower) != 1:
        errors.append("expected exactly one dot in each horizontal half")
    if any(row in (0, h - 1) or col in (0, w - 1) for row, col, _ in dots):
        errors.append("both dots must be interior")
    return errors


def strict_canonical_like(grid):
    """Task-domain membership, intentionally broader than scheduled slot positions."""
    return self_check(grid)


def _ordered_dots(grid):
    h, w, dots = _shape_and_dots(grid)
    findings = self_check(grid)
    if findings:
        raise ValueError("; ".join(findings))
    split_row = h // 2
    upper = next(dot for dot in dots if dot[0] < split_row)
    lower = next(dot for dot in dots if dot[0] >= split_row)
    return h, w, upper, lower


def observe_overrides(grid):
    """Recover every advertised exact axis from the returned pixels."""
    h, w, upper, lower = _ordered_dots(grid)
    try:
        return {
            "grid_h": h,
            "grid_w": w,
            "color_pair": _PAIR_INDEX[(upper[2], lower[2])],
            "upper_row_slot": _upper_rows(h).index(upper[0]),
            "lower_row_slot": _lower_rows(h).index(lower[0]),
            "upper_col_slot": _columns(w).index(upper[1]),
            "lower_col_slot": _columns(w).index(lower[1]),
        }
    except (KeyError, ValueError) as exc:
        raise ValueError("grid is lawful but not on the sampler's exact slot lattice") from exc


def _render_frames(h, w, upper_color, lower_color, upper_row, lower_row, split_row):
    output = full_grid(h, w, 0)
    for row in range(h):
        if row < split_row:
            color = upper_color
            horizontal = row in (0, upper_row)
        else:
            color = lower_color
            horizontal = row in (lower_row, h - 1)
        for col in range(w):
            if horizontal or col in (0, w - 1):
                output[row][col] = color
    return output


def _reference_output(grid):
    """Independent Python oracle for tests/rival scoring; Racket still owns labels."""
    h, w, upper, lower = _ordered_dots(grid)
    return _render_frames(
        h,
        w,
        upper[2],
        lower[2],
        upper[0],
        lower[0],
        h // 2,
    )


def _fixed_dot_rows(grid):
    """Rival: always draw the canonical examples' horizontal rows 2 and 7."""
    h, w, upper, lower = _ordered_dots(grid)
    return _render_frames(h, w, upper[2], lower[2], 2, 7, h // 2)


def _sorted_colors(grid):
    """Rival: assign the smaller colour to the upper frame, ignoring dot colour."""
    h, w, upper, lower = _ordered_dots(grid)
    upper_color, lower_color = sorted((upper[2], lower[2]))
    return _render_frames(
        h, w, upper_color, lower_color, upper[0], lower[0], h // 2
    )


def _fixed_split_row_five(grid):
    """Rival: use the canonical 10x10 side-colour transition at row 5."""
    h, w, upper, lower = _ordered_dots(grid)
    return _render_frames(h, w, upper[2], lower[2], upper[0], lower[0], 5)


def _refutes_fixed_dot_rows(grid):
    return _fixed_dot_rows(grid) != _reference_output(grid)


def _refutes_sorted_colors(grid):
    return _sorted_colors(grid) != _reference_output(grid)


def _refutes_fixed_split(grid):
    return _fixed_split_row_five(grid) != _reference_output(grid)


SEMANTIC_WITNESSES = {
    "noncanonical_dot_rows": _refutes_fixed_dot_rows,
    "reversed_color_order": _refutes_sorted_colors,
    "noncanonical_half_split": _refutes_fixed_split,
}
SEMANTIC_RIVALS = {
    "fixed_dot_rows_2_7": _fixed_dot_rows,
    "sort_colors_ascending": _sorted_colors,
    "fixed_split_row_5": _fixed_split_row_five,
}
WITNESS_RIVALS = {
    "noncanonical_dot_rows": ["fixed_dot_rows_2_7"],
    "reversed_color_order": ["sort_colors_ascending"],
    "noncanonical_half_split": ["fixed_split_row_5"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check; this does not claim universal uniqueness."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons
