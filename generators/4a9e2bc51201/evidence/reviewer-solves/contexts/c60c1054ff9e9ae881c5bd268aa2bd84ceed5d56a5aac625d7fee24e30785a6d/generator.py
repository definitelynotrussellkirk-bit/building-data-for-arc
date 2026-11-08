"""Constructive sampler for E110 — reflect across the vertical color-5 guide.

The selected rule finds the unique full-height column of 5s.  Every nonzero,
non-5 source cell is reflected across that guide only when its reflected target
is background.  Occupied mirror partners are therefore preserved, including
partners of different colors.

The sampler deliberately includes, in every ordinary example:
* one-sided marks on both sides of the guide (so reflection is bidirectional),
* at least one differently colored occupied mirror pair (so targets are not
  overwritten), and
* an exact canonical (height, width, palette-size) profile every fourth sample.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a9e2bc51201"
TASK_ID = GENERATOR_ID
RULE_HASH = "88c9535f3ba5"
VERSION = "2.0.0"
SUMMARY = (
    "A unique full-height color-5 guide separates reflection orbits. Copy each "
    "one-sided colored cell to its empty mirror target; preserve occupied mirror "
    "partners instead of overwriting them."
)

INVARIANTS = [
    "exactly one full-height column of 5s and no other color-5 cells",
    "every nonzero non-5 cell has an in-bounds reflected partner position",
    "at least one reflection orbit is one-sided, so the selected rule changes the input",
    "ordinary draws contain one-sided marks on both sides and a conflicting occupied pair",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-aware 6..11",
        "valid": "6..11",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-aware 7..11",
        "valid": "7..11",
    },
    "divider_bias": {
        "type": "str",
        "default": "uniform left|center|right",
        "valid": "left|center|right",
    },
    "n_open_pairs": {
        "type": "int",
        "default": "difficulty-aware 4..8",
        "valid": "4..8",
    },
    "n_occupied_pairs": {
        "type": "int",
        "default": "1..3",
        "valid": "0..3",
    },
    "open_side": {
        "type": "str",
        "default": "mixed (at least one one-sided mark on each side)",
        "valid": "left|right|mixed",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "canonical-profile schedule or difficulty-aware 2..4",
        "valid": "1..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

_INT_DOMAINS = {
    "grid_h": (6, 11),
    "grid_w": (7, 11),
    "n_open_pairs": (4, 8),
    "n_occupied_pairs": (0, 3),
    "n_distinct_colors": (1, 4),
}
_CHOICE_DOMAINS = {
    "divider_bias": ("left", "center", "right"),
    "open_side": ("left", "right", "mixed"),
}
_ALLOWED_OVERRIDES = frozenset(_INT_DOMAINS) | frozenset(_CHOICE_DOMAINS)
_CANONICAL_PROFILES = (
    (7, 7, 2),
    (7, 9, 2),
    (8, 9, 2),
    (9, 9, 3),
)
_MARK_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, got {type(value).__name__}")
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
            "grid_h": (6, 8), "grid_w": (7, 9),
            "n_open_pairs": (4, 5), "n_occupied_pairs": (1, 2),
            "n_distinct_colors": (2, 3),
        }
    if difficulty == "medium":
        return {
            "grid_h": (7, 10), "grid_w": (8, 10),
            "n_open_pairs": (5, 7), "n_occupied_pairs": (1, 3),
            "n_distinct_colors": (2, 4),
        }
    if difficulty == "hard":
        return {
            "grid_h": (8, 11), "grid_w": (9, 11),
            "n_open_pairs": (6, 8), "n_occupied_pairs": (2, 3),
            "n_distinct_colors": (3, 4),
        }
    return {
        "grid_h": (6, 11), "grid_w": (7, 11),
        "n_open_pairs": (4, 8), "n_occupied_pairs": (1, 3),
        "n_distinct_colors": (2, 4),
    }


def _draw_int(ctx, name, ordinary_bounds):
    full = _INT_DOMAINS[name]
    bounds = full if name in ctx.overrides and ctx.overrides[name] is not None else ordinary_bounds
    return ctx.draw_int(name, *bounds)


def _draw_choice(ctx, name, ordinary_options):
    options = _CHOICE_DOMAINS[name] if name in ctx.overrides and ctx.overrides[name] is not None else ordinary_options
    return ctx.draw_choice(name, options)


def _divider_for(width, bias):
    left = max(2, width // 3)
    if bias == "left":
        return left
    if bias == "right":
        return width - 1 - left
    if bias == "center":
        return width // 2
    raise ValueError(f"unknown divider bias {bias!r}")


def _bias_for(width, divider):
    matches = [name for name in _CHOICE_DOMAINS["divider_bias"]
               if _divider_for(width, name) == divider]
    if len(matches) != 1:
        raise ValueError(f"divider column {divider} is not a declared bias for width {width}")
    return matches[0]


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic canonical-anchor schedule to semantic tooling."""
    del seed, difficulty
    return "canonical_profile" if sample_index % 4 == 0 else "expanded_profile"


