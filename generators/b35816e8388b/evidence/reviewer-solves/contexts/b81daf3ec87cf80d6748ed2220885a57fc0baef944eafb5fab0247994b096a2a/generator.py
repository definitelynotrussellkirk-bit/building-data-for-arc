"""Input sampler for ``Mark the Segment Midpoint`` (task b35816e8388b).

The selected Racket rule is unchanged: two color-4 endpoints form a horizontal,
vertical, or 45-degree segment with an even coordinate span, and the output is a
blank grid with only the exact midpoint painted color 8.

The canonical examples all happen to place that midpoint at the canvas center.
This sampler therefore links every three-example lesson to an off-center witness
that falsifies the plausible but wrong ``always paint the grid center`` rule.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b35816e8388b"
TASK_ID = GENERATOR_ID
RULE_HASH = "259314225434"
VERSION = "2.0.0"
SUMMARY = (
    "Place exactly two color-4 endpoints on a horizontal, vertical, or 45-degree "
    "segment with an even coordinate span. Return only the segment midpoint as "
    "color 8 on an otherwise blank grid."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

ORIENTATIONS = ("horizontal", "vertical", "diag_down", "diag_up")
SPAN_STEPS = (2, 4, 6, 8, 10, 12)
SCHEDULE_PROFILES = ("canonical_anchor", "off_center", "broad")
_CANONICAL_SHAPES = ((7, 9), (9, 9))
_GRID_MIN = 5
_GRID_MAX = 16

INVARIANTS = [
    "the grid is 5..16 cells in each dimension and uses only colors 0 and 4",
    "exactly two color-4 endpoints are horizontal, vertical, or 45-degree aligned",
    "the coordinate span is one of 2,4,6,8,10,12, so a unique lattice midpoint exists",
    "the output is blank except for color 8 at that midpoint",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled and difficulty-skewed",
        "valid": "5..16",
        "doc": "Exact returned grid height; valid in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled and difficulty-skewed",
        "valid": "5..16",
        "doc": "Exact returned grid width; valid in every difficulty band.",
    },
    "orientation": {
        "type": "str",
        "default": "scheduled across all four line directions",
        "valid": "horizontal|vertical|diag_down|diag_up",
        "doc": "Exact endpoint orientation recoverable from the returned pixels.",
    },
    "span_steps": {
        "type": "int",
        "default": "difficulty-skewed even span",
        "valid": "2|4|6|8|10|12",
        "doc": "Exact Chebyshev distance between the two endpoints.",
    },
}

# Every single-axis override is realizable. Some explicit multi-axis requests
# cannot fit geometrically; those are rejected with a structured exception.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


class IncompatibleGeometry(ValueError):
    """A loud, machine-readable rejection of an impossible exact request."""

    def __init__(self, message: str, axes) -> None:
        super().__init__(message)
        self.incompatible_axes = tuple(sorted(str(axis) for axis in axes))


def schedule_profile(seed, sample_index, difficulty=None):
    """Every three consecutive examples contain all curriculum profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not _GRID_MIN <= value <= _GRID_MAX:
            raise ValueError(f"{name} must be an integer in {_GRID_MIN}..{_GRID_MAX}")

    if "orientation" in overrides and overrides["orientation"] is not None:
        value = overrides["orientation"]
        if type(value) is not str or value not in ORIENTATIONS:
            raise ValueError(
                "orientation must be one of " + ", ".join(ORIENTATIONS)
            )

    if "span_steps" in overrides and overrides["span_steps"] is not None:
        value = overrides["span_steps"]
        if type(value) is not int or value not in SPAN_STEPS:
            raise ValueError(
                "span_steps must be one of " + ", ".join(map(str, SPAN_STEPS))
            )


def _fits(height: int, width: int, orientation: str, span: int) -> bool:
    if orientation == "horizontal":
        return width >= span + 1
    if orientation == "vertical":
        return height >= span + 1
    return height >= span + 1 and width >= span + 1


@lru_cache(maxsize=1)
def _all_geometries():
    return tuple(
        (height, width, orientation, span)
        for height in range(_GRID_MIN, _GRID_MAX + 1)
        for width in range(_GRID_MIN, _GRID_MAX + 1)
        for orientation in ORIENTATIONS
        for span in SPAN_STEPS
        if _fits(height, width, orientation, span)
    )


@lru_cache(maxsize=None)
def _placements(height: int, width: int, orientation: str, span: int):
    if orientation == "horizontal":
        return tuple(
            ((row, col), (row, col + span))
            for row in range(height)
            for col in range(width - span)
        )
    if orientation == "vertical":
        return tuple(
            ((row, col), (row + span, col))
            for row in range(height - span)
            for col in range(width)
        )
    if orientation == "diag_down":
        return tuple(
            ((row, col), (row + span, col + span))
            for row in range(height - span)
            for col in range(width - span)
        )
    return tuple(
        ((row, col + span), (row + span, col))
        for row in range(height - span)
        for col in range(width - span)
    )


