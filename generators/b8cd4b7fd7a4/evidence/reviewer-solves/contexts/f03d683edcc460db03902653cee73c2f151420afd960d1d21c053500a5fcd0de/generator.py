"""Sampler for ARC task b8cd4b7fd7a4: draw only a segment's interior.

A lawful input contains exactly two equal-colored nonzero markers.  They are
aligned horizontally, vertically, or on a 45-degree diagonal, with at least one
strict interior lattice cell.  The selected rule discards both markers and
paints only the cells strictly between them cyan (8) on a blank same-size grid.

The eight-profile schedule keeps strong support on the public 8x8 and 9x9
profiles while one profile ranges across every 5..14 canvas size.  Non-anchor
profiles sample every legal non-3 marker color.  Every cyclic four-example
window contains two diagonals and non-3 evidence, so query rotations refute
both an axis-only rule and the public-fitting "only color 3" shortcut.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b8cd4b7fd7a4"
TASK_ID = GENERATOR_ID
RULE_HASH = "1b1807245196"
VERSION = "3.1.0"
SUMMARY = (
    "Find the two equal-colored aligned markers. Return a blank same-size grid "
    "with only the strict segment interior recolored cyan (8); omit both endpoints."
)

INVARIANTS = [
    "grid is rectangular, 5..14 by 5..14, with integer ARC colors",
    "exactly two nonzero cells are present and have the same color 1..7",
    "the two markers share a row, column, or 45-degree diagonal",
    "marker distance is at least two, so the strict interior is nonempty",
    "ordinary lessons cover all orientations and noncanonical marker colors",
]

ORIENTATIONS = ("horizontal", "vertical", "diagonal")
SCHEDULE_PROFILES = tuple(range(8))
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8/9 canonical anchors plus one broad profile per cycle",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "8/9 canonical anchors plus one broad profile per cycle",
        "valid": "5..14",
    },
    "orientation": {
        "type": "str",
        "default": "cyclic horizontal|diagonal|vertical|diagonal",
        "valid": "|".join(ORIENTATIONS),
    },
    "endpoint_color": {
        "type": "int",
        "default": "scheduled across 1..7 with color 3 retained as an anchor",
        "valid": "1..7",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

# Six of eight profiles exactly match a public (height,width,color-count)
# profile, one stays inside its envelope, and one deliberately broadens scale.
_SHAPE_PROFILES = (
    (8, 8),
    (9, 9),
    (8, 8),
    (9, 9),
    (8, 8),
    (9, 9),
    (8, 9),
)
_ORIENTATION_PROFILES = (
    "horizontal",
    "diagonal",
    "vertical",
    "diagonal",
    "horizontal",
    "diagonal",
    "vertical",
    "diagonal",
)
_ANCHOR_COLOR_PROFILES = {0, 4}
_NONCANONICAL_COLORS = (1, 2, 4, 5, 6, 7)


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic curriculum profile for an ordinary draw."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _shape_options(profile: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if profile < len(_SHAPE_PROFILES):
        height, width = _SHAPE_PROFILES[profile]
        return (height,), (width,)
    broad = tuple(range(5, 15))
    return broad, broad


def _color_options(profile: int) -> tuple[int, ...]:
    if profile in _ANCHOR_COLOR_PROFILES:
        return (3,)
    return _NONCANONICAL_COLORS


def _validate_request(seed, sample_index) -> None:
    if type(seed) is not int:
        raise ValueError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise ValueError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "endpoint_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    value = overrides.get("orientation")
    if value is not None and type(value) is not str:
        raise ValueError(
            f"orientation must be a string, not {type(value).__name__}"
        )


def _draw_int_axis(ctx, overrides, name: str, lo: int, hi: int, options) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(options))


def _draw_choice_axis(ctx, overrides, name: str, options, default):
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _distance_bounds(max_distance: int, band: str) -> tuple[int, int]:
    if max_distance < 2:
        raise ValueError("canvas cannot fit a segment with a strict interior")
    if band == "easy":
        return 2, min(max_distance, 4)
    if band == "hard":
        return max(2, (max_distance + 1) // 2), max_distance
    return 2, max_distance


def _pair(ctx, h: int, w: int, orientation: str, band: str):
    rng = ctx.draw_rng("segment_geometry")
    if orientation == "horizontal":
        lo, hi = _distance_bounds(w - 1, band)
        distance = rng.randint(lo, hi)
        row = rng.randrange(h)
        left = rng.randint(0, w - distance - 1)
        return (row, left), (row, left + distance)
    if orientation == "vertical":
        lo, hi = _distance_bounds(h - 1, band)
        distance = rng.randint(lo, hi)
        col = rng.randrange(w)
        top = rng.randint(0, h - distance - 1)
        return (top, col), (top + distance, col)
    if orientation != "diagonal":
        raise ValueError(f"unsupported orientation: {orientation!r}")
    lo, hi = _distance_bounds(min(h, w) - 1, band)
    distance = rng.randint(lo, hi)
    step_r = rng.choice((-1, 1))
    step_c = rng.choice((-1, 1))
    row = (
        rng.randint(0, h - distance - 1)
        if step_r > 0
        else rng.randint(distance, h - 1)
    )
    col = (
        rng.randint(0, w - distance - 1)
        if step_c > 0
        else rng.randint(distance, w - 1)
    )
    return (row, col), (row + step_r * distance, col + step_c * distance)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index)
    _validate_overrides(overrides)
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    height_options, width_options = _shape_options(profile)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_int_axis(ctx, overrides, "grid_h", 5, 14, height_options)
    w = _draw_int_axis(ctx, overrides, "grid_w", 5, 14, width_options)
    orientation = _draw_choice_axis(
        ctx,
        overrides,
        "orientation",
        ORIENTATIONS,
        _ORIENTATION_PROFILES[profile],
    )
    endpoint_color = _draw_int_axis(
        ctx,
        overrides,
        "endpoint_color",
        1,
        7,
        _color_options(profile),
    )
    first, second = _pair(ctx, h, w, orientation, band)
    grid = full_grid(h, w, 0)
    grid[first[0]][first[1]] = endpoint_color
    grid[second[0]][second[1]] = endpoint_color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "orientation": orientation,
        "endpoint_color": endpoint_color,
    }
    if observed != expected:
        raise AssertionError(f"observer mismatch: expected {expected}, got {observed}")
    return grid


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return None
    return len(grid), width


def _analyze(grid):
    shape = _shape(grid)
    if shape is None:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = shape
    if not 5 <= h <= 14:
        raise ValueError(f"grid_h={h} outside [5,14]")
    if not 5 <= w <= 14:
        raise ValueError(f"grid_w={w} outside [5,14]")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("cells must be integer ARC colors 0..9")
    points = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two nonzero cells, found {len(points)}")
    (r1, c1, color1), (r2, c2, color2) = points
    if color1 != color2:
        raise ValueError("the two endpoint colors must match")
    if not 1 <= color1 <= 7:
        raise ValueError(f"endpoint_color={color1} outside [1,7]")
    dr, dc = r2 - r1, c2 - c1
    if dr == 0 and dc != 0:
        orientation = "horizontal"
    elif dc == 0 and dr != 0:
        orientation = "vertical"
    elif dr != 0 and abs(dr) == abs(dc):
        orientation = "diagonal"
    else:
        raise ValueError("endpoints must share a row, column, or 45-degree diagonal")
    distance = max(abs(dr), abs(dc))
    if distance < 2:
        raise ValueError("endpoints must have at least one strict interior cell")
    return {
        "grid_h": h,
        "grid_w": w,
        "orientation": orientation,
        "endpoint_color": color1,
        "points": ((r1, c1), (r2, c2)),
        "distance": distance,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        _analyze(grid)
    except ValueError as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    """Return [] exactly for the lawful aligned two-marker manifold."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    info = _analyze(grid)
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "orientation": info["orientation"],
        "endpoint_color": info["endpoint_color"],
    }


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def _intended_output(grid):
    info = _analyze(grid)
    (r1, c1), (r2, c2) = info["points"]
    step_r, step_c = _sign(r2 - r1), _sign(c2 - c1)
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    for offset in range(1, info["distance"]):
        out[r1 + offset * step_r][c1 + offset * step_c] = 8
    return out


