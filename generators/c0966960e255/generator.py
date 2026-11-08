"""Generator for arc_additional_puzzle_bank_volume6:E36.

Each 4-connected red (2) component is considered independently.  Components
that are symmetric under a left-right reflection inside their own bounding box
are recolored green (3); asymmetric red components and gray (5) distractors are
unchanged.

Ordinary draws contain same-size symmetric/asymmetric contrast components,
including a left-right-only symmetric component paired with its top-bottom-only
rotation.  This makes the symmetry axis observable and blocks size, count,
position, and recolor-all shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c0966960e255"
TASK_ID = "c0966960e255"
VERSION = "3.0.0"
RULE_HASH = "4199c1ecbb19"
MIN_STRICT_FRAC = 0.99
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a 0-background grid, inspect each 4-connected red (2) component in "
    "its own bounding box. Recolor the whole component to green (3) exactly "
    "when its shape is left-right symmetric. Leave asymmetric red components "
    "and gray (5) distractors unchanged."
)

INVARIANTS = [
    "the input palette is exactly a subset of {0,2,5} and includes red and gray",
    "there are 1..2 left-right-symmetric and 1..2 asymmetric red components",
    "at least one symmetric/asymmetric component pair has the same cell count",
    "symmetric red components recolor to 3; asymmetric red and gray cells stay fixed",
    "ordinary draws include axis-specific contrast and vary component positions",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 9..10 easy; 11..17 medium; 18..24 hard",
        "valid": "9..24",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 10..12 easy; 12..19 medium; 18..24 hard",
        "valid": "10..24",
    },
    "n_sym": {
        "type": "int",
        "default": "2",
        "valid": "1..2",
    },
    "n_asym": {
        "type": "int",
        "default": "2",
        "valid": "1..2",
    },
    "n_gray": {
        "type": "int",
        "default": "2 easy; 2..3 medium; 2..4 hard",
        "valid": "1..4",
    },
}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CANONICAL_PROFILES = ((9, 10), (10, 10), (9, 11), (10, 12), (9, 12))

# Every template is 4-connected, occupies a 3x3 box, is left-right symmetric,
# and is not top-bottom symmetric.  Rotating one 90 degrees creates an
# equal-size top-bottom-symmetric but left-right-asymmetric contrast object.
_LR_ONLY_PATTERNS = (
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)),
)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _col in points)
    min_col = min(col for _row, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _rotate_once(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_row = max(row for row, _col in points)
    return _normalize((col, max_row - row) for row, col in points)


def _flip_vertical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_row = max(row for row, _col in points)
    return _normalize((max_row - row, col) for row, col in points)


def _left_right_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    points = _normalize(cells)
    if not points:
        return False
    width = max(col for _row, col in points) + 1
    point_set = set(points)
    return all((row, width - 1 - col) in point_set for row, col in points)


def _top_bottom_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    points = _normalize(cells)
    if not points:
        return False
    height = max(row for row, _col in points) + 1
    point_set = set(points)
    return all((height - 1 - row, col) in point_set for row, col in points)


def _components(grid: list[list[int]], color: int = 2) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        component: list[tuple[int, int]] = []
        for row, col in queue:
            component.append((row, col))
            for dr, dc in _CARD:
                neighbour = (row + dr, col + dc)
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    queue.append(neighbour)
        components.append(sorted(component))
    return components


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        if label in overrides and overrides[label] is not None:
            value = overrides[label]
            if type(value) is not int:
                raise ValueError(f"{label} must be an integer")


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    """Record a deterministic default while honoring the full override range."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _default_axes(ctx, difficulty: Any, sample_index: int) -> tuple[int, int, int, int, int]:
    band = "medium" if difficulty is None else difficulty
    if band == "easy":
        default_h, default_w = _CANONICAL_PROFILES[sample_index % len(_CANONICAL_PROFILES)]
        default_gray = 2
    elif band == "hard":
        default_h = ctx.draw_rng("grid_h_default").randint(18, 24)
        default_w = ctx.draw_rng("grid_w_default").randint(18, 24)
        default_gray = ctx.draw_rng("n_gray_default").randint(2, 4)
    else:
        default_h = ctx.draw_rng("grid_h_default").randint(11, 17)
        default_w = ctx.draw_rng("grid_w_default").randint(12, 19)
        default_gray = ctx.draw_rng("n_gray_default").randint(2, 3)

    height = _draw_scheduled_int(ctx, "grid_h", 9, 24, default_h)
    width = _draw_scheduled_int(ctx, "grid_w", 10, 24, default_w)
    symmetric_count = _draw_scheduled_int(ctx, "n_sym", 1, 2, 2)
    asymmetric_count = _draw_scheduled_int(ctx, "n_asym", 1, 2, 2)
    gray_count = _draw_scheduled_int(ctx, "n_gray", 1, 4, default_gray)
    return height, width, symmetric_count, asymmetric_count, gray_count


