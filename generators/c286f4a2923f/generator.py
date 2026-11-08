"""Generator for S15_E5: transfer a source mask into a target rectangle.

The color-2 source is interpreted in local coordinates relative to its bounding
box.  The same occupied offsets are painted color 8 at the top-left corner of
the solid color-3 target rectangle; every other cell becomes background.

The lesson schedule deliberately includes equal-count/different-shape sources,
a source with an internal hole, padded targets, both left/right layouts,
canonical-size anchors in every difficulty band, and broader variable canvases.
The semantic contract also checks center/bottom-right alignment and
"mirror-toward-target" rivals that fit every public canonical pair.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c286f4a2923f"
VERSION = "4.0.0"
TASK_ID = "c286f4a2923f"
RULE_HASH = "496d98097154"

SUMMARY = (
    "On a 0-background grid, read the single connected color-2 source as exact "
    "offsets from its own top-left corner. Find the single solid color-3 target "
    "rectangle and stamp those offsets at the target's top-left corner in color "
    "8 on an otherwise blank same-size output. Source orientation is preserved; "
    "unused target cells, the source, and the original target disappear."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input palette is exactly background 0 plus source color 2 and target color 3",
    "there is exactly one 4-connected color-2 source component",
    "the source is one of several connected non-rectangular masks, including equal-count alternatives and a holed mask",
    "there is exactly one 4-connected color-3 component and it is a solid rectangle",
    "the target rectangle is at least as tall and wide as the source bounding box",
    "source and target are horizontally separated by at least one background column",
    "both objects have a one-cell background margin from the canvas border",
]

SOURCE_SHAPES = (
    # Symmetric masks occupy even residues (source on the left); every odd
    # residue is horizontally asymmetric and appears with the source on the
    # right.  Thus every three-example window rebuts a "mirror toward target"
    # shortcut while residues 0/1 retain the equal-count teaching pair.
    "t_2x3",
    "l_3x2",
    "ring_3x3",
    "c_3x2",
    "cross_3x3",
    "zigzag_3x3",
)
SOURCE_SIDES = ("left", "right")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample_index canonical-profile anchor or difficulty-aware draw",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "sample_index canonical-profile anchor or difficulty-aware draw",
        "valid": "13..20",
    },
    "source_shape": {
        "type": "enum",
        "default": "sample_index schedule",
        "valid": "|".join(SOURCE_SHAPES),
    },
    "target_extra_h": {
        "type": "int",
        "default": "sample_index schedule",
        "valid": "0..2",
    },
    "target_extra_w": {
        "type": "int",
        "default": "sample_index schedule",
        "valid": "0..2",
    },
    "source_side": {
        "type": "enum",
        "default": "sample_index schedule",
        "valid": "|".join(SOURCE_SIDES),
    },
}

_SOURCE_CELLS = {
    # Canonical train example 1. Four cells.
    "l_3x2": ((0, 0), (1, 0), (2, 0), (2, 1)),
    # Canonical train example 2. Also four cells, so count alone is insufficient.
    "t_2x3": ((0, 1), (1, 0), (1, 1), (1, 2)),
    # A connected ring whose center must remain blank after transfer.
    "ring_3x3": (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
    # Canonical test example.
    "c_3x2": ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    "cross_3x3": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "zigzag_3x3": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
}
_SHAPE_FROM_CELLS = {
    tuple(sorted(cells)): name for name, cells in _SOURCE_CELLS.items()
}
_EXTRA_H_SCHEDULE = (0, 1, 2, 0, 2, 1)
_EXTRA_W_SCHEDULE = (0, 2, 1, 2, 0, 1)
_CANONICAL_GRID_PROFILES = ((8, 13), (9, 13), (9, 14))


def _shape_size(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _scheduled_choice(ctx, label, options, sample_index, *, offset=0):
    """Record a deterministic lesson schedule while honoring exact overrides."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    value = options[(sample_index + offset) % len(options)]
    return ctx.draw_choice(label, (value,))


def _scheduled_int(ctx, label, values, sample_index):
    """Schedule a small exact integer axis; explicit overrides use full bounds."""
    lo, hi = min(values), max(values)
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    value = values[sample_index % len(values)]
    return ctx.draw_int(label, value, value)