SCHEDULE_PROFILES = ("canonical_profile", "expanded_profile")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    ranges = _difficulty_ranges(difficulty)

    profile_locked = (
        sample_index % 4 == 0
        and all(overrides.get(name) is None for name in
                ("grid_h", "grid_w", "n_distinct_colors"))
    )
    if profile_locked:
        h0, w0, colors0 = _CANONICAL_PROFILES[(sample_index // 4) % len(_CANONICAL_PROFILES)]
        h = ctx.draw_choice("grid_h", (h0,))
        w = ctx.draw_choice("grid_w", (w0,))
        n_distinct_colors = ctx.draw_choice("n_distinct_colors", (colors0,))
    else:
        h = _draw_int(ctx, "grid_h", ranges["grid_h"])
        w = _draw_int(ctx, "grid_w", ranges["grid_w"])
        n_distinct_colors = _draw_int(
            ctx, "n_distinct_colors", ranges["n_distinct_colors"]
        )

    divider_bias = _draw_choice(
        ctx, "divider_bias", _CHOICE_DOMAINS["divider_bias"]
    )
    n_open = _draw_int(ctx, "n_open_pairs", ranges["n_open_pairs"])
    n_occupied = _draw_int(
        ctx, "n_occupied_pairs", ranges["n_occupied_pairs"]
    )
    open_side = _draw_choice(ctx, "open_side", ("mixed",))

    divider = _divider_for(w, divider_bias)
    span = min(divider, w - 1 - divider)
    orbits = [(r, distance) for r in range(h) for distance in range(1, span + 1)]
    needed = n_open + n_occupied
    if needed > len(orbits):
        # The declared cross-product is currently constructive.  Keep this loud
        # guard so a future domain expansion cannot silently drop requested pairs.
        raise ValueError(
            f"grid {h}x{w} with {divider_bias} divider has {len(orbits)} "
            f"reflection orbits, fewer than requested {needed}"
        )
    layout_rng = ctx.draw_rng("orbit_layout")
    layout_rng.shuffle(orbits)
    open_orbits = orbits[:n_open]
    occupied_orbits = orbits[n_open:needed]

    if open_side == "left":
        open_sides = ["left"] * n_open
    elif open_side == "right":
        open_sides = ["right"] * n_open
    else:
        open_sides = ["left" if i % 2 == 0 else "right" for i in range(n_open)]
        layout_rng.shuffle(open_sides)

    palette = list(ctx.draw_distinct_colors(
        "mark_palette", n=n_distinct_colors, exclude=(0, 5)
    ))
    grid = full_grid(h, w, 0)
    for row in grid:
        row[divider] = 5

    # Name every colored-cell slot first, then assign colors while guaranteeing
    # exact palette cardinality and a conflicting occupied pair whenever lawful.
    slots = [("open", i, open_sides[i]) for i in range(n_open)]
    slots += [("occupied", i, "left") for i in range(n_occupied)]
    slots += [("occupied", i, "right") for i in range(n_occupied)]
    assignments = {}
    used = set()
    if n_occupied and len(palette) >= 2:
        assignments[("occupied", 0, "left")] = palette[0]
        assignments[("occupied", 0, "right")] = palette[1]
        used.update(palette[:2])

    remaining_slots = [slot for slot in slots if slot not in assignments]
    missing = [color for color in palette if color not in used]
    color_rng = ctx.draw_rng("cell_colors")
    values = missing + [color_rng.choice(palette)
                        for _ in range(len(remaining_slots) - len(missing))]
    color_rng.shuffle(values)
    assignments.update(zip(remaining_slots, values))

    for index, (r, distance) in enumerate(open_orbits):
        side = open_sides[index]
        c = divider - distance if side == "left" else divider + distance
        grid[r][c] = assignments[("open", index, side)]
    for index, (r, distance) in enumerate(occupied_orbits):
        grid[r][divider - distance] = assignments[("occupied", index, "left")]
        grid[r][divider + distance] = assignments[("occupied", index, "right")]
    return grid


def _divider(grid):
    h, w = len(grid), len(grid[0])
    columns = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(columns) != 1:
        raise ValueError(f"expected exactly one full-height 5 divider, found {len(columns)}")
    return columns[0]


def _orbit_stats(grid):
    h, w = len(grid), len(grid[0])
    divider = _divider(grid)
    span = min(divider, w - 1 - divider)
    open_left = open_right = occupied = 0
    for r in range(h):
        for distance in range(1, span + 1):
            left = grid[r][divider - distance] not in (0, 5)
            right = grid[r][divider + distance] not in (0, 5)
            if left and right:
                occupied += 1
            elif left:
                open_left += 1
            elif right:
                open_right += 1
    return divider, open_left, open_right, occupied


def observe_overrides(grid):
    """Recover every public exact axis from returned pixels."""
    divider, open_left, open_right, occupied = _orbit_stats(grid)
    if open_left and open_right:
        open_side = "mixed"
    elif open_left:
        open_side = "left"
    elif open_right:
        open_side = "right"
    else:
        open_side = "none"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "divider_bias": _bias_for(len(grid[0]), divider),
        "n_open_pairs": open_left + open_right,
        "n_occupied_pairs": occupied,
        "open_side": open_side,
        "n_distinct_colors": len({
            value for row in grid for value in row if value not in (0, 5)
        }),
    }


def rule_mirror(grid):
    """Independent Python transcription used only by tests and rival contracts."""
    out = deepcopy(grid)
    try:
        divider = _divider(grid)
    except (TypeError, IndexError, ValueError):
        return out
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5) or c == divider:
                continue
            mirror = 2 * divider - c
            if 0 <= mirror < w and out[r][mirror] == 0:
                out[r][mirror] = value
    return out


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    divider_columns = [
        c for c in range(width) if all(grid[r][c] == 5 for r in range(height))
    ]
    if len(divider_columns) != 1:
        return [f"expected exactly one full-height 5 divider, found {len(divider_columns)}"]
    divider = divider_columns[0]
    errors = []
    marks = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 5 and c != divider:
                errors.append("color 5 may appear only in the full-height divider")
            if value in (0, 5):
                continue
            marks += 1
            mirror = 2 * divider - c
            if not 0 <= mirror < width:
                errors.append("colored cell has an out-of-bounds mirror position")
    if not marks:
        errors.append("expected at least one colored mark")
    elif rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("input is already closed under reflection; rule would be identity")
    return sorted(set(errors))


