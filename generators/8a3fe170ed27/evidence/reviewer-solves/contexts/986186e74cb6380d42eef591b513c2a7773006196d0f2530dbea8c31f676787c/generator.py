"""Connected rail/bar inputs for the unchanged 1c56ad9f row-wave authority.

Only inputs are generated here. Racket translates whole rows, including holes,
by (0,-1,0,+1)[distance above last nonempty row % 4], clipping at the canvas.
Four demonstrations include structured and irregular inputs; the four-position
schedule also retains a distinguishing example after any single query holdout.
Explicit controls may request smaller or simpler research cases.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a3fe170ed27"
TASK_ID = GENERATOR_ID
RULE_HASH = "a5b527116538"
VERSION = "3.0.0"
SUMMARY = (
    "One connected single-color object on zero background: frames and lattices "
    "alternate with irregular rails, sparse bottom rows, and left/right clipping "
    "witnesses. Translate each occupied row by (0,-1,0,+1) indexed by its "
    "distance above the LAST NONEMPTY row. Preserve its exact holes and details. "
    "Default lessons use four demonstrations; explicit controls are research "
    "draws and are checked against the same Racket authority."
)
INVARIANTS = [
    "one connected one-color object on zero background",
    "contiguous active rows with top and bottom background margins",
    "both internal holes and dense connecting bars occur in ordinary draws",
    "last nonempty row is the phase anchor; its shift is zero",
    "horizontal clipping is lawful; wrapping and clamping are different rules",
    "explicit counts are exact or rejected with the incompatible axes",
]
AXES = {
    "grid_h": {"type": "int", "default": "weighted 11..20", "valid": "5..20"},
    "grid_w": {"type": "int", "default": "weighted 8..20", "valid": "5..20"},
    "n_rows": {"type": "int", "default": "4..13, ordinary irregular even >=10", "valid": "2..18"},
    "n_cells_per_row": {
        "type": "int", "default": "4..12 maximum; sparse rows contain fewer",
        "valid": "1..18",
    },
    "color": {"type": "int", "default": "uniform 1..9", "valid": "1..9"},
    "pattern": {
        "type": "str", "default": "frame/lattice then three irregular profiles",
        "valid": "solid|frame|lattice|irregular",
    },
    "edge_mode": {
        "type": "str", "default": "interior,left,interior,right",
        "valid": "interior|left|right",
    },
}
# A named pair is refused only when its actual values cannot coexist.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("grid_h", "n_rows"), ("grid_w", "n_cells_per_row"),
    ("pattern", "n_rows"), ("pattern", "n_cells_per_row"),
    ("pattern", "grid_h"), ("pattern", "grid_w"),
    ("grid_h", "grid_w"),
]
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 0.25
_PATTERNS = ("solid", "frame", "lattice", "irregular")
_EDGES = ("interior", "left", "right")
_RANGES = {
    "grid_h": (5, 20), "grid_w": (5, 20), "n_rows": (2, 18),
    "n_cells_per_row": (1, 18), "color": (1, 9),
}


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not a Boolean, float or string")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (
        type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")
    ):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or retired override axes: {unknown}; see AXES")
    for name, value in overrides.items():
        if name in _RANGES:
            lo, hi = _RANGES[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        else:
            choices = _PATTERNS if name == "pattern" else _EDGES
            if type(value) is not str or value not in choices:
                raise ValueError(f"{name} must be one of {choices}")


def _incompatible(message, *axes):
    error = ValueError(message + "; incompatible axes: " + ", ".join(axes))
    error.incompatible_axes = axes
    raise error


def schedule_profile(seed, sample_index, difficulty=None):
    return sample_index % LESSON_SCHEDULE_PERIOD


def _weighted_dimension(ctx, name, minimum, anchor, lower_default, overrides):
    if name in overrides:
        return ctx.draw_int_strict(name, 5, 20)
    choices = list(range(max(minimum, lower_default), 21))
    if anchor in choices:
        choices += [anchor] * 48
    return ctx.draw_choice(name, choices)


def _pattern_options(n_rows, span):
    options = ["solid"]
    if n_rows >= 3 and span >= 3:
        options.append("frame")
        if n_rows >= 4 or span >= 4:
            options.append("lattice")
    if n_rows >= 5 and span >= 4:
        options.append("irregular")
    return options


def _draw_geometry(ctx, sample_index, difficulty, overrides):
    phase = schedule_profile(ctx.seed, sample_index, difficulty)
    preferred_edge = ("interior", "left", "interior", "right")[phase]
    requested_edge = overrides.get("edge_mode")
    requested_pattern = overrides.get("pattern")
    minimum_rows, minimum_span = {
        "solid": (2, 1), "frame": (3, 3),
        "lattice": (3, 3), "irregular": (5, 4),
        None: (2, 1),
    }[requested_pattern]
    if not overrides and phase:
        minimum_rows, minimum_span = 10, 4
    nr_pin, span_pin = overrides.get("n_rows"), overrides.get("n_cells_per_row")
    if nr_pin is not None and nr_pin < minimum_rows:
        _incompatible("n_rows is too small for pattern", "n_rows", "pattern")
    if span_pin is not None and span_pin < minimum_span:
        _incompatible("n_cells_per_row is too small for pattern",
                      "n_cells_per_row", "pattern")
    required_h = max(5, (nr_pin or minimum_rows) + 2)
    if not overrides and phase:
        required_h = max(required_h, minimum_rows + phase + 2)
    # One-sided placement needs only the opposite margin. When edge_mode is
    # unpinned, a tight exact span can select a feasible edge automatically.
    horizontal_margins = 2 if requested_edge == "interior" else 1
    required_w = max(5, (span_pin or minimum_span) + horizontal_margins)
    profile_h, profile_w = ctx.draw_choice(
        "canonical_profile", ((15, 15), (15, 14), (13, 14))
    )
    h = _weighted_dimension(ctx, "grid_h", required_h, profile_h, 11, overrides)
    w = _weighted_dimension(ctx, "grid_w", required_w, profile_w, 8, overrides)
    if h < required_h:
        axis = "n_rows" if nr_pin is not None else "pattern"
        _incompatible("grid_h cannot fit the requested object and two margins",
                      "grid_h", axis)
    if w < required_w:
        axis = "n_cells_per_row" if span_pin is not None else "pattern"
        _incompatible("grid_w cannot fit the requested span and horizontal margins",
                      "grid_w", axis)
    # Exact height overrides can reduce a scheduled margin, never an object count.
    margin = min(phase + 1, h - (nr_pin or minimum_rows) - 1)
    max_rows = min(18, h - margin - 1)
    if nr_pin is not None:
        n_rows = ctx.draw_int_strict("n_rows", 2, 18)
    else:
        desired_min = 10 if phase else 4
        lo = max(minimum_rows, min(desired_min, max_rows))
        choices = list(range(lo, min(13, max_rows) + 1))
        # One irregular example refutes first-row anchoring on every default draw.
        if phase and max_rows >= 6:
            even_choices = [value for value in choices if value % 2 == 0]
            # Tight explicit controls can leave only an odd feasible height.
            # Their lawful research draw takes priority over a lesson preference.
            if even_choices:
                choices = even_choices
        favored = (4, 6, 8) if difficulty == "easy" else (
            (10, 11, 12, 13) if difficulty == "hard" else (7, 8, 9, 10)
        )
        choices += [value for value in favored if value in choices]
        n_rows = ctx.draw_choice("n_rows", choices)
    if span_pin is not None:
        span = ctx.draw_int_strict("n_cells_per_row", 1, 18)
    else:
        span_limit = w - (2 if (requested_edge or preferred_edge) == "interior" else 1)
        if span_limit < minimum_span and requested_edge is None:
            span_limit = w - 1
        lo = max(minimum_span, min(4, span_limit))
        choices = list(range(lo, min(12, span_limit) + 1))
        choices += [value for value in (5, 6, 7, 8, 9) if value in choices]
        span = ctx.draw_choice("n_cells_per_row", choices)
    options = _pattern_options(n_rows, span)
    if requested_pattern is not None:
        if requested_pattern not in options:
            axes = ["pattern"] + [
                key for key in ("grid_h", "grid_w", "n_rows", "n_cells_per_row")
                if key in overrides
            ]
            _incompatible("pattern cannot be realized at the requested size", *axes)
        pattern = ctx.draw_choice("pattern", options)
    else:
        preferred = ("irregular",) if phase else ("frame", "lattice")
        choices = [p for p in preferred if p in options]
        if not choices:
            choices = ["frame"] if "frame" in options else ["solid"]
        pattern = ctx.draw_choice("pattern", choices)
    if "edge_mode" in overrides:
        edge = ctx.draw_choice("edge_mode", _EDGES)
    else:
        choices = [preferred_edge]
        if preferred_edge == "interior" and w - span < 2:
            choices = ["left", "right"]
        edge = ctx.draw_choice("edge_mode", choices)
    return h, w, n_rows, span, margin, pattern, edge


def _motif(ctx, n_rows, span, pattern, profile):
    rails, bars = {0, span - 1}, {0, n_rows - 1}
    if pattern == "solid":
        return {(r, c) for r in range(n_rows) for c in range(span)}
    if pattern == "lattice":
        rng = ctx.draw_rng("rail_bar_details")
        # Reserve a genuine hole while allowing uneven/consecutive interior rails.
        gap_c = rng.choice(list(range(1, span - 1)))
        gap_r = rng.choice(list(range(1, n_rows - 1)))
        rail_slots = [c for c in range(1, span - 1) if c != gap_c]
        bar_slots = [r for r in range(1, n_rows - 1) if r != gap_r]
        extra_c = rng.sample(rail_slots, rng.randint(0, min(3, len(rail_slots))))
        extra_r = rng.sample(bar_slots, rng.randint(0, min(3, len(bar_slots))))
        if not extra_c and not extra_r:
            kind, value = rng.choice(
                [("c", c) for c in rail_slots] + [("r", r) for r in bar_slots]
            )
            (extra_c if kind == "c" else extra_r).append(value)
        rails.update(extra_c)
        bars.update(extra_r)
    elif pattern == "irregular":
        # Three tail phases refute every constant-offset widest-row anchor.
        # Any five-pair window retains two phases after one query holdout.
        # Long tails leave distance-one and distance-three rows sparse for
        # clipping; explicit small research cases use the feasible short tail.
        base_tail = 4 + profile if profile else 5
        tails = list(range(base_tail, n_rows - 2, 4)) or [2]
        tail = ctx.draw_rng("sparse_tail_length").choice(tails)
        bars = {0, n_rows - 1 - tail}
    cells = {(r, c) for r in range(n_rows) for c in range(span)
             if r in bars or c in rails}
    if pattern == "irregular":
        cells.add((1, 1))  # partial, attached rail; never a complete row or column
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h, w, n_rows, span, margin, pattern, edge = _draw_geometry(
        ctx, sample_index, difficulty, overrides
    )
    color = ctx.draw_color_strict("color", exclude=(0,))
    top = h - margin - n_rows
    left = 0 if edge == "left" else (
        w - span if edge == "right" else ctx.draw_rng("horizontal_position").randint(1, w - span - 1)
    )
    grid = full_grid(h, w, 0)
    profile = schedule_profile(seed, sample_index, difficulty)
    for r, c in _motif(ctx, n_rows, span, pattern, profile):
        grid[top + r][left + c] = color
    return grid


def _wave_shift(distance_above_anchor):
    return (0, -1, 0, 1)[distance_above_anchor % 4]


def _supports(grid):
    return {r: {c for c, value in enumerate(row) if value != 0}
            for r, row in enumerate(grid) if any(row)}


def _nonzero_components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    components = []
    while remaining:
        start = remaining.pop()
        stack, component = [start], [start]
        while stack:
            r, c = stack.pop()
            for adjacent in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if adjacent in remaining:
                    remaining.remove(adjacent)
                    stack.append(adjacent)
                    component.append(adjacent)
        components.append(component)
    return components


def self_check(grid, *, difficulty=None, meta=None):
    if type(grid) is not list or not grid or any(type(row) is not list or not row for row in grid):
        return ["grid must be a nonempty rectangular list"]
    if len({len(row) for row in grid}) != 1:
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be native integer ARC colors 0..9, not Boolean/float"]
    supports = _supports(grid)
    if len(supports) < 2:
        return ["at least two active rows are required"]
    active = sorted(supports)
    errors = []
    if active != list(range(active[0], active[-1] + 1)):
        errors.append("active rows must form a contiguous band")
    if active[0] == 0 or active[-1] == len(grid) - 1:
        errors.append("leave top and bottom background margins")
    if len({value for row in grid for value in row if value}) != 1:
        errors.append("the input object must have one nonzero color")
    if len(_nonzero_components(grid)) != 1:
        errors.append("the input must have one connected non-background component")
    if not any(_wave_shift(active[-1] - r) for r in active):
        errors.append("at least one row must exercise a nonzero wave phase")
    return errors


def _classify_pattern(grid):
    supports = _supports(grid)
    active = sorted(supports)
    all_cols = set.union(*supports.values())
    full = set(range(min(all_cols), max(all_cols) + 1))
    if all(cols == full for cols in supports.values()):
        return "solid"
    common = set.intersection(*supports.values())
    full_rows = {r for r, cols in supports.items() if cols == full}
    if (active[0] in full_rows and active[-1] in full_rows
            and all(cols == full or cols == common for cols in supports.values())
            and {min(full), max(full)} <= common):
        return "frame" if common == {min(full), max(full)} and full_rows == {
            active[0], active[-1]
        } else "lattice"
    return "irregular"


def observe_overrides(grid):
    supports = _supports(grid)
    all_cols = set.union(*supports.values())
    edge = "left" if min(all_cols) == 0 else (
        "right" if max(all_cols) == len(grid[0]) - 1 else "interior"
    )
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "n_rows": len(supports),
        "n_cells_per_row": max(map(len, supports.values())),
        "color": next(value for row in grid for value in row if value),
        "pattern": _classify_pattern(grid), "edge_mode": edge,
    }


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    if observed["pattern"] not in ("frame", "lattice"):
        return ["canonical objects are sparse rails joined by full top/bottom bars"]
    if observed["edge_mode"] != "interior":
        return ["canonical objects leave horizontal room; clipping is a lawful extension"]
    return []


def _rival(grid, mode):
    supports = _supports(grid)
    if not supports:
        return [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    anchor = max(supports)
    if mode in ("last_widest_row", "last_widest_plus_one",
                "last_widest_plus_two", "last_widest_plus_three"):
        widest = max(map(len, supports.values()))
        anchor = max(r for r, cols in supports.items() if len(cols) == widest)
        if anchor != max(supports):
            anchor += {"last_widest_row": 0, "last_widest_plus_one": 1,
                       "last_widest_plus_two": 2, "last_widest_plus_three": 3}[mode]
    elif mode == "first_active_anchor":
        anchor = min(supports)
    elif mode == "grid_bottom_margin_one":
        anchor = h - 2
    elif mode == "grid_bottom":
        anchor = h - 1
    common = set.intersection(*supports.values())
    result = full_grid(h, w, 0)
    for r, cols in supports.items():
        dc = _wave_shift(anchor - r)
        if mode == "opposite_phase":
            dc = -dc
        selected = cols
        if mode == "shared_rails_reconstruction" and len(cols) < max(cols) - min(cols) + 1:
            selected = common
        elif mode == "row_envelope_fill":
            selected = range(min(cols), max(cols) + 1)
        color = grid[r][min(cols)]
        for c in selected:
            destination = c + dc
            if mode == "wrap_at_edge":
                destination %= w
            elif mode == "clamp_at_edge":
                destination = min(w - 1, max(0, destination))
            if 0 <= destination < w:
                result[r][destination] = grid[r][c] or color
    return result


def rival_last_widest(grid):
    return _rival(grid, "last_widest_row")


def rival_last_widest_plus_one(grid):
    return _rival(grid, "last_widest_plus_one")


def rival_last_widest_plus_two(grid):
    return _rival(grid, "last_widest_plus_two")


def rival_last_widest_plus_three(grid):
    return _rival(grid, "last_widest_plus_three")


def rival_shared_rails(grid):
    return _rival(grid, "shared_rails_reconstruction")


def rival_wrap(grid):
    return _rival(grid, "wrap_at_edge")


def rival_clamp(grid):
    return _rival(grid, "clamp_at_edge")


def rival_first_active(grid):
    return _rival(grid, "first_active_anchor")


def rival_grid_margin_one(grid):
    return _rival(grid, "grid_bottom_margin_one")


def rival_grid_bottom(grid):
    return _rival(grid, "grid_bottom")


def rival_opposite(grid):
    return _rival(grid, "opposite_phase")


def rival_envelope(grid):
    return _rival(grid, "row_envelope_fill")


def rival_identity(grid):
    return [row[:] for row in grid]


CANONICAL_SHORTCUTS = {
    "last_widest_row": rival_last_widest,
    "last_widest_plus_one": rival_last_widest_plus_one,
    "last_widest_plus_two": rival_last_widest_plus_two,
    "last_widest_plus_three": rival_last_widest_plus_three,
    "shared_rails_reconstruction": rival_shared_rails,
    "wrap_at_edge": rival_wrap,
    "clamp_at_edge": rival_clamp,
}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS,
    "first_active_anchor": rival_first_active,
    "grid_bottom_margin_one": rival_grid_margin_one,
    "grid_bottom": rival_grid_bottom,
    "opposite_phase": rival_opposite,
    "row_envelope_fill": rival_envelope,
    "identity": rival_identity,
}
SEMANTIC_RIVALS = LESSON_COMPETITORS


def _has_holes(grid):
    return any(len(cols) < max(cols) - min(cols) + 1 for cols in _supports(grid).values())


def _sparse_bottom(grid):
    supports = _supports(grid)
    widest = max(map(len, supports.values()))
    last_wide = max(r for r, cols in supports.items() if len(cols) == widest)
    return (max(supports) - last_wide) % 4 != 0


def _partial_rails(grid):
    supports = _supports(grid)
    common = set.intersection(*supports.values())
    return any(cols != common and len(cols) < max(cols) - min(cols) + 1
               for cols in supports.values())


def _left_clip(grid):
    supports = _supports(grid)
    return any(_wave_shift(max(supports) - r) == -1 and 0 in cols and 1 not in cols
               for r, cols in supports.items())


def _right_clip(grid):
    supports = _supports(grid)
    w = len(grid[0])
    return any(_wave_shift(max(supports) - r) == 1 and w-1 in cols and w-2 not in cols
               for r, cols in supports.items())


SEMANTIC_WITNESSES = {
    "internal_holes": _has_holes,
    "last_nonempty_not_last_widest": _sparse_bottom,
    "row_specific_rail_detail": _partial_rails,
    "left_clipping": _left_clip,
    "right_clipping": _right_clip,
}
WITNESS_RIVALS = {
    "internal_holes": ["row_envelope_fill"],
    "last_nonempty_not_last_widest": ["last_widest_row", "last_widest_plus_one",
                                    "last_widest_plus_two", "last_widest_plus_three"],
    "row_specific_rail_detail": ["shared_rails_reconstruction"],
    "left_clipping": ["wrap_at_edge", "clamp_at_edge"],
    "right_clipping": ["wrap_at_edge", "clamp_at_edge"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival diagnostic; not a claim of unique induction."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
