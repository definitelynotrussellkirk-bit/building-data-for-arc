"""Semantic generator for ARC task 5e619caf1f27 (source 3a301edc).

The input contains one solid non-zero rectangle with a second, distinct-color
solid rectangle strictly inside it.  The output preserves the input and adds a
new outer frame in the inner rectangle's color.  The frame thickness is the
minimum of:

* the inner rectangle's height,
* the inner rectangle's width, and
* the four margins between the outer rectangle and the grid edge.

The four-example curriculum alternates two rectangular-inner cases (to expose
``min(inner_h, inner_w)``) with two edge-capped cases.  The one-cell cap is
placed on a near edge (top/left), while the two-cell cap is placed on a far
edge (bottom/right).  Every sliding four-demo lesson therefore exposes all six
terms of the minimum and rejects fixed-one, max-dimension, uncapped-inner-size,
and top/left-margin-only shortcuts.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

GENERATOR_ID = "5e619caf1f27"
TASK_ID = "5e619caf1f27"
VERSION = "2.1.0"
# Re-pinned to the synchronized, commented selected authority by the task-local
# source patch.  Focused tests verify this through canonical_rule_hash().
RULE_HASH = "ca7c525a09b4"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Find the solid outer rectangle and the distinct solid inner rectangle. "
    "Preserve both, then add an outer frame in the inner color whose thickness "
    "is min(inner height, inner width, top/left/bottom/right grid margin)."
)

INVARIANTS = [
    "the background is color 0 and exactly two distinct non-zero colors occur",
    "all non-zero cells form one solid outer rectangle except for one solid inner rectangle",
    "the inner rectangle is strictly inset from every side of the outer rectangle",
    "the outer rectangle has at least one background cell of margin on every grid side",
    "the output authority is the canonical Racket rule; rule_mirror is audit-only",
]

# Only dimensions are exact public controls.  Shape, placement, palette, and
# limiting regime vary internally and are recovered as semantic observables,
# not advertised as exact override axes.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-biased with canonical anchors", "valid": "11..22"},
    "grid_w": {"type": "int", "default": "difficulty-biased with canonical anchors", "valid": "11..22"},
}

CURRICULUM_PROFILES = (
    "inner_width_limited",
    "edge_limited_one",
    "inner_height_limited",
    "edge_limited_two",
)
SCHEDULE_PROFILES = CURRICULUM_PROFILES


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty rectangle"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(
                    f"cells must be ARC integers 0..9; got {value!r} at "
                    f"({row_index},{col_index})"
                )
    return errors


def _bbox(points: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    return min(rows), min(cols), max(rows), max(cols)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    nonzero = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not nonzero:
        return {"errors": ["expected a non-zero outer rectangle"]}

    colors = sorted({grid[row][col] for row, col in nonzero})
    if len(colors) != 2:
        return {
            "errors": [
                f"expected exactly two distinct non-zero colors, got {len(colors)}: {colors}"
            ]
        }

    outer_bbox = _bbox(nonzero)
    r1, c1, r2, c2 = outer_bbox
    corner_values = {grid[r1][c1], grid[r1][c2], grid[r2][c1], grid[r2][c2]}
    if len(corner_values) != 1 or 0 in corner_values:
        return {
            "errors": [
                "the four corners of the non-zero bounding box must share the outer color"
            ]
        }
    outer_color = next(iter(corner_values))
    inner_candidates = [color for color in colors if color != outer_color]
    if len(inner_candidates) != 1:
        return {"errors": ["could not identify one distinct inner color"]}
    inner_color = inner_candidates[0]

    inner_points = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == inner_color
    ]
    if not inner_points:
        return {"errors": ["inner rectangle is missing"]}
    inner_bbox = _bbox(inner_points)
    ir1, ic1, ir2, ic2 = inner_bbox

    if not (r1 < ir1 <= ir2 < r2 and c1 < ic1 <= ic2 < c2):
        errors.append("inner rectangle must be strictly inside the outer rectangle")

    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            expected = (
                inner_color
                if ir1 <= row <= ir2 and ic1 <= col <= ic2
                else outer_color
            )
            if grid[row][col] != expected:
                errors.append(
                    "outer/inner rectangles must be solid and the inner color must occupy one rectangle"
                )
                break
        if errors:
            break

    top_margin, left_margin = r1, c1
    bottom_margin, right_margin = height - 1 - r2, width - 1 - c2
    margins = (top_margin, left_margin, bottom_margin, right_margin)
    if min(margins) < 1:
        errors.append("outer rectangle must leave at least one background cell on every grid side")

    inner_h = ir2 - ir1 + 1
    inner_w = ic2 - ic1 + 1
    outer_h = r2 - r1 + 1
    outer_w = c2 - c1 + 1
    thickness = min(inner_h, inner_w, *margins)
    if thickness < 1:
        errors.append("the added frame would be empty")

    limiting_factors: list[str] = []
    if inner_h == thickness:
        limiting_factors.append("inner_h")
    if inner_w == thickness:
        limiting_factors.append("inner_w")
    for name, value in zip(("top", "left", "bottom", "right"), margins):
        if value == thickness:
            limiting_factors.append(name)

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "colors": colors,
        "outer_color": outer_color,
        "inner_color": inner_color,
        "outer_bbox": outer_bbox,
        "inner_bbox": inner_bbox,
        "outer_h": outer_h,
        "outer_w": outer_w,
        "inner_h": inner_h,
        "inner_w": inner_w,
        "inner_offsets": (ir1 - r1, ic1 - c1, r2 - ir2, c2 - ic2),
        "margins": margins,
        "thickness": thickness,
        "limiting_factors": limiting_factors,
        "edge_limited": min(margins) < min(inner_h, inner_w),
    }


def _paint_frame(grid: Any, thickness: int, color: int) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    r1, c1, r2, c2 = analysis["outer_bbox"]
    nr1, nc1 = r1 - thickness, c1 - thickness
    nr2, nc2 = r2 + thickness, c2 + thickness
    output = [list(row) for row in grid]
    for row in range(nr1, nr2 + 1):
        for col in range(nc1, nc2 + 1):
            if not (r1 <= row <= r2 and c1 <= col <= c2):
                output[row][col] = color
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python audit mirror; canonical Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _paint_frame(grid, analysis["thickness"], analysis["inner_color"])


def _rival_identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_fixed_one(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _paint_frame(grid, 1, analysis["inner_color"])


def _rival_uncapped_inner_min(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    requested = min(analysis["inner_h"], analysis["inner_w"])
    r1, c1, r2, c2 = analysis["outer_bbox"]
    height, width = analysis["height"], analysis["width"]
    # This rival learned the old generator's shortcut: expand by the smaller
    # inner dimension and merely clip the oversized box to the canvas.  On an
    # edge-limited scene it leaves thicker bands on the non-limiting sides,
    # unlike the authority's uniform margin-capped thickness.
    nr1, nc1 = max(0, r1 - requested), max(0, c1 - requested)
    nr2, nc2 = min(height - 1, r2 + requested), min(width - 1, c2 + requested)
    output = [list(row) for row in grid]
    for row in range(nr1, nr2 + 1):
        for col in range(nc1, nc2 + 1):
            if not (r1 <= row <= r2 and c1 <= col <= c2):
                output[row][col] = analysis["inner_color"]
    return output


def _rival_top_left_margin_only_clipped(grid: Any) -> list[list[int]]:
    """Ignore the far grid edges when choosing frame thickness, then clip."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    requested = min(
        analysis["inner_h"],
        analysis["inner_w"],
        analysis["margins"][0],
        analysis["margins"][1],
    )
    r1, c1, r2, c2 = analysis["outer_bbox"]
    height, width = analysis["height"], analysis["width"]
    nr1, nc1 = max(0, r1 - requested), max(0, c1 - requested)
    nr2, nc2 = min(height - 1, r2 + requested), min(width - 1, c2 + requested)
    output = [list(row) for row in grid]
    for row in range(nr1, nr2 + 1):
        for col in range(nc1, nc2 + 1):
            if not (r1 <= row <= r2 and c1 <= col <= c2):
                output[row][col] = analysis["inner_color"]
    return output