def strict_canonical_like(grid):
    """Lawful selected-rule inputs, including canonical occupied mirror pairs."""
    return self_check(grid)


def _left_to_right_only(grid):
    out = deepcopy(grid)
    divider = _divider(grid)
    for r, row in enumerate(grid):
        for c in range(divider):
            value = row[c]
            mirror = 2 * divider - c
            if value not in (0, 5) and 0 <= mirror < len(row) and out[r][mirror] == 0:
                out[r][mirror] = value
    return out


def _right_to_left_only(grid):
    out = deepcopy(grid)
    divider = _divider(grid)
    for r, row in enumerate(grid):
        for c in range(divider + 1, len(row)):
            value = row[c]
            mirror = 2 * divider - c
            if value not in (0, 5) and 0 <= mirror < len(row) and out[r][mirror] == 0:
                out[r][mirror] = value
    return out


def _overwrite_occupied_targets(grid):
    out = deepcopy(grid)
    divider = _divider(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5) or c == divider:
                continue
            mirror = 2 * divider - c
            if 0 <= mirror < len(row):
                out[r][mirror] = value
    return out


def _has_open_left(grid):
    _, left, _, _ = _orbit_stats(grid)
    return left > 0


def _has_open_right(grid):
    _, _, right, _ = _orbit_stats(grid)
    return right > 0


def _has_conflicting_occupied_pair(grid):
    divider = _divider(grid)
    span = min(divider, len(grid[0]) - 1 - divider)
    return any(
        grid[r][divider - d] not in (0, 5)
        and grid[r][divider + d] not in (0, 5)
        and grid[r][divider - d] != grid[r][divider + d]
        for r in range(len(grid)) for d in range(1, span + 1)
    )


SEMANTIC_WITNESSES = {
    "open_source_on_left": _has_open_left,
    "open_source_on_right": _has_open_right,
    "occupied_target_preserved": _has_conflicting_occupied_pair,
}
SEMANTIC_RIVALS = {
    "left_to_right_only": _left_to_right_only,
    "right_to_left_only": _right_to_left_only,
    "overwrite_occupied_targets": _overwrite_occupied_targets,
}
WITNESS_RIVALS = {
    "open_source_on_left": ["right_to_left_only"],
    "open_source_on_right": ["left_to_right_only"],
    "occupied_target_preserved": ["overwrite_occupied_targets"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {}


def lesson_identifiable(demos, query):
    """Finite contract: reject a lesson when a declared rival changes its query."""
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            fits_demos = all(rival(deepcopy(pair["input"])) == pair["output"]
                             for pair in demos)
            changes_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:  # malformed lesson should fail visibly
            reasons.append(f"{name} evaluation failed: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
