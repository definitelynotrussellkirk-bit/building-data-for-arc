"""Generator for ``round3_md:rectangle_or_not`` (task 0050e48a0620).

Rule: treat each nonzero, same-color 4-connected component as one object.
Recolor the complete object yellow (4) iff it exactly fills its bounding box;
otherwise recolor it blue (1).  Input color is deliberately non-semantic.

The curriculum keeps the public ARC manifold visible instead of only emitting
large synthetic scenes.  Every fourth sample is a three-object, all-red (2)
canonical-profile anchor.  The other samples deliberately reuse one non-output color across a rectangle
and a non-rectangle so that input-color/label shortcuts fail,
and every sample includes a one-cell-missing near rectangle so that "looks
rectangular" is not enough.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import bbox_of
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0050e48a0620"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Comment-sensitive normalized hash of the live selected task source.
RULE_HASH = "4c30083aef18"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Every separated same-color 4-connected object is recolored by exact "
    "rectangularity: bbox completely filled -> 4, otherwise -> 1.  Every "
    "ordinary scene contains both classes and a missing-corner near miss; "
    "non-anchor scenes reuse one non-output input color across both classes so the "
    "same input color maps to both 4 and 1, proving input color is irrelevant."
)

INVARIANTS = [
    "background is 0 and all foreground cells use colors 1..9",
    "three to five foreground components are separated by at least one-cell halos",
    "ordinary generated scenes contain both rectangular and non-rectangular objects",
    "ordinary generated scenes contain a rectangle-missing-one-corner near miss",
    "every fourth sample is an all-color-2 canonical-profile anchor",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "1-in-4 canonical anchor; otherwise difficulty-weighted 8..12",
        "valid": "8..12",
        "doc": "Grid height; exactly observable as len(grid).",
    },
    "grid_w": {
        "type": "int",
        "default": "1-in-4 canonical anchor; otherwise difficulty-weighted 9..13",
        "valid": "9..13",
        "doc": "Grid width; exactly observable as len(grid[0]).",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# All public examples have exactly three red objects: two rectangles and one
# non-rectangle.  The dimensions are the four public train/test input profiles.
_CANONICAL_DIMS = ((8, 9), (9, 10), (10, 10), (9, 11))
_CANONICAL_SIGNATURES = {
    (8, 9, 3, 2, 1, (2,)),
    (9, 10, 3, 2, 1, (2,)),
    (10, 10, 3, 2, 1, (2,)),
    (9, 11, 3, 2, 1, (2,)),
}
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "shared_color_opposite_labels",
    "shared_color_opposite_labels",
    "shared_color_opposite_labels",
)

Cell = tuple[int, int]
Grid = list[list[int]]
Shape = frozenset[Cell]

_RECT_SHAPES: tuple[Shape, ...] = (
    frozenset({(0, 0)}),
    frozenset({(0, 0), (0, 1), (0, 2)}),
    frozenset({(0, 0), (1, 0), (2, 0)}),
    frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)}),
)
_NEAR_MISS_SHAPES: tuple[Shape, ...] = (
    # Each is a filled 2x3 or 3x2 rectangle with one corner removed.
    frozenset({(0, 1), (0, 2), (1, 0), (1, 1), (1, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)}),
    frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)}),
)
_IRREGULAR_SHAPES: tuple[Shape, ...] = (
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)}),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the teaching schedule for lesson-level sliding-window checks."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _shape_bbox_area(cells: set[Cell] | frozenset[Cell]) -> int:
    r1, c1, r2, c2 = bbox_of(cells)
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def _is_rect(cells: set[Cell] | frozenset[Cell]) -> bool:
    return bool(cells) and len(cells) == _shape_bbox_area(cells)


def _is_missing_one_corner(cells: set[Cell] | frozenset[Cell]) -> bool:
    if not cells:
        return False
    r1, c1, r2, c2 = bbox_of(cells)
    bh, bw = r2 - r1 + 1, c2 - c1 + 1
    if bh < 2 or bw < 2 or len(cells) != bh * bw - 1:
        return False
    corners = {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}
    bbox_cells = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
    missing = bbox_cells - set(cells)
    return len(missing) == 1 and next(iter(missing)) in corners


def _single_color_components(grid: Grid) -> list[tuple[int, set[Cell]]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[tuple[int, set[Cell]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[Cell] = set()
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _analyze(grid: Grid) -> dict[str, Any]:
    components = _single_color_components(grid)
    rects = [(color, cells) for color, cells in components if _is_rect(cells)]
    nonrects = [(color, cells) for color, cells in components if not _is_rect(cells)]
    near_misses = [
        (color, cells) for color, cells in nonrects if _is_missing_one_corner(cells)
    ]
    foreground_colors = tuple(sorted({color for color, _ in components}))
    return {
        "components": components,
        "rects": rects,
        "nonrects": nonrects,
        "near_misses": near_misses,
        "foreground_colors": foreground_colors,
        "shared_class_colors": tuple(sorted(
            {color for color, _ in rects} & {color for color, _ in nonrects}
        )),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's scene grammar without requiring teaching witnesses."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged"]
    if not (8 <= len(grid) <= 12 and 9 <= width <= 13):
        return [f"grid dimensions {len(grid)}x{width} are outside the task manifold"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]

    components = _single_color_components(grid)
    errors: list[str] = []
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3..5 foreground objects, found {len(components)}")

    h = len(grid)
    for color, cells in components:
        if color == 0:
            errors.append("background color 0 cannot be a foreground component")
        if any(r in (0, h - 1) or c in (0, width - 1) for r, c in cells):
            errors.append("foreground objects must retain a one-cell border margin")
            break

    # The public scenes and generated teaching scenes keep objects visually
    # separated; this prevents accidental same-rule ambiguity from touching
    # differently colored components.
    for index, (_, cells) in enumerate(components):
        halo = {
            (r + dr, c + dc)
            for r, c in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        }
        for _, other in components[index + 1 :]:
            if halo & other:
                errors.append("foreground objects must be halo-separated")
                return errors
    return errors


def _expected_output(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for _, cells in _single_color_components(grid):
        target = 4 if _is_rect(cells) else 1
        for r, c in cells:
            output[r][c] = target
    return output


# Test-only mirror; the canonical Racket program remains the output authority.
rule_mirror = _expected_output


def _linked_signature(grid: Grid) -> tuple[Any, ...] | None:
    if self_check(grid):
        return None
    facts = _analyze(grid)
    return (
        len(grid),
        len(grid[0]),
        len(facts["components"]),
        len(facts["rects"]),
        len(facts["nonrects"]),
        facts["foreground_colors"],
    )


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked public manifold, not merely marginal dimensions."""
    errors = self_check(grid)
    if errors:
        return errors
    signature = _linked_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked signature {signature!r} is outside the public manifold"]
    return []


