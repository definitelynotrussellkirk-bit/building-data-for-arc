"""Generator for 3b:m17 — keep components that enclose a true hole.

The canonical rule is topological, not a rectangle/size/color heuristic: split
non-zero cells into 4-connected same-colour components and keep exactly those
components that enclose at least one 4-connected background region fully
inside the component's bounding box.  Solid objects and open almost-rings are
erased.

Ordinary generated scenes deliberately include five shortcut rebuttals:
* an open ring whose bbox interior is missing but whose gap reaches the border;
* that leaking ring has nine cells, matching a true-hole component, so a
  bbox-gap-plus-size-threshold shortcut also fails;
* a non-rectangular hollow component (a ring with an exterior tab);
* a kept and erased component that share a colour; and
* a kept and erased component with the same cell count.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "629ec8fd452e"
TASK_ID = "629ec8fd452e"
VERSION = "3.1.0"
RULE_HASH = "83b51fc36bb6"

SUMMARY = (
    "On a 0-background grid, inspect each 4-connected same-colour component. "
    "Keep the component iff it encloses at least one background region that "
    "cannot reach the border of that component's bounding box. Erase solid "
    "components and open almost-rings. Generated lessons include non-rectangular "
    "hole-bearing objects plus color- and size-matched erased distractors so "
    "rectangle, color, cell-count, bbox-gap, and bbox-gap-plus-size shortcuts "
    "are contradicted."
)

INVARIANTS = [
    "background is 0",
    "at least one component encloses a true internal hole",
    "at least one component has no enclosed hole and is erased by the rule",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..14",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 10..16",
        "valid": "10..16",
    },
    "n_hollow": {
        "type": "int",
        "default": "difficulty-aware 1..2",
        "valid": "1..2",
    },
    "n_solid": {
        "type": "int",
        "default": "difficulty-aware 1..2",
        "valid": "1..2",
    },
    "shared_reject_role": {
        "type": "str",
        "default": "keyed solid|open",
        "valid": "solid|open",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_INT_AXIS_BOUNDS = {
    "grid_h": (9, 14),
    "grid_w": (10, 16),
    "n_hollow": (1, 2),
    "n_solid": (1, 2),
}
_VALID_SHARED_REJECT_ROLES = {"solid", "open"}


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    out: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            if not row or any(ch not in "0123456789" for ch in row):
                raise ValueError("row strings must contain ARC digits only")
            values = [int(ch) for ch in row]
        elif isinstance(row, list):
            values = list(row)
        else:
            raise ValueError("grid rows must be lists or digit strings")
        if width is None:
            width = len(values)
        if not values or len(values) != width:
            raise ValueError("grid must be rectangular and non-empty")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in values
        ):
            raise ValueError("grid values must be integer ARC colours 0..9")
        out.append(values)
    return out


def _components(grid: Any) -> list[dict[str, Any]]:
    g = _coerce_grid(grid)
    height, width = len(g), len(g[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for start_r in range(height):
        for start_c in range(width):
            color = g[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            cells: set[tuple[int, int]] = set()
            while queue:
                row, col = queue.popleft()
                cells.add((row, col))
                for drow, dcol in _DIR4:
                    nxt = row + drow, col + dcol
                    nr, nc = nxt
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and g[nr][nc] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            holes = _enclosed_holes(cells, bbox)
            r0, c0, r1, c1 = bbox
            interior_missing = any(
                (row, col) not in cells
                for row in range(r0 + 1, r1)
                for col in range(c0 + 1, c1)
            )
            border = {
                (row, col)
                for row in range(r0, r1 + 1)
                for col in range(c0, c1 + 1)
                if row in (r0, r1) or col in (c0, c1)
            }
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": bbox,
                    "holes": holes,
                    "has_hole": bool(holes),
                    "bbox_interior_missing": interior_missing,
                    "rectangular_frame": cells == border and r1 - r0 >= 2 and c1 - c0 >= 2,
                }
            )
    return components


def _enclosed_holes(
    cells: set[tuple[int, int]], bbox: tuple[int, int, int, int]
) -> list[set[tuple[int, int]]]:
    r0, c0, r1, c1 = bbox
    zeros = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in cells
    }
    unseen = set(zeros)
    holes: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        queue = deque([start])
        unseen.remove(start)
        region = {start}
        touches_border = False
        while queue:
            row, col = queue.popleft()
            if row in (r0, r1) or col in (c0, c1):
                touches_border = True
            for drow, dcol in _DIR4:
                nxt = row + drow, col + dcol
                if nxt in unseen:
                    unseen.remove(nxt)
                    region.add(nxt)
                    queue.append(nxt)
        if not touches_border:
            holes.append(region)
    return holes


def _analysis(grid: Any) -> dict[str, Any]:
    try:
        g = _coerce_grid(grid)
        components = _components(g)
    except ValueError as exc:
        return {"errors": [str(exc)]}
    hollow = [component for component in components if component["has_hole"]]
    rejected = [component for component in components if not component["has_hole"]]
    open_like = [
        component
        for component in rejected
        if component["bbox_interior_missing"]
    ]
    solid = [
        component
        for component in rejected
        if not component["bbox_interior_missing"]
    ]
    return {
        "errors": [],
        "grid": g,
        "height": len(g),
        "width": len(g[0]),
        "components": components,
        "hollow": hollow,
        "rejected": rejected,
        "open_like": open_like,
        "solid": solid,
        "palette": {value for row in g for value in row if value != 0},
    }


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate_shape(
    cells: Iterable[tuple[int, int]], turns: int
) -> tuple[tuple[int, int], ...]:
    shape = _normalize_shape(cells)
    for _ in range(turns % 4):
        height = max(row for row, _ in shape) + 1
        shape = _normalize_shape((col, height - 1 - row) for row, col in shape)
    return shape


def _rect_frame(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )


def _irregular_hollow() -> tuple[tuple[int, int], ...]:
    # 3x3 closed frame plus an exterior tab: 9 cells, one true hole, not a box.
    return _normalize_shape((*_rect_frame(3, 3), (1, 3)))


def _open_almost_ring(gap_col: int = 1) -> tuple[tuple[int, int], ...]:
    """Return a connected nine-cell 3x4 frame with one leaking border gap."""
    if gap_col not in (1, 2):
        raise ValueError("gap_col must select one of the two interior columns")
    return tuple(cell for cell in _rect_frame(3, 4) if cell != (2, gap_col))


def _filled_rect(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple((row, col) for row in range(height) for col in range(width))


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _boxes_have_blank_gap(
    a: tuple[int, int, int, int], b: tuple[int, int, int, int]
) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return (
        ar1 + 1 < br0
        or br1 + 1 < ar0
        or ac1 + 1 < bc0
        or bc1 + 1 < ac0
    )


def _place_shapes(
    height: int,
    width: int,
    shapes: list[tuple[tuple[int, int], ...]],
    rng,
) -> list[tuple[int, int]]:
    dims = [_shape_dims(shape) for shape in shapes]
    order = sorted(
        range(len(shapes)),
        key=lambda index: (dims[index][0] * dims[index][1], dims[index][0], dims[index][1]),
        reverse=True,
    )
    placements: list[tuple[int, int] | None] = [None] * len(shapes)
    boxes: dict[int, tuple[int, int, int, int]] = {}

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        sh, sw = dims[index]
        candidates = [
            (top, left)
            for top in range(height - sh + 1)
            for left in range(width - sw + 1)
        ]
        rng.shuffle(candidates)
        for top, left in candidates:
            box = (top, left, top + sh - 1, left + sw - 1)
            if any(not _boxes_have_blank_gap(box, other) for other in boxes.values()):
                continue
            placements[index] = (top, left)
            boxes[index] = box
            if search(depth + 1):
                return True
            del boxes[index]
            placements[index] = None
        return False

    if not search(0):
        raise ValueError(
            "requested grid/count combination cannot place separated components"
        )
    return [placement for placement in placements if placement is not None]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_AXIS_BOUNDS:
            if type(value) is not int:
                raise TypeError(
                    f"{name} must be an integer (not bool or a coercible value)"
                )
            low, high = _INT_AXIS_BOUNDS[name]
            if not low <= value <= high:
                raise ValueError(f"{name}={value} outside {low}..{high}")
        elif name == "shared_reject_role":
            if type(value) is not str:
                raise TypeError("shared_reject_role must be a string")
            if value not in _VALID_SHARED_REJECT_ROLES:
                raise ValueError(
                    "shared_reject_role must be either 'solid' or 'open'"
                )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Keep a deterministic canonical-scale anchor in every difficulty band.
    # Explicit overrides always retain the full declared domain; only ordinary
    # draws use the anchor.  The profile gate's pinned sample_index stream hits
    # this residue repeatedly in easy/medium/hard, preventing difficulty skew
    # from starving canonical-sized lessons.
    anchor = sample_index % 4 == 0
    height = (
        ctx.draw_int("grid_h", 10, 10)
        if anchor and "grid_h" not in overrides
        else ctx.draw_int_diff("grid_h", 9, 14)
    )
    width = (
        ctx.draw_int("grid_w", 12, 12)
        if anchor and "grid_w" not in overrides
        else ctx.draw_int_diff("grid_w", 10, 16)
    )
    n_hollow = (
        ctx.draw_int("n_hollow", 2, 2)
        if anchor and "n_hollow" not in overrides
        else ctx.draw_int_diff("n_hollow", 1, 2)
    )
    n_solid = ctx.draw_int_diff("n_solid", 1, 2)
    shared_role = ctx.draw_choice("shared_reject_role", ("solid", "open"))

    shape_rng = ctx.draw_rng("shape-variation")
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")

    hollow_shapes = [
        _rotate_shape(_irregular_hollow(), shape_rng.randrange(4))
    ]
    if n_hollow == 2:
        # Canonical survivors reach 14 cells.  On grids wide enough to carry it,
        # include the canonical-scale 3x6 frame; compact boundary overrides keep
        # the second survivor at 3x3 so every declared dimension/count tuple is
        # realizable.  This shape choice is not an exact override axis.
        if width >= 13:
            hollow_shapes.append(_rect_frame(3, 6))
        else:
            hollow_shapes.append(
                _rotate_shape(_rect_frame(3, 3), shape_rng.randrange(4))
            )
    solid_shapes = [_filled_rect(3, 3)]
    if n_solid == 2:
        solid_shapes.append(_filled_rect(2, 2))
    gap_col = shape_rng.choice((1, 2))
    open_shape = _rotate_shape(
        _open_almost_ring(gap_col), shape_rng.randrange(4)
    )

    shapes = hollow_shapes + solid_shapes + [open_shape]
    placements = _place_shapes(height, width, shapes, layout_rng)
    palette = palette_rng.sample(list(range(1, 10)), 3)

    colors: list[int] = []
    colors.extend([palette[0]] + ([palette[2]] if n_hollow == 2 else []))
    colors.append(palette[0] if shared_role == "solid" else palette[1])
    if n_solid == 2:
        colors.append(palette[1] if n_hollow == 2 else palette[2])
    colors.append(palette[0] if shared_role == "open" else palette[1])

    grid = full_grid(height, width, 0)
    for shape, (top, left), color in zip(shapes, placements, colors):
        for row, col in shape:
            grid[top + row][left + col] = color
    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a generated grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    hollow_colors = {component["color"] for component in analysis["hollow"]}
    solid_colors = {component["color"] for component in analysis["solid"]}
    open_colors = {component["color"] for component in analysis["open_like"]}
    shares_solid = bool(hollow_colors & solid_colors)
    shares_open = bool(hollow_colors & open_colors)
    if shares_solid and not shares_open:
        shared_role = "solid"
    elif shares_open and not shares_solid:
        shared_role = "open"
    else:
        shared_role = "ambiguous"
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_hollow": len(analysis["hollow"]),
        "n_solid": len(analysis["solid"]),
        "shared_reject_role": shared_role,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad authority-compatible input grammar and exact axes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not analysis["hollow"]:
        errors.append("no component with a true enclosed hole")
    if not analysis["rejected"]:
        errors.append("no non-hole component to erase")
    if len(analysis["components"]) < 2:
        errors.append("need at least two nonzero components")

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and name in observed and observed[name] != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed[name]!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate; accepts every canonical input."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    if not 9 <= analysis["height"] <= 14:
        reasons.append("height is outside the canonical/teaching envelope 9..14")
    if not 10 <= analysis["width"] <= 16:
        reasons.append("width is outside the canonical/teaching envelope 10..16")
    if not 2 <= len(analysis["palette"]) <= 4:
        reasons.append("expected 2..4 nonzero colours")
    return reasons


def rule_true(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    out = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["hollow"]:
        for row, col in component["cells"]:
            out[row][col] = component["color"]
    return out


def _rival_bbox_missing_interior(grid):
    """Wrong shortcut: any missing strict-bbox interior cell counts as a hole."""
    analysis = _analysis(grid)
    out = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        if component["bbox_interior_missing"]:
            for row, col in component["cells"]:
                out[row][col] = component["color"]
    return out


def _rival_bbox_missing_interior_at_least_8(grid):
    """Wrong shortcut: bbox interior missing plus an eight-cell size threshold."""
    analysis = _analysis(grid)
    out = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        if component["bbox_interior_missing"] and len(component["cells"]) >= 8:
            for row, col in component["cells"]:
                out[row][col] = component["color"]
    return out


def _rival_rectangular_frames_only(grid):
    """Wrong shortcut: keep only exact rectangular border frames."""
    analysis = _analysis(grid)
    out = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        if component["rectangular_frame"]:
            for row, col in component["cells"]:
                out[row][col] = component["color"]
    return out


def _rival_hole_colors(grid):
    """Wrong shortcut: once a colour survives, keep every object of that colour."""
    analysis = _analysis(grid)
    keep_colors = {component["color"] for component in analysis["hollow"]}
    out = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        if component["color"] in keep_colors:
            for row, col in component["cells"]:
                out[row][col] = component["color"]
    return out


def _rival_hole_cell_counts(grid):
    """Wrong shortcut: keep every object whose cell count matches a survivor."""
    analysis = _analysis(grid)
    keep_counts = {len(component["cells"]) for component in analysis["hollow"]}
    out = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        if len(component["cells"]) in keep_counts:
            for row, col in component["cells"]:
                out[row][col] = component["color"]
    return out


def _witness_open_false_hole(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["open_like"])


def _witness_large_open_false_hole(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        len(component["cells"]) >= 8 for component in analysis["open_like"]
    )


def _witness_irregular_hollow(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        not component["rectangular_frame"] for component in analysis["hollow"]
    )


def _witness_cross_role_color(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    hollow_colors = {component["color"] for component in analysis["hollow"]}
    rejected_colors = {component["color"] for component in analysis["rejected"]}
    return bool(hollow_colors & rejected_colors)


def _witness_equal_cell_count_cross_role(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    hollow_sizes = {len(component["cells"]) for component in analysis["hollow"]}
    rejected_sizes = {len(component["cells"]) for component in analysis["rejected"]}
    return bool(hollow_sizes & rejected_sizes)


SEMANTIC_WITNESSES = {
    "open_gap_rebuts_bbox_gap": _witness_open_false_hole,
    "large_open_gap_rebuts_bbox_size_threshold": _witness_large_open_false_hole,
    "irregular_hollow_rebuts_rect_frame": _witness_irregular_hollow,
    "cross_role_color_rebuts_color_rule": _witness_cross_role_color,
    "equal_cell_count_rebuts_count_rule": _witness_equal_cell_count_cross_role,
}

BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS = {
    "bbox_missing_interior": _rival_bbox_missing_interior,
    "bbox_missing_interior_at_least_8": _rival_bbox_missing_interior_at_least_8,
    "rectangular_frames_only": _rival_rectangular_frames_only,
    "survivor_color": _rival_hole_colors,
    "survivor_cell_count": _rival_hole_cell_counts,
}

WITNESS_RIVALS = {
    "open_gap_rebuts_bbox_gap": ["bbox_missing_interior"],
    "large_open_gap_rebuts_bbox_size_threshold": [
        "bbox_missing_interior_at_least_8"
    ],
    "irregular_hollow_rebuts_rect_frame": ["rectangular_frames_only"],
    "cross_role_color_rebuts_color_rule": ["survivor_color"],
    "equal_cell_count_rebuts_count_rule": ["survivor_cell_count"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named canonical-compatible shortcut survives."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        expected = rule_true(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the true-hole rule")
    query_answer = rule_true(query["input"])
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the true-hole rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
