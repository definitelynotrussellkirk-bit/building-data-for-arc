"""Generator for ARC task 4ee97d4d2321 — mirror across a cyan axis.

The first (and, in calibrated inputs, unique) full-height cyan column is a
vertical mirror axis.  Every non-zero cell outside the axis is copied to the
same row and equal distance on the opposite side when that destination is in
bounds.  Original cells stay in place; reflections that leave the grid are
ignored.

The teaching schedule covers all rule-critical source modes in every four
consecutive examples.  A twenty-slot Latin cycle independently crosses those
four modes with all five supported axis offsets, preventing axis position from
acting as a proxy for which side contains the source objects.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4ee97d4d2321"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "7546649ac4b7"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find the unique full-height cyan (8) column. Preserve the input, then "
    "copy every nonzero, non-axis cell to column 2*axis-c in the same row "
    "and color whenever that column is in bounds; ignore clipped reflections."
)

INVARIANTS = [
    "background is 0 and cyan occurs only in one full-height axis column",
    "4..10 non-{0,8} source cells use 2..4 colors",
    "source cells never occupy one another's reflected destinations",
    "every generated input has a visible in-bounds reflection",
    "every four consecutive samples cover left, right, both-side, and clipped cases",
    "every twenty scheduled samples cover all source-mode/axis-offset pairs",
]

SOURCE_MODES = ("left", "right", "both", "partial_oob")
AXIS_OFFSETS = (-2, -1, 0, 1, 2)
SOURCE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor every third sample; otherwise difficulty-banded",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor every third sample; otherwise difficulty-banded",
        "valid": "9..13",
    },
    "axis_offset": {
        "type": "int",
        "default": "twenty-slot Latin cross with source_mode",
        "valid": "-2..2",
        "doc": "axis column minus floor((grid_w-1)/2)",
    },
    "source_mode": {
        "type": "str",
        "default": "cyclic left|right|both|partial_oob by sample_index",
        "valid": "left|right|both|partial_oob",
    },
    "n_cells": {
        "type": "int",
        "default": "canonical 6/7 anchors; otherwise difficulty-banded",
        "valid": "4..10",
    },
    "n_colors": {
        "type": "int",
        "default": "2 on canonical anchors; otherwise cyclic 2..4",
        "valid": "2..4",
    },
}

# A centered axis in an odd-width grid has equally much room on both sides, so
# no source can have an out-of-bounds mirror while another remains in bounds.
# The generator adapts any unpinned member of this triple; only the fully pinned
# combinations below are impossible and therefore rejected explicitly.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {
        "source_mode": "partial_oob",
        "axis_offset": 0,
        "grid_w": [9, 11, 13],
    }
]

_CANONICAL_DIMS = ((7, 9), (8, 11), (9, 9), (6, 10), (8, 9))
_BAND_DIMS = {
    "easy": ((6, 9), (6, 10), (7, 9), (8, 10)),
    "medium": ((7, 10), (8, 11), (9, 12), (10, 11)),
    "hard": ((9, 11), (10, 12), (11, 13), (12, 13)),
}
def _schedule_profile_for_index(sample_index: int) -> tuple[str, int]:
    slot = int(sample_index) % len(SOURCE_MODES)
    block = int(sample_index) // len(SOURCE_MODES)
    return (
        SOURCE_MODES[slot],
        AXIS_OFFSETS[(block + slot) % len(AXIS_OFFSETS)],
    )


SCHEDULE_PROFILES = tuple(
    _schedule_profile_for_index(index)
    for index in range(len(SOURCE_MODES) * len(AXIS_OFFSETS))
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: int,
    lo: int,
    hi: int,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (default,)))


def _draw_choice_axis(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    options: Sequence[str],
) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, tuple(options)))
    return str(ctx.draw_choice(label, (default,)))


def schedule_profile(
    seed: int, sample_index: int, difficulty: Any = None
) -> tuple[str, int]:
    del seed, difficulty
    return _schedule_profile_for_index(sample_index)


def _scheduled_defaults(
    ctx,
    sample_index: int,
    band: str,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Choose a coherent default tuple before any exact axis is recorded."""
    rng = ctx.draw_rng("scheduled-defaults")
    scheduled_mode, default_offset = schedule_profile(
        ctx.seed, sample_index, band
    )
    canonical_anchor = sample_index % 3 == 0

    dims = _CANONICAL_DIMS if canonical_anchor else _BAND_DIMS[band]
    default_h, default_w = rng.choice(dims)
    mode_is_explicit = overrides.get("source_mode") is not None
    width_is_explicit = overrides.get("grid_w") is not None
    offset_is_explicit = overrides.get("axis_offset") is not None

    effective_mode = (
        str(overrides["source_mode"]) if mode_is_explicit else scheduled_mode
    )
    effective_width = (
        int(overrides["grid_w"]) if width_is_explicit else default_w
    )
    effective_offset = (
        int(overrides["axis_offset"]) if offset_is_explicit else default_offset
    )

    if (
        effective_mode == "partial_oob"
        and effective_offset == 0
        and effective_width % 2 == 1
    ):
        if not width_is_explicit:
            # Even width plus floor-centering leaves one extra column on the
            # right, which supplies the clipped source distance.
            default_w = 10 if band == "easy" else 12
            effective_width = default_w
        elif not offset_is_explicit:
            default_offset = 1
            effective_offset = default_offset
        elif not mode_is_explicit:
            scheduled_mode = "left"
            effective_mode = scheduled_mode
        else:
            raise ValueError(
                "incompatible overrides source_mode='partial_oob', "
                f"axis_offset=0, grid_w={effective_width}: a centered axis in "
                "an odd-width grid has no out-of-bounds mirror distance"
            )

    if canonical_anchor:
        default_cells = 6 + ((sample_index // 3) % 2)
        default_colors = 2
    else:
        cell_options = {
            "easy": (4, 5, 6),
            "medium": (6, 7, 8),
            "hard": (8, 9, 10),
        }[band]
        default_cells = cell_options[sample_index % len(cell_options)]
        default_colors = 2 + (sample_index % 3)

    return {
        "grid_h": default_h,
        "grid_w": default_w,
        "axis_offset": effective_offset,
        "source_mode": effective_mode,
        "n_cells": default_cells,
        "n_colors": default_colors,
    }


def _side_candidates(
    height: int,
    width: int,
    axis: int,
    side: str,
    *,
    in_bounds: bool | None,
) -> list[tuple[int, int]]:
    columns = range(axis) if side == "left" else range(axis + 1, width)
    cells: list[tuple[int, int]] = []
    for row in range(height):
        for col in columns:
            mirror_col = 2 * axis - col
            reflected = 0 <= mirror_col < width
            if in_bounds is None or reflected == in_bounds:
                cells.append((row, col))
    return cells


def _distance(axis: int, cell: tuple[int, int]) -> int:
    return abs(cell[1] - axis)


_SHAPES_BY_SIZE: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    2: (
        ((0, 0), (1, 0)),
        ((0, 0), (0, 1)),
    ),
    3: (
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (1, 1), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
        ((0, 1), (1, 1), (2, 1), (3, 0), (3, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
}


def _component_sizes(n_cells: int, n_colors: int) -> list[int]:
    base, remainder = divmod(n_cells, n_colors)
    return [base + (1 if index < remainder else 0) for index in range(n_colors)]


def _component_placements(
    height: int,
    width: int,
    axis: int,
    allowed: set[tuple[int, int]],
    size: int,
) -> list[tuple[tuple[int, int], ...]]:
    placements: set[tuple[tuple[int, int], ...]] = set()
    for shape in _SHAPES_BY_SIZE[size]:
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        for row0 in range(height - shape_h + 1):
            for col0 in range(width - shape_w + 1):
                cells = tuple(sorted((row0 + row, col0 + col) for row, col in shape))
                if not set(cells) <= allowed:
                    continue
                cell_set = set(cells)
                if any(
                    0 <= 2 * axis - col < width
                    and (row, 2 * axis - col) in cell_set
                    for row, col in cells
                ):
                    continue
                placements.add(cells)
    return sorted(placements)


def _placement_facts(
    placement: Sequence[tuple[int, int]],
    width: int,
    axis: int,
) -> dict[str, Any]:
    active = tuple(
        cell for cell in placement if 0 <= 2 * axis - cell[1] < width
    )
    clipped = tuple(cell for cell in placement if cell not in active)
    return {
        "active": active,
        "clipped": clipped,
        "distances": {abs(col - axis) for _, col in active},
        "left": any(col < axis for _, col in placement),
        "right": any(col > axis for _, col in placement),
    }


def _placement_allowed_for_component(
    facts: dict[str, Any],
    *,
    component_index: int,
    component_sizes: Sequence[int],
    mode: str,
) -> bool:
    # The first color component always supplies distance 1. When it has at
    # least two cells it also supplies distance 2; otherwise the second color
    # does. This makes the nearest-distance shortcut observably wrong.
    if component_index == 0:
        required = {1, 2} if component_sizes[0] >= 2 else {1}
        if not required <= facts["distances"]:
            return False
    elif component_index == 1 and component_sizes[0] == 1:
        if 2 not in facts["distances"]:
            return False

    if mode == "both":
        if component_index == 0 and not facts["left"]:
            return False
        if component_index == 1 and not facts["right"]:
            return False

    if mode == "partial_oob":
        if component_index in (0, 1) and not facts["active"]:
            return False
        if len(component_sizes) == 2 and component_index == 1:
            if not facts["clipped"]:
                return False
        elif len(component_sizes) >= 3 and component_index == 2:
            if not facts["clipped"]:
                return False
    return True


def _choose_components(
    rng,
    height: int,
    width: int,
    axis: int,
    mode: str,
    n_cells: int,
    n_colors: int,
) -> tuple[list[tuple[tuple[int, int], ...]], set[tuple[int, int]]]:
    if mode in ("left", "right"):
        allowed = set(
            _side_candidates(height, width, axis, mode, in_bounds=True)
        )
    elif mode == "both":
        allowed = set(
            _side_candidates(height, width, axis, "left", in_bounds=True)
            + _side_candidates(height, width, axis, "right", in_bounds=True)
        )
    elif mode == "partial_oob":
        left_span = axis
        right_span = width - axis - 1
        if left_span == right_span:
            raise ValueError(
                "source_mode='partial_oob' requires unequal room on the two sides"
            )
        side = "left" if left_span > right_span else "right"
        allowed = set(
            _side_candidates(height, width, axis, side, in_bounds=None)
        )
    else:
        raise ValueError(f"unknown source_mode: {mode!r}")

    sizes = _component_sizes(n_cells, n_colors)
    options: list[list[tuple[tuple[int, int], ...]]] = []
    for index, size in enumerate(sizes):
        candidates = _component_placements(
            height, width, axis, allowed, size
        )
        candidates = [
            placement
            for placement in candidates
            if _placement_allowed_for_component(
                _placement_facts(placement, width, axis),
                component_index=index,
                component_sizes=sizes,
                mode=mode,
            )
        ]
        rng.shuffle(candidates)
        if not candidates:
            raise ValueError(
                f"no connected placement for color component {index} "
                f"(size={size}, source_mode={mode!r})"
            )
        options.append(candidates)

    chosen: list[tuple[tuple[int, int], ...]] = []
    used: set[tuple[int, int]] = set()

    def search(index: int) -> bool:
        if index == len(options):
            flattened = [cell for component in chosen for cell in component]
            active = [
                cell for cell in flattened if 0 <= 2 * axis - cell[1] < width
            ]
            clipped = [cell for cell in flattened if cell not in active]
            distances = {abs(col - axis) for _, col in active}
            left = any(col < axis for _, col in flattened)
            right = any(col > axis for _, col in flattened)
            if not {1, 2} <= distances:
                return False
            if mode == "both" and not (left and right):
                return False
            if mode == "partial_oob" and not (active and clipped):
                return False
            active_components = sum(
                any(0 <= 2 * axis - col < width for _, col in component)
                for component in chosen
            )
            return active_components >= 2

        for placement in options[index]:
            cells = set(placement)
            if cells & used:
                continue
            if any(
                0 <= 2 * axis - col < width
                and (row, 2 * axis - col) in used
                for row, col in cells
            ):
                continue
            if any(
                0 <= 2 * axis - col < width
                and (row, 2 * axis - col) in cells
                for row, col in used
            ):
                continue
            chosen.append(placement)
            used.update(cells)
            if search(index + 1):
                return True
            chosen.pop()
            used.difference_update(cells)
        return False

    if not search(0):
        raise ValueError(
            f"could not place n_cells={n_cells}, n_colors={n_colors}, "
            f"source_mode={mode!r} without mirror-target collisions"
        )

    active_set = {
        cell
        for component in chosen
        for cell in component
        if 0 <= 2 * axis - cell[1] < width
    }
    return list(chosen), active_set


def _paint_components(
    grid: list[list[int]],
    components: Sequence[Sequence[tuple[int, int]]],
    n_colors: int,
    rng,
) -> None:
    palette = rng.sample(list(SOURCE_COLORS), n_colors)
    for color, component in zip(palette, components):
        for row, col in component:
            grid[row][col] = color


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    defaults = _scheduled_defaults(ctx, sample_index, band, overrides)

    height = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 6, 12)
    width = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 9, 13)
    mode = _draw_choice_axis(
        ctx, overrides, "source_mode", defaults["source_mode"], SOURCE_MODES
    )
    offset = _draw_int_axis(
        ctx, overrides, "axis_offset", defaults["axis_offset"], -2, 2
    )
    n_cells = _draw_int_axis(
        ctx, overrides, "n_cells", defaults["n_cells"], 4, 10
    )
    n_colors = _draw_int_axis(
        ctx, overrides, "n_colors", defaults["n_colors"], 2, 4
    )

    axis = (width - 1) // 2 + offset
    if not 1 <= axis < width - 1:
        raise ValueError(
            f"axis_offset={offset} places the axis at {axis} for grid_w={width}"
        )
    if mode == "partial_oob" and offset == 0 and width % 2 == 1:
        raise ValueError(
            "incompatible overrides source_mode='partial_oob', axis_offset=0, "
            f"grid_w={width}: a centered axis in an odd-width grid has no "
            "out-of-bounds mirror distance"
        )

    placement_rng = ctx.draw_rng("source-placement")
    components, active = _choose_components(
        placement_rng, height, width, axis, mode, n_cells, n_colors
    )
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][axis] = 8
    _paint_components(
        grid,
        components,
        n_colors,
        ctx.draw_rng("source-colors"),
    )

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "axis_offset": offset,
        "source_mode": mode,
        "n_cells": n_cells,
        "n_colors": n_colors,
    }
    if observed != expected:
        raise AssertionError(
            f"internal axis round-trip mismatch: expected {expected}, observed {observed}"
        )
    return grid


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {
        "grid_h": 0,
        "grid_w": 0,
        "axis": None,
        "axis_offset": None,
        "source_mode": None,
        "n_cells": 0,
        "n_colors": 0,
        "sources": (),
        "active_sources": (),
        "clipped_sources": (),
        "left_count": 0,
        "right_count": 0,
        "active_colors": (),
        "active_distances": (),
    }
    errors: list[str] = []
    if not _is_arc_grid(grid):
        return info, ["grid must be a nonempty rectangular ARC grid"]

    height, width = len(grid), len(grid[0])
    info["grid_h"], info["grid_w"] = height, width
    axes = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(axes) != 1:
        errors.append(
            f"expected exactly one full-height cyan axis column, found {len(axes)}"
        )
        return info, errors
    axis = axes[0]
    info["axis"] = axis
    info["axis_offset"] = axis - (width - 1) // 2

    extra_cyan = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8 and col != axis
    ]
    if extra_cyan:
        errors.append(
            f"cyan may occur only on the axis; found {len(extra_cyan)} off-axis cell(s)"
        )

    sources = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 8)
    ]
    source_set = set(sources)
    info["sources"] = tuple(sources)
    info["n_cells"] = len(sources)
    colors = {grid[row][col] for row, col in sources}
    info["n_colors"] = len(colors)
    if not sources:
        errors.append("at least one non-{0,8} source cell is required")
        return info, errors

    active: list[tuple[int, int]] = []
    clipped: list[tuple[int, int]] = []
    collisions: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for row, col in sources:
        mirror = (row, 2 * axis - col)
        if 0 <= mirror[1] < width:
            active.append((row, col))
            if mirror in source_set:
                collisions.append(((row, col), mirror))
        else:
            clipped.append((row, col))
    if collisions:
        errors.append(
            "source cells must not occupy reflected destinations; found "
            f"{len(collisions)} directed collision(s)"
        )

    left = sum(col < axis for _, col in sources)
    right = sum(col > axis for _, col in sources)
    info["left_count"], info["right_count"] = left, right
    info["active_sources"] = tuple(active)
    info["clipped_sources"] = tuple(clipped)
    info["active_colors"] = tuple(
        sorted({grid[row][col] for row, col in active})
    )
    info["active_distances"] = tuple(
        sorted({abs(col - axis) for _, col in active})
    )

    if left and right and not clipped:
        info["source_mode"] = "both"
    elif left and not right and not clipped:
        info["source_mode"] = "left"
    elif right and not left and not clipped:
        info["source_mode"] = "right"
    elif (left == 0 or right == 0) and active and clipped:
        info["source_mode"] = "partial_oob"
    return info, errors


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    if not 6 <= info["grid_h"] <= 12:
        errors.append(f"grid height must be 6..12, got {info['grid_h']}")
    if not 9 <= info["grid_w"] <= 13:
        errors.append(f"grid width must be 9..13, got {info['grid_w']}")
    if not -2 <= info["axis_offset"] <= 2:
        errors.append(
            f"axis offset must be -2..2, got {info['axis_offset']}"
        )
    if not 4 <= info["n_cells"] <= 10:
        errors.append(f"source count must be 4..10, got {info['n_cells']}")
    if not 2 <= info["n_colors"] <= 4:
        errors.append(f"source color count must be 2..4, got {info['n_colors']}")
    if not info["active_sources"]:
        errors.append("at least one source must have an in-bounds reflection")
    if info["source_mode"] not in SOURCE_MODES:
        errors.append("source layout does not match a calibrated source_mode")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return strict_canonical_like(grid)


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["source_mode"] not in SOURCE_MODES:
        raise ValueError("source layout has no exact source_mode observation")
    return {name: info[name] for name in AXES}


