"""Constructive input sampler for ARC task 92f4d4eb0dbb.

The selected authority finds the minimum and maximum rows containing color 1,
then recolors only color-1 cells strictly below their arithmetic midpoint to
color 2.  The curriculum deliberately mixes even-height shapes, on which
``r >= midpoint`` is answer-equivalent, with odd-height shapes whose occupied
middle row refutes that plausible shortcut.  Odd-height notched frames also
separate the intended bounding-box midpoint from a tempting pixel-centroid
shortcut that was answer-equivalent on the previous balanced morphology bank.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "92f4d4eb0dbb"
TASK_ID = GENERATOR_ID
RULE_HASH = "5e129c41777b"
VERSION = "3.1.0"
SUMMARY = (
    "A 7..14 rectangular zero-background grid contains one connected color-1 "
    "shape. Its occupied bounding box is 5..7 rows high and five columns wide; "
    "five morphology families and free lawful placement provide visual "
    "variation. The rule finds the minimum and maximum occupied rows and "
    "recolors each color-1 cell strictly below their arithmetic midpoint to "
    "color 2. A four-position schedule reserves half of draws for exact "
    "canonical canvas profiles and half for broader dimensions, while odd "
    "shape heights supply explicit counterexamples to the tempting but wrong "
    "inclusive-midpoint interpretation. Odd notched frames additionally "
    "distinguish the occupied bounding-box midpoint from the pixel centroid."
)

INVARIANTS = [
    "the input is a rectangular 7..14 by 7..14 ARC grid using exactly colors 0 and 1",
    "the color-1 cells form one 8-connected, non-solid shape with no empty row in its bounding box",
    "the occupied bounding box is 5..8 rows high and 3..10 columns wide (generated shapes use 5..7 by 5)",
    "both strict sides of the occupied-row midpoint contain color-1 cells",
    "all advertised exact overrides are constructive and recoverable from the returned grid",
]

SHAPE_KINDS = ("frame", "ladder", "diamond", "zigzag", "notched_frame")
_BALANCED_SHAPE_KINDS = SHAPE_KINDS[:-1]
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile or difficulty-skewed 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile or difficulty-skewed 7..14",
        "valid": "7..14",
    },
    "span": {
        "type": "int",
        "default": "scheduled 5|6|7",
        "valid": "5..7",
    },
    "shape_kind": {
        "type": "str",
        "default": "scheduled morphology",
        "valid": "|".join(SHAPE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "canonical_even",
    "canonical_odd",
    "broad_even",
    "broad_odd",
)

_DIM_LIMITS = (7, 14)
_SPAN_LIMITS = (5, 7)
_CANONICAL_DIMENSIONS = ((8, 9), (7, 7), (9, 9), (9, 11))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum state for one sample index."""
    _validate_call_arguments(seed, sample_index, difficulty)
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call_arguments(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise ValueError(f"seed must be an exact integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    if difficulty is not None and (
        type(difficulty) is not str
        or difficulty not in {"easy", "medium", "hard"}
    ):
        raise ValueError(
            "difficulty must be None or one of 'easy', 'medium', 'hard'"
        )


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in {"grid_h", "grid_w", "span"}:
            if type(value) is not int:
                raise ValueError(
                    f"{name} must be an integer, not {type(value).__name__}"
                )
            lo, hi = _SPAN_LIMITS if name == "span" else _DIM_LIMITS
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside {lo}..{hi}")
        elif name == "shape_kind":
            if type(value) is not str:
                raise ValueError(
                    f"shape_kind must be a string, not {type(value).__name__}"
                )
            if value not in SHAPE_KINDS:
                raise ValueError(
                    f"shape_kind={value!r} not in {list(SHAPE_KINDS)!r}"
                )


def _scheduled_int(ctx, name, lo, hi, scheduled):
    """Use a scheduled default while preserving the full explicit domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _scheduled_choice(ctx, name, options, scheduled):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _profile_axes(ctx, profile, sample_index):
    if profile in {"canonical_even", "canonical_odd"}:
        scheduled_h, scheduled_w = ctx.draw_choice(
            "canonical_dimensions", _CANONICAL_DIMENSIONS
        )
        h = _scheduled_int(ctx, "grid_h", *_DIM_LIMITS, scheduled_h)
        w = _scheduled_int(ctx, "grid_w", *_DIM_LIMITS, scheduled_w)
    else:
        h = ctx.draw_int_diff("grid_h", *_DIM_LIMITS)
        w = ctx.draw_int_diff("grid_w", *_DIM_LIMITS)

    default_span = {
        "canonical_even": 6,
        "canonical_odd": 5,
        "broad_even": 6,
        "broad_odd": 7,
    }[profile]
    span = _scheduled_int(ctx, "span", *_SPAN_LIMITS, default_span)

    if profile in {"canonical_odd", "broad_odd"}:
        # Every three-consecutive-example lesson includes an odd profile.  Make
        # those profiles asymmetric so the pixel-centroid rival is teachably
        # wrong on production support, not merely on a validator-only witness.
        default_kind = "notched_frame"
    else:
        cycle = sample_index // len(SCHEDULE_PROFILES)
        offset = 0 if profile == "canonical_even" else 1
        default_kind = _BALANCED_SHAPE_KINDS[
            (cycle + offset) % len(_BALANCED_SHAPE_KINDS)
        ]
    shape_kind = _scheduled_choice(
        ctx, "shape_kind", SHAPE_KINDS, default_kind
    )
    return h, w, span, shape_kind


def _shape_cells(kind, span):
    if kind == "frame":
        return {
            (r, c)
            for r in range(span)
            for c in range(5)
            if r in {0, span - 1} or c in {0, 4}
        }
    if kind == "notched_frame":
        cells = {
            (r, c)
            for r in range(span)
            for c in range(5)
            if r in {0, span - 1} or c in {0, 4}
        }
        cells.remove((span - 1, 2))
        return cells
    if kind == "ladder":
        return {
            (r, c)
            for r in range(span)
            for c in range(5)
            if r in {0, span - 1} or c in {0, 2, 4}
        }
    if kind == "diamond":
        cells = set()
        for r in range(span):
            distance = min(r, span - 1 - r)
            if distance == 0:
                columns = {2}
            elif distance == 1:
                columns = {1, 2, 3}
            else:
                columns = {0, 2, 4}
            cells.update((r, c) for c in columns)
        return cells
    if kind == "zigzag":
        positions = (0, 1, 2, 3, 2, 1)
        cells = set()
        for r in range(span):
            left = positions[r % len(positions)]
            cells.update({(r, left), (r, left + 1)})
        return cells
    raise ValueError(f"unknown shape kind {kind!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, span, shape_kind = _profile_axes(ctx, profile, sample_index)
    cells = _shape_cells(shape_kind, span)
    if ctx.draw_choice("horizontal_reflection", (False, True)):
        cells = {(r, 4 - c) for r, c in cells}

    top = ctx.draw_int("shape_top", 0, h - span)
    left = ctx.draw_int("shape_left", 0, w - 5)
    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[top + r][left + c] = 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive sampler violated its contract: {errors}")
    return grid


def _one_cells(grid):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    }


def _is_eight_connected(cells):
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = {pending[0]}
    while pending:
        r, c = pending.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                neighbor = (r + dr, c + dc)
                if neighbor in cells and neighbor not in seen:
                    seen.add(neighbor)
                    pending.append(neighbor)
    return seen == cells


def self_check(grid, *, difficulty=None, meta=None):
    """Return diagnostics for malformed or off-domain inputs; never raise."""
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["ragged grid"]

    h, w = len(grid), width
    errors = []
    if not (_DIM_LIMITS[0] <= h <= _DIM_LIMITS[1]):
        errors.append(f"grid height {h} outside 7..14")
    if not (_DIM_LIMITS[0] <= w <= _DIM_LIMITS[1]):
        errors.append(f"grid width {w} outside 7..14")
    if any(
        type(value) is not int or value not in {0, 1}
        for row in grid
        for value in row
    ):
        errors.append("cells must be exact integer colors 0 or 1")
        return errors

    cells = _one_cells(grid)
    if not cells:
        errors.append("at least one color-1 cell is required")
        return errors
    if len(cells) == h * w:
        errors.append("background color 0 must be present")

    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    bbox_h = max_r - min_r + 1
    bbox_w = max_c - min_c + 1
    if not 5 <= bbox_h <= 8:
        errors.append(f"occupied height {bbox_h} outside canonical-backed 5..8")
    if not 3 <= bbox_w <= 10:
        errors.append(f"occupied width {bbox_w} outside canonical-backed 3..10")
    if len(cells) >= bbox_h * bbox_w:
        errors.append("the occupied bounding box must contain at least one zero")
    if len(cells) < bbox_h + bbox_w:
        errors.append("shape is too sparse for the task morphology")

    empty_rows = [
        r for r in range(min_r, max_r + 1)
        if not any((r, c) in cells for c in range(min_c, max_c + 1))
    ]
    if empty_rows:
        errors.append(f"occupied bounding box has empty row(s) {empty_rows[:3]}")
    if not _is_eight_connected(cells):
        errors.append("color-1 cells must form one 8-connected component")

    midpoint_twice = min_r + max_r
    if not any(2 * r < midpoint_twice for r, _ in cells):
        errors.append("shape has no color-1 cell strictly above its midpoint")
    if not any(2 * r > midpoint_twice for r, _ in cells):
        errors.append("shape has no color-1 cell strictly below its midpoint")
    return errors


def strict_canonical_like(grid):
    """The generated contract is intentionally a canonical-backed envelope."""
    return self_check(grid)


def _normalized_shape(grid):
    cells = _one_cells(grid)
    if not cells:
        return 0, set()
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return max_r - min_r + 1, {
        (r - min_r, c - min_c) for r, c in cells
    }


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors}")
    span, normalized = _normalized_shape(grid)
    kind = None
    for candidate in SHAPE_KINDS:
        cells = _shape_cells(candidate, span)
        if normalized == cells or normalized == {(r, 4 - c) for r, c in cells}:
            kind = candidate
            break
    if kind is None:
        raise ValueError("grid is lawful but not one of the generated morphologies")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "span": span,
        "shape_kind": kind,
    }


def _intended_output(grid):
    rows = [r for r, row in enumerate(grid) for value in row if value == 1]
    if not rows:
        return deepcopy(grid)
    midpoint_twice = min(rows) + max(rows)
    return [
        [
            2 if value == 1 and 2 * r > midpoint_twice else value
            for value in row
        ]
        for r, row in enumerate(grid)
    ]


def _inclusive_midpoint(grid):
    """Wrong rival: treats an occupied integer midpoint row as lower half."""
    rows = [r for r, row in enumerate(grid) for value in row if value == 1]
    if not rows:
        return deepcopy(grid)
    midpoint_twice = min(rows) + max(rows)
    return [
        [
            2 if value == 1 and 2 * r >= midpoint_twice else value
            for value in row
        ]
        for r, row in enumerate(grid)
    ]


def _pixel_centroid(grid):
    """Wrong rival: split using the mean row of color-1 pixels."""
    rows = [r for r, row in enumerate(grid) for value in row if value == 1]
    if not rows:
        return deepcopy(grid)
    row_sum = sum(rows)
    count = len(rows)
    return [
        [
            2 if value == 1 and count * r > row_sum else value
            for value in row
        ]
        for r, row in enumerate(grid)
    ]


def _strict_midpoint_witness(grid):
    return _inclusive_midpoint(grid) != _intended_output(grid)


def _bounding_box_midpoint_witness(grid):
    return _pixel_centroid(grid) != _intended_output(grid)


SEMANTIC_WITNESSES = {
    "strict_midpoint": _strict_midpoint_witness,
    "bounding_box_midpoint": _bounding_box_midpoint_witness,
}
SEMANTIC_RIVALS = {
    "inclusive_midpoint": _inclusive_midpoint,
    "pixel_centroid": _pixel_centroid,
}
WITNESS_RIVALS = {
    "strict_midpoint": ["inclusive_midpoint"],
    "bounding_box_midpoint": ["pixel_centroid"],
}
CANONICAL_SHORTCUTS = {
    "inclusive_midpoint": _inclusive_midpoint,
    "pixel_centroid": _pixel_centroid,
}
LESSON_COMPETITORS = {
    "inclusive_midpoint": _inclusive_midpoint,
    "pixel_centroid": _pixel_centroid,
}


def lesson_identifiable(train_pairs, query_pair):
    """Require the demonstrations to refute every declared lesson rival."""
    del query_pair
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for pair in train_pairs:
            try:
                if rival(deepcopy(pair["input"])) != pair["output"]:
                    survived = False
                    break
            except Exception as exc:
                reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
                survived = False
                break
        if survived:
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons


def mutation_fixtures():
    """Task-local tiny/off-palette impostors that self_check must reject."""
    background = [[0] * 7 for _ in range(7)]
    singleton = deepcopy(background)
    singleton[3][3] = 1
    short_line = deepcopy(background)
    short_line[3][1:5] = [1, 1, 1, 1]
    solid = deepcopy(background)
    for r in range(2, 4):
        for c in range(2, 4):
            solid[r][c] = 1
    color_two = deepcopy(background)
    for r in range(1, 6):
        color_two[r][3] = 2
    return [
        ("all_background", background),
        ("singleton", singleton),
        ("short_line", short_line),
        ("solid_2x2", solid),
        ("input_color_2", color_two),
    ]
