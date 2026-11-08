"""Task-linked generator for ARC task ``08ed6ac7`` / ``dd09ba465298``.

The authoritative Racket rule ranks every same-color 4-connected nonzero
component by cell count (largest first) and recolors rank ``i`` with color
``i``.  This generator deliberately alternates canonical vertical-bar anchors
with horizontal bars and non-rectangular shape scenes.  The shape scenes contain
a size-5 object whose bounding-box height/area exceed those of the size-6
object, so height and bounding-box shortcuts that fit every canonical example
are visibly falsified in every two-example lesson window.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "dd09ba465298"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6dce763a142e"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find every same-color 4-connected nonzero component, sort components by "
    "cell count from largest to smallest, and recolor the i-th component with "
    "color i. Generated lessons use distinct component sizes and include "
    "non-rectangular counterexamples to height, bounding-box-area, reading-"
    "order, input-color, smallest-first, and identity shortcuts."
)

INVARIANTS = [
    "background is fixed at color 0",
    "there are 3..5 pairwise background-separated components",
    "all component cell counts are at least 2 and pairwise distinct",
    "the input palette is either one shared nonzero color or one color per component",
    "ordinary two-example windows contain a non-rectangular size-vs-bbox discriminator",
    "the returned input is never already colored by its correct size ranks",
]

SCENE_KINDS = ("columns", "rows", "shapes")
PALETTE_MODES = ("same_color", "distinct_colors")
RANK_ORDERS = ("ascending", "descending", "scrambled")
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw in 9..17; canonical anchors use 9",
        "valid": "9..17",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw in 9..17; canonical anchors use 9",
        "valid": "9..17",
    },
    "n_objects": {
        "type": "int",
        "default": "scheduled 3..5",
        "valid": "3..5",
    },
    "scene_kind": {
        "type": "str",
        "default": "scheduled columns|rows|shapes",
        "valid": "columns|rows|shapes",
    },
    "palette_mode": {
        "type": "str",
        "default": "scheduled same_color|distinct_colors",
        "valid": "same_color|distinct_colors",
    },
    "rank_order": {
        "type": "str",
        "default": "scheduled ascending|descending|scrambled",
        "valid": "ascending|descending|scrambled",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# The canonical left-to-right component-size profiles.  Foreground relabeling
# is lawful because the selected rule ignores input color.
_CANONICAL_SIZE_SEQUENCES = (
    (2, 5, 4, 8),
    (8, 6, 9, 3),
    (8, 3, 7, 5),
)

# Connected templates keyed by exact cell count.  Sizes 5 and 6 are the key
# discriminator: size 5 has bbox 3x3, while size 6 has bbox 2x3.
_SHAPE_TEMPLATES: dict[int, frozenset[Cell]] = {
    2: frozenset({(0, 0), (0, 1)}),
    3: frozenset({(0, 0), (1, 0), (1, 1)}),
    4: frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
    5: frozenset({(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}),
    6: frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)}),
}

# Eight explicit residues make the curriculum auditable.  Every pair of
# consecutive residues contains a shapes scene, a distinct-palette scene, and
# a non-descending spatial size order.
SCHEDULE_PROFILES = (
    "r0_canonical_columns_same_scrambled_n4",
    "r1_shapes_distinct_descending_n3",
    "r2_rows_same_scrambled_n5",
    "r3_shapes_distinct_ascending_n4",
    "r4_canonical_columns_same_scrambled_n4",
    "r5_shapes_distinct_descending_n3",
    "r6_rows_same_scrambled_n5",
    "r7_shapes_distinct_ascending_n4",
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the exact ordinary schedule residue used by a draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_axes(sample_index: int) -> dict[str, Any]:
    residue = int(sample_index) % 8
    return {
        "n_objects": (4, 3, 5, 4, 4, 3, 5, 4)[residue],
        "scene_kind": (
            "columns", "shapes", "rows", "shapes",
            "columns", "shapes", "rows", "shapes",
        )[residue],
        "palette_mode": "same_color" if residue % 2 == 0 else "distinct_colors",
        "rank_order": (
            "scrambled", "descending", "scrambled", "ascending",
            "scrambled", "descending", "scrambled", "ascending",
        )[residue],
    }


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _bbox(cells: list[Cell] | tuple[Cell, ...]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalize_cells(cells: list[Cell] | tuple[Cell, ...]) -> frozenset[Cell]:
    top, left, _, _ = _bbox(cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _components(grid: Grid) -> list[dict[str, Any]]:
    """Return same-color 4-connected nonzero components, matching Racket."""
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells: list[Cell] = []
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            box = _bbox(cells)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "color": color,
                    "size": len(cells),
                    "bbox": box,
                    "bbox_h": box[2] - box[0] + 1,
                    "bbox_w": box[3] - box[1] + 1,
                    "bbox_area": (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
                    "normalized": _normalize_cells(cells),
                }
            )
    return components


def _line_positions(dimension: int, count: int, *, canonical: bool = False) -> list[int]:
    if canonical:
        if dimension != 9 or count != 4:
            raise ValueError("canonical line positions require dimension=9 and count=4")
        return [1, 3, 5, 7]
    # dimension >= 9 and count <= 5 guarantee at least one background line
    # between adjacent positions.
    return [round(i * (dimension - 1) / (count - 1)) for i in range(count)]


def _shape_anchors(h: int, w: int, count: int) -> list[Cell]:
    tl = (0, 0)
    tr = (0, w - 3)
    center = (h // 2 - 1, w // 2 - 1)
    bl = (h - 3, 0)
    br = (h - 3, w - 3)
    if count == 3:
        return [tl, center, br]
    if count == 4:
        return [tl, tr, bl, br]
    if count == 5:
        return [tl, tr, center, bl, br]
    raise ValueError(f"shape count must be 3..5, found {count}")


def _classify_scene(
    grid: Grid, components: list[dict[str, Any]], errors: list[str]
) -> str | None:
    h, w = len(grid), len(grid[0])
    count = len(components)

    column_like = bool(components) and all(
        comp["bbox_w"] == 1
        and comp["bbox_h"] == comp["size"]
        and comp["bbox"][2] == h - 1
        for comp in components
    )
    if column_like:
        columns = sorted(comp["bbox"][1] for comp in components)
        if any(right - left < 2 for left, right in zip(columns, columns[1:])):
            column_like = False

    row_like = bool(components) and all(
        comp["bbox_h"] == 1
        and comp["bbox_w"] == comp["size"]
        and comp["bbox"][1] == 0
        for comp in components
    )
    if row_like:
        rows = sorted(comp["bbox"][0] for comp in components)
        if any(bottom - top < 2 for top, bottom in zip(rows, rows[1:])):
            row_like = False

    shape_like = False
    if 3 <= count <= 5:
        expected_sizes = set(range(7 - count, 7))
        actual_sizes = {comp["size"] for comp in components}
        templates_match = all(
            comp["size"] in _SHAPE_TEMPLATES
            and comp["normalized"] == _SHAPE_TEMPLATES[comp["size"]]
            for comp in components
        )
        actual_anchors = sorted((comp["bbox"][0], comp["bbox"][1]) for comp in components)
        expected_anchors = sorted(_shape_anchors(h, w, count))
        shape_like = (
            actual_sizes == expected_sizes
            and templates_match
            and actual_anchors == expected_anchors
        )

    kinds = [
        name
        for name, matches in (
            ("columns", column_like),
            ("rows", row_like),
            ("shapes", shape_like),
        )
        if matches
    ]
    if len(kinds) != 1:
        errors.append(
            "scene must be exactly one of bottom-aligned separated columns, "
            "left-aligned separated rows, or the scheduled shape templates"
        )
        return None
    return kinds[0]


def _spatial_components(
    components: list[dict[str, Any]], scene_kind: str
) -> list[dict[str, Any]]:
    if scene_kind == "columns":
        return sorted(components, key=lambda comp: (comp["bbox"][1], comp["bbox"][0]))
    return sorted(components, key=lambda comp: (comp["bbox"][0], comp["bbox"][1]))


def _rank_order_from_sizes(sizes: list[int]) -> str:
    if sizes == sorted(sizes):
        return "ascending"
    if sizes == sorted(sizes, reverse=True):
        return "descending"
    return "scrambled"


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "components": []}
    normalized = [list(row) for row in grid]
    h, w = len(normalized), len(normalized[0])
    if not 9 <= h <= 17:
        errors.append(f"height must be 9..17, found {h}")
    if not 9 <= w <= 17:
        errors.append(f"width must be 9..17, found {w}")

    components = _components(normalized)
    count = len(components)
    if not 3 <= count <= 5:
        errors.append(f"expected 3..5 components, found {count}")
    sizes = [comp["size"] for comp in components]
    if any(size < 2 for size in sizes):
        errors.append("every component must contain at least two cells")
    if len(set(sizes)) != len(sizes):
        errors.append("component cell counts must be pairwise distinct")

    # Different-colored cells that touch are distinct objects to Racket, but
    # they are excluded from this teaching grammar so visual object boundaries
    # are never carried only by color.
    for r in range(h):
        for c in range(w):
            if normalized[r][c] == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if (
                    nr < h
                    and nc < w
                    and normalized[nr][nc] != 0
                    and normalized[nr][nc] != normalized[r][c]
                ):
                    errors.append("all components must be separated by background cells")
                    break
            else:
                continue
            break
        if any("separated by background" in reason for reason in errors):
            break

    palette = sorted({comp["color"] for comp in components})
    if len(palette) == 1:
        palette_mode: str | None = "same_color"
    elif len(palette) == count:
        palette_mode = "distinct_colors"
    else:
        palette_mode = None
        errors.append(
            "foreground palette must use either one shared color or one distinct color per component"
        )

    scene_kind = _classify_scene(normalized, components, errors)
    spatial = _spatial_components(components, scene_kind) if scene_kind else []
    size_sequence = [comp["size"] for comp in spatial]
    rank_order = _rank_order_from_sizes(size_sequence) if spatial else None

    analysis = {
        "errors": errors,
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "components": components,
        "n_objects": count,
        "scene_kind": scene_kind,
        "palette": palette,
        "palette_mode": palette_mode,
        "size_sequence": size_sequence,
        "rank_order": rank_order,
    }
    if not errors and rule_mirror(normalized) == normalized:
        errors.append("input is already colored by size rank, so the rule would be a no-op")
    return analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, shortcut-only, and identity scenes."""
    if difficulty not in _VALID_DIFFICULTIES:
        return ["difficulty must be one of None, 'easy', 'medium', or 'hard'"]
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and requested[axis] is not None:
                    if observed[axis] != requested[axis]:
                        errors.append(
                            f"override {axis}={requested[axis]!r} realized as {observed[axis]!r}"
                        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept exactly the task-linked, unambiguous component-ranking grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared axis exactly from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_objects": analysis["n_objects"],
        "scene_kind": analysis["scene_kind"],
        "palette_mode": analysis["palette_mode"],
        "rank_order": analysis["rank_order"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        **observe_overrides(grid),
        "component_sizes_spatial": list(analysis["size_sequence"]),
        "foreground_palette": list(analysis["palette"]),
        "canonical_anchor": _is_canonical_anchor_analysis(analysis),
        "shape_size5_bbox_area": next(
            (comp["bbox_area"] for comp in analysis["components"] if comp["size"] == 5),
            None,
        ),
        "shape_size6_bbox_area": next(
            (comp["bbox_area"] for comp in analysis["components"] if comp["size"] == 6),
            None,
        ),
    }


def _draw_axis_int(ctx, label: str, lo: int, hi: int, scheduled: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if scheduled is not None:
        return ctx.draw_int(label, scheduled, scheduled)
    return ctx.draw_int_diff(label, lo, hi)


def _draw_axis_choice(
    ctx, label: str, options: tuple[str, ...], scheduled: str
) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _arrange_sizes(sorted_sizes: list[int], rank_order: str) -> list[int]:
    values = sorted(sorted_sizes)
    if rank_order == "ascending":
        return values
    if rank_order == "descending":
        return list(reversed(values))
    permutations = {
        3: (1, 2, 0),
        4: (1, 3, 0, 2),
        5: (2, 4, 0, 3, 1),
    }
    return [values[index] for index in permutations[len(values)]]


def _ordinary_sizes(count: int, limit: int, rank_order: str, rng) -> list[int]:
    pool = list(range(2, min(limit, 9) + 1))
    if len(pool) < count:
        raise ValueError(f"dimension {limit} cannot host {count} distinct legal sizes")
    chosen = sorted(rng.sample(pool, count))
    return _arrange_sizes(chosen, rank_order)


def _shape_sizes(count: int, rank_order: str) -> list[int]:
    return _arrange_sizes(list(range(7 - count, 7)), rank_order)


def _component_colors(ctx, sizes: list[int], palette_mode: str) -> list[int]:
    count = len(sizes)
    if palette_mode == "same_color":
        foreground = ctx.draw_color("foreground_color", exclude={0, 1, 2, 3, 4})
        return [foreground] * count

    palette = sorted(
        ctx.draw_distinct_colors(
            "foreground_colors", n=count, exclude={0, 1, 2, 3, 4}
        )
    )
    rank_by_size = {
        size: rank for rank, size in enumerate(sorted(sizes, reverse=True), start=1)
    }
    # Cyclically shift colors by true rank.  Sorting by input color therefore
    # yields rank n, rank 1, rank 2, ... rather than the correct rank order.
    return [palette[rank_by_size[size] % count] for size in sizes]


def _paint_scene(
    h: int,
    w: int,
    scene_kind: str,
    sizes: list[int],
    colors: list[int],
    *,
    canonical_anchor: bool,
) -> Grid:
    grid = full_grid(h, w, 0)
    count = len(sizes)
    if scene_kind == "columns":
        columns = _line_positions(w, count, canonical=canonical_anchor)
        for col, size, color in zip(columns, sizes, colors):
            for row in range(h - size, h):
                grid[row][col] = color
        return grid
    if scene_kind == "rows":
        rows = _line_positions(h, count)
        for row, size, color in zip(rows, sizes, colors):
            for col in range(size):
                grid[row][col] = color
        return grid
    if scene_kind == "shapes":
        for (top, left), size, color in zip(_shape_anchors(h, w, count), sizes, colors):
            for dr, dc in _SHAPE_TEMPLATES[size]:
                grid[top + dr][left + dc] = color
        return grid
    raise ValueError(f"unknown scene_kind {scene_kind!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    scheduled = _scheduled_axes(sample_index)
    canonical_anchor = not overrides and int(sample_index) % 4 == 0
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_axis_int(ctx, "grid_h", 9, 17, 9 if canonical_anchor else None)
    w = _draw_axis_int(ctx, "grid_w", 9, 17, 9 if canonical_anchor else None)
    n_objects = _draw_axis_int(
        ctx, "n_objects", 3, 5, 4 if canonical_anchor else scheduled["n_objects"]
    )
    scene_kind = _draw_axis_choice(
        ctx,
        "scene_kind",
        SCENE_KINDS,
        "columns" if canonical_anchor else scheduled["scene_kind"],
    )
    palette_mode = _draw_axis_choice(
        ctx,
        "palette_mode",
        PALETTE_MODES,
        "same_color" if canonical_anchor else scheduled["palette_mode"],
    )
    rank_order = _draw_axis_choice(
        ctx,
        "rank_order",
        RANK_ORDERS,
        "scrambled" if canonical_anchor else scheduled["rank_order"],
    )

    if canonical_anchor:
        profile_index = (int(seed) + int(sample_index) // 8) % len(_CANONICAL_SIZE_SEQUENCES)
        sizes = list(_CANONICAL_SIZE_SEQUENCES[profile_index])
    elif scene_kind == "shapes":
        sizes = _shape_sizes(n_objects, rank_order)
    else:
        limit = h if scene_kind == "columns" else w
        sizes = _ordinary_sizes(
            n_objects, limit, rank_order, ctx.draw_rng("component_sizes")
        )

    colors = _component_colors(ctx, sizes, palette_mode)
    grid = _paint_scene(
        h,
        w,
        scene_kind,
        sizes,
        colors,
        canonical_anchor=canonical_anchor,
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid component-ranking lesson: " + "; ".join(errors))
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_objects": n_objects,
        "scene_kind": scene_kind,
        "palette_mode": palette_mode,
        "rank_order": rank_order,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"constructed axes drifted: expected {expected}, observed {observed}")
    return grid


def _apply_order(grid: Any, order_key: Callable[[dict[str, Any]], Any]) -> Grid:
    analysis = _analyze_without_identity(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    components = sorted(analysis["components"], key=order_key)
    out = [list(row) for row in analysis["grid"]]
    for rank, component in enumerate(components, start=1):
        for row, col in component["cells"]:
            out[row][col] = rank
    return out


def _analyze_without_identity(grid: Any) -> dict[str, Any]:
    """Analyze while avoiding the rule_mirror -> _analyze recursion edge."""
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "components": []}
    normalized = [list(row) for row in grid]
    h, w = len(normalized), len(normalized[0])
    components = _components(normalized)
    return {
        "errors": [],
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "components": components,
    }


def _generic_spatial_key(component: dict[str, Any]) -> tuple[int, int]:
    return component["bbox"][0], component["bbox"][1]


def rule_mirror(grid: Any) -> Grid:
    """Faithful Python mirror; the canonical Racket program remains authority."""
    return _apply_order(
        grid,
        lambda comp: (-comp["size"], *_generic_spatial_key(comp)),
    )


def _smallest_first(grid: Any) -> Grid:
    return _apply_order(grid, lambda comp: (comp["size"], *_generic_spatial_key(comp)))


def _reading_order(grid: Any) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    scene = analysis["scene_kind"]
    if scene == "columns":
        key = lambda comp: (comp["bbox"][1], comp["bbox"][0])
    else:
        key = _generic_spatial_key
    return _apply_order(grid, key)


def _height_rank(grid: Any) -> Grid:
    return _apply_order(
        grid,
        lambda comp: (-comp["bbox_h"], *_generic_spatial_key(comp)),
    )


def _bbox_area_rank(grid: Any) -> Grid:
    return _apply_order(
        grid,
        lambda comp: (-comp["bbox_area"], *_generic_spatial_key(comp)),
    )


def _input_color_rank(grid: Any) -> Grid:
    return _apply_order(
        grid,
        lambda comp: (comp["color"], *_generic_spatial_key(comp)),
    )


def _identity(grid: Any) -> Grid:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    return [list(row) for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "smallest_first": _smallest_first,
    "reading_order": _reading_order,
    "height_rank": _height_rank,
    "bbox_area_rank": _bbox_area_rank,
    "input_color_rank": _input_color_rank,
    "identity": _identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _is_canonical_anchor_analysis(analysis: dict[str, Any]) -> bool:
    if analysis["errors"]:
        return False
    if (
        analysis["grid_h"] != 9
        or analysis["grid_w"] != 9
        or analysis["n_objects"] != 4
        or analysis["scene_kind"] != "columns"
        or analysis["palette_mode"] != "same_color"
    ):
        return False
    columns = [
        comp["bbox"][1]
        for comp in _spatial_components(analysis["components"], "columns")
    ]
    return columns == [1, 3, 5, 7] and tuple(analysis["size_sequence"]) in _CANONICAL_SIZE_SEQUENCES


def _witness_axis(axis: str, value: Any):
    def predicate(grid: Any) -> bool:
        analysis = _valid_analysis(grid)
        return analysis is not None and analysis.get(axis) == value

    return predicate


def _rival_disagreement_witness(rival_name: str, extra: Callable[[dict[str, Any]], bool]):
    rival = SEMANTIC_RIVALS[rival_name]

    def predicate(grid: Any) -> bool:
        analysis = _valid_analysis(grid)
        return (
            analysis is not None
            and extra(analysis)
            and rival(grid) != rule_mirror(grid)
        )

    return predicate


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "canonical_anchor": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and _is_canonical_anchor_analysis(analysis)
    ),
    "scene_columns": _witness_axis("scene_kind", "columns"),
    "scene_rows": _witness_axis("scene_kind", "rows"),
    "scene_shapes": _witness_axis("scene_kind", "shapes"),
    "palette_same": _witness_axis("palette_mode", "same_color"),
    "palette_distinct": _rival_disagreement_witness(
        "input_color_rank", lambda analysis: analysis["palette_mode"] == "distinct_colors"
    ),
    "rank_ascending": _witness_axis("rank_order", "ascending"),
    "rank_descending": _witness_axis("rank_order", "descending"),
    "rank_scrambled": _witness_axis("rank_order", "scrambled"),
    "three_components": _witness_axis("n_objects", 3),
    "four_components": _witness_axis("n_objects", 4),
    "five_components": _witness_axis("n_objects", 5),
    "shape_height_discriminator": _rival_disagreement_witness(
        "height_rank", lambda analysis: analysis["scene_kind"] == "shapes"
    ),
    "shape_bbox_discriminator": _rival_disagreement_witness(
        "bbox_area_rank", lambda analysis: analysis["scene_kind"] == "shapes"
    ),
    "non_identity": _rival_disagreement_witness("identity", lambda analysis: True),
    "size_not_smallest_first": _rival_disagreement_witness(
        "smallest_first", lambda analysis: True
    ),
}

_BASE_RIVALS = ["smallest_first", "identity"]
WITNESS_RIVALS = {
    "canonical_anchor": ["reading_order", *_BASE_RIVALS],
    "scene_columns": list(_BASE_RIVALS),
    "scene_rows": list(_BASE_RIVALS),
    "scene_shapes": ["height_rank", "bbox_area_rank", *_BASE_RIVALS],
    "palette_same": list(_BASE_RIVALS),
    "palette_distinct": ["input_color_rank", *_BASE_RIVALS],
    "rank_ascending": ["reading_order", *_BASE_RIVALS],
    "rank_descending": list(_BASE_RIVALS),
    "rank_scrambled": ["reading_order", *_BASE_RIVALS],
    "three_components": list(_BASE_RIVALS),
    "four_components": list(_BASE_RIVALS),
    "five_components": list(_BASE_RIVALS),
    "shape_height_discriminator": ["height_rank"],
    "shape_bbox_discriminator": ["bbox_area_rank"],
    "non_identity": ["identity"],
    "size_not_smallest_first": ["smallest_first"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to eliminate every named plausible rival."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the component-size rule")

    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_analysis = _analyze(query["input"])
        if query_analysis["errors"]:
            reasons.append("query input is outside the teaching grammar")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the component-size rule")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Targeted destructive mutations that the validator must reject."""
    fixtures: list[tuple[str, Grid]] = []

    single = full_grid(9, 9, 0)
    for row in range(5, 9):
        single[row][1] = 8
    fixtures.append(("single_component", single))

    tied = full_grid(9, 9, 0)
    for col, size in zip((1, 3, 5), (4, 4, 6)):
        for row in range(9 - size, 9):
            tied[row][col] = 8
    fixtures.append(("tied_component_sizes", tied))

    singleton = full_grid(9, 9, 0)
    for col, size in zip((1, 3, 5, 7), (1, 3, 4, 5)):
        for row in range(9 - size, 9):
            singleton[row][col] = 8
    fixtures.append(("singleton_component", singleton))

    mixed_palette = full_grid(9, 9, 0)
    for col, size, color in zip((1, 3, 5, 7), (2, 3, 4, 5), (8, 8, 7, 6)):
        for row in range(9 - size, 9):
            mixed_palette[row][col] = color
    fixtures.append(("partial_palette_partition", mixed_palette))

    touching = full_grid(9, 9, 0)
    for row in range(5, 9):
        touching[row][1] = 8
    for row in range(4, 9):
        touching[row][2] = 7
    for row in range(3, 9):
        touching[row][5] = 6
    fixtures.append(("different_color_components_touch", touching))

    identity = full_grid(9, 9, 0)
    for col, size, color in zip((1, 3, 5), (5, 4, 3), (1, 2, 3)):
        for row in range(9 - size, 9):
            identity[row][col] = color
    fixtures.append(("rank_colored_identity", identity))

    broken_shape = generate(
        99173,
        1,
        grid_h=9,
        grid_w=9,
        n_objects=3,
        scene_kind="shapes",
        palette_mode="same_color",
        rank_order="descending",
    )
    broken_shape = [row[:] for row in broken_shape]
    # Remove the far corner of the size-5 L.  The object stays connected but no
    # longer matches the only lawful template for its new/old size.
    broken_shape[5][5] = 0
    fixtures.append(("broken_shape_template", broken_shape))

    fixtures.append(("ragged_grid", [[0] * 9, [0] * 8]))
    return fixtures