def _draw_grid_size(ctx, sample_index):
    """Interleave public-scale anchors without collapsing broader bands.

    Every third sample uses one of the three canonical (height, width) profiles,
    cycling through all of them every nine samples.  Explicit per-axis
    overrides still take precedence and use the full declared range.
    """
    anchor = None
    if sample_index % 3 == 0:
        anchor = _CANONICAL_GRID_PROFILES[
            (sample_index // 3) % len(_CANONICAL_GRID_PROFILES)
        ]

    values = []
    for index, (label, lo, hi) in enumerate(
        (("grid_h", 8, 16), ("grid_w", 13, 20))
    ):
        if label in ctx.overrides and ctx.overrides[label] is not None:
            values.append(ctx.draw_int_diff(label, lo, hi))
        elif anchor is not None:
            values.append(ctx.draw_int(label, anchor[index], anchor[index]))
        else:
            values.append(ctx.draw_int_diff(label, lo, hi))
    return tuple(values)


def _paint_cells(grid, top, left, cells, color):
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _paint_rect(grid, top, left, height, width, color):
    for r in range(top, top + height):
        for c in range(left, left + width):
            grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_h, grid_w = _draw_grid_size(ctx, sample_index)
    source_shape = _scheduled_choice(
        ctx, "source_shape", SOURCE_SHAPES, sample_index
    )
    target_extra_h = _scheduled_int(
        ctx, "target_extra_h", _EXTRA_H_SCHEDULE, sample_index
    )
    target_extra_w = _scheduled_int(
        ctx, "target_extra_w", _EXTRA_W_SCHEDULE, sample_index
    )
    source_side = _scheduled_choice(
        ctx, "source_side", SOURCE_SIDES, sample_index
    )

    source_cells = _SOURCE_CELLS[source_shape]
    source_h, source_w = _shape_size(source_cells)
    target_h = source_h + target_extra_h
    target_w = source_w + target_extra_w

    # The declared minima guarantee this grammar is feasible at every boundary:
    # one-cell outer margins, both objects, and at least one blank separator.
    interior_w = grid_w - 2
    max_gap = interior_w - source_w - target_w
    if max_gap < 1 or grid_h < max(source_h, target_h) + 2:
        raise ValueError(
            "incompatible dimensions for source/target grammar: "
            f"grid={grid_h}x{grid_w}, source={source_h}x{source_w}, "
            f"target={target_h}x{target_w}"
        )

    rng = ctx.draw_rng("layout")
    gap = rng.randint(1, min(3, max_gap))
    slack = interior_w - source_w - target_w - gap
    leftmost = 1 + rng.randint(0, slack)

    if source_side == "left":
        source_c = leftmost
        target_c = source_c + source_w + gap
    else:
        target_c = leftmost
        source_c = target_c + target_w + gap

    source_r = rng.randint(1, grid_h - source_h - 1)
    target_r = rng.randint(1, grid_h - target_h - 1)

    grid = full_grid(grid_h, grid_w, 0)
    _paint_cells(grid, source_r, source_c, source_cells, 2)
    _paint_rect(grid, target_r, target_c, target_h, target_w, 3)
    return grid


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    stack.append((nr, nc))
        result.append(cells)
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalized(cells):
    r1, c1, _, _ = _bbox(cells)
    return tuple(sorted((r - r1, c - c1) for r, c in cells))


def _analyze(grid):
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular and non-empty"]
    height = len(grid)
    if not (8 <= height <= 16 and 13 <= width <= 20):
        errors.append(f"grid size {height}x{width} lies outside 8..16 by 13..20")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value not in (0, 2, 3)
        for row in grid
        for value in row
    ):
        errors.append("input palette must contain only colors 0, 2, and 3")

    source_components = _components(grid, 2)
    target_components = _components(grid, 3)
    if len(source_components) != 1:
        errors.append(
            f"expected exactly one color-2 source component, found {len(source_components)}"
        )
    if len(target_components) != 1:
        errors.append(
            f"expected exactly one color-3 target component, found {len(target_components)}"
        )
    if len(source_components) != 1 or len(target_components) != 1:
        return {}, errors

    source = source_components[0]
    target = target_components[0]
    sr1, sc1, sr2, sc2 = _bbox(source)
    tr1, tc1, tr2, tc2 = _bbox(target)
    source_h, source_w = sr2 - sr1 + 1, sc2 - sc1 + 1
    target_h, target_w = tr2 - tr1 + 1, tc2 - tc1 + 1

    source_shape = _SHAPE_FROM_CELLS.get(_normalized(source), "unknown")
    if source_shape == "unknown":
        errors.append("source mask is not one of the supported non-rectangular teaching shapes")

    expected_target = {
        (r, c)
        for r in range(tr1, tr2 + 1)
        for c in range(tc1, tc2 + 1)
    }
    if set(target) != expected_target:
        errors.append("color-3 target component is not a solid rectangle")

    target_extra_h = target_h - source_h
    target_extra_w = target_w - source_w
    if not (0 <= target_extra_h <= 2 and 0 <= target_extra_w <= 2):
        errors.append(
            "target rectangle must exceed the source bbox by 0..2 rows and 0..2 columns; "
            f"observed extras {target_extra_h}x{target_extra_w}"
        )

    if sc2 + 1 < tc1:
        source_side = "left"
        separator = tc1 - sc2 - 1
    elif tc2 + 1 < sc1:
        source_side = "right"
        separator = sc1 - tc2 - 1
    else:
        source_side = "overlap"
        separator = 0
        errors.append(
            "source and target must be horizontally separated by at least one background column"
        )
    if source_side != "overlap" and separator < 1:
        errors.append("source and target lack a full background separator column")

    for label, (r1, c1, r2, c2) in {
        "source": (sr1, sc1, sr2, sc2),
        "target": (tr1, tc1, tr2, tc2),
    }.items():
        if r1 < 1 or c1 < 1 or r2 > height - 2 or c2 > width - 2:
            errors.append(f"{label} lacks a one-cell background margin from the border")

    return {
        "grid_h": height,
        "grid_w": width,
        "source_shape": source_shape,
        "target_extra_h": target_extra_h,
        "target_extra_w": target_extra_w,
        "source_side": source_side,
        "source_bbox": (sr1, sc1, sr2, sc2),
        "target_bbox": (tr1, tc1, tr2, tc2),
        "source_cells": tuple(sorted(source)),
        "target_cells": tuple(sorted(target)),
    }, errors