def _color_three_only(grid):
    """RIVAL: apply the selected rule only when both markers are color 3."""
    info = _analyze(grid)
    if info["endpoint_color"] != 3:
        return full_grid(info["grid_h"], info["grid_w"], 0)
    return _intended_output(grid)


def _axis_only(grid):
    """RIVAL: handle horizontal/vertical markers but ignore diagonals."""
    info = _analyze(grid)
    if info["orientation"] == "diagonal":
        return full_grid(info["grid_h"], info["grid_w"], 0)
    return _intended_output(grid)


def _include_endpoints(grid):
    """RIVAL: paint the full segment, incorrectly retaining both endpoints."""
    info = _analyze(grid)
    (r1, c1), (r2, c2) = info["points"]
    step_r, step_c = _sign(r2 - r1), _sign(c2 - c1)
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    for offset in range(info["distance"] + 1):
        out[r1 + offset * step_r][c1 + offset * step_c] = 8
    return out


def _paint_endpoint_color(grid):
    """RIVAL: draw the interior using the marker color instead of cyan."""
    info = _analyze(grid)
    out = _intended_output(grid)
    color = info["endpoint_color"]
    return [[color if value == 8 else value for value in row] for row in out]


def _orientation_is(name: str):
    def predicate(grid):
        return _analyze(grid)["orientation"] == name

    return predicate


def _noncanonical_endpoint_color(grid) -> bool:
    return _analyze(grid)["endpoint_color"] != 3


def _always_lawful(grid) -> bool:
    _analyze(grid)
    return True


SEMANTIC_WITNESSES = {
    "horizontal": _orientation_is("horizontal"),
    "vertical": _orientation_is("vertical"),
    "diagonal": _orientation_is("diagonal"),
    "noncanonical_endpoint_color": _noncanonical_endpoint_color,
    "endpoint_exclusion": _always_lawful,
    "recolor_to_cyan": _always_lawful,
}
SEMANTIC_RIVALS = {
    "color_three_only": _color_three_only,
    "axis_only": _axis_only,
    "include_endpoints": _include_endpoints,
    "paint_endpoint_color": _paint_endpoint_color,
}
WITNESS_RIVALS = {
    "diagonal": ["axis_only"],
    "noncanonical_endpoint_color": ["color_three_only"],
    "endpoint_exclusion": ["include_endpoints"],
    "recolor_to_cyan": ["paint_endpoint_color"],
}
BRANCH_WITNESSES = {"horizontal", "vertical", "diagonal"}
CANONICAL_SHORTCUTS = {"color_three_only": _color_three_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Name any declared rival left able to change the query answer."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"]
                for pair in demos
            )
            disagrees_query = (
                rival(deepcopy(query["input"])) != query["output"]
            )
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and disagrees_query:
            reasons.append(
                f"{name} fits all demonstrations but changes the query"
            )
    return reasons
