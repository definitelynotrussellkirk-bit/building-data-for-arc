"""Generator for Marker-Count Scale (task 486794347a11).

The top row is a key: its number of blue (1) cells is the integer scale factor.
After those key cells are erased, the remaining one-colour object is cropped to
its tight bounding box and enlarged by nearest-neighbour cell replication.

The schedule deliberately breaks shortcuts that fit every canonical pair:
``grid-height parity -> scale``, ``body-colour parity -> scale``, marker
position/spacing rules, and ``rightmost blue marker -> scale``.  Consecutive
lessons therefore expose the actual cell-count relation rather than accidental
correlations in the canonical examples or the generated marker layouts.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "486794347a11"
TASK_ID = GENERATOR_ID
VERSION = "4.2.0"
RULE_HASH = "ba0ff57b853e"

SUMMARY = (
    "Count the colour-1 cells in the top row to obtain K. Erase those marker "
    "cells, crop the unique connected one-colour object below the blank "
    "separator row to its tight bounding box, and enlarge that crop by factor "
    "K in both dimensions; each source cell becomes a K by K block."
)

INVARIANTS = [
    "background is colour 0",
    "row 0 contains exactly two or three colour-1 marker cells and no other colour",
    "row 1 is an all-zero separator",
    "below row 1 there is exactly one 4-connected object in one colour from 2..9",
    "the object is a supported non-rectangular 2x2, 2x3, or 3x2 shape",
    "the upscaled crop has smaller area than the input, matching the canonical size relation",
]

# These are the only caller-facing exact knobs.  Every value is recoverable
# from the returned grid by observe_overrides(), and every Cartesian boundary
# combination is constructible on the minimum 7x8 canvas.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 7..12", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "scheduled 8..14", "valid": "8..14"},
    "n_markers": {"type": "int", "default": "alternating 2,3", "valid": "2..3"},
    "blob_color": {"type": "color", "default": "scheduled 2..9", "valid": "2..9"},
    "shape_kind": {
        "type": "str",
        "default": "scheduled supported shape",
        "valid": [
            "l3_right",
            "l3_left",
            "s4_h",
            "z4_h",
            "s4_v",
            "z4_v",
            "t4_down",
            "l4_right",
        ],
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
MIN_STRICT_FRAC = 1.0
# Four demonstrations are the minimum window that always contains a
# counterexample to every declared marker-geometry rival in the eight-slot
# schedule.  Three can leave the span/min-gap proxy alive for the query.
EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = tuple(range(4))

# Binary masks, already tight-cropped.  The first four include every canonical
# body shape; the rest add lawful orientation/texture variation.  All have bbox
# area <= 6, so even K=3 produces at most 54 output cells, below the minimum
# 7x8 input area.
SHAPES: dict[str, tuple[tuple[int, ...], ...]] = {
    "l3_right": ((1, 0), (1, 1)),
    "l3_left": ((0, 1), (1, 1)),
    "s4_h": ((0, 1, 1), (1, 1, 0)),
    "z4_h": ((1, 1, 0), (0, 1, 1)),
    "s4_v": ((1, 0), (1, 1), (0, 1)),
    "z4_v": ((0, 1), (1, 1), (1, 0)),
    "t4_down": ((1, 1, 1), (0, 1, 0)),
    "l4_right": ((1, 0, 0), (1, 1, 1)),
}
_SHAPE_BY_MASK = {mask: name for name, mask in SHAPES.items()}
_SHAPE_NAMES = tuple(SHAPES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-phase lesson schedule; seed/difficulty affect layout, not the profile."""
    del seed, difficulty
    return int(sample_index) % 4


