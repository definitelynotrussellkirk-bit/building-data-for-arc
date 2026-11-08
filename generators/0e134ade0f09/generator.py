"""Semantic generator for ARC task 0e134ade0f09 (source 5b37cb25).

The input is a rectangular field with four differently colored frame sides.
Inside the frame, a seventh foreground color forms dense rectangular objects
with five-cell directional ring edges around background-colored plus notches.  The ring orientation names one frame side;
the rule fills the associated five-cell plus with that side's color.

Version 2 rebuilds the teaching distribution around the actual relation.  Every
ordinary draw contains all four directional branches, includes markers whose
orientation both agrees and disagrees with geometric border proximity, rejects
malformed marker grammars, exposes exact composable overrides, and declares
rivals that would otherwise turn the task into a position or constant-color
shortcut.  A deterministic 30x30 schedule keeps the canonical scale anchored
without making the generalized dimensions inert.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0e134ade0f09"
TASK_ID = "0e134ade0f09"
VERSION = "2.1.0"
RULE_HASH = "71fca8698886"
EXAMPLES_NEEDED = 1
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read each foreground directional ring around a background plus, then "
    "fill that five-cell plus with the color of the frame side named by the "
    "ring orientation."
)

INVARIANTS = [
    "the rectangular grid is 24..30 cells on each side and has zero corners",
    "the top, left, right, and bottom frame sides are uniform, nonzero, and pairwise distinct",
    "one nonzero background color fills every unmarked interior cell",
    "one distinct foreground color forms 3..4 dense rectangular components with edge plus notches",
    "ordinary generated grids contain four dense objects, 4..8 separated edge notches, and all orientations",
    "at least one generated marker agrees with its nearest border and at least one disagrees",
    "the six nonzero semantic colors are pairwise distinct, yielding a seven-color ARC palette including zero",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 24..30 with deterministic 30x30 anchors",
        "valid": "24..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 24..30 with deterministic 30x30 anchors",
        "valid": "24..30",
    },
    "n_notches": {
        "type": "int",
        "default": "difficulty-skewed 4..8",
        "valid": "4..8",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SIDES = ("top", "right", "bottom", "left")
SIDE_ROTATE_CLOCKWISE = {
    "top": "right",
    "right": "bottom",
    "bottom": "left",
    "left": "top",
}

# Ring offsets relative to a notch center.  The open side of each ring points
# toward the frame side whose color must fill the background plus.
RINGS = {
    "top": ((2, 0), (0, -2), (0, 2), (1, -1), (1, 1)),
    "bottom": ((-2, 0), (0, -2), (0, 2), (-1, -1), (-1, 1)),
    "left": ((-2, 0), (2, 0), (0, 2), (-1, 1), (1, 1)),
    "right": ((-2, 0), (2, 0), (0, -2), (-1, -1), (1, -1)),
}
CROSS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the deterministic canonical-scale schedule to the semantic gate."""
    del difficulty
    return "canonical_anchor" if (seed + sample_index) % 4 == 0 else "generalized"


SCHEDULE_PROFILES = ("canonical_anchor", "generalized")


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _nearest_side(r: int, c: int, h: int, w: int) -> str:
    distances = {
        "top": r,
        "right": w - 1 - c,
        "bottom": h - 1 - r,
        "left": c,
    }
    return min(SIDES, key=lambda side: (distances[side], SIDES.index(side)))