def _midpoint(points):
    (row_a, col_a), (row_b, col_b) = points
    return (row_a + row_b) // 2, (col_a + col_b) // 2


def _fixed_grid_center(height: int, width: int):
    # The upper/left member is used for even dimensions; canonical dimensions
    # are odd, so all canonical pairs have an unambiguous center.
    return (height - 1) // 2, (width - 1) // 2


def _has_off_center_placement(geometry) -> bool:
    height, width, orientation, span = geometry
    center = _fixed_grid_center(height, width)
    return any(
        _midpoint(points) != center
        for points in _placements(height, width, orientation, span)
    )


def _scheduled_orientation(sample_index: int, profile: str) -> str:
    cycle = int(sample_index) // len(SCHEDULE_PROFILES)
    offset = 0 if profile == "off_center" else 2
    return ORIENTATIONS[(cycle + offset) % len(ORIENTATIONS)]


def _scheduled_span(sample_index: int, profile: str, difficulty) -> int:
    cycle = int(sample_index) // len(SCHEDULE_PROFILES)
    if difficulty == "easy":
        choices = (2, 4, 6)
    elif difficulty == "medium":
        choices = (2, 4, 6, 8, 10)
    else:
        choices = SPAN_STEPS
    offset = 0 if profile == "off_center" else 3
    return choices[(cycle + offset) % len(choices)]


def _matches_overrides(geometry, overrides) -> bool:
    height, width, orientation, span = geometry
    observed = {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "span_steps": span,
    }
    return all(
        value is None or observed[name] == value
        for name, value in overrides.items()
    )


def _preferred_dimensions(geometry, difficulty) -> bool:
    height, width, _, _ = geometry
    if difficulty == "easy":
        return height <= 9 and width <= 9
    if difficulty == "medium":
        return 7 <= height <= 13 and 7 <= width <= 13
    if difficulty == "hard":
        return height >= 10 and width >= 10
    return 7 <= height <= 13 and 7 <= width <= 13


def _geometry_pool(profile: str, difficulty, sample_index: int, overrides):
    candidates = [
        geometry
        for geometry in _all_geometries()
        if _matches_overrides(geometry, overrides)
    ]
    if not candidates:
        requested = ", ".join(
            f"{name}={value!r}" for name, value in sorted(overrides.items())
        )
        axes = set(overrides) or set(AXES)
        raise IncompatibleGeometry(
            f"incompatible exact geometry overrides ({requested}) across axes "
            + ", ".join(sorted(axes)),
            axes,
        )

    # Profiles are curriculum defaults, never stronger than explicit axes.
    if profile == "canonical_anchor":
        anchored = [
            geometry
            for geometry in candidates
            if geometry[:2] in _CANONICAL_SHAPES and geometry[3] == 6
        ]
        if anchored:
            candidates = anchored
    elif profile == "off_center":
        witnessed = [g for g in candidates if _has_off_center_placement(g)]
        if witnessed:
            candidates = witnessed

    if profile != "canonical_anchor":
        target_orientation = _scheduled_orientation(sample_index, profile)
        target_span = _scheduled_span(sample_index, profile, difficulty)
        scheduled = [
            geometry
            for geometry in candidates
            if (
                "orientation" in overrides
                or geometry[2] == target_orientation
            )
            and (
                "span_steps" in overrides
                or geometry[3] == target_span
            )
        ]
        if scheduled:
            candidates = scheduled

        preferred = [g for g in candidates if _preferred_dimensions(g, difficulty)]
        if preferred:
            candidates = preferred

    return tuple(candidates)


