"""Constructive input sampler for ARC task 9fbd0923e6ae.

The unchanged authority reads the target color from ``grid[0][0]``, finds the
full color-5 guide (a row or a column), and reflects every *other* target-color
cell across that guide when the destination is in bounds.  The selector itself
is metadata and is not reflected.

The curriculum intentionally includes both guide orientations, off-centre
lines, clipped/identity cases, isolated guide-color noise, two distractor
palette sizes, and target cells on either side of the guide.  Opposite-side
examples refute the strongest shortcut left by the canonical demonstrations:
"copy only from the selector's side of the guide."
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9fbd0923e6ae"
TASK_ID = GENERATOR_ID
RULE_HASH = "63d7f8006f35"
VERSION = "3.0.0"
ALLOW_IDENTITY_OUTPUT = True
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A zero-background grid contains a target-color selector at (0,0), one "
    "full color-5 guide row or column, 2..7 further target cells on the "
    "selector side, opposite side, or both sides, 2..6 distractors in one or "
    "two other colors, and optional isolated color-5 noise. Reflect every "
    "target-color cell except the selector across the guide when its mirror is "
    "in bounds. A six-profile schedule supplies canonical-size examples, both "
    "guide orientations, clipped identity cases, and opposite-side witnesses."
)

INVARIANTS = [
    "grid[0][0] is a nonzero, non-5 target-color selector",
    "exactly one full color-5 guide line exists, horizontal or vertical",
    "at least two non-selector target cells are present",
    "at least two non-target distractor cells are present",
    "scheduled opposite-side examples disagree with the selector-side-only rival",
    "one scheduled profile is an intentional clipped identity instance",
]

GUIDE_ORIENTATIONS = ("vertical", "horizontal")
GUIDE_POSITIONS = ("start", "middle", "end")
TARGET_LAYOUTS = ("selector_side", "opposite_side", "both_sides")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five canonical schedules plus difficulty-scaled broad 8..11",
        "valid": "8..11",
    },
    "grid_w": {
        "type": "int",
        "default": "five canonical schedules plus difficulty-scaled broad 9..12",
        "valid": "9..12",
    },
    "guide_orientation": {
        "type": "str",
        "default": "scheduled vertical/horizontal",
        "valid": "|".join(GUIDE_ORIENTATIONS),
    },
    "guide_position": {
        "type": "str",
        "default": "scheduled one-third/middle/two-thirds position",
        "valid": "|".join(GUIDE_POSITIONS),
    },
    "n_targets": {
        "type": "int",
        "default": "scheduled 3..6",
        "valid": "2..7",
    },
    "target_layout": {
        "type": "str",
        "default": "scheduled selector/opposite/both sides",
        "valid": "|".join(TARGET_LAYOUTS),
    },
    "n_distractors": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "2..6",
    },
    "n_distractor_colors": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
    },
    "n_guide_noise": {
        "type": "int",
        "default": "scheduled 0..2",
        "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = (
    "vertical_canonical",
    "horizontal_opposite",
    "vertical_opposite",
    "horizontal_clipped",
    "vertical_opposite_end",
    "horizontal_both_broad",
)

_PROFILE_CONFIG = {
    "vertical_canonical": {
        "dimensions": (8, 10),
        "guide_orientation": "vertical",
        "guide_position": "middle",
        "n_targets": 3,
        "target_layout": "selector_side",
        "n_distractors": 3,
        "n_distractor_colors": 2,
        "n_guide_noise": 0,
    },
    "horizontal_opposite": {
        "dimensions": (9, 9),
        "guide_orientation": "horizontal",
        "guide_position": "middle",
        "n_targets": 4,
        "target_layout": "opposite_side",
        "n_distractors": 2,
        "n_distractor_colors": 1,
        "n_guide_noise": 1,
    },
    "vertical_opposite": {
        "dimensions": (8, 11),
        "guide_orientation": "vertical",
        "guide_position": "middle",
        "n_targets": 4,
        "target_layout": "opposite_side",
        "n_distractors": 4,
        "n_distractor_colors": 2,
        "n_guide_noise": 0,
    },
    "horizontal_clipped": {
        "dimensions": (10, 10),
        "guide_orientation": "horizontal",
        "guide_position": "end",
        "n_targets": 3,
        "target_layout": "selector_side",
        "n_distractors": 4,
        "n_distractor_colors": 2,
        "n_guide_noise": 0,
    },
    "vertical_opposite_end": {
        "dimensions": (9, 11),
        "guide_orientation": "vertical",
        "guide_position": "end",
        "n_targets": 5,
        "target_layout": "opposite_side",
        "n_distractors": 3,
        "n_distractor_colors": 2,
        "n_guide_noise": 1,
    },
    "horizontal_both_broad": {
        "dimensions": None,
        "guide_orientation": "horizontal",
        "guide_position": "start",
        "n_targets": 6,
        "target_layout": "both_sides",
        "n_distractors": 5,
        "n_distractor_colors": 1,
        "n_guide_noise": 2,
    },
}

_INT_LIMITS = {
    "grid_h": (8, 11),
    "grid_w": (9, 12),
    "n_targets": (2, 7),
    "n_distractors": (2, 6),
    "n_distractor_colors": (1, 2),
    "n_guide_noise": (0, 3),
}
_STR_OPTIONS = {
    "guide_orientation": GUIDE_ORIENTATIONS,
    "guide_position": GUIDE_POSITIONS,
    "target_layout": TARGET_LAYOUTS,
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic profile for one sample index."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_LIMITS:
            if type(value) is not int:
                raise ValueError(
                    f"{name} must be an integer, not {type(value).__name__}"
                )
            lo, hi = _INT_LIMITS[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside {lo}..{hi}")
        else:
            if type(value) is not str:
                raise ValueError(
                    f"{name} must be a string, not {type(value).__name__}"
                )
            if value not in _STR_OPTIONS[name]:
                raise ValueError(
                    f"{name}={value!r} not in {list(_STR_OPTIONS[name])!r}"
                )


def _scheduled_int(ctx, name, scheduled):
    lo, hi = _INT_LIMITS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _scheduled_choice(ctx, name, scheduled):
    options = _STR_OPTIONS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _guide_index(length, position):
    if position == "start":
        return length // 3
    if position == "middle":
        return length // 2
    if position == "end":
        return (2 * length) // 3
    raise ValueError(f"unknown guide position {position!r}")


def _guide_position_name(length, axis):
    for name in GUIDE_POSITIONS:
        if _guide_index(length, name) == axis:
            return name
    return "custom"


def _mirror_point(point, orientation, axis):
    r, c = point
    if orientation == "vertical":
        return r, 2 * axis - c
    return 2 * axis - r, c


def _side(point, orientation, axis):
    r, c = point
    coordinate = c if orientation == "vertical" else r
    return "selector" if coordinate < axis else "opposite"


def _candidate_records(h, w, orientation, axis):
    records = {"selector": [], "opposite": []}
    for r in range(h):
        for c in range(w):
            if (r, c) == (0, 0):
                continue
            if (orientation == "vertical" and c == axis) or (
                orientation == "horizontal" and r == axis
            ):
                continue
            mirror = _mirror_point((r, c), orientation, axis)
            # A cell whose mirror is the selector cannot demonstrate a paint.
            if mirror == (0, 0):
                continue
            in_bounds = 0 <= mirror[0] < h and 0 <= mirror[1] < w
            records[_side((r, c), orientation, axis)].append(
                ((r, c), mirror, in_bounds)
            )
    return records


def _choose_target_cells(
    ctx,
    h,
    w,
    orientation,
    axis,
    n_targets,
    layout,
    *,
    clipped_only=False,
):
    records = _candidate_records(h, w, orientation, axis)
    if layout == "selector_side":
        required = {"selector": n_targets, "opposite": 0}
    elif layout == "opposite_side":
        required = {"selector": 0, "opposite": n_targets}
    else:
        selector_count = n_targets // 2
        required = {
            "selector": selector_count,
            "opposite": n_targets - selector_count,
        }

    rng = ctx.draw_rng("target_cells")
    selected = []
    blocked = {(0, 0)}

    def eligible(side, in_bounds=None):
        result = []
        for point, mirror, visible in records[side]:
            if point in blocked:
                continue
            if in_bounds is not None and visible != in_bounds:
                continue
            result.append((point, mirror, visible))
        return result

    def take(side, in_bounds=None):
        choices = eligible(side, in_bounds)
        if not choices:
            kind = "in-bounds" if in_bounds is True else (
                "clipped" if in_bounds is False else "lawful"
            )
            raise ValueError(f"cannot place requested {kind} target on {side} side")
        point, mirror, visible = rng.choice(choices)
        selected.append(point)
        blocked.add(point)
        if visible:
            blocked.add(mirror)
        required[side] -= 1

    if clipped_only:
        if layout != "selector_side":
            raise ValueError("clipped-only profile requires selector-side targets")
        while required["selector"]:
            take("selector", False)
        return selected

    # Every non-identity scene has an explicit visible paint.  Opposite-side
    # layouts use that paint as a counterexample to the one-way rival.
    if required["opposite"]:
        take("opposite", True)
    elif required["selector"]:
        take("selector", True)

    for side in ("selector", "opposite"):
        while required[side]:
            take(side)
    return selected


def _place_distractors(ctx, grid, target, count, n_colors):
    colors = ctx.draw_distinct_colors(
        "distractor_palette", n=n_colors, exclude={0, 5, target}
    )
    candidates = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    ]
    if len(candidates) < count:
        raise ValueError("not enough empty cells for distractors")
    rng = ctx.draw_rng("distractor_cells")
    positions = rng.sample(candidates, count)
    assignments = list(colors)
    assignments.extend(colors[index % len(colors)] for index in range(count - len(colors)))
    rng.shuffle(assignments)
    for (r, c), color in zip(positions, assignments):
        grid[r][c] = color


def _place_guide_noise(ctx, grid, orientation, axis, count):
    if not count:
        return
    candidates = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
        and not (orientation == "vertical" and c == axis)
        and not (orientation == "horizontal" and r == axis)
    ]
    if len(candidates) < count:
        raise ValueError("not enough empty cells for guide-color noise")
    for r, c in ctx.draw_rng("guide_noise_cells").sample(candidates, count):
        grid[r][c] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    config = _PROFILE_CONFIG[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if config["dimensions"] is None:
        h = ctx.draw_int_diff("grid_h", *_INT_LIMITS["grid_h"])
        w = ctx.draw_int_diff("grid_w", *_INT_LIMITS["grid_w"])
    else:
        default_h, default_w = config["dimensions"]
        h = _scheduled_int(ctx, "grid_h", default_h)
        w = _scheduled_int(ctx, "grid_w", default_w)

    orientation = _scheduled_choice(
        ctx, "guide_orientation", config["guide_orientation"]
    )
    position = _scheduled_choice(ctx, "guide_position", config["guide_position"])
    n_targets = _scheduled_int(ctx, "n_targets", config["n_targets"])
    layout = _scheduled_choice(ctx, "target_layout", config["target_layout"])
    n_distractors = _scheduled_int(
        ctx, "n_distractors", config["n_distractors"]
    )
    n_distractor_colors = _scheduled_int(
        ctx, "n_distractor_colors", config["n_distractor_colors"]
    )
    n_guide_noise = _scheduled_int(
        ctx, "n_guide_noise", config["n_guide_noise"]
    )

    axis_length = w if orientation == "vertical" else h
    axis = _guide_index(axis_length, position)
    grid = full_grid(h, w, 0)
    if orientation == "vertical":
        for r in range(h):
            grid[r][axis] = 5
    else:
        for c in range(w):
            grid[axis][c] = 5

    target = ctx.draw_color("target_color", exclude={0, 5})
    grid[0][0] = target
    clipped_only = (
        profile == "horizontal_clipped"
        and all(
            overrides.get(name) is None
            for name in ("guide_orientation", "guide_position", "target_layout")
        )
    )
    target_cells = _choose_target_cells(
        ctx,
        h,
        w,
        orientation,
        axis,
        n_targets,
        layout,
        clipped_only=clipped_only,
    )
    for r, c in target_cells:
        grid[r][c] = target

    _place_distractors(
        ctx, grid, target, n_distractors, n_distractor_colors
    )
    _place_guide_noise(ctx, grid, orientation, axis, n_guide_noise)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive sampler violated its contract: {errors}")
    if clipped_only and _intended_output(grid) != grid:
        raise RuntimeError("clipped identity profile unexpectedly changes output")
    return grid


def _analysis(grid):
    errors = []
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return {"errors": ["expected a nonempty rectangular grid"]}
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return {"errors": ["ragged grid"]}
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be exact integer ARC colors 0..9"]}

    h, w = len(grid), width
    if not (5 <= h <= 30 and 5 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} outside supported 5..30 envelope")
    target = grid[0][0]
    if target in (0, 5):
        errors.append("grid[0][0] must be a nonzero, non-5 selector color")

    guide_columns = [
        c for c in range(w) if all(grid[r][c] == 5 for r in range(h))
    ]
    guide_rows = [
        r for r in range(h) if all(grid[r][c] == 5 for c in range(w))
    ]
    if len(guide_columns) + len(guide_rows) != 1:
        errors.append(
            "expected exactly one full color-5 guide row or column; "
            f"found rows={guide_rows}, columns={guide_columns}"
        )
        return {
            "errors": errors,
            "target": target,
            "guide_rows": guide_rows,
            "guide_columns": guide_columns,
        }

    if guide_columns:
        orientation, axis = "vertical", guide_columns[0]
    else:
        orientation, axis = "horizontal", guide_rows[0]

    target_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == target and (r, c) != (0, 0)
    ]
    if len(target_cells) < 1:
        errors.append("at least one non-selector target cell is required")
    distractor_values = [
        value
        for row in grid
        for value in row
        if value not in (0, 5, target)
    ]
    if not distractor_values:
        errors.append("at least one non-target distractor is required")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")

    return {
        "errors": errors,
        "h": h,
        "w": w,
        "target": target,
        "orientation": orientation,
        "axis": axis,
        "target_cells": target_cells,
        "distractor_values": distractor_values,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Return authority-domain diagnostics without raising on malformed grids."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Generated inputs stay inside a canonical-backed authority envelope."""
    return self_check(grid)


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe malformed grid: {analysis['errors']}")
    orientation = analysis["orientation"]
    axis = analysis["axis"]
    target_cells = analysis["target_cells"]
    before = sum(
        (c if orientation == "vertical" else r) < axis
        for r, c in target_cells
    )
    after = len(target_cells) - before
    if before and after:
        layout = "both_sides"
    elif before:
        layout = "selector_side"
    else:
        layout = "opposite_side"
    axis_length = analysis["w"] if orientation == "vertical" else analysis["h"]
    guide_length = analysis["h"] if orientation == "vertical" else analysis["w"]
    guide_noise = sum(value == 5 for row in grid for value in row) - guide_length
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "guide_orientation": orientation,
        "guide_position": _guide_position_name(axis_length, axis),
        "n_targets": len(target_cells),
        "target_layout": layout,
        "n_distractors": len(analysis["distractor_values"]),
        "n_distractor_colors": len(set(analysis["distractor_values"])),
        "n_guide_noise": guide_noise,
    }