def _axis_for_rule(grid: Sequence[Sequence[int]]) -> int:
    height = len(grid)
    width = len(grid[0])
    axes = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if not axes:
        raise ValueError("rule requires a full-height cyan axis column")
    return axes[0]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python reference matching the selected Racket rule, including order."""
    if not _is_arc_grid(grid):
        raise ValueError("grid must be a nonempty rectangular ARC grid")
    axis = _axis_for_rule(grid)
    height, width = len(grid), len(grid[0])
    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            mirror_col = 2 * axis - col
            if (
                value != 0
                and col != axis
                and 0 <= mirror_col < width
            ):
                out[row][mirror_col] = value
    return out


def _rival_one_side(grid: Any, side: str) -> list[list[int]]:
    axis = _axis_for_rule(grid)
    height, width = len(grid), len(grid[0])
    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            on_selected_side = col < axis if side == "left" else col > axis
            mirror_col = 2 * axis - col
            if value not in (0, 8) and on_selected_side and 0 <= mirror_col < width:
                out[row][mirror_col] = value
    return out


def _rival_left_only(grid: Any) -> list[list[int]]:
    return _rival_one_side(grid, "left")


def _rival_right_only(grid: Any) -> list[list[int]]:
    return _rival_one_side(grid, "right")


def _rival_axis_offset_side(grid: Any) -> list[list[int]]:
    """Infer the source side from axis displacement instead of the scene."""
    axis = _axis_for_rule(grid)
    height, width = len(grid), len(grid[0])
    offset = axis - (width - 1) // 2
    if offset == 0:
        selected_side = "both"
    elif abs(offset) == 1:
        selected_side = "left" if offset < 0 else "right"
    else:
        selected_side = "right" if offset < 0 else "left"

    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value in (0, 8):
                continue
            if selected_side == "left" and col > axis:
                continue
            if selected_side == "right" and col < axis:
                continue
            mirror_col = 2 * axis - col
            if 0 <= mirror_col < width:
                out[row][mirror_col] = value
    return out


def _rival_grid_center(grid: Any) -> list[list[int]]:
    true_axis = _axis_for_rule(grid)
    height, width = len(grid), len(grid[0])
    center = (width - 1) // 2
    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            mirror_col = 2 * center - col
            if (
                value != 0
                and col != true_axis
                and 0 <= mirror_col < width
            ):
                out[row][mirror_col] = value
    return out


def _rival_drop_clipped_originals(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = rule_mirror(grid)
    for row, col in info["clipped_sources"]:
        out[row][col] = 0
    return out


def _rival_nearest_distance_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    axis = info["axis"]
    nearest = min(info["active_distances"])
    height, width = len(grid), len(grid[0])
    out = deepcopy(grid)
    for row, col in info["active_sources"]:
        if abs(col - axis) == nearest:
            mirror_col = 2 * axis - col
            if 0 <= mirror_col < width:
                out[row][mirror_col] = grid[row][col]
    return out


def _rival_lowest_active_color_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    axis = info["axis"]
    selected_color = min(info["active_colors"])
    width = len(grid[0])
    out = deepcopy(grid)
    for row, col in info["active_sources"]:
        if grid[row][col] == selected_color:
            mirror_col = 2 * axis - col
            if 0 <= mirror_col < width:
                out[row][mirror_col] = grid[row][col]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "mirror_left_side_only": _rival_left_only,
    "mirror_right_side_only": _rival_right_only,
    "infer_source_side_from_axis_offset": _rival_axis_offset_side,
    "mirror_across_grid_center": _rival_grid_center,
    "drop_sources_with_clipped_reflections": _rival_drop_clipped_originals,
    "mirror_nearest_distance_only": _rival_nearest_distance_only,
    "mirror_lowest_active_color_only": _rival_lowest_active_color_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_mode(mode: str) -> Callable[[Any], bool]:
    def witness(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and info["source_mode"] == mode

    return witness


def _witness_off_center(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["axis_offset"] != 0


def _witness_multiple_active_distances(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and len(info["active_distances"]) >= 2


def _witness_multiple_active_colors(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and len(info["active_colors"]) >= 2


SEMANTIC_WITNESSES = {
    "left_only_sources": _witness_mode("left"),
    "right_only_sources": _witness_mode("right"),
    "sources_on_both_sides": _witness_mode("both"),
    "partial_out_of_bounds_reflections": _witness_mode("partial_oob"),
    "off_center_axis": _witness_off_center,
    "multiple_active_distances": _witness_multiple_active_distances,
    "multiple_active_colors": _witness_multiple_active_colors,
}
WITNESS_RIVALS = {
    "left_only_sources": ["mirror_right_side_only"],
    "right_only_sources": ["mirror_left_side_only"],
    "sources_on_both_sides": [
        "mirror_left_side_only",
        "mirror_right_side_only",
    ],
    "partial_out_of_bounds_reflections": [
        "drop_sources_with_clipped_reflections"
    ],
    "off_center_axis": ["mirror_across_grid_center"],
    "multiple_active_distances": ["mirror_nearest_distance_only"],
    "multiple_active_colors": ["mirror_lowest_active_color_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    modes: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the mirror rule")
        if info["source_mode"] is not None:
            modes.add(info["source_mode"])

    missing_modes = sorted(set(SOURCE_MODES) - modes)
    if missing_modes:
        reasons.append(f"demonstrations miss source modes: {missing_modes}")

    survivors: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(
                rival(pair["input"]) == pair["output"]
                for pair in demos
                if isinstance(pair, dict)
                and "input" in pair
                and "output" in pair
            ):
                survivors.append(name)
        except Exception as exc:
            reasons.append(
                f"competitor {name!r} could not be evaluated: "
                f"{type(exc).__name__}: {exc}"
            )
    if survivors:
        reasons.append(f"demonstrations do not refute competitors: {survivors}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the mirror rule")
    return reasons