def _analyze_grid(grid) -> tuple[dict[str, object], list[str]]:
    """Recover the task grammar and return (analysis, errors)."""
    errors = _grid_shape_errors(grid)
    if errors:
        return {}, errors

    h, w = len(grid), len(grid[0])
    if not 24 <= h <= 30:
        errors.append(f"height must be in 24..30, got {h}")
    if not 24 <= w <= 30:
        errors.append(f"width must be in 24..30, got {w}")
    if errors:
        return {"grid_h": h, "grid_w": w}, errors

    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    for r, c in corners:
        if grid[r][c] != 0:
            errors.append(f"corner ({r},{c}) must be zero")

    top = grid[0][1]
    right = grid[1][w - 1]
    bottom = grid[h - 1][1]
    left = grid[1][0]
    frame_colors = {"top": top, "right": right, "bottom": bottom, "left": left}

    if any(value == 0 for value in frame_colors.values()):
        errors.append("all four frame-side colors must be nonzero")
    if len(set(frame_colors.values())) != 4:
        errors.append("the four frame-side colors must be pairwise distinct")
    if any(grid[0][c] != top for c in range(1, w - 1)):
        errors.append("top frame side must be uniform")
    if any(grid[h - 1][c] != bottom for c in range(1, w - 1)):
        errors.append("bottom frame side must be uniform")
    if any(grid[r][0] != left for r in range(1, h - 1)):
        errors.append("left frame side must be uniform")
    if any(grid[r][w - 1] != right for r in range(1, h - 1)):
        errors.append("right frame side must be uniform")

    bg = grid[1][1]
    if bg == 0 or bg in frame_colors.values():
        errors.append("background must be nonzero and distinct from every frame color")

    palette = {value for row in grid for value in row}
    semantic_known = {0, bg, *frame_colors.values()}
    fg_candidates = palette - semantic_known
    if len(palette) != 7:
        errors.append(f"palette must contain exactly seven colors including zero, got {len(palette)}")
    if len(fg_candidates) != 1:
        errors.append(
            "exactly one foreground ring color must remain after removing zero, background, and frame colors"
        )
        return {
            "grid_h": h,
            "grid_w": w,
            "frame_colors": frame_colors,
            "background": bg,
            "palette": palette,
            "markers": [],
        }, errors
    fg = next(iter(fg_candidates))
    if fg == 0:
        errors.append("foreground ring color must be nonzero")

    illegal_interior = [
        (r, c, grid[r][c])
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] not in (bg, fg)
    ]
    if illegal_interior:
        r, c, value = illegal_interior[0]
        errors.append(
            f"interior may contain only background and foreground ring colors; found {value} at ({r},{c})"
        )

    markers: list[dict[str, object]] = []
    for r in range(2, h - 2):
        for c in range(2, w - 2):
            if not all(grid[r + dr][c + dc] == bg for dr, dc in CROSS):
                continue
            matches = [
                side
                for side, offsets in RINGS.items()
                if all(grid[r + dr][c + dc] == fg for dr, dc in offsets)
            ]
            if len(matches) > 1:
                errors.append(f"marker centered at ({r},{c}) matches multiple ring orientations: {matches}")
            elif len(matches) == 1:
                side = matches[0]
                markers.append(
                    {
                        "row": r,
                        "col": c,
                        "side": side,
                        "nearest_side": _nearest_side(r, c, h, w),
                    }
                )

    if not 3 <= len(markers) <= 8:
        errors.append(f"grid must contain 3..8 complete directional markers, got {len(markers)}")

    marker_centers = {(int(m["row"]), int(m["col"])) for m in markers}
    if len(marker_centers) != len(markers):
        errors.append("marker centers must be distinct")

    occupied_footprints: list[set[tuple[int, int]]] = []
    marker_rings: list[set[tuple[int, int]]] = []
    for marker in markers:
        r, c, side = int(marker["row"]), int(marker["col"]), str(marker["side"])
        ring_cells = {(r + dr, c + dc) for dr, dc in RINGS[side]}
        cross_cells = {(r + dr, c + dc) for dr, dc in CROSS}
        marker_rings.append(ring_cells)
        footprint = ring_cells | cross_cells
        if any(footprint & previous for previous in occupied_footprints):
            errors.append("directional marker footprints must not overlap")
            break
        occupied_footprints.append(footprint)

    actual_fg = {
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == fg
    }
    unseen = set(actual_fg)
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            rr, cc = stack.pop()
            for nxt in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(component)

    if not 3 <= len(components) <= 4:
        errors.append(f"foreground must form 3..4 dense objects, got {len(components)} components")

    component_summaries: list[dict[str, object]] = []
    for index, component in enumerate(components):
        rows = [cell[0] for cell in component]
        cols = [cell[1] for cell in component]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        bbox_area = (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1)
        fill_ratio = len(component) / bbox_area
        contained_markers = [
            marker_index
            for marker_index, ring_cells in enumerate(marker_rings)
            if ring_cells <= component
        ]
        if len(component) < 20:
            errors.append(
                f"foreground object {index} is too small for the canonical dense-object grammar: {len(component)} cells"
            )
        if fill_ratio < 0.70:
            errors.append(
                f"foreground object {index} must be mostly rectangular/dense, fill ratio {fill_ratio:.3f}"
            )
        if not contained_markers:
            errors.append(f"foreground object {index} has no complete edge-notch marker")
        component_summaries.append(
            {
                "size": len(component),
                "bbox": bbox,
                "fill_ratio": fill_ratio,
                "marker_indices": contained_markers,
            }
        )

    for marker_index, ring_cells in enumerate(marker_rings):
        owners = [index for index, component in enumerate(components) if ring_cells <= component]
        if len(owners) != 1:
            errors.append(
                f"marker {marker_index} ring must belong to exactly one dense foreground object, got {owners}"
            )

    side_counts = Counter(str(marker["side"]) for marker in markers)
    return {
        "grid_h": h,
        "grid_w": w,
        "frame_colors": frame_colors,
        "background": bg,
        "foreground": fg,
        "palette": palette,
        "markers": markers,
        "side_counts": side_counts,
        "n_notches": len(markers),
        "components": component_summaries,
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full marker/frame grammar rather than palette marginals."""
    del difficulty, meta
    _, errors = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic census."""
    analysis, errors = _analyze_grid(grid)
    if errors:
        return errors
    if len(analysis["palette"]) != 7:
        return ["canonical-like grids use exactly seven colors including zero"]
    if int(analysis["n_notches"]) < 3:
        return ["canonical-like grids contain at least three directional markers"]
    if not 3 <= len(analysis["components"]) <= 4:
        return ["canonical-like grids contain three or four dense foreground objects"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    """Recover each declared exact axis from the materialized input grid."""
    analysis, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe overrides on malformed grid: " + "; ".join(errors[:3]))
    return {
        "grid_h": int(analysis["grid_h"]),
        "grid_w": int(analysis["grid_w"]),
        "n_notches": int(analysis["n_notches"]),
    }


def _quadrant_rectangles(h: int, w: int, rng) -> list[tuple[int, int, int, int]]:
    """Four separated, asymmetric dense objects with background still modal.

    Starting from four 7x7 objects guarantees the opposite-edge notch grammar.
    A bounded area budget then grows a deliberately uneven subset, preserving
    the canonical mix of dense small and large components without allowing the
    foreground to become the modal color (which would invert morphology gates).
    """
    regions = [
        (2, 2, h // 2 - 2, w // 2 - 2),
        (2, w // 2 + 1, h // 2 - 2, w - 3),
        (h // 2 + 1, w // 2 + 1, h - 3, w - 3),
        (h // 2 + 1, 2, h - 3, w // 2 - 2),
    ]
    capacities = [
        (r1 - r0 + 1, c1 - c0 + 1) for r0, c0, r1, c1 in regions
    ]
    if any(rh < 7 or rw < 7 for rh, rw in capacities):
        raise RuntimeError(f"grid {h}x{w} cannot host four canonical dense objects")

    dims = [[7, 7] for _ in regions]
    # One canonical-scale component is intentionally much larger.  This is a
    # semantic morphology anchor, not an inert template: its edge branch and
    # colors still vary, while its size reaches the real task's large objects.
    dims[0] = [capacities[0][0], capacities[0][1]]
    current_area = sum(rh * rw for rh, rw in dims)
    area_budget = max(current_area, int((h - 2) * (w - 2) * 0.45))
    while True:
        candidates: list[tuple[int, int, int]] = []
        for index, ((max_h, max_w), (rect_h, rect_w)) in enumerate(zip(capacities, dims)):
            if rect_h < max_h and current_area + rect_w <= area_budget:
                candidates.append((index, 0, rect_w))
            if rect_w < max_w and current_area + rect_h <= area_budget:
                candidates.append((index, 1, rect_h))
        if not candidates:
            break
        # Grow the remaining objects unevenly rather than cloning one shape.
        weighted = candidates + [candidate for candidate in candidates if candidate[0] == 1]
        index, axis, delta = rng.choice(weighted)
        dims[index][axis] += 1
        current_area += delta

    rectangles: list[tuple[int, int, int, int]] = []
    for (region_r0, region_c0, region_r1, region_c1), (rect_h, rect_w) in zip(regions, dims):
        r0 = rng.randint(region_r0, region_r1 - rect_h + 1)
        c0 = rng.randint(region_c0, region_c1 - rect_w + 1)
        rectangles.append((r0, c0, r0 + rect_h - 1, c0 + rect_w - 1))
    return rectangles


def _edge_center(rect: tuple[int, int, int, int], side: str) -> tuple[int, int]:
    r0, c0, r1, c1 = rect
    if side == "top":
        return r0, (c0 + c1) // 2
    if side == "bottom":
        return r1, (c0 + c1) // 2
    if side == "left":
        return (r0 + r1) // 2, c0
    if side == "right":
        return (r0 + r1) // 2, c1
    raise ValueError(side)


def _assign_primary_sides(
    rectangles: list[tuple[int, int, int, int]], h: int, w: int, rng
) -> list[str]:
    """Assign all four branches while proving nearness is not the rule."""
    from itertools import permutations

    trials = list(permutations(SIDES))
    rng.shuffle(trials)
    for trial in trials:
        matches = sum(
            side == _nearest_side(*_edge_center(rect, side), h, w)
            for rect, side in zip(rectangles, trial)
        )
        if 0 < matches < len(rectangles):
            return list(trial)
    raise RuntimeError("could not assign a mixed nearest/mismatched directional lesson")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    has_override = any(name in overrides and overrides[name] is not None for name in AXES)
    canonical_anchor = not has_override and schedule_profile(seed, sample_index, difficulty) == "canonical_anchor"
    if canonical_anchor:
        h = ctx.draw_int("grid_h", 30, 30)
        w = ctx.draw_int("grid_w", 30, 30)
    else:
        h = ctx.draw_int_diff("grid_h", 24, 30)
        w = ctx.draw_int_diff("grid_w", 24, 30)
    n_notches = ctx.draw_int_diff("n_notches", 4, 8)

    bg, top, right, bottom, left, fg = ctx.draw_distinct_colors(
        "colors", n=6, exclude={0}
    )
    grid = full_grid(h, w, bg)

    for c in range(w):
        grid[0][c] = top
        grid[h - 1][c] = bottom
    for r in range(h):
        grid[r][0] = left
        grid[r][w - 1] = right
    for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        grid[r][c] = 0

    rng = ctx.draw_rng("layout")
    rectangles = _quadrant_rectangles(h, w, rng)
    for r0, c0, r1, c1 in rectangles:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                grid[r][c] = fg

    primary_sides = _assign_primary_sides(rectangles, h, w, rng)
    opposite = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
    marker_specs = [
        (rect, side) for rect, side in zip(rectangles, primary_sides)
    ]
    extra_indices = list(range(4))
    rng.shuffle(extra_indices)
    for rectangle_index in extra_indices[: n_notches - 4]:
        marker_specs.append(
            (rectangles[rectangle_index], opposite[primary_sides[rectangle_index]])
        )
    rng.shuffle(marker_specs)

    for rect, side in marker_specs:
        r, c = _edge_center(rect, side)
        for dr, dc in CROSS:
            grid[r + dr][c + dc] = bg

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(errors))
    analysis, _ = _analyze_grid(grid)
    generated_sides = set(analysis["side_counts"])
    if generated_sides != set(SIDES):
        raise RuntimeError(f"ordinary draw omitted directional branches: {sorted(set(SIDES) - generated_sides)}")
    match_count = sum(
        marker["side"] == marker["nearest_side"] for marker in analysis["markers"]
    )
    if not 0 < match_count < int(analysis["n_notches"]):
        raise RuntimeError("ordinary draw must contain both nearest-side matches and mismatches")
    return grid


def _paint_marker_crosses(
    grid, color_for_marker: Callable[[dict[str, object], dict[str, object]], int]
):
    analysis, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("malformed task grid: " + "; ".join(errors[:3]))
    output = [list(row) for row in grid]
    for marker in analysis["markers"]:
        color = int(color_for_marker(marker, analysis))
        r, c = int(marker["row"]), int(marker["col"])
        for dr, dc in CROSS:
            output[r + dr][c + dc] = color
    return output


def rule_mirror(grid):
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    return _paint_marker_crosses(
        grid,
        lambda marker, analysis: int(analysis["frame_colors"][str(marker["side"])]),
    )


def _rival_foreground_fill(grid):
    return _paint_marker_crosses(
        grid, lambda marker, analysis: int(analysis["foreground"])
    )


def _rival_constant_top_frame(grid):
    return _paint_marker_crosses(
        grid, lambda marker, analysis: int(analysis["frame_colors"]["top"])
    )


def _rival_rotate_side_mapping_clockwise(grid):
    return _paint_marker_crosses(
        grid,
        lambda marker, analysis: int(
            analysis["frame_colors"][SIDE_ROTATE_CLOCKWISE[str(marker["side"])]]
        ),
    )


def _rival_nearest_frame_side(grid):
    return _paint_marker_crosses(
        grid,
        lambda marker, analysis: int(
            analysis["frame_colors"][str(marker["nearest_side"])]
        ),
    )


SEMANTIC_RIVALS = {
    "fill_with_foreground": _rival_foreground_fill,
    "constant_top_frame": _rival_constant_top_frame,
    "rotate_side_mapping_clockwise": _rival_rotate_side_mapping_clockwise,
    "nearest_frame_side": _rival_nearest_frame_side,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_side(side: str):
    def predicate(grid) -> bool:
        analysis, errors = _analyze_grid(grid)
        return not errors and analysis["side_counts"].get(side, 0) > 0

    return predicate


def _witness_nearest_mismatch(grid) -> bool:
    analysis, errors = _analyze_grid(grid)
    return not errors and any(
        marker["side"] != marker["nearest_side"] for marker in analysis["markers"]
    )


def _witness_multiple_output_colors(grid) -> bool:
    analysis, errors = _analyze_grid(grid)
    return not errors and len(analysis["side_counts"]) >= 2


def _witness_background_crosses(grid) -> bool:
    analysis, errors = _analyze_grid(grid)
    if errors:
        return False
    bg = int(analysis["background"])
    return all(
        grid[int(marker["row"]) + dr][int(marker["col"]) + dc] == bg
        for marker in analysis["markers"]
        for dr, dc in CROSS
    )


SEMANTIC_WITNESSES = {
    "top_ring_branch": _witness_side("top"),
    "right_ring_branch": _witness_side("right"),
    "bottom_ring_branch": _witness_side("bottom"),
    "left_ring_branch": _witness_side("left"),
    "ring_orientation_overrides_geometric_nearness": _witness_nearest_mismatch,
    "multiple_frame_colors_required": _witness_multiple_output_colors,
    "background_crosses_are_recolored": _witness_background_crosses,
}

WITNESS_RIVALS = {
    "top_ring_branch": ["rotate_side_mapping_clockwise"],
    "right_ring_branch": ["rotate_side_mapping_clockwise"],
    "bottom_ring_branch": ["rotate_side_mapping_clockwise"],
    "left_ring_branch": ["rotate_side_mapping_clockwise"],
    "ring_orientation_overrides_geometric_nearness": ["nearest_frame_side"],
    "multiple_frame_colors_required": ["constant_top_frame"],
    "background_crosses_are_recolored": ["fill_with_foreground"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when plausible named rivals survive all demonstrations."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is malformed: {type(exc).__name__}: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(f"demo {index} output does not match the directional-ring rule")

    try:
        expected_query = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query input is malformed: {type(exc).__name__}: {exc}")
        return reasons
    if expected_query != query.get("output"):
        reasons.append("query output does not match the directional-ring rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo.get("output") for demo in demos
            )
            competitor_query = competitor(query["input"])
        except Exception as exc:
            reasons.append(f"competing rule '{name}' raised {type(exc).__name__}: {exc}")
            continue
        if survives and competitor_query != query.get("output"):
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons


def mutation_fixtures():
    """Task-linked impostors that the structural self-check must reject."""
    valid = generate(
        20260726,
        7,
        difficulty="medium",
        grid_h=24,
        grid_w=25,
        n_notches=4,
    )
    analysis, errors = _analyze_grid(valid)
    if errors:
        raise AssertionError(errors)
    marker = analysis["markers"][0]
    r, c, side = int(marker["row"]), int(marker["col"]), str(marker["side"])
    bg = int(analysis["background"])
    fg = int(analysis["foreground"])
    top = int(analysis["frame_colors"]["top"])

    broken_frame = [row[:] for row in valid]
    broken_frame[0][2] = bg

    missing_ring_cell = [row[:] for row in valid]
    dr, dc = RINGS[side][0]
    missing_ring_cell[r + dr][c + dc] = bg

    prefilled_cross = [row[:] for row in valid]
    prefilled_cross[r][c] = top

    stray_foreground = [row[:] for row in valid]
    occupied = {
        (int(m["row"]) + dr, int(m["col"]) + dc)
        for m in analysis["markers"]
        for dr, dc in (*CROSS, *RINGS[str(m["side"])])
    }
    stray_cell = next(
        (rr, cc)
        for rr in range(2, len(valid) - 2)
        for cc in range(2, len(valid[0]) - 2)
        if (rr, cc) not in occupied
        and valid[rr][cc] == bg
        and all(
            valid[nr][nc] != fg
            for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1))
        )
    )
    stray_foreground[stray_cell[0]][stray_cell[1]] = fg

    duplicate_frame_color = [row[:] for row in valid]
    for rr in range(1, len(valid) - 1):
        duplicate_frame_color[rr][-1] = top

    nonzero_corner = [row[:] for row in valid]
    nonzero_corner[0][0] = top

    return [
        ("broken_frame_side", broken_frame),
        ("missing_ring_cell", missing_ring_cell),
        ("prefilled_background_cross", prefilled_cross),
        ("stray_foreground_cell", stray_foreground),
        ("duplicate_frame_side_color", duplicate_frame_color),
        ("nonzero_corner", nonzero_corner),
    ]
