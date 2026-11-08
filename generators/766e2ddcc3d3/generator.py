"""Generator for ARC task 766e2ddcc3d3 — control-coded shape rotation.

The input contains exactly one connected blue polyomino and one marker whose
color is 2, 3, 4, or 5.  The marker value encodes zero, one, two, or three
clockwise quarter-turns.  The output is the normalized rotated polyomino,
cropped to its bounding box and recolored cyan.

The public examples link each marker value to one particular grid/profile and
always place the marker at the upper-left corner.  Ordinary generated lessons
therefore interleave exact public-profile anchors with translated linked-profile anchors and counterexamples that move the
marker and vary the shape.  This prevents a learner from succeeding
by reading only cell (0,0) or by memorizing one answer per marker color.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "766e2ddcc3d3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a22bbdd04976"
SUMMARY = (
    "Find the unique color-1 shape and the unique marker 2..5. Rotate the "
    "normalized shape (marker-2) quarter-turns clockwise, crop it to its "
    "bounding box, and recolor it 8. Exact public-profile anchors are mixed "
    "with translated anchors and moved-marker/new-shape counterexamples so "
    "location and lookup shortcuts cannot identify a lesson."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "the input is a rectangular 7..14 by 7..16 ARC grid",
    "exactly one marker cell has a value in 2..5",
    "the blue cells form one cardinally connected, non-rectangular polyomino of size 3..8",
    "the marker is separated from the blue shape by at least one background cell",
    "marker 2/3/4/5 means 0/1/2/3 clockwise quarter-turns",
    "the output is only the normalized transformed shape in color 8",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "easy 7..8; medium 8..11; hard 10..14",
        "valid": "7..14",
        "doc": "Exact returned input height.",
    },
    "grid_w": {
        "type": "int",
        "default": "easy 7..8; medium 8..12; hard 11..16",
        "valid": "7..16",
        "doc": "Exact returned input width.",
    },
    "ctrl": {
        "type": "int",
        "default": "scheduled 2,3,4,5 cycle",
        "valid": "2..5",
        "doc": "Exact marker value and therefore clockwise turn count ctrl-2.",
    },
    "shape_size": {
        "type": "int",
        "default": "easy 3..4; medium 4..6; hard 6..8",
        "valid": "3..8",
        "doc": "Exact number of blue cells.",
    },
    "marker_location": {
        "type": "str",
        "default": "16-slot top_left|other_corner|edge|interior schedule",
        "valid": "top_left|other_corner|edge|interior",
        "doc": "Exact topological location class of the unique marker cell.",
    },
}

# An empty declaration means every Cartesian combination of the five exact
# axes is intended to work; no ValueError is being used to hide a placement bug.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
_MARKER_LOCATIONS = ("top_left", "other_corner", "edge", "interior")

# The four linked public profiles.  The absolute blue coordinates identify the
# original examples for evidence, while scheduled anchor slots translate the same
# normalized template so fixed inputs cannot masquerade as semantic support.
_CANONICAL_PROFILES: dict[int, dict[str, Any]] = {
    2: {
        "name": "public_ctrl2_l3_7x7",
        "height": 7,
        "width": 7,
        "shape": ((0, 0), (1, 0), (1, 1)),
        "absolute_shape": ((2, 2), (3, 2), (3, 3)),
        "output": ((8, 0), (8, 8)),
    },
    3: {
        "name": "public_ctrl3_l3_7x7",
        "height": 7,
        "width": 7,
        "shape": ((0, 0), (1, 0), (1, 1)),
        "absolute_shape": ((2, 3), (3, 3), (3, 4)),
        "output": ((8, 8), (8, 0)),
    },
    4: {
        "name": "public_ctrl4_l4_7x8",
        "height": 7,
        "width": 8,
        "shape": ((0, 0), (0, 1), (1, 1), (2, 1)),
        "absolute_shape": ((2, 2), (2, 3), (3, 3), (4, 3)),
        "output": ((8, 0), (8, 0), (8, 8)),
    },
    5: {
        "name": "public_ctrl5_l4_8x8",
        "height": 8,
        "width": 8,
        "shape": ((0, 0), (1, 0), (2, 0), (2, 1)),
        "absolute_shape": ((2, 2), (3, 2), (4, 2), (4, 3)),
        "output": ((0, 0, 8), (8, 8, 8)),
    },
}

# A Latin-square schedule over control and marker location.  Every four
# consecutive sample indexes contain all four controls.  Exact public anchors
# are spaced at 0,5,10,15, leaving at least two generalized examples in every
# four-demo sliding window, including the 15->0 wraparound.
_SCHEDULE: tuple[tuple[str, int, str, bool], ...] = (
    ("slot00_public_ctrl2", 2, "top_left", True),
    ("slot01_ctrl3_other_corner", 3, "other_corner", False),
    ("slot02_ctrl4_edge", 4, "edge", False),
    ("slot03_ctrl5_interior", 5, "interior", False),
    ("slot04_ctrl2_other_corner", 2, "other_corner", False),
    ("slot05_public_ctrl3", 3, "top_left", True),
    ("slot06_ctrl4_interior", 4, "interior", False),
    ("slot07_ctrl5_edge", 5, "edge", False),
    ("slot08_ctrl2_edge", 2, "edge", False),
    ("slot09_ctrl3_interior", 3, "interior", False),
    ("slot10_public_ctrl4", 4, "top_left", True),
    ("slot11_ctrl5_other_corner", 5, "other_corner", False),
    ("slot12_ctrl2_interior", 2, "interior", False),
    ("slot13_ctrl3_edge", 3, "edge", False),
    ("slot14_ctrl4_other_corner", 4, "other_corner", False),
    ("slot15_public_ctrl5", 5, "top_left", True),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _SCHEDULE)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic teaching profile selected by sample_index."""
    del seed, difficulty
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)][0]


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((col, -row) for row, col in cells)