def _shape_pairs(rng, symmetric_count: int, asymmetric_count: int):
    order = list(range(len(_LR_ONLY_PATTERNS)))
    rng.shuffle(order)
    required = max(symmetric_count, asymmetric_count)
    sym_shapes: list[tuple[tuple[int, int], ...]] = []
    asym_shapes: list[tuple[tuple[int, int], ...]] = []
    for index in range(required):
        shape = _LR_ONLY_PATTERNS[order[index % len(order)]]
        if rng.randrange(2):
            shape = _flip_vertical(shape)
        symmetric = _normalize(shape)
        asymmetric = _rotate_once(symmetric)
        if not _left_right_symmetric(symmetric) or _top_bottom_symmetric(symmetric):
            raise AssertionError("invalid left-right-only template")
        if _left_right_symmetric(asymmetric) or not _top_bottom_symmetric(asymmetric):
            raise AssertionError("invalid rotated contrast template")
        sym_shapes.append(symmetric)
        asym_shapes.append(asymmetric)
    return sym_shapes[:symmetric_count], asym_shapes[:asymmetric_count]


def _quadrant_anchors(height: int, width: int, rng) -> list[tuple[int, int]]:
    top_hi = max(0, height // 2 - 3)
    bottom_lo = min(height - 3, height // 2 + 1)
    left_hi = max(0, width // 2 - 3)
    right_lo = min(width - 3, width // 2 + 1)
    return [
        (rng.randint(0, top_hi), rng.randint(0, left_hi)),
        (rng.randint(0, top_hi), rng.randint(right_lo, width - 3)),
        (rng.randint(bottom_lo, height - 3), rng.randint(0, left_hi)),
        (rng.randint(bottom_lo, height - 3), rng.randint(right_lo, width - 3)),
    ]


def _paint_shape(
    grid: list[list[int]], anchor: tuple[int, int], cells: Iterable[tuple[int, int]], color: int
) -> None:
    top, left = anchor
    for row, col in cells:
        grid[top + row][left + col] = color


def _place_red_components(
    grid: list[list[int]],
    sym_shapes: list[tuple[tuple[int, int], ...]],
    asym_shapes: list[tuple[tuple[int, int], ...]],
    rng,
) -> None:
    anchors = _quadrant_anchors(len(grid), len(grid[0]), rng)
    if len(sym_shapes) == 2 and len(asym_shapes) == 2:
        # Each class spans top/bottom and left/right, so no half-grid position
        # rule can reproduce the component labels in an ordinary draw.
        if rng.randrange(2):
            sym_anchor_indices = (0, 3)
            asym_anchor_indices = (1, 2)
        else:
            sym_anchor_indices = (1, 2)
            asym_anchor_indices = (0, 3)
        for shape, anchor_index in zip(sym_shapes, sym_anchor_indices):
            _paint_shape(grid, anchors[anchor_index], shape, 2)
        for shape, anchor_index in zip(asym_shapes, asym_anchor_indices):
            _paint_shape(grid, anchors[anchor_index], shape, 2)
        return

    placements = [("sym", shape) for shape in sym_shapes] + [
        ("asym", shape) for shape in asym_shapes
    ]
    rng.shuffle(placements)
    rng.shuffle(anchors)
    for (_role, shape), anchor in zip(placements, anchors):
        _paint_shape(grid, anchor, shape, 2)


def _place_gray_cells(grid: list[list[int]], count: int, rng) -> None:
    height, width = len(grid), len(grid[0])
    border = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in {0, height - 1} or col in {0, width - 1}
    ]
    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(border)
    rng.shuffle(interior)
    candidates = border + interior
    chosen: list[tuple[int, int]] = []
    for row, col in candidates:
        if grid[row][col] != 0:
            continue
        if any(abs(row - rr) + abs(col - cc) <= 1 for rr, cc in chosen):
            continue
        chosen.append((row, col))
        if len(chosen) == count:
            break
    if len(chosen) != count:
        raise ValueError("could not place requested gray distractors")
    for row, col in chosen:
        grid[row][col] = 5


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["empty or malformed grid"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    height = len(grid)
    if not (9 <= height <= 24 and 10 <= width <= 24):
        errors.append(f"grid dimensions {height}x{width} outside 9..24 by 10..24")
    if any(type(value) is not int for row in grid for value in row):
        errors.append("grid values must be integers")
        return {"errors": errors}
    palette = {value for row in grid for value in row}
    unexpected = palette - {0, 2, 5}
    if unexpected:
        errors.append(f"unexpected colors in input: {sorted(unexpected)}")

    components = _components(grid, 2)
    symmetric: list[list[tuple[int, int]]] = []
    asymmetric: list[list[tuple[int, int]]] = []
    for component in components:
        if not 3 <= len(component) <= 9:
            errors.append(f"red component size {len(component)} outside 3..9")
        (symmetric if _left_right_symmetric(component) else asymmetric).append(component)

    if not 1 <= len(symmetric) <= 2:
        errors.append(f"expected 1..2 left-right-symmetric red components, found {len(symmetric)}")
    if not 1 <= len(asymmetric) <= 2:
        errors.append(f"expected 1..2 asymmetric red components, found {len(asymmetric)}")

    symmetric_sizes = {len(component) for component in symmetric}
    asymmetric_sizes = {len(component) for component in asymmetric}
    shared_sizes = sorted(symmetric_sizes & asymmetric_sizes)

    gray_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not 1 <= len(gray_cells) <= 4:
        errors.append(f"expected 1..4 gray distractor cells, found {len(gray_cells)}")

    return {
        "errors": sorted(set(errors)),
        "grid_h": height,
        "grid_w": width,
        "palette": sorted(palette),
        "components": components,
        "symmetric": symmetric,
        "asymmetric": asymmetric,
        "n_sym": len(symmetric),
        "n_asym": len(asymmetric),
        "n_gray": len(gray_cells),
        "gray_cells": gray_cells,
        "shared_sizes": shared_sizes,
        "lr_only_symmetric": sum(
            not _top_bottom_symmetric(component) for component in symmetric
        ),
        "tb_only_asymmetric": sum(
            _top_bottom_symmetric(component) for component in asymmetric
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, shortcut-prone, or non-canonical teaching scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_sym": analysis["n_sym"],
        "n_asym": analysis["n_asym"],
        "n_gray": analysis["n_gray"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; the Racket rule remains authoritative."""
    output = [row[:] for row in grid]
    for component in _components(grid, 2):
        if _left_right_symmetric(component):
            for row, col in component:
                output[row][col] = 3
    return output


def strict_canonical_like(grid) -> list[str]:
    """[] exactly for task-valid canonical-like teaching inputs."""
    return list(_analyze(grid)["errors"])


def _lawful_analysis(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _witness(grid, predicate) -> bool:
    analysis = _lawful_analysis(grid)
    return False if analysis is None else bool(predicate(analysis))


SEMANTIC_WITNESSES = {
    "symmetric_recolor_branch": lambda grid: _witness(grid, lambda a: a["n_sym"] >= 1),
    "asymmetric_unchanged_branch": lambda grid: _witness(grid, lambda a: a["n_asym"] >= 1),
    "gray_unchanged_distractor": lambda grid: _witness(grid, lambda a: a["n_gray"] >= 1),
    "same_size_role_contrast": lambda grid: _witness(grid, lambda a: bool(a["shared_sizes"])),
    "left_right_not_top_bottom": lambda grid: _witness(
        grid, lambda a: a["lr_only_symmetric"] >= 1
    ),
    "top_bottom_not_left_right": lambda grid: _witness(
        grid, lambda a: a["tb_only_asymmetric"] >= 1
    ),
}


def _paint_selected(grid: list[list[int]], selected) -> list[list[int]]:
    output = [row[:] for row in grid]
    for component in _components(grid, 2):
        if selected(component):
            for row, col in component:
                output[row][col] = 3
    return output


def _competitor_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]] | None:
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    height, width = analysis["grid_h"], analysis["grid_w"]

    def centre(component):
        rows = [row for row, _col in component]
        cols = [col for _row, col in component]
        return ((min(rows) + max(rows)) / 2.0, (min(cols) + max(cols)) / 2.0)

    return {
        "recolor_all_red": _paint_selected(grid, lambda _component: True),
        "recolor_no_red": _paint_selected(grid, lambda _component: False),
        "top_bottom_symmetry": _paint_selected(grid, _top_bottom_symmetric),
        "even_cell_count": _paint_selected(grid, lambda component: len(component) % 2 == 0),
        "left_half_position": _paint_selected(grid, lambda component: centre(component)[1] < width / 2),
        "top_half_position": _paint_selected(grid, lambda component: centre(component)[0] < height / 2),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut fits all demos but changes the query."""
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_competitors = _competitor_outputs(query_input)
    if query_competitors is None:
        return ["query input is not a lawful scene for this task"]
    query_truth = rule_mirror(query_input)

    prepared = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is malformed")
            continue
        competitors = _competitor_outputs(demo["input"])
        if competitors is None:
            reasons.append(f"demo {index} input is not a lawful scene for this task")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the rule mirror")
            continue
        prepared.append((demo["output"], competitors))
    if reasons:
        return sorted(set(reasons))

    for name in sorted(query_competitors):
        survives = all(competitors[name] == output for output, competitors in prepared)
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo yet answers the query differently"
            )
    return sorted(set(reasons))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, structurally informative input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, symmetric_count, asymmetric_count, gray_count = _default_axes(
        ctx, difficulty, sample_index
    )
    shape_rng = ctx.draw_rng("shape_family")
    layout_rng = ctx.draw_rng("layout")
    gray_rng = ctx.draw_rng("gray_layout")
    sym_shapes, asym_shapes = _shape_pairs(shape_rng, symmetric_count, asymmetric_count)

    grid = full_grid(height, width, 0)
    _place_red_components(grid, sym_shapes, asym_shapes, layout_rng)
    _place_gray_cells(grid, gray_count, gray_rng)
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if not analysis["shared_sizes"]:
        errors.append("missing same-size symmetric/asymmetric contrast pair")
    if analysis["lr_only_symmetric"] < 1:
        errors.append("missing left-right-only symmetric component")
    if analysis["tb_only_asymmetric"] < 1:
        errors.append("missing top-bottom-only asymmetric component")
    if errors:
        raise ValueError("constructed invalid scene: " + "; ".join(sorted(set(errors))))
    return grid
