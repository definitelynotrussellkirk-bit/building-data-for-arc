"""Constructive sampler for blue-to-cyan reflection across a gray divider.

The selected Racket rule finds the unique full-height color-5 column, starts
from a blank output, and reflects every blue (1) cell across that column as
cyan (8). Reflections outside the canvas are clipped. All input cells,
including the divider and unrelated distractors, are discarded.
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
    "A unique full-height gray (5) column is the reflection axis. Reflect the "
    "single connected blue (1) object from either side across that axis, clip "
    "out-of-bounds cells, recolor retained cells cyan (8), and discard the "
    "entire input canvas including unrelated colored and extra-gray distractors."
)

LAYOUT_PROFILES = (
    "left_centered",
    "right_clipped",
    "right_centered",
    "left_clipped",
    "left_offcenter",
    "right_offcenter",
)

INVARIANTS = [
    "exactly one full-height color-5 divider column; isolated extra gray cells are allowed",
    "one nonempty 4-connected blue object lies wholly on one side of the divider",
    "at least one blue reflection remains in bounds; clipped profiles also lose at least one cell",
    "ordinary draws include a reflectable non-blue distractor and an isolated extra-gray distractor",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors plus difficulty-aware 7..12",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors plus difficulty-aware 9..15",
        "valid": "9..15",
    },
    "layout_profile": {
        "type": "str",
        "default": "six-sample deterministic semantic schedule",
        "valid": "|".join(LAYOUT_PROFILES),
    },
    "blue_size": {
        "type": "int",
        "default": "difficulty-aware 3..8",
        "valid": "3..8",
    },
    "n_distractors": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 5
SCHEDULE_PROFILES = LAYOUT_PROFILES

_INT_DOMAINS = {
    "grid_h": (7, 12),
    "grid_w": (9, 15),
    "blue_size": (3, 8),
    "n_distractors": (2, 4),
}
_ALLOWED_OVERRIDES = frozenset(_INT_DOMAINS) | {"layout_profile"}
_CANONICAL_SHAPES = ((8, 11), (9, 13), (10, 12), (8, 14))
_NOISE_COLORS = (2, 3, 4, 6, 7, 9)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    if "layout_profile" in overrides and overrides["layout_profile"] is not None:
        value = overrides["layout_profile"]
        if type(value) is not str or value not in LAYOUT_PROFILES:
            raise ValueError(
                f"layout_profile={value!r} must be one of {LAYOUT_PROFILES}"
            )


def _difficulty_ranges(difficulty):
    if difficulty == "easy":
        return {
            "grid_h": (7, 9), "grid_w": (9, 12),
            "blue_size": (3, 4), "n_distractors": (2, 2),
        }
    if difficulty == "medium":
        return {
            "grid_h": (8, 11), "grid_w": (10, 14),
            "blue_size": (4, 6), "n_distractors": (2, 3),
        }
    if difficulty == "hard":
        return {
            "grid_h": (9, 12), "grid_w": (12, 15),
            "blue_size": (6, 8), "n_distractors": (3, 4),
        }
    return dict(_INT_DOMAINS)


def _draw_int(ctx, name, ordinary_bounds):
    bounds = _INT_DOMAINS[name] if ctx.overrides.get(name) is not None else ordinary_bounds
    return ctx.draw_int_strict(name, *bounds)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic semantic layout schedule."""
    del seed, difficulty
    return LAYOUT_PROFILES[sample_index % len(LAYOUT_PROFILES)]