def _rotate(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    shape = _normalize(cells)
    for _ in range(turns % 4):
        shape = _rotate_cw(shape)
    return shape


def _shape_dimensions(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen: set[tuple[int, int]] = set()
    while stack:
        cell = stack.pop()
        if cell in seen:
            continue
        seen.add(cell)
        row, col = cell
        for drow, dcol in _CARDINAL:
            neighbor = (row + drow, col + dcol)
            if neighbor in remaining and neighbor not in seen:
                stack.append(neighbor)
    return seen == remaining


def _is_non_rectangular(shape: Sequence[tuple[int, int]]) -> bool:
    height, width = _shape_dimensions(shape)
    return len(shape) < height * width


def _has_four_orientations(shape: Sequence[tuple[int, int]]) -> bool:
    return len({_rotate(shape, turns) for turns in range(4)}) == 4


def _enumerate_shape_pools() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """Enumerate fixed polyominoes deterministically up to size eight."""
    by_size: dict[int, set[tuple[tuple[int, int], ...]]] = {1: {((0, 0),)}}
    for size in range(2, 9):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in sorted(by_size[size - 1]):
            occupied = set(shape)
            for row, col in shape:
                for drow, dcol in _CARDINAL:
                    candidate = (row + drow, col + dcol)
                    if candidate not in occupied:
                        expanded.add(_normalize((*shape, candidate)))
        by_size[size] = expanded
    pools: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(3, 9):
        pools[size] = tuple(
            shape
            for shape in sorted(by_size[size])
            if _is_non_rectangular(shape) and _has_four_orientations(shape)
        )
        if not pools[size]:
            raise RuntimeError(f"no asymmetric non-rectangular polyominoes of size {size}")
    return pools


_SHAPE_POOLS = _enumerate_shape_pools()


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], len(grid), 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _marker_class(row: int, col: int, height: int, width: int) -> str:
    if (row, col) == (0, 0):
        return "top_left"
    if (row, col) in ((0, width - 1), (height - 1, 0), (height - 1, width - 1)):
        return "other_corner"
    if row in (0, height - 1) or col in (0, width - 1):
        return "edge"
    return "interior"


def _analyze(grid: Any) -> dict[str, Any]:
    errors, height, width = _validate_grid(grid)
    if errors:
        return {"errors": errors, "height": height, "width": width}

    blue = tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )
    markers = tuple(
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in (2, 3, 4, 5)
    )
    illegal = sorted({value for row in grid for value in row if value not in (0, 1, 2, 3, 4, 5)})
    if illegal:
        errors.append(f"unexpected colors: {illegal}")
    if not (7 <= height <= 14 and 7 <= width <= 16):
        errors.append(f"expected dimensions within 7..14 by 7..16, got {height}x{width}")
    if len(markers) != 1:
        errors.append(f"expected exactly one control marker in 2..5, found {len(markers)}")
    if not 3 <= len(blue) <= 8:
        errors.append(f"expected 3..8 blue cells, found {len(blue)}")
    if blue and not _is_connected(blue):
        errors.append("blue cells must be one cardinally connected component")

    normalized = _normalize(blue)
    if blue and not _is_non_rectangular(normalized):
        errors.append("blue shape must not fill its bounding rectangle")
    if blue and not _has_four_orientations(normalized):
        errors.append("blue shape must expose four distinct quarter-turn orientations")

    marker = markers[0] if len(markers) == 1 else None
    if marker is not None and blue:
        marker_row, marker_col, _ = marker
        if any(
            abs(marker_row - row) <= 1 and abs(marker_col - col) <= 1
            for row, col in blue
        ):
            errors.append("control marker must have a one-cell background moat from the blue shape")

    marker_location = None
    if marker is not None:
        marker_location = _marker_class(marker[0], marker[1], height, width)
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "blue": blue,
        "shape": normalized,
        "shape_size": len(blue),
        "marker": marker,
        "ctrl": marker[2] if marker is not None else None,
        "marker_location": marker_location,
    }


