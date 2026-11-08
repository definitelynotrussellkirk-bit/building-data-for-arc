"""Generator for v1_e_m_h_keys:H4 (mirror inside a local frame).

The input contains one cyan (8) rectangular frame on a black background.  A
non-empty colored pattern is placed in the left half of the frame interior;
odd-width frames may also contain cells on the vertical centerline.  The
Racket oracle copies every colored interior cell to its horizontal mirror
inside the frame.

The teaching distribution guarantees at least one off-center source cell and
an empty mirror target, so the transformation always changes the grid.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "528bbb532b67"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1684ca9647a8"

SUMMARY = (
    "One cyan (8) rectangular frame contains a colored pattern only on the "
    "left half (and optionally the centerline) of its interior. Mirror every "
    "nonzero non-8 interior cell across the frame's vertical centerline, "
    "preserving the source cells and frame."
)

INVARIANTS = [
    "exactly one complete cyan rectangular frame is present",
    "all other nonzero cells lie strictly inside that frame",
    "source cells lie left of or on the frame centerline",
    "at least one off-center source has an empty in-frame mirror target",
    "the outer canvas remains black and the frame has a one-cell margin",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware with a 25% canonical-size prior",
        "valid": "7..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware with a 25% canonical-size prior",
        "valid": "9..24",
    },
    "box_h": {
        "type": "int",
        "default": "difficulty-aware; always leaves a one-cell margin",
        "valid": "5..12",
    },
    "box_w": {
        "type": "int",
        "default": "difficulty-aware; odd and even widths both occur",
        "valid": "7..14",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "difficulty-aware, 1..5",
        "valid": "1..5",
    },
}

_ALLOWED_PATTERN_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIFFICULTY_RANGES = {
    "easy": {
        "grid_h": (7, 12),
        "grid_w": (9, 14),
        "box_h": (5, 7),
        "box_w": (7, 9),
        "n_distinct_colors": (1, 3),
        "fill": (0.25, 0.48),
    },
    "medium": {
        "grid_h": (10, 17),
        "grid_w": (11, 19),
        "box_h": (5, 10),
        "box_w": (7, 12),
        "n_distinct_colors": (1, 4),
        "fill": (0.32, 0.62),
    },
    "hard": {
        "grid_h": (14, 22),
        "grid_w": (15, 24),
        "box_h": (7, 12),
        "box_w": (9, 14),
        "n_distinct_colors": (2, 5),
        "fill": (0.42, 0.75),
    },
}
_CANONICAL_PRIOR = {
    "grid_h": (7, 10),
    "grid_w": (9, 13),
    "box_h": (5, 6),
    "box_w": (7, 9),
    "n_distinct_colors": (1, 2),
    "fill": (0.20, 0.42),
}


def _frame(grid: list[list[int]], r0: int, c0: int, r1: int, c1: int) -> None:
    for row in range(r0, r1 + 1):
        grid[row][c0] = 8
        grid[row][c1] = 8
    for col in range(c0, c1 + 1):
        grid[r0][col] = 8
        grid[r1][col] = 8


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid is empty or not a row sequence")
    if not all(isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("grid contains a non-row value")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid is empty or ragged")
    out = [list(row) for row in grid]
    if any(type(value) is not int or not 0 <= value <= 9 for row in out for value in row):
        raise ValueError("grid values must be integer ARC colors 0..9")
    return out


def _analyze(grid: Any) -> dict[str, Any]:
    """Recover the exact semantic axes and structural validity from a grid."""
    try:
        g = _coerce_grid(grid)
    except ValueError as exc:
        return {"errors": [str(exc)], "facts": {}}

    height, width = len(g), len(g[0])
    eights = [(r, c) for r in range(height) for c in range(width) if g[r][c] == 8]
    errors: list[str] = []
    if not eights:
        return {"errors": ["missing cyan frame"], "facts": {}}

    r0 = min(r for r, _ in eights)
    r1 = max(r for r, _ in eights)
    c0 = min(c for _, c in eights)
    c1 = max(c for _, c in eights)
    box_h = r1 - r0 + 1
    box_w = c1 - c0 + 1

    if box_h < 5 or box_w < 7:
        errors.append("cyan frame is smaller than the lawful minimum")
    if r0 < 1 or c0 < 1 or r1 >= height - 1 or c1 >= width - 1:
        errors.append("cyan frame must have a one-cell black canvas margin")

    border = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    if set(eights) != border:
        missing = border - set(eights)
        extra = set(eights) - border
        if missing:
            errors.append("cyan bounding box is not a complete rectangular frame")
        if extra:
            errors.append("cyan cells occur away from the frame border")

    pattern = [
        (r, c, g[r][c])
        for r in range(height)
        for c in range(width)
        if g[r][c] not in (0, 8)
    ]
    if not pattern:
        errors.append("interior pattern is empty")

    inside: list[tuple[int, int, int]] = []
    for row, col, color in pattern:
        if not (r0 < row < r1 and c0 < col < c1):
            errors.append("a colored source lies outside the frame interior")
        else:
            inside.append((row, col, color))
        if color not in _ALLOWED_PATTERN_COLORS:
            errors.append("pattern uses a reserved color")

    off_center = 0
    occupied = {(r, c) for r, c, _ in inside}
    for row, col, _ in inside:
        mirror_col = c0 + c1 - col
        if 2 * col > c0 + c1:
            errors.append("a source cell lies on the right half of the frame")
        if mirror_col != col:
            off_center += 1
            if (row, mirror_col) in occupied:
                errors.append("an off-center source has a non-empty mirror target")

    if inside and off_center == 0:
        errors.append("pattern has no off-center source, so the rule would be an identity")

    colors = sorted({color for _, _, color in inside})
    if len(colors) > 5:
        errors.append("pattern uses more than five distinct colors")

    facts = {
        "grid_h": height,
        "grid_w": width,
        "box_h": box_h,
        "box_w": box_w,
        "frame_bbox": [r0, c0, r1, c1],
        "n_distinct_colors": len(colors),
        "pattern_cells": len(inside),
        "off_center_cells": off_center,
        "centerline_cells": sum(2 * c == c0 + c1 for _, c, _ in inside),
        "source_colors": colors,
    }
    return {"errors": list(dict.fromkeys(errors)), "facts": facts}


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    facts = analysis["facts"]
    for axis in AXES:
        if axis in requested and requested[axis] is not None and facts.get(axis) != requested[axis]:
            errors.append(
                f"{axis} requested {requested[axis]!r}, observed {facts.get(axis)!r}"
            )
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "box_h": facts["box_h"],
        "box_w": facts["box_w"],
        "n_distinct_colors": facts["n_distinct_colors"],
    }


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = difficulty or "medium"
    if band not in _DIFFICULTY_RANGES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    bounds = {
        "grid_h": (7, 22),
        "grid_w": (9, 24),
        "box_h": (5, 12),
        "box_w": (7, 14),
        "n_distinct_colors": (1, 5),
    }
    for axis, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{axis} must be an integer")
        lo, hi = bounds[axis]
        if not lo <= value <= hi:
            raise ValueError(f"{axis}={value} outside [{lo}, {hi}]")
    if (
        overrides.get("grid_h") is not None
        and overrides.get("box_h") is not None
        and overrides["box_h"] + 2 > overrides["grid_h"]
    ):
        raise ValueError("box_h requires grid_h >= box_h + 2")
    if (
        overrides.get("grid_w") is not None
        and overrides.get("box_w") is not None
        and overrides["box_w"] + 2 > overrides["grid_w"]
    ):
        raise ValueError("box_w requires grid_w >= box_w + 2")
    return band


def _draw_axis(
    ctx: Any,
    axis: str,
    default_bounds: tuple[int, int],
    valid_bounds: tuple[int, int],
) -> int:
    bounds = valid_bounds if axis in ctx.overrides and ctx.overrides[axis] is not None else default_bounds
    return ctx.draw_int(axis, bounds[0], bounds[1])


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    prior_rng = ctx.draw_rng("canonical_prior")
    use_canonical_prior = prior_rng.random() < 0.25 and not overrides
    profile = _CANONICAL_PRIOR if use_canonical_prior else _DIFFICULTY_RANGES[band]

    requested_box_h = overrides.get("box_h")
    h_default = profile["grid_h"]
    h_lo = max(h_default[0], (requested_box_h + 2) if requested_box_h is not None else h_default[0])
    h_hi = max(h_lo, h_default[1])
    grid_h = _draw_axis(ctx, "grid_h", (h_lo, h_hi), (max(7, (requested_box_h or 5) + 2), 22))

    requested_box_w = overrides.get("box_w")
    w_default = profile["grid_w"]
    w_lo = max(w_default[0], (requested_box_w + 2) if requested_box_w is not None else w_default[0])
    w_hi = max(w_lo, w_default[1])
    grid_w = _draw_axis(ctx, "grid_w", (w_lo, w_hi), (max(9, (requested_box_w or 7) + 2), 24))

    box_h_hi = min(profile["box_h"][1], grid_h - 2)
    box_w_hi = min(profile["box_w"][1], grid_w - 2)
    box_h_default = (min(profile["box_h"][0], box_h_hi), box_h_hi)
    box_w_default = (min(profile["box_w"][0], box_w_hi), box_w_hi)
    box_h = _draw_axis(ctx, "box_h", box_h_default, (5, min(12, grid_h - 2)))
    box_w = _draw_axis(ctx, "box_w", box_w_default, (7, min(14, grid_w - 2)))

    color_default = profile["n_distinct_colors"]
    ncolors = _draw_axis(ctx, "n_distinct_colors", color_default, (1, 5))

    layout_rng = ctx.draw_rng("layout")
    r0 = layout_rng.randint(1, grid_h - box_h - 1)
    c0 = layout_rng.randint(1, grid_w - box_w - 1)
    r1 = r0 + box_h - 1
    c1 = c0 + box_w - 1

    grid = full_grid(grid_h, grid_w, 0)
    _frame(grid, r0, c0, r1, c1)

    left_cells = [
        (row, col)
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
        if 2 * col < c0 + c1
    ]
    if len(left_cells) < ncolors:
        raise ValueError("requested color count does not fit the left-half source area")

    pattern_rng = ctx.draw_rng("pattern")
    fill_lo, fill_hi = profile["fill"]
    fraction = pattern_rng.uniform(fill_lo, fill_hi)
    target_count = max(ncolors, 2, round(len(left_cells) * fraction))
    target_count = min(target_count, len(left_cells))
    chosen = pattern_rng.sample(left_cells, target_count)

    palette = pattern_rng.sample(list(_ALLOWED_PATTERN_COLORS), ncolors)
    pattern_rng.shuffle(chosen)
    for index, (row, col) in enumerate(chosen):
        color = palette[index] if index < ncolors else pattern_rng.choice(palette)
        grid[row][col] = color

    # Odd-width frames sometimes carry centerline evidence, matching the first
    # canonical demonstration.  It never replaces the mandatory off-axis cue.
    if box_w % 2 == 1 and pattern_rng.random() < 0.55:
        center_col = (c0 + c1) // 2
        center_rows = [row for row in range(r0 + 1, r1)]
        for row in pattern_rng.sample(center_rows, pattern_rng.randint(1, min(2, len(center_rows)))):
            grid[row][center_col] = pattern_rng.choice(palette)

    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise AssertionError("constructed invalid mirror lesson: " + "; ".join(errors))
    return grid