def _rival_max_inner_dimension(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    thickness = min(max(analysis["inner_h"], analysis["inner_w"]), *analysis["margins"])
    return _paint_frame(grid, thickness, analysis["inner_color"])


def _rival_inner_height_only(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _paint_frame(
        grid, min(analysis["inner_h"], *analysis["margins"]), analysis["inner_color"]
    )


def _rival_inner_width_only(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _paint_frame(
        grid, min(analysis["inner_w"], *analysis["margins"]), analysis["inner_color"]
    )


def _rival_outer_color_frame(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _paint_frame(grid, analysis["thickness"], analysis["outer_color"])


def _rival_fill_expanded_box(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    r1, c1, r2, c2 = analysis["outer_bbox"]
    thickness = analysis["thickness"]
    output = [list(row) for row in grid]
    fill_box(
        output,
        r1 - thickness,
        c1 - thickness,
        r2 + thickness,
        c2 + thickness,
        analysis["inner_color"],
    )
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _rival_identity,
    "fixed_one_cell_frame": _rival_fixed_one,
    "uncapped_inner_minimum": _rival_uncapped_inner_min,
    "top_left_margin_only_clipped": _rival_top_left_margin_only_clipped,
    "maximum_inner_dimension": _rival_max_inner_dimension,
    "inner_height_only": _rival_inner_height_only,
    "inner_width_only": _rival_inner_width_only,
    "outer_color_frame": _rival_outer_color_frame,
    "fill_expanded_box": _rival_fill_expanded_box,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# This registry is evidence about the six canonical pairs, not a synonym for
# every plausible semantic rival.  Keep only rivals that actually reproduce
# every canonical output; focused tests derive and verify this set.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "top_left_margin_only_clipped",
        "maximum_inner_dimension",
        "inner_height_only",
        "inner_width_only",
    )
}


def _witness_multi_cell_frame(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["thickness"] >= 2


def _witness_edge_cap(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["edge_limited"]


def _witness_bottom_or_right_cap(grid: Any) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    top, left, bottom, right = analysis["margins"]
    return (
        analysis["edge_limited"]
        and min(bottom, right) == analysis["thickness"]
        and analysis["thickness"] < min(
            analysis["inner_h"], analysis["inner_w"], top, left
        )
    )


def _witness_width_limits(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and not analysis["edge_limited"]
        and analysis["inner_w"] < analysis["inner_h"]
        and analysis["thickness"] == analysis["inner_w"]
    )


def _witness_height_limits(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and not analysis["edge_limited"]
        and analysis["inner_h"] < analysis["inner_w"]
        and analysis["thickness"] == analysis["inner_h"]
    )


def _witness_inner_is_off_center(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and (
        analysis["inner_offsets"][0] != analysis["inner_offsets"][2]
        or analysis["inner_offsets"][1] != analysis["inner_offsets"][3]
    )


def _witness_rectangular_outer(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["outer_h"] != analysis["outer_w"]


SEMANTIC_WITNESSES = {
    "multi_cell_frame_rejects_fixed_one": _witness_multi_cell_frame,
    "edge_margin_caps_inner_size": _witness_edge_cap,
    "bottom_or_right_margin_caps_frame": _witness_bottom_or_right_cap,
    "inner_width_can_be_limiting_dimension": _witness_width_limits,
    "inner_height_can_be_limiting_dimension": _witness_height_limits,
    "inner_position_is_not_a_center_marker": _witness_inner_is_off_center,
    "outer_rectangle_need_not_be_square": _witness_rectangular_outer,
}
WITNESS_RIVALS = {
    "multi_cell_frame_rejects_fixed_one": ["identity", "fixed_one_cell_frame"],
    "edge_margin_caps_inner_size": ["uncapped_inner_minimum"],
    "bottom_or_right_margin_caps_frame": ["top_left_margin_only_clipped"],
    "inner_width_can_be_limiting_dimension": [
        "maximum_inner_dimension",
        "inner_height_only",
    ],
    "inner_height_can_be_limiting_dimension": [
        "maximum_inner_dimension",
        "inner_width_only",
    ],
}
BRANCH_WITNESSES = {
    "inner_position_is_not_a_center_marker",
    "outer_rectangle_need_not_be_square",
}


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-safe input grammar, including exact overrides."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-linked predicate for canonical inputs and ordinary teaching draws."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if analysis["thickness"] < 1:
        errors.append("the authority must add a visible non-empty frame")
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def semantic_observables(grid: Any) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "outer_color": analysis["outer_color"],
        "inner_color": analysis["inner_color"],
        "outer_bbox": list(analysis["outer_bbox"]),
        "inner_bbox": list(analysis["inner_bbox"]),
        "outer_h": analysis["outer_h"],
        "outer_w": analysis["outer_w"],
        "inner_h": analysis["inner_h"],
        "inner_w": analysis["inner_w"],
        "inner_offsets": list(analysis["inner_offsets"]),
        "margins": list(analysis["margins"]),
        "thickness": analysis["thickness"],
        "limiting_factors": list(analysis["limiting_factors"]),
        "edge_limited": analysis["edge_limited"],
        "profile": _profile_from_analysis(analysis),
    }


def _profile_from_analysis(analysis: dict[str, Any]) -> str:
    if analysis["edge_limited"]:
        return "edge_limited_one" if analysis["thickness"] == 1 else "edge_limited_two"
    if analysis["inner_w"] < analysis["inner_h"]:
        return "inner_width_limited"
    if analysis["inner_h"] < analysis["inner_w"]:
        return "inner_height_limited"
    return "square_inner_limited"


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return CURRICULUM_PROFILES[sample_index % len(CURRICULUM_PROFILES)]


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where any named plausible shortcut still fits all demos."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        structural = strict_canonical_like(pair["input"])
        if structural:
            reasons.append(f"demo {index} is not a lawful teaching scene: {structural[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the frame rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query is not a lawful teaching scene: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the frame rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} still fits every demonstration")
    return reasons


def mutation_fixtures():
    """Named malformed near-misses the structural checker must reject."""
    missing_inner = full_grid(11, 11, 0)
    fill_box(missing_inner, 3, 3, 7, 7, 2)

    inner_touches_outer = full_grid(11, 11, 0)
    fill_box(inner_touches_outer, 3, 3, 7, 7, 2)
    fill_box(inner_touches_outer, 3, 4, 5, 5, 4)

    hollow_outer = full_grid(11, 11, 0)
    fill_box(hollow_outer, 3, 3, 7, 7, 2)
    fill_box(hollow_outer, 4, 4, 6, 6, 4)
    hollow_outer[3][5] = 0

    split_inner = full_grid(11, 11, 0)
    fill_box(split_inner, 3, 3, 7, 7, 2)
    split_inner[4][4] = 4
    split_inner[6][6] = 4

    third_color = full_grid(11, 11, 0)
    fill_box(third_color, 3, 3, 7, 7, 2)
    fill_box(third_color, 4, 4, 6, 6, 4)
    third_color[5][5] = 7

    outer_at_grid_edge = full_grid(11, 11, 0)
    fill_box(outer_at_grid_edge, 0, 2, 4, 6, 2)
    fill_box(outer_at_grid_edge, 1, 3, 3, 5, 4)

    return [
        ("missing_inner_rectangle", missing_inner),
        ("inner_touches_outer_edge", inner_touches_outer),
        ("hole_in_outer_rectangle", hollow_outer),
        ("split_nonrectangular_inner_color", split_inner),
        ("third_nonzero_color", third_color),
        ("outer_rectangle_touches_grid_edge", outer_at_grid_edge),
    ]


def _default_dimensions(ctx) -> tuple[int, int]:
    # Explicit canonical-size anchors guarantee every difficulty band retains
    # exact mechanical-profile support.  Other indices use deterministic,
    # difficulty-shaped variation over the full public domain.
    anchors = {
        "easy": (12, 11),
        "medium": (16, 17),
        "hard": (21, 21),
        None: (13, 14),
    }
    if ctx.sample_index % 5 == 0:
        return anchors.get(ctx.difficulty, anchors[None])

    ranges = {
        "easy": ((11, 15), (11, 15)),
        "medium": ((14, 19), (14, 19)),
        "hard": ((18, 22), (18, 22)),
        None: ((11, 22), (11, 22)),
    }
    (hlo, hhi), (wlo, whi) = ranges.get(ctx.difficulty, ranges[None])
    rng = ctx.draw_rng("default_dimensions")
    return rng.randint(hlo, hhi), rng.randint(wlo, whi)


def _draw_dimension(ctx, label: str, default: int) -> int:
    # Override calls validate against the complete declared boundary.  Default
    # calls pin the preselected deterministic value while retaining keyed draw
    # provenance for the axis audit.
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, 11, 22)
    return ctx.draw_int(label, default, default)


def _shape_candidates(height: int, width: int, profile: str):
    candidates: list[tuple[int, int, int, int, int, int, int, int]] = []
    # tuple: inner_h, inner_w, inner_top_gap, inner_left_gap,
    #        inner_bottom_gap, inner_right_gap, cap, profile_code_unused
    if profile in ("inner_width_limited", "inner_height_limited"):
        for small in (2, 3):
            for large in range(small + 1, min(5, small + 2) + 1):
                ih, iw = (large, small) if profile == "inner_width_limited" else (small, large)
                for gaps in product((1, 2), repeat=4):
                    gt, gl, gb, gr = gaps
                    outer_h = ih + gt + gb
                    outer_w = iw + gl + gr
                    thickness = small
                    separation_margin = max(ih, iw)
                    if (
                        outer_h + 2 * separation_margin <= height
                        and outer_w + 2 * separation_margin <= width
                    ):
                        candidates.append((ih, iw, gt, gl, gb, gr, thickness, 0))
    else:
        cap = 1 if profile == "edge_limited_one" else 2
        minimum_inner = 2 if cap == 1 else 3
        maximum_inner = 4 if cap == 1 else 4
        for ih in range(minimum_inner, maximum_inner + 1):
            for iw in range(minimum_inner, maximum_inner + 1):
                if min(ih, iw) <= cap:
                    continue
                for gaps in product((1, 2), repeat=4):
                    gt, gl, gb, gr = gaps
                    outer_h = ih + gt + gb
                    outer_w = iw + gl + gr
                    # At least one side must be able to sit at cap while all
                    # other margins remain >= min(inner_h, inner_w).
                    inner_min = min(ih, iw)
                    vertical_ok = outer_h + cap + inner_min <= height and outer_w + 2 * inner_min <= width
                    horizontal_ok = outer_w + cap + inner_min <= width and outer_h + 2 * inner_min <= height
                    if vertical_ok or horizontal_ok:
                        candidates.append((ih, iw, gt, gl, gb, gr, cap, 0))
    return candidates


def _place_outer(
    height: int,
    width: int,
    outer_h: int,
    outer_w: int,
    profile: str,
    inner_min: int,
    cap: int,
    rng,
) -> tuple[int, int]:
    if profile.startswith("inner_"):
        row_lo, row_hi = inner_min, height - outer_h - inner_min
        col_lo, col_hi = inner_min, width - outer_w - inner_min
        return rng.randint(row_lo, row_hi), rng.randint(col_lo, col_hi)

    feasible: list[str] = []
    if height - outer_h - cap >= inner_min and width - outer_w >= 2 * inner_min:
        feasible.extend(("top", "bottom"))
    if width - outer_w - cap >= inner_min and height - outer_h >= 2 * inner_min:
        feasible.extend(("left", "right"))
    if not feasible:
        raise AssertionError("edge-limited template has no feasible limiting side")
    desired_sides = (
        {"top", "left"}
        if profile == "edge_limited_one"
        else {"bottom", "right"}
    )
    feasible = [side for side in feasible if side in desired_sides]
    if not feasible:
        raise AssertionError(f"{profile!r} template has no feasible scheduled side")
    side = rng.choice(feasible)
    if side == "top":
        return cap, rng.randint(inner_min, width - outer_w - inner_min)
    if side == "bottom":
        return height - outer_h - cap, rng.randint(inner_min, width - outer_w - inner_min)
    if side == "left":
        return rng.randint(inner_min, height - outer_h - inner_min), cap
    return rng.randint(inner_min, height - outer_h - inner_min), width - outer_w - cap


def _construct_scene(
    height: int,
    width: int,
    profile: str,
    outer_color: int,
    inner_color: int,
    rng,
) -> list[list[int]]:
    candidates = _shape_candidates(height, width, profile)
    if not candidates:
        raise AssertionError(f"no lawful {profile!r} shape for {height}x{width}")
    ih, iw, gt, gl, gb, gr, cap, _ = rng.choice(candidates)
    outer_h, outer_w = ih + gt + gb, iw + gl + gr
    inner_min = min(ih, iw)
    placement_margin = max(ih, iw) if profile.startswith("inner_") else inner_min
    outer_row, outer_col = _place_outer(
        height, width, outer_h, outer_w, profile, placement_margin, cap, rng
    )
    inner_row, inner_col = outer_row + gt, outer_col + gl

    grid = full_grid(height, width, 0)
    fill_box(
        grid,
        outer_row,
        outer_col,
        outer_row + outer_h - 1,
        outer_col + outer_w - 1,
        outer_color,
    )
    fill_box(
        grid,
        inner_row,
        inner_col,
        inner_row + ih - 1,
        inner_col + iw - 1,
        inner_color,
    )
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for axis, value in overrides.items():
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError(f"override {axis!r} must be an integer or None, got {value!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = _default_dimensions(ctx)
    height = _draw_dimension(ctx, "grid_h", default_h)
    width = _draw_dimension(ctx, "grid_w", default_w)
    outer_color, inner_color = ctx.draw_distinct_colors("palette", n=2, exclude={0})
    profile = schedule_profile(seed, sample_index, difficulty)
    grid = _construct_scene(
        height,
        width,
        profile,
        outer_color,
        inner_color,
        ctx.draw_rng("geometry"),
    )

    observed = observe_overrides(grid)
    for axis, requested in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != requested:
            raise AssertionError(
                f"internal axis drift for {axis}: requested {requested!r}, observed {observed[axis]!r}"
            )
    return grid
