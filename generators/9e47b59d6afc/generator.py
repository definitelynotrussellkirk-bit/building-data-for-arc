"""Constructive input sampler for normalized two-shape overlap task 9e47b59d6afc.

The unchanged Racket authority independently normalizes the color-2 and color-3
objects to their own bounding-box origins.  It overlays the normalized cell
sets, painting shared cells 8, red-only cells 2, and green-only cells 3.

Ordinary draws use a finite schedule of canonical-sized and broader canvases,
keyed draws over 144 deterministically vetted ordered shape pairs, and all four opposite-corner placements.  The
sampler is constructive: it has no capped placement loop and never returns a
partial fallback grid.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9e47b59d6afc"
TASK_ID = GENERATOR_ID
RULE_HASH = "cc8053a66713"
VERSION = "3.3.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 0-background grid contains exactly one connected red(2) shape and one "
    "connected green(3) shape in opposite regions. Normalize each shape to its "
    "own bounding-box origin, then overlay the normalized cell sets: shared "
    "cells become cyan(8), red-only cells stay 2, and green-only cells stay 3. "
    "Generated pairs always have a nonempty overlap and at least one exclusive "
    "cell on each side, so all three output colors are required."
)

INVARIANTS = [
    "only colors 0, 2, and 3 occur in the input",
    "exactly one 4-connected color-2 object and one 4-connected color-3 object",
    "the two input objects are spatially separated and occupy opposite regions",
    "their independently normalized cell sets overlap in at least one cell",
    "each normalized shape has an exclusive cell, so output colors 2, 3, and 8 all appear",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "eight-sample size schedule with canonical anchors",
        "valid": "9..13",
        "doc": "Input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "eight-sample size schedule with canonical anchors",
        "valid": "11..15",
        "doc": "Input-grid width.",
    },
    "placement": {
        "type": "str",
        "default": "four-profile opposite-corner schedule",
        "valid": "red_nw|red_ne|red_sw|red_se",
        "doc": "Corner occupied by red; green is placed in the opposite corner.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Cell = tuple[int, int]
Shape = frozenset[Cell]
Grid = list[list[int]]
OutputSignature = tuple[tuple[int, ...], ...]


def _shape_hw(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _normalize(cells: set[Cell] | frozenset[Cell]) -> Shape:
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _is_connected(shape: Shape) -> bool:
    remaining = set(shape)
    if not remaining:
        return False
    start = remaining.pop()
    stack = [start]
    while stack:
        r, c = stack.pop()
        for point in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if point in remaining:
                remaining.remove(point)
                stack.append(point)
    return not remaining


def _overlay_signature(red: Shape, green: Shape) -> OutputSignature:
    union = red | green
    height = max(r for r, _ in union) + 1
    width = max(c for _, c in union) + 1
    return tuple(
        tuple(
            8
            if (r, c) in red and (r, c) in green
            else 2
            if (r, c) in red
            else 3
            if (r, c) in green
            else 0
            for c in range(width)
        )
        for r in range(height)
    )


def _filled_bbox_signature(red: Shape, green: Shape) -> OutputSignature:
    red_h, red_w = _shape_hw(red)
    green_h, green_w = _shape_hw(green)
    red_rect = frozenset((r, c) for r in range(red_h) for c in range(red_w))
    green_rect = frozenset(
        (r, c) for r in range(green_h) for c in range(green_w)
    )
    return _overlay_signature(red_rect, green_rect)


def _connected_shapes_3x3() -> tuple[Shape, ...]:
    """Enumerate normalized 4-connected shapes in a 3x3 box deterministically."""
    shapes: set[Shape] = set()
    for mask in range(1, 1 << 9):
        cells = frozenset(
            (index // 3, index % 3)
            for index in range(9)
            if mask & (1 << index)
        )
        if _is_connected(cells):
            shapes.add(_normalize(cells))
    return tuple(
        sorted(
            shapes,
            key=lambda shape: (
                len(shape),
                _shape_hw(shape),
                tuple(sorted(shape)),
            ),
        )
    )


def _build_shape_pairs(limit: int = 144) -> tuple[tuple[Shape, Shape], ...]:
    """Select distinct, strong normalized-overlap lessons from a finite space.

    Each retained pair is connected on both sides, has shared and exclusive
    cells, and differs from the tempting filled-bounding-box shortcut.  The
    first pair for each distinct authoritative output is retained, giving an
    auditable finite profile bank without a rejection sampler at generation
    time.
    """
    pairs: list[tuple[Shape, Shape]] = []
    seen_outputs: set[OutputSignature] = set()
    shapes = _connected_shapes_3x3()
    for red in shapes:
        for green in shapes:
            if not (red & green) or not (red - green) or not (green - red):
                continue
            signature = _overlay_signature(red, green)
            if signature == _filled_bbox_signature(red, green):
                continue
            if signature in seen_outputs:
                continue
            seen_outputs.add(signature)
            pairs.append((red, green))
            if len(pairs) == limit:
                return tuple(pairs)
    raise RuntimeError(
        f"only constructed {len(pairs)} distinct strong shape pairs; need {limit}"
    )


_SHAPE_PAIRS = _build_shape_pairs()
_PAIR_INDEX = {pair: index for index, pair in enumerate(_SHAPE_PAIRS)}
_PLACEMENTS = ("red_nw", "red_ne", "red_sw", "red_se")
_OPPOSITE = {"nw": "se", "ne": "sw", "sw": "ne", "se": "nw"}
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 3, "hard": 5}

# The first three profiles exactly match canonical input dimensions.  Repeating
# this finite schedule guarantees canonical-size support in every difficulty
# band while the remaining profiles broaden the canvas distribution.
_DIMENSION_PROFILES = (
    (10, 12),
    (11, 13),
    (9, 11),
    (12, 14),
    (13, 15),
    (10, 14),
    (9, 13),
    (11, 15),
)


def _bbox(cells: set[Cell] | frozenset[Cell]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        max(r for r, _ in cells),
        min(c for _, c in cells),
        max(c for _, c in cells),
    )


def _cells(grid: Grid, color: int) -> set[Cell]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def _components(cells: set[Cell]) -> list[set[Cell]]:
    remaining = set(cells)
    result: list[set[Cell]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def _paint(grid: Grid, top: int, left: int, shape: Shape, color: int) -> None:
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Record a scheduled default while keeping the complete override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _scheduled_choice(
    ctx,
    name: str,
    options: tuple[str, ...],
    default: str,
) -> str:
    available = options if name in ctx.overrides and ctx.overrides[name] is not None else (default,)
    return str(ctx.draw_choice(name, available))


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    placement = overrides.get("placement")
    if placement is not None and type(placement) is not str:
        raise TypeError("placement must be a string")


def _corner_position(
    h: int,
    w: int,
    shape: Shape,
    corner: str,
    rng,
) -> tuple[int, int]:
    """Place a small shape near one corner with one-cell keyed jitter."""
    sh, sw = _shape_hw(shape)
    north = corner[0] == "n"
    west = corner[1] == "w"

    max_row_jitter = max(0, min(1, h // 2 - sh - 1))
    max_col_jitter = max(0, min(1, w // 2 - sw - 1))
    row_jitter = rng.randint(0, max_row_jitter)
    col_jitter = rng.randint(0, max_col_jitter)

    top = 1 + row_jitter if north else h - sh - 1 - row_jitter
    left = 1 + col_jitter if west else w - sw - 1 - col_jitter
    if not (0 <= top <= h - sh and 0 <= left <= w - sw):
        raise ValueError("grid is too small for the requested corner placement")
    return top, left


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, structurally checked teaching input."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _DIMENSION_PROFILES[sample_index % len(_DIMENSION_PROFILES)]
    h = _scheduled_int(ctx, "grid_h", 9, 13, default_h)
    w = _scheduled_int(ctx, "grid_w", 11, 15, default_w)
    pair_index = ctx.draw_rng("shape_profile").randrange(len(_SHAPE_PAIRS))
    placement_default = _PLACEMENTS[(sample_index + _BAND_OFFSETS[difficulty]) % len(_PLACEMENTS)]
    placement = _scheduled_choice(ctx, "placement", _PLACEMENTS, placement_default)

    red_shape, green_shape = _SHAPE_PAIRS[pair_index]
    red_corner = placement.removeprefix("red_")
    green_corner = _OPPOSITE[red_corner]
    red_top, red_left = _corner_position(
        h, w, red_shape, red_corner, ctx.draw_rng("red_position")
    )
    green_top, green_left = _corner_position(
        h, w, green_shape, green_corner, ctx.draw_rng("green_position")
    )

    grid = full_grid(h, w, 0)
    _paint(grid, red_top, red_left, red_shape, 2)
    _paint(grid, green_top, green_left, green_shape, 3)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    requested = {
        "grid_h": h,
        "grid_w": w,
        "placement": placement,
    }
    if observed != requested:
        raise RuntimeError(f"generated override observability mismatch: {observed} != {requested}")
    if observe_profile(grid) != pair_index:
        raise RuntimeError("generated shape profile is not recoverable from pixels")
    return grid


def _valid_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {len(grid)}x{width}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
            elif value not in (0, 2, 3):
                errors.append(f"cell ({r},{c}) uses unexpected input color {value}")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, disconnected, ambiguous, or weak overlap scenes."""
    del difficulty, meta
    errors = _valid_grid_errors(grid)
    if errors:
        return errors

    red = _cells(grid, 2)
    green = _cells(grid, 3)
    if not red:
        errors.append("no color-2 object")
    if not green:
        errors.append("no color-3 object")
    if errors:
        return errors

    red_components = _components(red)
    green_components = _components(green)
    if len(red_components) != 1:
        errors.append(f"expected one color-2 component, found {len(red_components)}")
    if len(green_components) != 1:
        errors.append(f"expected one color-3 component, found {len(green_components)}")

    if any(
        (r + dr, c + dc) in green
        for r, c in red
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    ):
        errors.append("color-2 and color-3 objects must be spatially separated")
    if errors:
        return errors

    red_norm = _normalize(red)
    green_norm = _normalize(green)
    if not (red_norm & green_norm):
        errors.append("normalized shapes must overlap")
    if not (red_norm - green_norm):
        errors.append("color-2 shape needs an exclusive normalized cell")
    if not (green_norm - red_norm):
        errors.append("color-3 shape needs an exclusive normalized cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict task grammar includes all canonical inputs and generated draws."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def expected_output(grid: Grid) -> Grid:
    """Independent Python mirror for tests and rivals; Racket remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("input is outside the task grammar: " + "; ".join(errors))
    red = _normalize(_cells(grid, 2))
    green = _normalize(_cells(grid, 3))
    union = red | green
    height = max(r for r, _ in union) + 1
    width = max(c for _, c in union) + 1
    out = full_grid(height, width, 0)
    for r, c in union:
        if (r, c) in red and (r, c) in green:
            out[r][c] = 8
        elif (r, c) in red:
            out[r][c] = 2
        else:
            out[r][c] = 3
    return out


def observe_profile(grid: Grid) -> int:
    """Recover the internal teaching profile from generated pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    pair = (_normalize(_cells(grid, 2)), _normalize(_cells(grid, 3)))
    if pair not in _PAIR_INDEX:
        raise ValueError("normalized shapes do not match a generated profile")
    return _PAIR_INDEX[pair]


def observe_overrides(grid: Grid) -> dict[str, int | str]:
    """Recover every advertised exact axis from returned pixels."""
    observe_profile(grid)
    red = _cells(grid, 2)
    green = _cells(grid, 3)

    red_top, _, red_left, _ = _bbox(red)
    green_top, _, green_left, _ = _bbox(green)
    vertical = "n" if red_top < green_top else "s"
    horizontal = "w" if red_left < green_left else "e"
    if red_top == green_top or red_left == green_left:
        raise ValueError("placement is not observable from object bounding boxes")
    placement = f"red_{vertical}{horizontal}"
    if placement not in _PLACEMENTS:
        raise ValueError(f"unrecognized placement {placement}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "placement": placement,
    }


def _joint_bbox_without_independent_normalization(grid: Grid) -> Grid:
    """Plausible rival: crop both objects together, preserving input spacing."""
    red = _cells(grid, 2)
    green = _cells(grid, 3)
    all_cells = red | green
    top, bottom, left, right = _bbox(all_cells)
    out = full_grid(bottom - top + 1, right - left + 1, 0)
    for r, c in red:
        out[r - top][c - left] = 2
    for r, c in green:
        out[r - top][c - left] = 3
    return out


def _priority_overlay(grid: Grid, overlap_color: int) -> Grid:
    red = _normalize(_cells(grid, 2))
    green = _normalize(_cells(grid, 3))
    union = red | green
    out = full_grid(
        max(r for r, _ in union) + 1,
        max(c for _, c in union) + 1,
        0,
    )
    for r, c in union:
        if (r, c) in red and (r, c) in green:
            out[r][c] = overlap_color
        elif (r, c) in red:
            out[r][c] = 2
        else:
            out[r][c] = 3
    return out


def _red_wins_overlap(grid: Grid) -> Grid:
    return _priority_overlay(grid, 2)


def _green_wins_overlap(grid: Grid) -> Grid:
    return _priority_overlay(grid, 3)


def _filled_bbox_overlay(grid: Grid) -> Grid:
    """Plausible rival: normalize bounding rectangles instead of shape cells."""
    red = _normalize(_cells(grid, 2))
    green = _normalize(_cells(grid, 3))
    red_h, red_w = _shape_hw(red)
    green_h, green_w = _shape_hw(green)
    red_rect = {(r, c) for r in range(red_h) for c in range(red_w)}
    green_rect = {(r, c) for r in range(green_h) for c in range(green_w)}
    union = red_rect | green_rect
    out = full_grid(
        max(r for r, _ in union) + 1,
        max(c for _, c in union) + 1,
        0,
    )
    for r, c in union:
        if (r, c) in red_rect and (r, c) in green_rect:
            out[r][c] = 8
        elif (r, c) in red_rect:
            out[r][c] = 2
        else:
            out[r][c] = 3
    return out


def _differs(rival: Callable[[Grid], Grid]) -> Callable[[Grid], bool]:
    return lambda grid: rival(grid) != expected_output(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "keep_input_spacing": _joint_bbox_without_independent_normalization,
    "red_wins_overlap": _red_wins_overlap,
    "green_wins_overlap": _green_wins_overlap,
    "overlay_filled_bboxes": _filled_bbox_overlay,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "independent_normalization_decisive": _differs(
        _joint_bbox_without_independent_normalization
    ),
    "cyan_overlap_code_decisive": lambda grid: (
        _red_wins_overlap(grid) != expected_output(grid)
        and _green_wins_overlap(grid) != expected_output(grid)
    ),
    "cell_shape_not_bbox_decisive": _differs(_filled_bbox_overlay),
}

WITNESS_RIVALS = {
    "independent_normalization_decisive": ["keep_input_spacing"],
    "cyan_overlap_code_decisive": ["red_wins_overlap", "green_wins_overlap"],
    "cell_shape_not_bbox_decisive": ["overlay_filled_bboxes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a named rival viable."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            truth = expected_output(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is outside the task grammar: {exc}")
            continue
        if pair["output"] != truth:
            reasons.append(f"pair {index} output disagrees with normalized overlap")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised: {exc}")
            continue
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not refute competitor: {name}")
    return reasons