def _divider_for(width, profile):
    if profile.endswith("centered"):
        return width // 2
    if profile == "left_offcenter":
        return max(2, (width - 1) // 3)
    if profile == "right_offcenter":
        return width - 1 - max(2, (width - 1) // 3)
    if profile == "left_clipped":
        return width - 3
    if profile == "right_clipped":
        return 2
    raise ValueError(f"unknown layout profile {profile!r}")


def _source_side(profile):
    return "left" if profile.startswith("left_") else "right"


def _mirror(divider, column):
    return 2 * divider - column


def _grow_connected(allowed, seeds, size, rng):
    cells = set(seeds)
    if not cells <= allowed:
        raise RuntimeError("blue seed lies outside the constructive region")
    while len(cells) < size:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _NEIGHBORS
            if (r + dr, c + dc) in allowed and (r + dr, c + dc) not in cells
        })
        if not frontier:
            raise RuntimeError("constructive blue growth exhausted its region")
        cells.add(rng.choice(frontier))
    return cells


def _blue_cells(ctx, height, width, divider, profile, size):
    side = _source_side(profile)
    side_cells = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (c < divider if side == "left" else c > divider)
    }
    rng = ctx.draw_rng("blue_shape")

    if profile.endswith("clipped"):
        row = rng.randrange(height)
        if side == "left":
            target_span = width - 1 - divider
            valid_c = divider - target_span
            seeds = {(row, valid_c), (row, valid_c - 1)}
        else:
            target_span = divider
            valid_c = divider + target_span
            seeds = {(row, valid_c), (row, valid_c + 1)}
        cells = _grow_connected(side_cells, seeds, size, rng)
        reflected = [_mirror(divider, c) for _, c in cells]
        if not any(0 <= c < width for c in reflected) or not any(
            not 0 <= c < width for c in reflected
        ):
            raise RuntimeError("clipped profile did not realize both retained and clipped cells")
        return cells

    fully_visible = {
        (r, c) for r, c in side_cells if 0 <= _mirror(divider, c) < width
    }
    seed = rng.choice(sorted(fully_visible))
    return _grow_connected(fully_visible, {seed}, size, rng)


def _reflected_blue_positions(grid, divider):
    width = len(grid[0])
    return {
        (r, mirror)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
        for mirror in (_mirror(divider, c),)
        if 0 <= mirror < width
    }