def canonical_profile_signature(grid: Any) -> str | None:
    """Return the linked public profile name, ignoring blue translation."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["marker"][:2] != (0, 0):
        return None
    profile = _CANONICAL_PROFILES.get(analysis["ctrl"])
    if profile is None:
        return None
    if (
        analysis["height"] == profile["height"]
        and analysis["width"] == profile["width"]
        and analysis["shape"] == profile["shape"]
    ):
        return str(profile["name"])
    return None


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Expose task-linked structure for focused tests and evidence."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    rotations = tuple(_rotate(analysis["shape"], turns) for turns in range(4))
    return {
        "errors": [],
        "height": analysis["height"],
        "width": analysis["width"],
        "ctrl": analysis["ctrl"],
        "turns_clockwise": analysis["ctrl"] - 2,
        "shape_size": analysis["shape_size"],
        "shape_signature": analysis["shape"],
        "shape_bbox": _shape_dimensions(analysis["shape"]),
        "rotation_orbit_size": len(set(rotations)),
        "marker_cell": analysis["marker"][:2],
        "marker_location": analysis["marker_location"],
        "canonical_profile": canonical_profile_signature(grid),
    }


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid itself."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "ctrl": analysis["ctrl"],
        "shape_size": analysis["shape_size"],
        "marker_location": analysis["marker_location"],
    }


def _draw_int(
    ctx: Any,
    overrides: dict[str, Any],
    label: str,
    default_bounds: tuple[int, int],
    global_bounds: tuple[int, int],
) -> int:
    bounds = global_bounds if label in overrides else default_bounds
    return ctx.draw_int(label, *bounds)


def _draw_choice(
    ctx: Any,
    overrides: dict[str, Any],
    label: str,
    default_value: str,
    global_values: Sequence[str],
) -> str:
    options = global_values if label in overrides else (default_value,)
    return str(ctx.draw_choice(label, options))


def _band_bounds(difficulty: Any) -> dict[str, tuple[int, int]]:
    if difficulty == "easy":
        return {"grid_h": (7, 8), "grid_w": (7, 8), "shape_size": (3, 4)}
    if difficulty == "medium":
        return {"grid_h": (8, 11), "grid_w": (8, 12), "shape_size": (4, 6)}
    if difficulty == "hard":
        return {"grid_h": (10, 14), "grid_w": (11, 16), "shape_size": (6, 8)}
    return {"grid_h": (7, 14), "grid_w": (7, 16), "shape_size": (3, 8)}


def _marker_candidates(height: int, width: int, location: str) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if _marker_class(row, col, height, width) == location
    ]


def _render_shape(shape: Sequence[tuple[int, int]], turns: int) -> list[list[int]]:
    rotated = _rotate(shape, turns)
    height, width = _shape_dimensions(rotated)
    output = full_grid(height, width, 0)
    for row, col in rotated:
        output[row][col] = 8
    return output


def _lookup_output(ctrl: int) -> list[list[int]]:
    return [list(row) for row in _CANONICAL_PROFILES[ctrl]["output"]]


def _construct_general(
    ctx: Any,
    height: int,
    width: int,
    ctrl: int,
    shape_size: int,
    marker_location: str,
) -> list[list[int]]:
    marker_order = _marker_candidates(height, width, marker_location)
    ctx.draw_rng("marker_cell").shuffle(marker_order)

    shapes = list(_SHAPE_POOLS[shape_size])
    ctx.draw_rng("shape_morphology").shuffle(shapes)
    placement_rng = ctx.draw_rng("shape_placement")

    for marker_row, marker_col in marker_order:
        for shape in shapes:
            shape_height, shape_width = _shape_dimensions(shape)
            if shape_height > height or shape_width > width:
                continue
            placements = [
                (top, left)
                for top in range(height - shape_height + 1)
                for left in range(width - shape_width + 1)
            ]
            placement_rng.shuffle(placements)
            for top, left in placements:
                absolute = tuple((top + row, left + col) for row, col in shape)
                if any(
                    abs(marker_row - row) <= 1 and abs(marker_col - col) <= 1
                    for row, col in absolute
                ):
                    continue
                # Generated teaching examples must break the tempting public
                # marker->answer lookup.  Public anchors cover that manifold.
                if _render_shape(shape, ctrl - 2) == _lookup_output(ctrl):
                    continue
                grid = full_grid(height, width, 0)
                grid[marker_row][marker_col] = ctrl
                for row, col in absolute:
                    grid[row][col] = 1
                return grid
    raise RuntimeError(
        "no legal placement for exact axes "
        f"height={height} width={width} ctrl={ctrl} "
        f"shape_size={shape_size} marker_location={marker_location}"
    )


def _construct_public_anchor(ctx: Any, ctrl: int) -> list[list[int]]:
    """Translate one linked public template while preserving its exact profile."""
    profile = _CANONICAL_PROFILES[ctrl]
    height, width = profile["height"], profile["width"]
    shape = profile["shape"]
    shape_height, shape_width = _shape_dimensions(shape)
    placements = [
        (top, left)
        for top in range(height - shape_height + 1)
        for left in range(width - shape_width + 1)
        if all(top + row > 1 or left + col > 1 for row, col in shape)
    ]
    ctx.draw_rng("public_shape_placement").shuffle(placements)
    top, left = placements[0]
    grid = full_grid(height, width, 0)
    grid[0][0] = ctrl
    for row, col in shape:
        grid[top + row][left + col] = 1
    return grid


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    """Return one deterministic, rule-identifying input grid."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    _, scheduled_ctrl, scheduled_location, public_slot = _SCHEDULE[
        int(sample_index) % len(_SCHEDULE)
    ]
    use_public_anchor = public_slot and not overrides

    if use_public_anchor:
        profile = _CANONICAL_PROFILES[scheduled_ctrl]
        height = ctx.draw_int("grid_h", profile["height"], profile["height"])
        width = ctx.draw_int("grid_w", profile["width"], profile["width"])
        ctrl = ctx.draw_int("ctrl", scheduled_ctrl, scheduled_ctrl)
        shape_size = ctx.draw_int(
            "shape_size", len(profile["shape"]), len(profile["shape"])
        )
        marker_location = ctx.draw_choice("marker_location", ("top_left",))
        grid = _construct_public_anchor(ctx, ctrl)
    else:
        bounds = _band_bounds(difficulty)
        height = _draw_int(ctx, overrides, "grid_h", bounds["grid_h"], (7, 14))
        width = _draw_int(ctx, overrides, "grid_w", bounds["grid_w"], (7, 16))
        ctrl = _draw_int(ctx, overrides, "ctrl", (scheduled_ctrl, scheduled_ctrl), (2, 5))
        shape_size = _draw_int(
            ctx, overrides, "shape_size", bounds["shape_size"], (3, 8)
        )
        marker_location = _draw_choice(
            ctx,
            overrides,
            "marker_location",
            scheduled_location,
            _MARKER_LOCATIONS,
        )
        grid = _construct_general(
            ctx, height, width, ctrl, shape_size, marker_location
        )

    errors = self_check(grid, difficulty=difficulty, meta=ctx.recorded_draws())
    if errors:
        raise RuntimeError("constructed invalid rotation lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "ctrl": ctrl,
        "shape_size": shape_size,
        "marker_location": marker_location,
    }
    if observed != expected:
        raise RuntimeError(f"keyed axes were not realized: {expected} -> {observed}")
    return _copy_grid(grid)


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the authority-valid input grammar and exact keyed axes."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update({name: meta[name] for name in AXES if name in meta})
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update({name: nested[name] for name in AXES if name in nested})
    if requested:
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if expected is not None and observed.get(name) != expected:
                errors.append(
                    f"axis {name!r} requested {expected!r}, realized {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept exactly one of the four linked public control/profile manifolds."""
    errors = self_check(grid)
    if errors:
        return errors
    if canonical_profile_signature(grid) is None:
        return [
            "grid dimensions, marker value/location, and normalized blue shape "
            "do not match one linked public profile"
        ]
    return []


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python audit mirror of the selected canonical Racket rule."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_shape(analysis["shape"], analysis["ctrl"] - 2)


def _rival_ignore_control(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_shape(analysis["shape"], 0)


def _rival_counterclockwise(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_shape(analysis["shape"], -(analysis["ctrl"] - 2))


def _rival_fixed_top_left_control(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    assumed_ctrl = grid[0][0] if grid[0][0] in (2, 3, 4, 5) else 2
    return _render_shape(analysis["shape"], assumed_ctrl - 2)


def _rival_control_value_lookup(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _lookup_output(analysis["ctrl"])


def _rival_solid_bbox(grid: Any) -> list[list[int]]:
    true_output = rule_mirror(grid)
    return full_grid(len(true_output), len(true_output[0]), 8)


def _differs(grid: Any, rival: Callable[[Any], list[list[int]]]) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (IndexError, TypeError, ValueError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_control_identity": _rival_ignore_control,
    "rotate_counterclockwise": _rival_counterclockwise,
    "read_control_only_at_top_left": _rival_fixed_top_left_control,
    "memorize_one_output_per_control": _rival_control_value_lookup,
    "fill_rotated_bounding_box": _rival_solid_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "read_control_only_at_top_left": _rival_fixed_top_left_control,
    "memorize_one_output_per_control": _rival_control_value_lookup,
}

SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "non_identity_control_changes_shape": lambda grid: _differs(
        grid, _rival_ignore_control
    ),
    "clockwise_direction_is_observable": lambda grid: _differs(
        grid, _rival_counterclockwise
    ),
    "moved_marker_refutes_fixed_cell_read": lambda grid: _differs(
        grid, _rival_fixed_top_left_control
    ),
    "new_shape_refutes_control_lookup": lambda grid: _differs(
        grid, _rival_control_value_lookup
    ),
    "shape_is_not_its_solid_bbox": lambda grid: _differs(
        grid, _rival_solid_bbox
    ),
}
WITNESS_RIVALS = {
    "non_identity_control_changes_shape": ["ignore_control_identity"],
    "clockwise_direction_is_observable": ["rotate_counterclockwise"],
    "moved_marker_refutes_fixed_cell_read": ["read_control_only_at_top_left"],
    "new_shape_refutes_control_lookup": ["memorize_one_output_per_control"],
    "shape_is_not_its_solid_bbox": ["fill_rotated_bounding_box"],
}


def lesson_identifiable(demos: Sequence[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Require every declared plausible rival to be eliminated by the demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} consecutive demonstrations")
    for index, pair in enumerate((*demos, query)):
        try:
            expected = rule_mirror(pair["input"])
            actual = pair["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is malformed: {type(exc).__name__}: {exc}")
            continue
        if expected != actual:
            reasons.append(f"pair {index} output disagrees with the task rule")
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                reasons.append(f"competitor {name!r} still fits every demonstration")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            reasons.append(f"competitor {name!r} could not be scored: {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local must-reject near-misses for the strict defect lint."""
    base = generate(94177, 9, difficulty="medium")

    no_marker = _copy_grid(base)
    for row, values in enumerate(no_marker):
        for col, value in enumerate(values):
            if value in (2, 3, 4, 5):
                no_marker[row][col] = 0

    duplicate_marker = _copy_grid(base)
    duplicate_marker[-1][-1] = 2 if duplicate_marker[-1][-1] == 0 else 3

    disconnected = _copy_grid(base)
    blue = [(r, c) for r, row in enumerate(disconnected) for c, value in enumerate(row) if value == 1]
    disconnected[blue[-1][0]][blue[-1][1]] = 0
    for row in range(len(disconnected) - 1, -1, -1):
        for col in range(len(disconnected[0]) - 1, -1, -1):
            if disconnected[row][col] == 0 and all(
                abs(row - br) + abs(col - bc) > 1 for br, bc in blue[:-1]
            ):
                disconnected[row][col] = 1
                break
        else:
            continue
        break

    wrong_color = _copy_grid(base)
    for row, values in enumerate(wrong_color):
        for col, value in enumerate(values):
            if value == 1:
                wrong_color[row][col] = 6
                break
        else:
            continue
        break

    adjacent_marker = _copy_grid(base)
    marker = next(
        (r, c) for r, row in enumerate(adjacent_marker) for c, value in enumerate(row)
        if value in (2, 3, 4, 5)
    )
    ctrl = adjacent_marker[marker[0]][marker[1]]
    adjacent_marker[marker[0]][marker[1]] = 0
    blue_cell = next(
        (r, c) for r, row in enumerate(adjacent_marker) for c, value in enumerate(row)
        if value == 1
    )
    placed = False
    for drow in (-1, 0, 1):
        for dcol in (-1, 0, 1):
            row, col = blue_cell[0] + drow, blue_cell[1] + dcol
            if (
                0 <= row < len(adjacent_marker)
                and 0 <= col < len(adjacent_marker[0])
                and adjacent_marker[row][col] == 0
            ):
                adjacent_marker[row][col] = ctrl
                placed = True
                break
        if placed:
            break

    solid_rectangle = full_grid(7, 7, 0)
    solid_rectangle[0][0] = 4
    for row in (3, 4):
        for col in (3, 4):
            solid_rectangle[row][col] = 1

    return [
        ("missing_control_marker", no_marker),
        ("duplicate_control_marker", duplicate_marker),
        ("disconnected_blue_shape", disconnected),
        ("unexpected_foreground_color", wrong_color),
        ("marker_adjacent_to_shape", adjacent_marker),
        ("solid_rectangle_shape", solid_rectangle),
    ]
