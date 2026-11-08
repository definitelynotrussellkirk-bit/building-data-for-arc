"""Generator for ``b19deac47327`` — border-color marker projections.

Two opposite borders carry distinct colors.  Every color-1 marker projects the
matching border color one cell toward that border: markers in the first half
project up/left and markers in the second half project down/right.  The input
sampler uses a four-slot curriculum that alternates orientations, includes
odd-axis tie cases, places markers on previously unseen orthogonal edges, and
crosses the canonical shape/orientation association.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b19deac47327"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "2b2e46dd36cc"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

SUMMARY = (
    "Two opposite borders have distinct colors. Each color-1 marker projects "
    "the color of its matching border into the adjacent cell toward that "
    "border: up/left in the first half and down/right in the second half."
)

INVARIANTS = [
    "background is color 0 and markers are color 1",
    "exactly one pair of opposite borders is solid in two distinct nonzero, non-1 colors",
    "every marker has a unique background destination one cell toward its matching border",
    "ordinary draws contain markers in both halves of the projection axis",
]

SCHEDULE_PROFILES = (
    "cross_horizontal",
    "tie_vertical",
    "cross_vertical",
    "tie_horizontal",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-envelope anchor",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-envelope anchor",
        "valid": "9..18",
    },
    "orientation": {
        "type": "str",
        "default": "scheduled horizontal/vertical",
        "valid": "horizontal|vertical",
    },
    "marker_count": {
        "type": "int",
        "default": "scheduled 6..9",
        "valid": "4..12",
    },
    "edge_pair": {
        "type": "str",
        "default": "scheduled canonical and broad pairs",
        "valid": "2_4|8_3|3_4|2_8|5_9",
    },
    "side_balance": {
        "type": "str",
        "default": "scheduled first/second-heavy",
        "valid": "balanced|first_heavy|second_heavy",
    },
    "edge_marker_mode": {
        "type": "str",
        "default": "scheduled none/seen/unseen orthogonal edge",
        "valid": "none|seen|unseen",
    },
    "midline_marker": {
        "type": "bool",
        "default": "scheduled false/true",
        "valid": "true|false",
    },
}

# Every declared cross-product is constructive on the minimum 9x9 canvas.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()
MIN_STRICT_FRAC = 1.0

_EDGE_PAIRS = {
    "2_4": (2, 4),
    "8_3": (8, 3),
    "3_4": (3, 4),
    "2_8": (2, 8),
    "5_9": (5, 9),
}

_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    # 12x10 is canonical only with vertical borders.  Deliberately crossing it
    # with horizontal borders falsifies a canonical-shape orientation shortcut.
    "cross_horizontal": {
        "grid_h": 12,
        "grid_w": 10,
        "orientation": "horizontal",
        "marker_count": 6,
        "edge_pair": "3_4",
        "side_balance": "first_heavy",
        "edge_marker_mode": "none",
        "midline_marker": False,
    },
    # Odd projection axis plus the bottom orthogonal edge teaches both the
    # tie-to-first convention and an edge position absent from canonical data.
    "tie_vertical": {
        "grid_h": 13,
        "grid_w": 13,
        "orientation": "vertical",
        "marker_count": 7,
        "edge_pair": "5_9",
        "side_balance": "second_heavy",
        "edge_marker_mode": "unseen",
        "midline_marker": True,
    },
    # 12x13 is canonical only with horizontal borders; cross it the other way.
    "cross_vertical": {
        "grid_h": 12,
        "grid_w": 13,
        "orientation": "vertical",
        "marker_count": 8,
        "edge_pair": "8_3",
        "side_balance": "first_heavy",
        "edge_marker_mode": "seen",
        "midline_marker": False,
    },
    # Horizontal tie case on the left orthogonal edge, also absent canonically.
    "tie_horizontal": {
        "grid_h": 13,
        "grid_w": 13,
        "orientation": "horizontal",
        "marker_count": 9,
        "edge_pair": "2_4",
        "side_balance": "second_heavy",
        "edge_marker_mode": "unseen",
        "midline_marker": True,
    },
}


# Default generation stays inside the strict canonical height envelope while
# exercising enough of the declared height axis to avoid a hidden 12/13-only
# curriculum. Canonical anchor heights are intentionally weighted.
_PROFILE_HEIGHT_CHOICES: dict[str, tuple[int, ...]] = {
    # Keep both shape/orientation counterexamples exact so every query rotation
    # still has a crossed canonical shape among its demonstrations.
    "cross_horizontal": (12,),
    # Width is the projection axis here, so height may span the strict envelope.
    "tie_vertical": (12, 13, 14, 15, 16),
    "cross_vertical": (12,),
    # Height is the projection axis here, so only odd heights preserve a midline.
    "tie_horizontal": (13, 15),
}


def _validate_public_call(seed: Any, sample_index: Any, difficulty: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be easy, medium, hard, or None; got {difficulty!r}"
        )


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic four-slot curriculum profile."""
    _validate_public_call(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(difficulty: Any, overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be easy, medium, hard, or None; got {difficulty!r}"
        )

    for name in ("grid_h", "grid_w", "marker_count"):
        if name in overrides and overrides[name] is not None:
            if type(overrides[name]) is not int:
                raise TypeError(f"{name} must be an integer, not bool or another type")
    for name in ("orientation", "edge_pair", "side_balance", "edge_marker_mode"):
        if name in overrides and overrides[name] is not None:
            if type(overrides[name]) is not str:
                raise TypeError(f"{name} must be a string")
    if "midline_marker" in overrides and overrides["midline_marker"] is not None:
        if type(overrides["midline_marker"]) is not bool:
            raise TypeError("midline_marker must be a bool")


def _draw_int_default(
    ctx,
    label: str,
    lo: int,
    hi: int,
    default: int | tuple[int, ...],
) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    choices = default if isinstance(default, tuple) else (default,)
    return ctx.draw_choice(label, choices)


def _draw_choice_default(ctx, label: str, options: tuple[Any, ...], default: Any) -> Any:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _side_counts(marker_count: int, side_balance: str) -> tuple[int, int]:
    if side_balance == "balanced":
        first = (marker_count + 1) // 2
        return first, marker_count - first
    heavy = min(marker_count - 1, (marker_count + 1) // 2 + 1)
    if side_balance == "first_heavy":
        return heavy, marker_count - heavy
    if side_balance == "second_heavy":
        return marker_count - heavy, heavy
    raise ValueError(f"unknown side_balance {side_balance!r}")


def _lane_roles(orientation: str, lane_extent: int) -> tuple[int, int]:
    """Return (seen, unseen) orthogonal edge lanes.

    Canonical horizontal data reaches the right edge but not the left; canonical
    vertical data reaches the top edge but not the bottom.
    """
    if orientation == "horizontal":
        return lane_extent - 1, 0
    return 0, lane_extent - 1


def _marker_cell(orientation: str, axis: int, lane: int) -> tuple[int, int]:
    return (axis, lane) if orientation == "horizontal" else (lane, axis)


def _choose_markers(
    *,
    ctx,
    height: int,
    width: int,
    orientation: str,
    marker_count: int,
    side_balance: str,
    edge_marker_mode: str,
    midline_marker: bool,
    difficulty: str | None,
) -> list[tuple[int, int]]:
    axis_extent = height if orientation == "horizontal" else width
    lane_extent = width if orientation == "horizontal" else height
    midline = (axis_extent - 1) // 2
    first_count, second_count = _side_counts(marker_count, side_balance)

    first_positions = [
        axis
        for axis in range(2, axis_extent - 2)
        if 2 * axis < axis_extent and axis != midline
    ]
    second_positions = [
        axis
        for axis in range(2, axis_extent - 2)
        if 2 * axis >= axis_extent
    ]
    if not first_positions or not second_positions:
        raise ValueError("grid is too small for visible projections in both halves")

    seen_lane, unseen_lane = _lane_roles(orientation, lane_extent)
    if edge_marker_mode == "none":
        allowed_lanes = list(range(1, lane_extent - 1))
        required_lane = None
    elif edge_marker_mode == "seen":
        allowed_lanes = [*range(1, lane_extent - 1), seen_lane]
        required_lane = seen_lane
    elif edge_marker_mode == "unseen":
        allowed_lanes = [*range(1, lane_extent - 1), unseen_lane]
        required_lane = unseen_lane
    else:
        raise ValueError(f"unknown edge_marker_mode {edge_marker_mode!r}")

    if len(allowed_lanes) < max(first_count, second_count):
        raise ValueError("requested marker balance does not fit the selected canvas")

    rng = ctx.draw_rng(f"marker_layout:{difficulty or 'default'}")
    shuffled = allowed_lanes[:]
    rng.shuffle(shuffled)
    if required_lane is not None:
        first_lanes = [required_lane]
        first_lanes.extend(
            lane for lane in shuffled if lane != required_lane
        )
        first_lanes = first_lanes[:first_count]
    else:
        first_lanes = shuffled[:first_count]

    second_lanes = allowed_lanes[:]
    rng.shuffle(second_lanes)
    second_lanes = second_lanes[:second_count]

    markers: list[tuple[int, int]] = []
    for index, lane in enumerate(first_lanes):
        if midline_marker and index == 0:
            axis = midline
        else:
            axis = rng.choice(first_positions)
        markers.append(_marker_cell(orientation, axis, lane))
    for lane in second_lanes:
        axis = rng.choice(second_positions)
        markers.append(_marker_cell(orientation, axis, lane))

    # The construction uses at most one first-half and one second-half marker
    # per lane. Their marker/destination dominoes lie in disjoint axis halves.
    occupied: set[tuple[int, int]] = set()
    for row, col in markers:
        axis = row if orientation == "horizontal" else col
        delta = -1 if 2 * axis < axis_extent else 1
        destination = (
            (row + delta, col)
            if orientation == "horizontal"
            else (row, col + delta)
        )
        for cell in ((row, col), destination):
            if cell in occupied:
                raise RuntimeError("constructive marker placement collided")
            occupied.add(cell)
    return markers


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _PROFILE_DEFAULTS[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = _draw_int_default(
        ctx, "grid_h", 9, 18, _PROFILE_HEIGHT_CHOICES[profile]
    )
    width = _draw_int_default(ctx, "grid_w", 9, 18, defaults["grid_w"])
    orientation = _draw_choice_default(
        ctx,
        "orientation",
        ("horizontal", "vertical"),
        defaults["orientation"],
    )
    marker_count = _draw_int_default(
        ctx, "marker_count", 4, 12, defaults["marker_count"]
    )
    edge_pair = _draw_choice_default(
        ctx, "edge_pair", tuple(_EDGE_PAIRS), defaults["edge_pair"]
    )
    side_balance = _draw_choice_default(
        ctx,
        "side_balance",
        ("balanced", "first_heavy", "second_heavy"),
        defaults["side_balance"],
    )
    edge_marker_mode = _draw_choice_default(
        ctx,
        "edge_marker_mode",
        ("none", "seen", "unseen"),
        defaults["edge_marker_mode"],
    )
    midline_marker = _draw_choice_default(
        ctx,
        "midline_marker",
        (False, True),
        defaults["midline_marker"],
    )

    edge_a, edge_b = _EDGE_PAIRS[edge_pair]
    grid = full_grid(height, width, 0)
    if orientation == "horizontal":
        grid[0] = [edge_a] * width
        grid[-1] = [edge_b] * width
    else:
        for row in range(height):
            grid[row][0] = edge_a
            grid[row][-1] = edge_b

    markers = _choose_markers(
        ctx=ctx,
        height=height,
        width=width,
        orientation=orientation,
        marker_count=marker_count,
        side_balance=side_balance,
        edge_marker_mode=edge_marker_mode,
        midline_marker=midline_marker,
        difficulty=difficulty,
    )
    for row, col in markers:
        grid[row][col] = 1
    return grid


def _solid_color(values: list[int]) -> int | None:
    if values and len(set(values)) == 1 and values[0] not in (0, 1):
        return values[0]
    return None


def _facts_or_raise(grid) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a nonempty list of rows")
    if not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid palette must contain integer colors 0..9")

    height = len(grid)
    if not (9 <= height <= 18 and 9 <= width <= 18):
        raise ValueError("grid dimensions must be within 9..18")

    top = _solid_color(grid[0])
    bottom = _solid_color(grid[-1])
    left = _solid_color([row[0] for row in grid])
    right = _solid_color([row[-1] for row in grid])
    horizontal = top is not None and bottom is not None
    vertical = left is not None and right is not None
    if horizontal == vertical:
        raise ValueError("expected exactly one solid opposite-border orientation")

    if horizontal:
        orientation = "horizontal"
        edge_a, edge_b = top, bottom
        axis_extent = height
    else:
        orientation = "vertical"
        edge_a, edge_b = left, right
        axis_extent = width
    assert edge_a is not None and edge_b is not None
    if edge_a == edge_b:
        raise ValueError("the two border colors must be distinct")

    allowed = {0, 1, edge_a, edge_b}
    palette = {value for row in grid for value in row}
    if not palette <= allowed:
        raise ValueError(
            f"unexpected palette colors {sorted(palette - allowed)} outside {sorted(allowed)}"
        )

    for row in range(height):
        for col in range(width):
            on_colored_border = (
                row in (0, height - 1)
                if orientation == "horizontal"
                else col in (0, width - 1)
            )
            if not on_colored_border and grid[row][col] in (edge_a, edge_b):
                raise ValueError("border colors may not appear in the input interior")

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    if not 4 <= len(markers) <= 12:
        raise ValueError(f"expected 4..12 markers; found {len(markers)}")

    destinations: list[tuple[int, int]] = []
    sides: list[str] = []
    for row, col in markers:
        axis = row if orientation == "horizontal" else col
        if not 2 <= axis <= axis_extent - 3:
            raise ValueError("markers must project visibly into an interior background cell")
        first = 2 * axis < axis_extent
        delta = -1 if first else 1
        destination = (
            (row + delta, col)
            if orientation == "horizontal"
            else (row, col + delta)
        )
        if grid[destination[0]][destination[1]] != 0:
            raise ValueError("every marker destination must be background")
        destinations.append(destination)
        sides.append("first" if first else "second")

    if len(set(destinations)) != len(destinations):
        raise ValueError("marker destinations must be unique")
    first_count = sides.count("first")
    second_count = sides.count("second")
    if not first_count or not second_count:
        raise ValueError("markers must occupy both halves of the projection axis")

    return {
        "height": height,
        "width": width,
        "orientation": orientation,
        "edge_a": edge_a,
        "edge_b": edge_b,
        "markers": markers,
        "destinations": destinations,
        "first_count": first_count,
        "second_count": second_count,
        "axis_extent": axis_extent,
        "palette": palette,
    }


def _observed_side_balance(first_count: int, second_count: int) -> str:
    if abs(first_count - second_count) <= 1:
        return "balanced"
    return "first_heavy" if first_count > second_count else "second_heavy"


def _observed_edge_mode(facts: dict[str, Any]) -> str:
    orientation = facts["orientation"]
    lane_extent = facts["width"] if orientation == "horizontal" else facts["height"]
    seen, unseen = _lane_roles(orientation, lane_extent)
    lanes = [col if orientation == "horizontal" else row for row, col in facts["markers"]]
    if unseen in lanes:
        return "unseen"
    if seen in lanes:
        return "seen"
    return "none"


def observe_overrides(grid) -> dict[str, Any]:
    facts = _facts_or_raise(grid)
    midline = (facts["axis_extent"] - 1) // 2
    marker_axes = [
        row if facts["orientation"] == "horizontal" else col
        for row, col in facts["markers"]
    ]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "orientation": facts["orientation"],
        "marker_count": len(facts["markers"]),
        "edge_pair": f"{facts['edge_a']}_{facts['edge_b']}",
        "side_balance": _observed_side_balance(
            facts["first_count"], facts["second_count"]
        ),
        "edge_marker_mode": _observed_edge_mode(facts),
        "midline_marker": midline in marker_axes,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    try:
        facts = _facts_or_raise(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    reasons: list[str] = []
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for name, requested in meta["overrides"].items():
            if name in observed and observed[name] != requested:
                reasons.append(
                    f"override {name!r} requested {requested!r}, "
                    f"observed {observed[name]!r}"
                )
    if not facts["markers"] or not facts["destinations"]:
        reasons.append("missing parsed markers or projection destinations")
    return reasons


def rule_mirror(grid):
    """Independent Python mirror of the pinned canonical Racket authority."""
    facts = _facts_or_raise(grid)
    result = [row[:] for row in grid]
    for (row, col), (dest_row, dest_col) in zip(
        facts["markers"], facts["destinations"]
    ):
        axis = row if facts["orientation"] == "horizontal" else col
        color = facts["edge_a"] if 2 * axis < facts["axis_extent"] else facts["edge_b"]
        result[dest_row][dest_col] = color
    return result


def strict_canonical_like(grid) -> list[str]:
    try:
        facts = _facts_or_raise(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    reasons: list[str] = []
    if not (12 <= facts["height"] <= 16 and 10 <= facts["width"] <= 18):
        reasons.append("outside canonical 12..16 by 10..18 dimension envelope")
    if len(facts["palette"]) != 4:
        reasons.append("canonical inputs use exactly four colors")
    if not 6 <= len(facts["markers"]) <= 12:
        reasons.append("canonical marker count lies within 6..12")
    return reasons


def _copy_grid(grid):
    return [row[:] for row in grid]


def _variant_projection(
    grid,
    *,
    side_mode: str = "correct",
    orientation_required: str | None = None,
    tie_to_second: bool = False,
    skip_unseen: bool = False,
    skip_all_orthogonal_edges: bool = False,
):
    facts = _facts_or_raise(grid)
    if orientation_required is not None and facts["orientation"] != orientation_required:
        return _copy_grid(grid)

    result = _copy_grid(grid)
    orientation = facts["orientation"]
    extent = facts["axis_extent"]
    lane_extent = facts["width"] if orientation == "horizontal" else facts["height"]
    _seen_lane, unseen_lane = _lane_roles(orientation, lane_extent)
    midline = (extent - 1) // 2

    for row, col in facts["markers"]:
        axis = row if orientation == "horizontal" else col
        lane = col if orientation == "horizontal" else row
        if skip_unseen and lane == unseen_lane:
            continue
        if skip_all_orthogonal_edges and lane in (0, lane_extent - 1):
            continue

        first = 2 * axis < extent
        if side_mode == "first":
            first = True
        elif side_mode == "second":
            first = False
        elif tie_to_second and extent % 2 == 1 and axis == midline:
            first = False

        delta = -1 if first else 1
        dest_row, dest_col = (
            (row + delta, col)
            if orientation == "horizontal"
            else (row, col + delta)
        )
        result[dest_row][dest_col] = facts["edge_a"] if first else facts["edge_b"]
    return result


def _project_all_to_first(grid):
    return _variant_projection(grid, side_mode="first")


def _project_all_to_second(grid):
    return _variant_projection(grid, side_mode="second")


def _horizontal_only(grid):
    return _variant_projection(grid, orientation_required="horizontal")


def _vertical_only(grid):
    return _variant_projection(grid, orientation_required="vertical")


def _tie_to_second(grid):
    return _variant_projection(grid, tie_to_second=True)


def _ignore_unseen_orthogonal_edge(grid):
    return _variant_projection(grid, skip_unseen=True)


def _ignore_all_orthogonal_edges(grid):
    return _variant_projection(grid, skip_all_orthogonal_edges=True)


def _canonical_shape_orientation(grid):
    facts = _facts_or_raise(grid)
    expected = {
        (14, 10): "horizontal",
        (12, 13): "horizontal",
        (12, 10): "vertical",
        (16, 18): "vertical",
    }.get((facts["height"], facts["width"]))
    if expected is not None and expected != facts["orientation"]:
        return _copy_grid(grid)
    return rule_mirror(grid)


def _differs(grid, rival: Callable[[Any], Any]) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _two_sided_discriminator(grid) -> bool:
    try:
        facts = _facts_or_raise(grid)
    except (TypeError, ValueError):
        return False
    return (
        facts["first_count"] > 0
        and facts["second_count"] > 0
        and _differs(grid, _project_all_to_first)
        and _differs(grid, _project_all_to_second)
    )


def _horizontal_discriminator(grid) -> bool:
    try:
        return _facts_or_raise(grid)["orientation"] == "horizontal" and _differs(
            grid, _vertical_only
        )
    except (TypeError, ValueError):
        return False


def _vertical_discriminator(grid) -> bool:
    try:
        return _facts_or_raise(grid)["orientation"] == "vertical" and _differs(
            grid, _horizontal_only
        )
    except (TypeError, ValueError):
        return False


def _tie_break_discriminator(grid) -> bool:
    try:
        facts = _facts_or_raise(grid)
    except (TypeError, ValueError):
        return False
    midline = (facts["axis_extent"] - 1) // 2
    marker_axes = [
        row if facts["orientation"] == "horizontal" else col
        for row, col in facts["markers"]
    ]
    return (
        facts["axis_extent"] % 2 == 1
        and midline in marker_axes
        and _differs(grid, _tie_to_second)
    )


def _orthogonal_edge_discriminator(grid) -> bool:
    try:
        mode = _observed_edge_mode(_facts_or_raise(grid))
    except (TypeError, ValueError):
        return False
    return mode != "none" and _differs(grid, _ignore_all_orthogonal_edges)


def _unseen_edge_discriminator(grid) -> bool:
    try:
        mode = _observed_edge_mode(_facts_or_raise(grid))
    except (TypeError, ValueError):
        return False
    return mode == "unseen" and _differs(grid, _ignore_unseen_orthogonal_edge)


def _shape_orientation_discriminator(grid) -> bool:
    return _differs(grid, _canonical_shape_orientation)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "two_sided_projection_discriminator": _two_sided_discriminator,
    "horizontal_orientation_discriminator": _horizontal_discriminator,
    "vertical_orientation_discriminator": _vertical_discriminator,
    "tie_break_to_first_discriminator": _tie_break_discriminator,
    "orthogonal_edge_discriminator": _orthogonal_edge_discriminator,
    "unseen_edge_discriminator": _unseen_edge_discriminator,
    "shape_orientation_discriminator": _shape_orientation_discriminator,
}

SEMANTIC_RIVALS = {
    "project_all_to_first": _project_all_to_first,
    "project_all_to_second": _project_all_to_second,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "tie_to_second": _tie_to_second,
    "ignore_unseen_orthogonal_edge": _ignore_unseen_orthogonal_edge,
    "ignore_all_orthogonal_edges": _ignore_all_orthogonal_edges,
    "canonical_shape_orientation": _canonical_shape_orientation,
}

WITNESS_RIVALS = {
    "two_sided_projection_discriminator": [
        "project_all_to_first",
        "project_all_to_second",
    ],
    "horizontal_orientation_discriminator": ["vertical_only"],
    "vertical_orientation_discriminator": ["horizontal_only"],
    "tie_break_to_first_discriminator": ["tie_to_second"],
    "orthogonal_edge_discriminator": ["ignore_all_orthogonal_edges"],
    "unseen_edge_discriminator": ["ignore_unseen_orthogonal_edge"],
    "shape_orientation_discriminator": ["canonical_shape_orientation"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "tie_to_second": _tie_to_second,
    "ignore_unseen_orthogonal_edge": _ignore_unseen_orthogonal_edge,
    "canonical_shape_orientation": _canonical_shape_orientation,
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]

    episodes = [*demos, query]
    reasons: list[str] = []
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{role} input is malformed: {errors[:2]}")
            continue
        if rule_mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with the border-projection rule")
    if reasons:
        return reasons

    truth = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != truth:
                reasons.append(f"demos do not falsify shortcut {name!r}")
    return reasons