def canonical_profile_signature(grid):
    return _linked_signature(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact override axis from the returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("cannot observe dimensions from an empty grid")
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        raise ValueError("cannot observe dimensions from a ragged grid")
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def semantic_signature(grid) -> dict[str, Any]:
    """Linked task observables used by strict semantic census/evidence scripts."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _analyze(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "objects": len(facts["components"]),
        "rectangles": len(facts["rects"]),
        "non_rectangles": len(facts["nonrects"]),
        "near_misses": len(facts["near_misses"]),
        "foreground_colors": facts["foreground_colors"],
        "shared_class_colors": facts["shared_class_colors"],
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _place(grid: Grid, rng, shape: Shape, color: int) -> bool:
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    # Preserve a one-cell outer margin.  range upper bounds are exclusive.
    if sh > h - 2 or sw > w - 2:
        return False
    spots = [
        (r0, c0)
        for r0 in range(1, h - sh)
        for c0 in range(1, w - sw)
    ]
    rng.shuffle(spots)
    for r0, c0 in spots:
        absolute = {(r0 + r, c0 + c) for r, c in shape}
        blocked = False
        for r, c in absolute:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                        blocked = True
                        break
                if blocked:
                    break
            if blocked:
                break
        if blocked:
            continue
        for r, c in absolute:
            grid[r][c] = color
        return True
    return False


def _anchor_dims(seed: int, sample_index: int) -> tuple[int, int]:
    # Stable without relying on process hash randomization.
    return _CANONICAL_DIMS[(int(seed) + int(sample_index) // 4) % len(_CANONICAL_DIMS)]


def _draw_dimensions(ctx, seed: int, sample_index: int, overrides) -> tuple[int, int]:
    if not any(overrides.get(name) is not None for name in AXES) and sample_index % 4 == 0:
        target_h, target_w = _anchor_dims(seed, sample_index)
        return (
            ctx.draw_int("grid_h", target_h, target_h),
            ctx.draw_int("grid_w", target_w, target_w),
        )
    return (
        ctx.draw_int_diff("grid_h", 8, 12),
        ctx.draw_int_diff("grid_w", 9, 13),
    )


def _scene_specs(ctx, seed: int, sample_index: int, canonical_anchor: bool):
    rect_rng = ctx.draw_rng("rect_shape_family")
    nonrect_rng = ctx.draw_rng("nonrect_shape_family")
    if canonical_anchor:
        # Exactly the public linked class counts/palette: 2 rect, 1 non-rect.
        rect_a = _RECT_SHAPES[(seed + sample_index) % len(_RECT_SHAPES)]
        rect_b = _RECT_SHAPES[(seed + sample_index + 2) % len(_RECT_SHAPES)]
        near = _NEAR_MISS_SHAPES[(seed + sample_index) % len(_NEAR_MISS_SHAPES)]
        return [(rect_a, 2), (rect_b, 2), (near, 2)]

    # Reuse one non-output color across opposite shape classes: the same input
    # color must map to both labels, which directly refutes color-based rules.
    rect_a = rect_rng.choice(_RECT_SHAPES)
    near = nonrect_rng.choice(_NEAR_MISS_SHAPES)
    third = rect_rng.choice(_RECT_SHAPES)
    role_color = ctx.draw_rng("role_color").choice((2, 3, 5, 6, 7, 8, 9))
    extra_color = ctx.draw_rng("extra_color").choice((2, 3, 5, 6, 7, 8, 9))
    specs: list[tuple[Shape, int]] = [(rect_a, role_color), (near, role_color), (third, extra_color)]

    # Add one harder irregular distractor on medium/hard-ish draws, when space
    # allows.  It is optional because object count is intentionally not an exact
    # public axis; the three mandatory objects carry all task semantics.
    if ctx.draw_rng("extra_object_gate").random() < 0.60:
        irregular = nonrect_rng.choice(_IRREGULAR_SHAPES)
        color = ctx.draw_rng("irregular_color").choice((2, 3, 5, 6, 7, 8, 9))
        specs.append((irregular, color))
    return specs


def _build_scene(ctx, seed: int, sample_index: int, h: int, w: int, canonical_anchor: bool) -> Grid:
    specs = _scene_specs(ctx, seed, sample_index, canonical_anchor)
    # The first three specs carry the mandatory lesson semantics.  Sort only
    # within that subset so an optional large distractor can never displace a
    # mandatory role when packing gets tight.
    ordered = sorted(specs[:3], key=lambda item: _shape_bbox_area(item[0]), reverse=True)
    ordered += sorted(specs[3:], key=lambda item: _shape_bbox_area(item[0]), reverse=True)
    mandatory = 3
    for attempt in range(24):
        grid = full_grid(h, w, 0)
        rng = ctx.draw_rng(f"layout_attempt_{attempt}")
        placed = 0
        for index, (shape, color) in enumerate(ordered):
            if _place(grid, rng, shape, color):
                placed += 1
            elif index < mandatory:
                break
        else:
            if placed >= mandatory:
                return grid
        if placed >= mandatory and not canonical_anchor:
            return grid
    raise RuntimeError(f"could not place three separated objects on {h}x{w}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_anchor = not overrides and sample_index % 4 == 0
    h, w = _draw_dimensions(ctx, seed, sample_index, overrides)
    grid = _build_scene(ctx, seed, sample_index, h, w, canonical_anchor)
    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------- rivals / teaching contract

def _paint_all_foreground(grid: Grid, color: int) -> Grid:
    return [[color if value else 0 for value in row] for row in grid]


def _rival_all_yellow(grid: Grid) -> Grid:
    return _paint_all_foreground(grid, 4)


def _rival_all_blue(grid: Grid) -> Grid:
    return _paint_all_foreground(grid, 1)


def _rival_identity(grid: Grid) -> Grid:
    return deepcopy(grid)


def _rival_almost_rectangle_is_rectangle(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for _, cells in _single_color_components(grid):
        target = 4 if _is_rect(cells) or _is_missing_one_corner(cells) else 1
        for r, c in cells:
            output[r][c] = target
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "all_yellow": _rival_all_yellow,
    "all_blue": _rival_all_blue,
    "identity_input_color": _rival_identity,
    "almost_rectangle_counts_as_rectangle": _rival_almost_rectangle_is_rectangle,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _has_rect(grid: Grid) -> bool:
    return bool(_analyze(grid)["rects"])


def _has_nonrect(grid: Grid) -> bool:
    return bool(_analyze(grid)["nonrects"])


def _has_near_miss(grid: Grid) -> bool:
    return bool(_analyze(grid)["near_misses"])


def _has_visible_recolor(grid: Grid) -> bool:
    return _expected_output(grid) != grid


def _has_shared_color_opposite_labels(grid: Grid) -> bool:
    return bool(_analyze(grid)["shared_class_colors"])


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "rectangular_branch": _has_rect,
    "nonrectangular_branch": _has_nonrect,
    "near_miss_is_nonrectangular": _has_near_miss,
    "input_color_is_not_output_label": _has_visible_recolor,
    "same_input_color_maps_to_both_labels": _has_shared_color_opposite_labels,
}
WITNESS_RIVALS = {
    "rectangular_branch": ["all_blue"],
    "nonrectangular_branch": ["all_yellow"],
    "near_miss_is_nonrectangular": ["almost_rectangle_counts_as_rectangle"],
    "input_color_is_not_output_label": ["identity_input_color"],
    "same_input_color_maps_to_both_labels": ["identity_input_color"],
}


def _validate_pair(pair, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    expected = _expected_output(pair["input"])
    if pair["output"] != expected:
        return [f"{label} output is not exact rectangularity recoloring"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require every two-demo window to kill the named shortcut programs."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    reasons.extend(f"query input: {error}" for error in query_errors)
    if reasons:
        return reasons

    # At most one of any two consecutive scheduled demos is an all-red anchor;
    # therefore the pair must contain a same-color/opposite-label discriminator.
    if not any(_has_shared_color_opposite_labels(demo["input"]) for demo in demos):
        reasons.append("demos lack one input color shared by rect and non-rect objects")
    if not any(_has_near_miss(demo["input"]) for demo in demos):
        reasons.append("demos lack a missing-corner near-miss discriminator")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            rival_query = competitor(query["input"])
            expected_query = _expected_output(query["input"])
            if rival_query != expected_query:
                reasons.append(
                    f"named competitor {name!r} fits every demo but disagrees on the query"
                )
    return reasons