def observe_overrides(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {axis: info[axis] for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes that do not uniquely instantiate the mask-transfer rule."""
    info, errors = _analyze(grid)
    requested = (meta or {}).get("overrides") if isinstance(meta, dict) else None
    if not errors and isinstance(requested, dict):
        observed = {axis: info[axis] for axis in AXES}
        for axis, expected in requested.items():
            if axis in AXES and observed.get(axis) != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the complete lawful input grammar used by this generator."""
    return _analyze(grid)[1]


def _source_offsets(info):
    sr1, sc1, _, _ = info["source_bbox"]
    return tuple((r - sr1, c - sc1) for r, c in info["source_cells"])


def _render_offsets(grid, offsets, *, row_shift=0, col_shift=0):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    tr1, tc1, _, _ = info["target_bbox"]
    out = full_grid(len(grid), len(grid[0]), 0)
    _paint_cells(out, tr1 + row_shift, tc1 + col_shift, offsets, 8)
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror of the selected Racket rule for semantic review hooks."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    return _render_offsets(grid, _source_offsets(info))


def _rival_center_mask_in_target(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    sr1, sc1, sr2, sc2 = info["source_bbox"]
    tr1, tc1, tr2, tc2 = info["target_bbox"]
    source_h, source_w = sr2 - sr1 + 1, sc2 - sc1 + 1
    target_h, target_w = tr2 - tr1 + 1, tc2 - tc1 + 1
    return _render_offsets(
        grid,
        _source_offsets(info),
        row_shift=(target_h - source_h) // 2,
        col_shift=(target_w - source_w) // 2,
    )


def _rival_bottom_right_mask_in_target(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    sr1, sc1, sr2, sc2 = info["source_bbox"]
    tr1, tc1, tr2, tc2 = info["target_bbox"]
    source_h, source_w = sr2 - sr1 + 1, sc2 - sc1 + 1
    target_h, target_w = tr2 - tr1 + 1, tc2 - tc1 + 1
    return _render_offsets(
        grid,
        _source_offsets(info),
        row_shift=target_h - source_h,
        col_shift=target_w - source_w,
    )


def _rival_mirror_source_toward_target(grid: Any) -> list[list[int]]:
    """Plausible reading-direction rule: reflect only when source is right."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    offsets = _source_offsets(info)
    if info["source_side"] == "right":
        _, sc1, _, sc2 = info["source_bbox"]
        source_w = sc2 - sc1 + 1
        offsets = tuple((dr, source_w - 1 - dc) for dr, dc in offsets)
    return _render_offsets(grid, offsets)


def _rival_fill_source_bbox(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    sr1, sc1, sr2, sc2 = info["source_bbox"]
    offsets = tuple(
        (dr, dc)
        for dr in range(sr2 - sr1 + 1)
        for dc in range(sc2 - sc1 + 1)
    )
    return _render_offsets(grid, offsets)


def _rival_recolor_target(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    tr1, tc1, tr2, tc2 = info["target_bbox"]
    out = full_grid(len(grid), len(grid[0]), 0)
    _paint_rect(out, tr1, tc1, tr2 - tr1 + 1, tc2 - tc1 + 1, 8)
    return out


def _rival_cell_count_row_major(grid: Any) -> list[list[int]]:
    """Ignore source geometry; paint the same number of target cells row-major."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid mask-transfer input: " + "; ".join(errors))
    tr1, tc1, tr2, tc2 = info["target_bbox"]
    target_w = tc2 - tc1 + 1
    count = len(info["source_cells"])
    offsets = tuple((index // target_w, index % target_w) for index in range(count))
    return _render_offsets(grid, offsets)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "center_mask_in_target": _rival_center_mask_in_target,
    "bottom_right_mask_in_target": _rival_bottom_right_mask_in_target,
    "mirror_source_toward_target": _rival_mirror_source_toward_target,
    "fill_source_bbox": _rival_fill_source_bbox,
    "recolor_target": _rival_recolor_target,
    "cell_count_row_major": _rival_cell_count_row_major,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "center_mask_in_target",
        "bottom_right_mask_in_target",
        "mirror_source_toward_target",
    )
}


def _witness_any_padding(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return not errors and bool(info["target_extra_h"] or info["target_extra_w"])


def _witness_two_cell_padding(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return not errors and bool(
        info["target_extra_h"] >= 2 or info["target_extra_w"] >= 2
    )


def _witness_right_asymmetric_source(grid: Any) -> bool:
    info, errors = _analyze(grid)
    if errors or info["source_side"] != "right":
        return False
    offsets = _source_offsets(info)
    _, sc1, _, sc2 = info["source_bbox"]
    source_w = sc2 - sc1 + 1
    mirrored = tuple(sorted((dr, source_w - 1 - dc) for dr, dc in offsets))
    return tuple(sorted(offsets)) != mirrored


def _witness_internal_hole(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return not errors and info["source_shape"] == "ring_3x3"


def _witness_geometry_not_count_or_target_fill(grid: Any) -> bool:
    if _analyze(grid)[1]:
        return False
    expected = rule_mirror(grid)
    return (
        _rival_cell_count_row_major(grid) != expected
        and _rival_recolor_target(grid) != expected
    )


SEMANTIC_WITNESSES = {
    "padded_target_rejects_bottom_right_anchor": _witness_any_padding,
    "two_cell_padding_rejects_center_anchor": _witness_two_cell_padding,
    "right_side_asymmetric_source_preserves_orientation": (
        _witness_right_asymmetric_source
    ),
    "internal_hole_stays_blank": _witness_internal_hole,
    "exact_offsets_not_count_or_target_fill": (
        _witness_geometry_not_count_or_target_fill
    ),
}
WITNESS_RIVALS = {
    "padded_target_rejects_bottom_right_anchor": [
        "bottom_right_mask_in_target"
    ],
    "two_cell_padding_rejects_center_anchor": ["center_mask_in_target"],
    "right_side_asymmetric_source_preserves_orientation": [
        "mirror_source_toward_target"
    ],
    "internal_hole_stays_blank": ["fill_source_bbox"],
    "exact_offsets_not_count_or_target_fill": [
        "cell_count_row_major",
        "recolor_target",
    ],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require each three-demo lesson to eliminate every named rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match mask transfer")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query input is invalid: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match mask transfer")

    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
                reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def mutation_fixtures():
    """Task-semantic impostors that the structural checker must reject."""
    base = generate(
        911,
        2,
        difficulty="medium",
        grid_h=10,
        grid_w=16,
        source_shape="ring_3x3",
        target_extra_h=2,
        target_extra_w=2,
        source_side="left",
    )
    info = observe_overrides(base)
    _, structural = _analyze(base)
    if structural:
        raise AssertionError(structural)

    # Recover boxes from the internal analyzer once; fixtures are then plain grids.
    detail, _ = _analyze(base)
    sr1, sc1, sr2, sc2 = detail["source_bbox"]
    tr1, tc1, tr2, tc2 = detail["target_bbox"]

    missing_source = deepcopy(base)
    for r, c in detail["source_cells"]:
        missing_source[r][c] = 0

    disconnected_source = deepcopy(base)
    disconnected_source[sr1][sc1 + 1] = 0
    disconnected_source[sr1 + 1][sc1] = 0

    target_with_hole = deepcopy(base)
    target_with_hole[(tr1 + tr2) // 2][(tc1 + tc2) // 2] = 0

    target_too_short = deepcopy(base)
    for c in range(tc1, tc2 + 1):
        target_too_short[tr2][c] = 0
    for c in range(tc1, tc2 + 1):
        target_too_short[tr2 - 1][c] = 0
    for c in range(tc1, tc2 + 1):
        target_too_short[tr2 - 2][c] = 0

    solid_source = deepcopy(base)
    for r in range(sr1, sr2 + 1):
        for c in range(sc1, sc2 + 1):
            solid_source[r][c] = 2

    extra_color = deepcopy(base)
    extra_color[0][0] = 4

    return [
        ("missing_source_marker_as_answer", missing_source),
        ("disconnected_source_count_only", disconnected_source),
        ("target_rectangle_with_hole", target_with_hole),
        ("source_does_not_fit_target", target_too_short),
        ("solid_source_bbox_fill_shortcut", solid_source),
        ("unexplained_extra_color", extra_color),
    ]