def _scheduled_defaults(seed: int, sample_index: int) -> dict[str, Any]:
    """Return a correlation-breaking exact-axis schedule.

    Phases 0/1 preserve the canonical parity shortcuts; phases 2/3 invert them.
    Every three consecutive demonstrations therefore contain a counterexample.
    """
    index = int(sample_index)
    phase = index % 4
    schedule_rng = stable_rng(int(seed), f"{TASK_ID}|{index}|scheduled_axes", VERSION)

    # K alternates, so any three consecutive demonstrations show both factors.
    n_markers = 2 + (index % 2)

    # Rival: odd height -> 2, even height -> 3.  Phases 2/3 invert it.
    odd_height = schedule_rng.choice((7, 7, 7, 7, 9, 11))
    even_height = schedule_rng.choice((8, 8, 8, 8, 10, 12))
    grid_h = odd_height if phase in (0, 3) else even_height

    # Seed variation covers the full width domain while retaining substantial
    # support for the canonical 7x8/8x9/7x10/8x8 profiles.
    grid_w = schedule_rng.choice((8, 8, 8, 8, 9, 9, 10, 10, 11, 12, 13, 14))

    # Rival: even body colour -> 2, odd body colour -> 3.  Again invert on 2/3.
    even_colour = schedule_rng.choice((2, 4, 6, 8))
    odd_colour = schedule_rng.choice((3, 5, 7, 9))
    blob_color = even_colour if phase in (0, 3) else odd_colour

    return {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_markers": n_markers,
        "blob_color": blob_color,
        "shape_kind": schedule_rng.choice(_SHAPE_NAMES),
    }


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            values = [int(ch) for ch in row.strip()]
        elif isinstance(row, (list, tuple)):
            values = [int(value) for value in row]
        else:
            raise ValueError("every grid row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(value < 0 or value > 9 for value in values):
            raise ValueError("grid colours must be integers in 0..9")
        rows.append(values)
    return rows


def _normalised_body_mask(
    cells: list[tuple[int, int]],
) -> tuple[tuple[tuple[int, ...], ...], tuple[int, int, int, int]]:
    rs = [row for row, _ in cells]
    cs = [col for _, col in cells]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    mask = tuple(
        tuple(int((r1 + rr, c1 + cc) in set(cells)) for cc in range(c2 - c1 + 1))
        for rr in range(r2 - r1 + 1)
    )
    return mask, (r1, c1, r2, c2)


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    start = next(iter(cells))
    queue = deque([start])
    seen = {start}
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    errors: list[str] = []
    if not (7 <= h <= 12):
        errors.append(f"grid height {h} outside supported 7..12")
    if not (8 <= w <= 14):
        errors.append(f"grid width {w} outside supported 8..14")

    row0 = values[0]
    markers = [col for col, value in enumerate(row0) if value == 1]
    other_top = [(col, value) for col, value in enumerate(row0) if value not in (0, 1)]
    if len(markers) not in (2, 3):
        errors.append(f"top row has {len(markers)} colour-1 markers, expected 2 or 3")
    if other_top:
        errors.append("top row contains a non-{0,1} colour")
    if any(value != 0 for value in values[1]):
        errors.append("row 1 must be an all-zero separator")

    below_ones = [(r, c) for r in range(1, h) for c in range(w) if values[r][c] == 1]
    if below_ones:
        errors.append("colour 1 may occur only in row 0")

    body_cells = [(r, c) for r in range(2, h) for c in range(w) if values[r][c] != 0]
    body_colours = {values[r][c] for r, c in body_cells}
    if not body_cells:
        errors.append("no body object below the separator")
        return {
            "errors": errors,
            "grid": values,
            "height": h,
            "width": w,
            "markers": markers,
            "n_markers": len(markers),
        }
    if len(body_colours) != 1:
        errors.append(f"body uses {len(body_colours)} colours, expected exactly one")
    body_color = next(iter(body_colours)) if len(body_colours) == 1 else None
    if body_color in (0, 1) or body_color is None:
        errors.append("body colour must be one of 2..9")

    body_set = set(body_cells)
    if not _is_connected(body_set):
        errors.append("body object is not 4-connected")

    mask, bbox = _normalised_body_mask(body_cells)
    shape_kind = _SHAPE_BY_MASK.get(mask)
    if shape_kind is None:
        errors.append("body mask is not one of the supported non-rectangular shapes")
    r1, c1, r2, c2 = bbox
    bbox_h, bbox_w = r2 - r1 + 1, c2 - c1 + 1
    if len(body_cells) == bbox_h * bbox_w:
        errors.append("body is a solid rectangle and hides the crop texture")

    k = len(markers)
    output_area = (k * bbox_h) * (k * bbox_w)
    if output_area >= h * w:
        errors.append(
            f"upscaled crop area {output_area} is not smaller than input area {h * w}"
        )

    crop = [row[c1 : c2 + 1] for row in values[r1 : r2 + 1]]
    output = _scale(crop, k) if k > 0 else []
    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "markers": markers,
        "n_markers": k,
        "body_cells": body_cells,
        "body_color": body_color,
        "mask": mask,
        "shape_kind": shape_kind,
        "bbox": bbox,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "crop": crop,
        "output": output,
        "output_area": output_area,
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid marker-count-scale grid: " + "; ".join(analysis["errors"]))
    return analysis


def _scale(grid: list[list[int]], factor: int) -> list[list[int]]:
    return [
        [value for value in row for _ in range(factor)]
        for row in grid
        for _ in range(factor)
    ]


def _marker_positions(width: int, count: int, phase: int, difficulty, rng) -> list[int]:
    if count == 2:
        base = {
            0: [0, 1],
            1: [0, 2],
            2: [width - 2, width - 1],
            3: [0, width - 1],
            4: [3, 4],
            5: [0, width - 1],
            6: [0, 2],
            7: [0, 1],
        }[phase]
    else:
        base = {
            0: [0, 2, 4],
            1: [0, 1, 2],
            2: [0, 1, 3],
            3: [0, 2, 4],
            4: [0, 1, 2],
            5: [0, 3, 6],
            6: [0, 2, 4],
            7: [0, 1, 3],
        }[phase]

    # The eight marker slots deliberately cross marker count with adjacency,
    # run count, span, gap size, edge contact, and rightmost position.  Slots
    # 0/2/4 make K=2 a single contiguous run; slot 7 makes K=3 two runs; slots
    # 1/5 make K=3 defeat the learned span/min-gap proxy.  Canonical [0,2] and
    # [0,2,4] layouts remain ordinary defaults in slots 6 and 3.
    if difficulty == "medium" and phase in (0, 1):
        max_shift = width - 1 - max(base)
        shift = rng.randint(0, max_shift) if max_shift > 0 else 0
        base = [col + shift for col in base]
    elif difficulty == "hard":
        base = [width - 1 - col for col in reversed(base)]
    return sorted(set(base))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")

    defaults = _scheduled_defaults(int(seed), int(sample_index))
    effective_overrides = {**defaults, **overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    h = ctx.draw_int("grid_h", 7, 12)
    w = ctx.draw_int("grid_w", 8, 14)
    n_markers = ctx.draw_int("n_markers", 2, 3)
    blob_color = ctx.draw_color("blob_color", exclude=(0, 1))
    shape_kind = ctx.draw_choice("shape_kind", _SHAPE_NAMES)
    shape = SHAPES[shape_kind]
    shape_h, shape_w = len(shape), len(shape[0])

    grid = full_grid(h, w, 0)
    marker_phase = int(sample_index) % 8
    marker_rng = ctx.draw_rng("marker_layout")
    marker_cols = _marker_positions(w, n_markers, marker_phase, difficulty, marker_rng)
    if len(marker_cols) != n_markers:
        raise AssertionError("marker layout collapsed distinct marker columns")
    for col in marker_cols:
        grid[0][col] = 1

    layout_rng = ctx.draw_rng("body_layout")
    max_top = h - shape_h
    max_left = w - shape_w
    if difficulty == "easy":
        top = min(max_top, 2 + layout_rng.randint(0, min(1, max_top - 2)))
        left = layout_rng.randint(0, min(max_left, 2))
    elif difficulty == "hard":
        top = max(2, max_top - layout_rng.randint(0, min(1, max_top - 2)))
        left = max(0, max_left - layout_rng.randint(0, min(max_left, 2)))
    else:
        top = layout_rng.randint(2, max_top)
        left = layout_rng.randint(0, max_left)

    for rr, row in enumerate(shape):
        for cc, bit in enumerate(row):
            if bit:
                grid[top + rr][left + cc] = blob_color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise AssertionError("generator produced invalid grid: " + "; ".join(errors))
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = observe_overrides(grid)
    for axis, value in requested.items():
        if axis in observed and observed[axis] != value:
            errors.append(f"meta {axis} requested {value!r}, observed {observed[axis]!r}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis_or_raise(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_markers": analysis["n_markers"],
        "blob_color": analysis["body_color"],
        "shape_kind": analysis["shape_kind"],
    }


def strict_canonical_like(grid) -> list[str]:
    """The teaching manifold is the canonical one-key/one-body grammar."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic mirror only; the canonical Racket program remains authority."""
    return [row[:] for row in _analysis_or_raise(grid)["output"]]


def _output_with_factor(grid, factor: int) -> list[list[int]]:
    return _scale(_analysis_or_raise(grid)["crop"], factor)


def _rival_fixed_scale_2(grid):
    return _output_with_factor(grid, 2)


def _rival_fixed_scale_3(grid):
    return _output_with_factor(grid, 3)


def _rival_marker_rightmost_stride2(grid):
    analysis = _analysis_or_raise(grid)
    factor = max(1, analysis["markers"][-1] // 2 + 1)
    return _scale(analysis["crop"], factor)


def _marker_geometry_factor(analysis: dict[str, Any]) -> int:
    markers = analysis["markers"]
    has_adjacent_pair = any(
        right - left == 1 for left, right in zip(markers, markers[1:])
    )
    spans_both_edges = markers[0] == 0 and markers[-1] == analysis["width"] - 1
    return 3 if has_adjacent_pair or spans_both_edges else 2


def _rival_marker_geometry_scale(grid):
    analysis = _analysis_or_raise(grid)
    return _scale(analysis["crop"], _marker_geometry_factor(analysis))


def _marker_component_factor(analysis: dict[str, Any]) -> int:
    markers = analysis["markers"]
    components = 1 + sum(
        right - left > 1 for left, right in zip(markers, markers[1:])
    )
    return 2 if components == 2 else 3


def _rival_marker_component_scale(grid):
    analysis = _analysis_or_raise(grid)
    return _scale(analysis["crop"], _marker_component_factor(analysis))


def _marker_span_gap_factor(analysis: dict[str, Any]) -> int:
    markers = analysis["markers"]
    gaps = [right - left for left, right in zip(markers, markers[1:])]
    span = markers[-1] - markers[0]
    return 3 if span > 2 and min(gaps) <= 2 else 2


def _rival_marker_span_gap_scale(grid):
    analysis = _analysis_or_raise(grid)
    return _scale(analysis["crop"], _marker_span_gap_factor(analysis))


def _rival_height_parity_scale(grid):
    analysis = _analysis_or_raise(grid)
    return _scale(analysis["crop"], 2 if analysis["height"] % 2 else 3)


def _rival_color_parity_scale(grid):
    analysis = _analysis_or_raise(grid)
    return _scale(analysis["crop"], 2 if analysis["body_color"] % 2 == 0 else 3)


def _rival_solid_bbox(grid):
    analysis = _analysis_or_raise(grid)
    solid = [
        [analysis["body_color"] for _ in range(analysis["bbox_w"])]
        for _ in range(analysis["bbox_h"])
    ]
    return _scale(solid, analysis["n_markers"])


def _rival_no_scaling(grid):
    return [row[:] for row in _analysis_or_raise(grid)["crop"]]


SEMANTIC_RIVALS = {
    "fixed_scale_2": _rival_fixed_scale_2,
    "fixed_scale_3": _rival_fixed_scale_3,
    "rightmost_marker_stride2": _rival_marker_rightmost_stride2,
    "marker_geometry_scale": _rival_marker_geometry_scale,
    "marker_component_scale": _rival_marker_component_scale,
    "marker_span_gap_scale": _rival_marker_span_gap_scale,
    "height_parity_scale": _rival_height_parity_scale,
    "body_color_parity_scale": _rival_color_parity_scale,
    "solid_bbox_upscale": _rival_solid_bbox,
    "crop_without_scaling": _rival_no_scaling,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _k_is(grid, value: int) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["n_markers"] == value


def _bbox_is(grid, dims: tuple[int, int]) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and (analysis["bbox_h"], analysis["bbox_w"]) == dims


def _irregular_markers(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    rival_factor = analysis["markers"][-1] // 2 + 1
    return rival_factor != analysis["n_markers"]


def _marker_geometry_decoupled(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and _marker_geometry_factor(analysis) != analysis["n_markers"]
    )


def _marker_component_decoupled(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and _marker_component_factor(analysis) != analysis["n_markers"]
    )


def _marker_span_gap_decoupled(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and _marker_span_gap_factor(analysis) != analysis["n_markers"]
    )


def _height_decoupled(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    rival_factor = 2 if analysis["height"] % 2 else 3
    return rival_factor != analysis["n_markers"]


def _colour_decoupled(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    rival_factor = 2 if analysis["body_color"] % 2 == 0 else 3
    return rival_factor != analysis["n_markers"]


def _canonical_dimension_profile(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    return (analysis["height"], analysis["width"]) in {(7, 8), (8, 9), (7, 10), (8, 8)}


SEMANTIC_WITNESSES = {
    "scale_factor_2": lambda grid: _k_is(grid, 2),
    "scale_factor_3": lambda grid: _k_is(grid, 3),
    "bbox_2x2": lambda grid: _bbox_is(grid, (2, 2)),
    "bbox_2x3": lambda grid: _bbox_is(grid, (2, 3)),
    "bbox_3x2": lambda grid: _bbox_is(grid, (3, 2)),
    "irregular_marker_positions": _irregular_markers,
    "marker_geometry_decoupling": _marker_geometry_decoupled,
    "marker_component_decoupling": _marker_component_decoupled,
    "marker_span_gap_decoupling": _marker_span_gap_decoupled,
    "height_count_decoupling": _height_decoupled,
    "color_count_decoupling": _colour_decoupled,
    "nonrectangular_texture": lambda grid: _valid_analysis(grid) is not None,
    "scale_is_required": lambda grid: _valid_analysis(grid) is not None,
    "canonical_dimension_profile": _canonical_dimension_profile,
}

WITNESS_RIVALS = {
    "scale_factor_2": ["fixed_scale_3"],
    "scale_factor_3": ["fixed_scale_2"],
    "bbox_2x2": ["crop_without_scaling"],
    "bbox_2x3": ["crop_without_scaling"],
    "bbox_3x2": ["crop_without_scaling"],
    "irregular_marker_positions": ["rightmost_marker_stride2"],
    "marker_geometry_decoupling": ["marker_geometry_scale"],
    "marker_component_decoupling": ["marker_component_scale"],
    "marker_span_gap_decoupling": ["marker_span_gap_scale"],
    "height_count_decoupling": ["height_parity_scale"],
    "color_count_decoupling": ["body_color_parity_scale"],
    "nonrectangular_texture": ["solid_bbox_upscale"],
    "scale_is_required": ["crop_without_scaling"],
    "canonical_dimension_profile": ["crop_without_scaling"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named plausible rival survives the demos."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output grids")
            continue
        input_errors = self_check(pair["input"])
        if input_errors:
            reasons.append(f"{label} input violates the teaching grammar: {input_errors[0]}")
            continue
        try:
            observed_output = _coerce_grid(pair["output"])
        except ValueError as exc:
            reasons.append(f"{label} output is malformed: {exc}")
            continue
        if rule_mirror(pair["input"]) != observed_output:
            reasons.append(f"{label} output disagrees with count-and-upscale")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == _coerce_grid(demo["output"])
            for demo in demos
        )
        if survives and competitor(query["input"]) != _coerce_grid(query["output"]):
            reasons.append(
                f"competing rule {name!r} fits every demo but answers the query differently"
            )
    return reasons
