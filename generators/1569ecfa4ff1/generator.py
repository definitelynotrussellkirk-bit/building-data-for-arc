"""Generator for ARC task 1569ecfa4ff1 — pivot-relative clockwise rotation.

The unique color-8 cell is a fixed pivot.  Every foreground cell of the one
other color moves by the relative-coordinate map ``(dr, dc) -> (dc, -dr)``;
the output is otherwise background and keeps the pivot unchanged.

The curriculum stays close to the five canonical dimension profiles while
varying pivot location, foreground color, cell count, and an unconstrained
asymmetric arrangement.  Every ordinary draw contains a directional witness:
clockwise, counterclockwise, half-turn, grid-center rotation, marker-only, and
solid-bounding-box rivals all disagree with the selected rule.
"""
from __future__ import annotations

import copy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1569ecfa4ff1"
TASK_ID = "1569ecfa4ff1"
VERSION = "2.0.1"
# Updated after the comment-preserving selected-source synchronization in this
# review; sha256[:12] of the whitespace-normalized selected Racket rule.
RULE_HASH = "094a5ceb0473"

SUMMARY = (
    "A zero-background grid has one color-8 pivot and three or four cells of "
    "one other color. Rotate each foreground cell 90 degrees clockwise around "
    "the pivot, preserve its color, keep the pivot fixed, and clear the old "
    "foreground positions."
)

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid uses one of the five canonical height/width profiles",
    "there is exactly one color-8 pivot and exactly one other nonzero color",
    "there are three or four foreground cells, all within two cells of the pivot",
    "the foreground spans both rows and columns and includes a diagonal pivot offset",
    "the clockwise rotation remains in bounds and is not an identity transformation",
]

GRID_PROFILES = ("7x7", "8x8", "7x9", "9x7", "8x9")
PIVOT_REGIONS = ("center", "northwest", "northeast", "southwest", "southeast")
FOREGROUND_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_profile": {
        "type": "str",
        "default": "keyed canonical profile",
        "valid": "7x7|8x8|7x9|9x7|8x9",
    },
    "pivot_region": {
        "type": "str",
        "default": "keyed visible pivot position",
        "valid": "center|northwest|northeast|southwest|southeast",
    },
    "n_cells": {
        "type": "int",
        "default": "keyed 3 or 4",
        "valid": "3|4",
    },
    "foreground_color": {
        "type": "int",
        "default": "keyed non-0/non-8 color",
        "valid": "1|2|3|4|5|6|7|9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PROFILE_DIMS = {
    "7x7": (7, 7),
    "8x8": (8, 8),
    "7x9": (7, 9),
    "9x7": (9, 7),
    "8x9": (8, 9),
}
_DIMS_PROFILE = {dims: name for name, dims in _PROFILE_DIMS.items()}

# Positions are deliberately at least two cells from every edge so any offset
# in [-2, 2]^2 and its quarter-turn remain in bounds.  Three entries reproduce
# canonical pivot placements exactly (7x9 NE, 9x7 SW, and 8x9 center).
_PIVOT_POSITIONS = {
    "7x7": {
        "center": (3, 3),
        "northwest": (2, 2),
        "northeast": (2, 4),
        "southwest": (4, 2),
        "southeast": (4, 4),
    },
    "8x8": {
        "center": (4, 4),
        "northwest": (2, 2),
        "northeast": (2, 5),
        "southwest": (5, 2),
        "southeast": (5, 5),
    },
    "7x9": {
        "center": (3, 4),
        "northwest": (2, 2),
        "northeast": (2, 6),
        "southwest": (4, 2),
        "southeast": (4, 6),
    },
    "9x7": {
        "center": (4, 3),
        "northwest": (2, 2),
        "northeast": (2, 4),
        "southwest": (5, 2),
        "southeast": (5, 4),
    },
    "8x9": {
        "center": (4, 5),
        "northwest": (2, 2),
        "northeast": (2, 6),
        "southwest": (5, 2),
        "southeast": (5, 6),
    },
}

_OFFSET_POOL = tuple(
    (dr, dc)
    for dr in range(-2, 3)
    for dc in range(-2, 3)
    if (dr, dc) != (0, 0)
)