def _record_exact_axes(ctx, geometry):
    height, width, orientation, span = geometry
    # Singleton choices record the already-constructed exact tuple in GenCtx.
    # Overrides are still consumed and validity-checked by the public API.
    return (
        ctx.draw_choice("grid_h", (height,)),
        ctx.draw_choice("grid_w", (width,)),
        ctx.draw_choice("orientation", (orientation,)),
        ctx.draw_choice("span_steps", (span,)),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
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
    pool = _geometry_pool(profile, difficulty, sample_index, overrides)
    geometry = ctx.draw_rng("geometry").choice(pool)
    height, width, orientation, span = _record_exact_axes(ctx, geometry)

    placements = _placements(height, width, orientation, span)
    if profile == "off_center":
        center = _fixed_grid_center(height, width)
        off_center = tuple(
            points for points in placements if _midpoint(points) != center
        )
        if off_center:
            placements = off_center
    points = ctx.draw_rng("endpoint_placement").choice(placements)

    grid = full_grid(height, width, 0)
    for row, col in points:
        grid[row][col] = 4
    return grid


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty sequence of rows"]}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid rows must be nonempty sequences"]}

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not (_GRID_MIN <= height <= _GRID_MAX and _GRID_MIN <= width <= _GRID_MAX):
        errors.append(
            f"grid dimensions must be within {_GRID_MIN}..{_GRID_MAX}"
        )

    invalid_value = next(
        (
            value
            for row in grid
            for value in row
            if type(value) is not int or value not in (0, 4)
        ),
        None,
    )
    if invalid_value is not None:
        errors.append("input cells must be integer colors 0 or 4")

    endpoints = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    ]
    if len(endpoints) != 2:
        errors.append(f"expected exactly two color-4 endpoints, got {len(endpoints)}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "endpoints": tuple(endpoints),
        }

    (row_a, col_a), (row_b, col_b) = endpoints
    dr, dc = row_b - row_a, col_b - col_a
    if dr == 0 and dc != 0:
        orientation = "horizontal"
    elif dc == 0 and dr != 0:
        orientation = "vertical"
    elif abs(dr) == abs(dc) and dr * dc > 0:
        orientation = "diag_down"
    elif abs(dr) == abs(dc) and dr * dc < 0:
        orientation = "diag_up"
    else:
        orientation = None
        errors.append("endpoints must be horizontal, vertical, or 45-degree aligned")

    span = max(abs(dr), abs(dc))
    if span not in SPAN_STEPS:
        errors.append(
            "endpoint span must be one of " + ", ".join(map(str, SPAN_STEPS))
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "endpoints": tuple(endpoints),
        "orientation": orientation,
        "span_steps": span,
        "midpoint": _midpoint(endpoints),
    }


def self_check(grid, *, seed=None, sample_index=None, difficulty=None, meta=None, **kwargs):
    del seed, sample_index, difficulty, meta, kwargs
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    """Recover every exact declared axis from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides from an invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "orientation": analysis["orientation"],
        "span_steps": analysis["span_steps"],
    }


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint instance: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    row, col = analysis["midpoint"]
    output[row][col] = 8
    return output


def strict_canonical_like(grid):
    """Accept the two canonical size profiles with their canonical span 6."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if (analysis["height"], analysis["width"]) not in _CANONICAL_SHAPES:
        errors.append(
            f"shape {(analysis['height'], analysis['width'])} is not canonical"
        )
    if analysis["span_steps"] != 6:
        errors.append("canonical examples use span_steps=6")
    return errors


def _rival_fixed_grid_center(grid):
    analysis = _analyze(grid)
    if "height" not in analysis or "width" not in analysis:
        return []
    output = full_grid(analysis["height"], analysis["width"], 0)
    row, col = _fixed_grid_center(analysis["height"], analysis["width"])
    output[row][col] = 8
    return output


def _rival_keep_endpoints(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = rule_mirror(grid)
    for row, col in analysis["endpoints"]:
        output[row][col] = 4
    return output


def _rival_paint_whole_segment(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = full_grid(analysis["height"], analysis["width"], 0)
    (row_a, col_a), (row_b, col_b) = analysis["endpoints"]
    dr = (row_b > row_a) - (row_b < row_a)
    dc = (col_b > col_a) - (col_b < col_a)
    for offset in range(analysis["span_steps"] + 1):
        output[row_a + offset * dr][col_a + offset * dc] = 8
    return output


SEMANTIC_RIVALS = {
    "fixed_grid_center": _rival_fixed_grid_center,
    "keep_endpoints": _rival_keep_endpoints,
    "paint_whole_segment": _rival_paint_whole_segment,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_grid_center": _rival_fixed_grid_center}


def _witness_off_grid_center(grid):
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["midpoint"]
        != _fixed_grid_center(analysis["height"], analysis["width"])
    )


SEMANTIC_WITNESSES = {"off_grid_center": _witness_off_grid_center}
WITNESS_RIVALS = {"off_grid_center": ["fixed_grid_center"]}


def lesson_identifiable(demos, query):
    """A lesson passes only when all declared rivals are query-discriminated."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:  # reported as a contract reason, never hidden
            reasons.append(f"demo {index} is invalid: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with the midpoint rule")

    try:
        query_expected = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is invalid: {exc}")
        query_expected = None
    if query_expected is not None and query_expected != query["output"]:
        reasons.append("query disagrees with the midpoint rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(pair["input"]) == pair["output"]
            for pair in demos
        )
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