def _place_distractors(ctx, grid, divider, count):
    height, width = len(grid), len(grid[0])
    intended = _reflected_blue_positions(grid, divider)
    rng = ctx.draw_rng("distractor_layout")
    noise_color = rng.choice(_NOISE_COLORS)

    reflectable = []
    for r in range(height):
        for c in range(width):
            if c == divider or grid[r][c] != 0 or (r, c) in intended:
                continue
            mirror = _mirror(divider, c)
            if (
                0 <= mirror < width
                and grid[r][mirror] == 0
                and (r, mirror) not in intended
            ):
                reflectable.append((r, c))
    if not reflectable:
        raise RuntimeError("no room for the semantic distractor witness")
    first_noise = rng.choice(reflectable)
    grid[first_noise[0]][first_noise[1]] = noise_color

    gray_candidates = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if c != divider and grid[r][c] == 0 and (r, c) not in intended
    ]
    if not gray_candidates:
        raise RuntimeError("no room for an extra-gray distractor")
    extra_gray = rng.choice(gray_candidates)
    grid[extra_gray[0]][extra_gray[1]] = 5

    remaining = count - 2
    if remaining:
        candidates = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if c != divider and grid[r][c] == 0 and (r, c) not in intended
        ]
        if len(candidates) < remaining:
            raise RuntimeError("not enough cells for requested distractors")
        for r, c in rng.sample(candidates, remaining):
            grid[r][c] = noise_color


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
    ranges = _difficulty_ranges(difficulty)

    canonical_anchor = (
        sample_index % 4 == 0
        and overrides.get("grid_h") is None
        and overrides.get("grid_w") is None
    )
    if canonical_anchor:
        h0, w0 = _CANONICAL_SHAPES[(sample_index // 4) % len(_CANONICAL_SHAPES)]
        height = ctx.draw_choice("grid_h", (h0,))
        width = ctx.draw_choice("grid_w", (w0,))
    else:
        height = _draw_int(ctx, "grid_h", ranges["grid_h"])
        width = _draw_int(ctx, "grid_w", ranges["grid_w"])

    if overrides.get("layout_profile") is not None:
        profile = ctx.draw_choice("layout_profile", LAYOUT_PROFILES)
    else:
        profile = ctx.draw_choice("layout_profile", (schedule_profile(seed, sample_index),))
    blue_size = _draw_int(ctx, "blue_size", ranges["blue_size"])
    n_distractors = _draw_int(ctx, "n_distractors", ranges["n_distractors"])

    divider = _divider_for(width, profile)
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 5
    for row, col in _blue_cells(ctx, height, width, divider, profile, blue_size):
        grid[row][col] = 1
    _place_distractors(ctx, grid, divider, n_distractors)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generator violated its contract: {errors}")
    expected = {
        "grid_h": height,
        "grid_w": width,
        "layout_profile": profile,
        "blue_size": blue_size,
        "n_distractors": n_distractors,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"observable override mismatch: expected {expected}, got {observed}")
    return grid


def _shape_errors(grid):
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    invalid = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        return None, [f"invalid ARC color at {invalid[0][:2]}: {invalid[0][2]!r}"]
    return (len(grid), width), []


def _divider_columns(grid):
    height, width = len(grid), len(grid[0])
    return [c for c in range(width) if all(grid[r][c] == 5 for r in range(height))]


def _blue_positions(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def _connected(points):
    remaining = set(points)
    if not remaining:
        return False
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for dr, dc in _NEIGHBORS:
            neighbor = (r + dr, c + dc)
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def _distractor_positions(grid, divider):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and value != 1 and not (c == divider and value == 5)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input domain without evaluating output labels."""
    del difficulty, meta
    shape, errors = _shape_errors(grid)
    if errors:
        return errors
    height, width = shape
    dividers = _divider_columns(grid)
    if len(dividers) != 1:
        return [f"expected exactly one full-height gray divider, found {len(dividers)}"]
    divider = dividers[0]

    blue = _blue_positions(grid)
    errors = []
    if not blue:
        errors.append("no blue object")
        return errors
    left = any(c < divider for _, c in blue)
    right = any(c > divider for _, c in blue)
    if left == right:
        errors.append("blue cells must lie wholly on exactly one side of the divider")
    if not _connected(blue):
        errors.append("blue cells must form one 4-connected object")
    if any(value == 8 for row in grid for value in row):
        errors.append("cyan 8 is reserved for the output and must not appear in input")
    valid_reflections = sum(0 <= _mirror(divider, c) < width for _, c in blue)
    if valid_reflections == 0:
        errors.append("all blue reflections fall outside the grid")
    if not _distractor_positions(grid, divider):
        errors.append("at least one unrelated input distractor is required")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _divider_column(grid):
    dividers = _divider_columns(grid)
    if len(dividers) != 1:
        raise ValueError(f"expected one divider, found {len(dividers)}")
    return dividers[0]


def _rule_output(grid):
    height, width = len(grid), len(grid[0])
    divider = _divider_column(grid)
    output = full_grid(height, width, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            mirror = _mirror(divider, c)
            if 0 <= mirror < width:
                output[r][mirror] = 8
    return output


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors}")
    height, width = len(grid), len(grid[0])
    divider = _divider_column(grid)
    blue = _blue_positions(grid)
    side = "left" if all(c < divider for _, c in blue) else "right"
    clipped = any(not 0 <= _mirror(divider, c) < width for _, c in blue)
    if clipped:
        profile = f"{side}_clipped"
    elif divider == width // 2:
        profile = f"{side}_centered"
    else:
        profile = f"{side}_offcenter"
    return {
        "grid_h": height,
        "grid_w": width,
        "layout_profile": profile,
        "blue_size": len(blue),
        "n_distractors": len(_distractor_positions(grid, divider)),
    }


def _blank_like(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _left_only(grid):
    divider = _divider_column(grid)
    output = _blank_like(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirror = _mirror(divider, c)
            if value == 1 and c < divider and 0 <= mirror < len(row):
                output[r][mirror] = 8
    return output


def _right_only(grid):
    divider = _divider_column(grid)
    output = _blank_like(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirror = _mirror(divider, c)
            if value == 1 and c > divider and 0 <= mirror < len(row):
                output[r][mirror] = 8
    return output


def _canvas_midline(grid):
    width = len(grid[0])
    output = _blank_like(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1:
                output[r][width - 1 - c] = 8
    return output


def _all_or_nothing(grid):
    divider = _divider_column(grid)
    width = len(grid[0])
    if any(
        not 0 <= _mirror(divider, c) < width
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ):
        return _blank_like(grid)
    return _rule_output(grid)


def _overlay_input(grid):
    output = deepcopy(grid)
    divider = _divider_column(grid)
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirror = _mirror(divider, c)
            if value == 1 and 0 <= mirror < width:
                output[r][mirror] = 8
    return output


def _reflect_all_colored(grid):
    divider = _divider_column(grid)
    width = len(grid[0])
    output = _blank_like(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirror = _mirror(divider, c)
            if value not in (0, 5) and 0 <= mirror < width:
                output[r][mirror] = 8
    return output


def _keep_blue_color(grid):
    divider = _divider_column(grid)
    width = len(grid[0])
    output = _blank_like(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirror = _mirror(divider, c)
            if value == 1 and 0 <= mirror < width:
                output[r][mirror] = 1
    return output


def _source_left(grid):
    divider = _divider_column(grid)
    return all(c < divider for _, c in _blue_positions(grid))


def _source_right(grid):
    divider = _divider_column(grid)
    return all(c > divider for _, c in _blue_positions(grid))


def _offcenter_counterexample(grid):
    return _divider_column(grid) != len(grid[0]) // 2 and _canvas_midline(grid) != _rule_output(grid)


def _clipping_counterexample(grid):
    divider = _divider_column(grid)
    width = len(grid[0])
    clipped = any(
        not 0 <= _mirror(divider, c) < width for _, c in _blue_positions(grid)
    )
    return clipped and _all_or_nothing(grid) != _rule_output(grid)


def _cleared_canvas_counterexample(grid):
    return _overlay_input(grid) != _rule_output(grid)


def _distractor_counterexample(grid):
    return _reflect_all_colored(grid) != _rule_output(grid)


def _recolor_counterexample(grid):
    return _keep_blue_color(grid) != _rule_output(grid)


SEMANTIC_RIVALS = {
    "left_only": _left_only,
    "right_only": _right_only,
    "canvas_midline": _canvas_midline,
    "all_or_nothing_clipping": _all_or_nothing,
    "overlay_on_input": _overlay_input,
    "reflect_all_colored": _reflect_all_colored,
    "keep_blue_color": _keep_blue_color,
}
SEMANTIC_WITNESSES = {
    "source_on_left": _source_left,
    "source_on_right": _source_right,
    "offcenter_axis": _offcenter_counterexample,
    "partial_clipping": _clipping_counterexample,
    "discard_input_canvas": _cleared_canvas_counterexample,
    "ignore_nonblue_distractors": _distractor_counterexample,
    "recolor_blue_to_cyan": _recolor_counterexample,
}
WITNESS_RIVALS = {
    "source_on_left": ["right_only"],
    "source_on_right": ["left_only"],
    "offcenter_axis": ["canvas_midline"],
    "partial_clipping": ["all_or_nothing_clipping"],
    "discard_input_canvas": ["overlay_on_input"],
    "ignore_nonblue_distractors": ["reflect_all_colored"],
    "recolor_blue_to_cyan": ["keep_blue_color"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject a lesson when a declared wrong rule survives its demonstrations."""
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
            )
            changes_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} evaluation failed: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