def _cw(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    return dc, -dr


def _ccw(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    return -dc, dr


def _half(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    return -dr, -dc


def _transpose(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    return dc, dr


def _normalize_offsets(offsets: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(offsets))


def _shape_is_teaching(offsets: Iterable[tuple[int, int]]) -> bool:
    """A compact input-level discriminator, not merely a validity predicate."""
    shape = set(offsets)
    if len(shape) not in (3, 4) or (0, 0) in shape:
        return False
    rows = {dr for dr, _ in shape}
    cols = {dc for _, dc in shape}
    if len(rows) < 2 or len(cols) < 2:
        return False
    if not any(dr != 0 and dc != 0 for dr, dc in shape):
        return False
    if not any(abs(dr) + abs(dc) == 1 for dr, dc in shape):
        return False
    if max(abs(dr) for dr, _ in shape) > 2 or max(abs(dc) for _, dc in shape) > 2:
        return False
    row_span = max(rows) - min(rows) + 1
    col_span = max(cols) - min(cols) + 1
    if len(shape) == row_span * col_span:
        return False
    transforms = (
        {_cw(p) for p in shape},
        {_ccw(p) for p in shape},
        {_half(p) for p in shape},
        {_transpose(p) for p in shape},
    )
    if any(candidate == shape for candidate in transforms):
        return False
    if len({frozenset(candidate) for candidate in transforms}) != len(transforms):
        return False
    return True


def _choose_offsets(rng, n_cells: int) -> tuple[tuple[int, int], ...]:
    for _ in range(512):
        offsets = tuple(rng.sample(_OFFSET_POOL, n_cells))
        if _shape_is_teaching(offsets):
            return _normalize_offsets(offsets)
    # Fixed, asymmetric, sparse fallbacks.  They are used only if a Python RNG
    # regression makes the bounded search unexpectedly fail.
    fallback = {
        3: ((-1, 0), (0, 1), (1, 1)),
        4: ((-1, 0), (0, 1), (1, 1), (2, 0)),
    }[n_cells]
    if not _shape_is_teaching(fallback):
        raise RuntimeError("internal fallback shape is not teaching")
    return _normalize_offsets(fallback)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["rows must be non-empty lists"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    profile = _DIMS_PROFILE.get((height, width))
    if profile is None:
        errors.append(
            "dimensions must be one of 7x7, 8x8, 7x9, 9x7, or 8x9"
        )

    pivots = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-8 pivot; found {len(pivots)}")
        pivot = None
    else:
        pivot = pivots[0]

    colors = sorted({value for row in grid for value in row if value not in (0, 8)})
    if len(colors) != 1:
        errors.append(
            "expected exactly one foreground color besides 0 and 8; "
            f"found {colors}"
        )
        color = None
        cells: list[tuple[int, int]] = []
    else:
        color = colors[0]
        cells = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        ]
    if len(cells) not in (3, 4):
        errors.append(f"expected three or four foreground cells; found {len(cells)}")

    offsets: tuple[tuple[int, int], ...] = ()
    rotated_cells: tuple[tuple[int, int], ...] = ()
    if pivot is not None and cells:
        pr, pc = pivot
        offsets = _normalize_offsets((row - pr, col - pc) for row, col in cells)
        if any(max(abs(dr), abs(dc)) > 2 for dr, dc in offsets):
            errors.append("every foreground cell must lie within Chebyshev radius 2")
        if len({dr for dr, _ in offsets}) < 2 or len({dc for _, dc in offsets}) < 2:
            errors.append("foreground must span at least two rows and two columns")
        if not any(dr != 0 and dc != 0 for dr, dc in offsets):
            errors.append("foreground must include a diagonal offset from the pivot")
        if not any(abs(dr) + abs(dc) == 1 for dr, dc in offsets):
            errors.append("foreground must include a cell orthogonally adjacent to the pivot")
        row_span = max(dr for dr, _ in offsets) - min(dr for dr, _ in offsets) + 1
        col_span = max(dc for _, dc in offsets) - min(dc for _, dc in offsets) + 1
        if len(offsets) == row_span * col_span:
            errors.append("foreground must not be a solid rectangular block")
        rotated_cells = tuple((pr + dc, pc - dr) for dr, dc in offsets)
        if any(
            not (0 <= row < height and 0 <= col < width)
            for row, col in rotated_cells
        ):
            errors.append("clockwise rotation would leave the grid")
        if set(rotated_cells) == set(cells):
            errors.append("clockwise rotation must change the foreground positions")
        transformed = [
            {_cw(offset) for offset in offsets},
            {_ccw(offset) for offset in offsets},
            {_half(offset) for offset in offsets},
            {_transpose(offset) for offset in offsets},
        ]
        if len({frozenset(candidate) for candidate in transformed}) != len(transformed):
            errors.append("shape does not distinguish the named directional transforms")

    pivot_region = None
    if profile is not None and pivot is not None:
        pivot_region = next(
            (
                region
                for region, position in _PIVOT_POSITIONS[profile].items()
                if position == pivot
            ),
            None,
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "profile": profile,
        "pivot": pivot,
        "pivot_region": pivot_region,
        "color": color,
        "cells": tuple(cells),
        "offsets": offsets,
        "rotated_cells": rotated_cells,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes and verify exact overrides."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as "
                f"{observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared axis from a valid returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    if analysis["pivot_region"] is None:
        return {}
    return {
        "grid_profile": analysis["profile"],
        "pivot_region": analysis["pivot_region"],
        "n_cells": len(analysis["cells"]),
        "foreground_color": analysis["color"],
    }


def canonical_profile_signature(grid) -> str:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return (
        f"{analysis['profile']}:{analysis['pivot_region'] or 'other'}:"
        f"n{len(analysis['cells'])}:c{analysis['color']}"
    )


def strict_canonical_like(grid) -> list[str]:
    """The generated lawful manifold; all five canonical inputs satisfy it."""
    return self_check(grid)


def _paint_transform(
    grid: list[list[int]], transform: Callable[[tuple[int, int]], tuple[int, int]],
    *, fixed_color: int | None = None,
) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid pivot-rotation scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    pr, pc = analysis["pivot"]
    output[pr][pc] = 8
    color = analysis["color"] if fixed_color is None else fixed_color
    for offset in analysis["offsets"]:
        dr, dc = transform(offset)
        row, col = pr + dr, pc + dc
        if 0 <= row < analysis["height"] and 0 <= col < analysis["width"]:
            output[row][col] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; the selected Racket rule is authority."""
    return _paint_transform(grid, _cw)


def _rival_identity(grid):
    return copy.deepcopy(grid)


def _rival_counterclockwise(grid):
    return _paint_transform(grid, _ccw)


def _rival_half_turn(grid):
    return _paint_transform(grid, _half)


def _rival_transpose_about_pivot(grid):
    return _paint_transform(grid, _transpose)


def _rival_grid_center_clockwise(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    center = (analysis["height"] // 2, analysis["width"] // 2)
    output = full_grid(analysis["height"], analysis["width"], 0)
    pr, pc = analysis["pivot"]
    output[pr][pc] = 8
    cr, cc = center
    for row, col in analysis["cells"]:
        dr, dc = row - cr, col - cc
        new_row, new_col = cr + dc, cc - dr
        if 0 <= new_row < analysis["height"] and 0 <= new_col < analysis["width"]:
            output[new_row][new_col] = analysis["color"]
    return output


def _rival_pivot_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    output = full_grid(analysis["height"], analysis["width"], 0)
    pr, pc = analysis["pivot"]
    output[pr][pc] = 8
    return output


def _rival_fixed_color_4(grid):
    return _paint_transform(grid, _cw, fixed_color=4)


def _rival_rotate_filled_bbox(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    output = full_grid(analysis["height"], analysis["width"], 0)
    pr, pc = analysis["pivot"]
    output[pr][pc] = 8
    rotated = [_cw(offset) for offset in analysis["offsets"]]
    top = min(dr for dr, _ in rotated)
    bottom = max(dr for dr, _ in rotated)
    left = min(dc for _, dc in rotated)
    right = max(dc for _, dc in rotated)
    for dr in range(top, bottom + 1):
        for dc in range(left, right + 1):
            row, col = pr + dr, pc + dc
            if 0 <= row < analysis["height"] and 0 <= col < analysis["width"]:
                output[row][col] = analysis["color"]
    output[pr][pc] = 8
    return output


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "counterclockwise_about_pivot": _rival_counterclockwise,
    "half_turn_about_pivot": _rival_half_turn,
    "transpose_about_pivot": _rival_transpose_about_pivot,
    "clockwise_about_grid_center": _rival_grid_center_clockwise,
    "pivot_only": _rival_pivot_only,
    "correct_geometry_fixed_color_4": _rival_fixed_color_4,
    "rotate_filled_bounding_box": _rival_rotate_filled_bbox,
}


def _rival_differs(grid, name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


def _witness_direction(grid) -> bool:
    return all(
        _rival_differs(grid, name)
        for name in (
            "identity",
            "counterclockwise_about_pivot",
            "half_turn_about_pivot",
            "transpose_about_pivot",
        )
    )


def _witness_pivot_center(grid) -> bool:
    return _rival_differs(grid, "clockwise_about_grid_center")


def _witness_all_cells(grid) -> bool:
    return _rival_differs(grid, "pivot_only")


def _witness_color_preserved(grid) -> bool:
    return _rival_differs(grid, "correct_geometry_fixed_color_4")


def _witness_sparse_shape(grid) -> bool:
    return _rival_differs(grid, "rotate_filled_bounding_box")


SEMANTIC_WITNESSES = {
    "clockwise_direction_not_dihedral_rivals": _witness_direction,
    "unique_8_is_pivot_not_grid_center": _witness_pivot_center,
    "all_foreground_cells_move_not_marker_only": _witness_all_cells,
    "foreground_color_is_preserved": _witness_color_preserved,
    "rotate_cells_not_filled_bbox": _witness_sparse_shape,
}

WITNESS_RIVALS = {
    "clockwise_direction_not_dihedral_rivals": [
        "identity",
        "counterclockwise_about_pivot",
        "half_turn_about_pivot",
        "transpose_about_pivot",
    ],
    "unique_8_is_pivot_not_grid_center": ["clockwise_about_grid_center"],
    "all_foreground_cells_move_not_marker_only": ["pivot_only"],
    "foreground_color_is_preserved": ["correct_geometry_fixed_color_4"],
    "rotate_cells_not_filled_bbox": ["rotate_filled_bounding_box"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "identity",
        "counterclockwise_about_pivot",
        "half_turn_about_pivot",
        "transpose_about_pivot",
        "clockwise_about_grid_center",
        "pivot_only",
        "correct_geometry_fixed_color_4",
        "rotate_filled_bounding_box",
    )
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson on which a named wrong rule survives the demos."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with pivot-clockwise rule")
    query_input = query["input"]
    query_answer = rule_mirror(query_input)
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with pivot-clockwise rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
        )
        if survives and competitor(query_input) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons



def _draw_scheduled_choice(ctx, label: str, options: tuple, scheduled_index: int):
    """Use a lesson-safe visible schedule unless the caller explicitly overrides.

    The draw still flows through GenCtx, so provenance and exact-override
    validation remain available.  Consecutive sample indices visit consecutive
    values; two-demo lessons therefore cannot hide a fixed-color or centered-
    pivot rival behind two identical controls.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    scheduled = options[scheduled_index % len(options)]
    return ctx.draw_choice(label, (scheduled,))

def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("grid_profile", GRID_PROFILES)
    pivot_region = _draw_scheduled_choice(
        ctx, "pivot_region", PIVOT_REGIONS, sample_index
    )
    n_cells = ctx.draw_choice("n_cells", (3, 4))
    foreground_color = _draw_scheduled_choice(
        ctx, "foreground_color", FOREGROUND_COLORS, sample_index
    )

    height, width = _PROFILE_DIMS[profile]
    pivot = _PIVOT_POSITIONS[profile][pivot_region]
    offsets = _choose_offsets(ctx.draw_rng("foreground_offsets"), n_cells)
    # Difficulty changes only the presentation, never the underlying rule.
    # A quarter-turn/half-turn of an already asymmetric teaching shape remains
    # legal and keeps all named directional rivals distinguishable.
    band_transform = {
        None: lambda offset: offset,
        "easy": lambda offset: offset,
        "medium": _cw,
        "hard": _half,
    }[difficulty]
    offsets = _normalize_offsets(band_transform(offset) for offset in offsets)

    grid = full_grid(height, width, 0)
    pr, pc = pivot
    grid[pr][pc] = 8
    for dr, dc in offsets:
        grid[pr + dr][pc + dc] = foreground_color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={
            "overrides": {
                "grid_profile": profile,
                "pivot_region": pivot_region,
                "n_cells": n_cells,
                "foreground_color": foreground_color,
            }
        },
    )
    if errors:
        raise RuntimeError("internal construction error: " + "; ".join(errors))
    return grid