def _intended_output(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot solve malformed grid: {analysis['errors']}")
    out = deepcopy(grid)
    h, w = analysis["h"], analysis["w"]
    for point in analysis["target_cells"]:
        rr, cc = _mirror_point(point, analysis["orientation"], analysis["axis"])
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = analysis["target"]
    return out


def _selector_side_only(grid):
    """Wrong rival: copy target cells only away from the selector's side."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot solve malformed grid: {analysis['errors']}")
    out = deepcopy(grid)
    h, w = analysis["h"], analysis["w"]
    for point in analysis["target_cells"]:
        if _side(point, analysis["orientation"], analysis["axis"]) != "selector":
            continue
        rr, cc = _mirror_point(point, analysis["orientation"], analysis["axis"])
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = analysis["target"]
    return out


def _opposite_side_target_witness(grid):
    try:
        return _intended_output(grid) != _selector_side_only(grid)
    except ValueError:
        return False


SEMANTIC_WITNESSES = {"opposite_side_target": _opposite_side_target_witness}
SEMANTIC_RIVALS = {"selector_side_only": _selector_side_only}
WITNESS_RIVALS = {"opposite_side_target": ["selector_side_only"]}
CANONICAL_SHORTCUTS = {"selector_side_only": _selector_side_only}
LESSON_COMPETITORS = {"selector_side_only": _selector_side_only}


def lesson_identifiable(train_pairs, query_pair):
    """Require demonstrations to refute every declared lesson competitor."""
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
                reasons.append(
                    f"competitor {name!r} raised {type(exc).__name__}: {exc}"
                )
                survived = False
                break
        if survived:
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
