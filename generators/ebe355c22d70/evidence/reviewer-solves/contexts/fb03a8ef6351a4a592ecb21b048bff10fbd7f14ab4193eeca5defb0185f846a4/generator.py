"""Input sampler for ``ebe355c22d70`` — opposite corners to a cropped fill.

Exactly two blue cells mark diagonally opposite corners of a nondegenerate
axis-aligned rectangle.  The unchanged Racket authority returns a *cropped*
solid color-8 grid whose dimensions equal that inclusive bounding box.

The sixteen-slot teaching schedule exhausts the lawful 3..6 by 3..6 output
alphabet while preserving every canonical linked profile.  Its four-phase
orientation pattern and rectangular odd slots mean that any three
demonstrations left after rotating one query contain both diagonal
orientations and a non-square output, refuting orientation-only and
square-only shortcuts without changing the authoritative rule.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ebe355c22d70"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "cd9402783d01"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15
EXPECTED_OUTPUT_CODOMAIN = 16  # all solid-8 rectangles with h,w independently 3..6

SUMMARY = (
    "A 6..14 by 6..14 zero-background grid contains exactly two blue (1) "
    "cells at different rows and columns.  They are opposite corners of an "
    "inclusive 3..6 by 3..6 rectangle, in either diagonal orientation.  The "
    "answer is not placed back into the input canvas: return a freshly cropped "
    "rectangle of exactly that height and width, with every cell color 8."
)
INVARIANTS = [
    "background is 0 and exactly two cells are blue (1)",
    "the two blue cells differ in row and column and span a 3..6 by 3..6 bbox",
    "both positive- and negative-slant opposite-corner pairs are ordinary",
    "output is a cropped solid-8 grid with the inclusive bbox dimensions",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sixteen-slot schedule with canonical anchors; 6..14",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "sixteen-slot schedule with canonical anchors; 6..14",
        "valid": "6..14",
    },
    "bbox_h": {
        "type": "int",
        "default": "sixteen-slot exhaustive schedule",
        "valid": "3..6",
    },
    "bbox_w": {
        "type": "int",
        "default": "sixteen-slot exhaustive schedule",
        "valid": "3..6",
    },
    "slant": {
        "type": "str",
        "default": "scheduled positive/negative",
        "valid": "positive|negative",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# (input height, input width, bbox height, bbox width, slant)
_CANONICAL_PROFILES = (
    (8, 9, 5, 5, "positive"),
    (10, 10, 6, 5, "negative"),
    (9, 12, 6, 6, "negative"),
)
_CANONICAL_SIGNATURES = set(_CANONICAL_PROFILES)
_BBOX_SCHEDULE = (
    (5, 5),  # canonical positive
    (6, 5),  # canonical negative
    (6, 6),  # canonical negative
    (3, 6),
    (3, 3),
    (3, 4),
    (4, 4),
    (4, 3),
    (3, 5),
    (4, 5),
    (5, 3),
    (5, 4),
    (4, 6),
    (5, 6),
    (6, 3),
    (6, 4),
)
_SLANT_PHASE = ("positive", "negative", "negative", "positive")
SCHEDULE_PROFILES = tuple(
    (
        "canonical-" if slot < 3 else "broad-"
    )
    + _SLANT_PHASE[slot % 4]
    + f"-{bbox_h}x{bbox_w}"
    for slot, (bbox_h, bbox_w) in enumerate(_BBOX_SCHEDULE)
)


def _band(difficulty: Any) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return "medium" if difficulty is None else str(difficulty)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic exhaustive teaching schedule."""
    del difficulty
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _scheduled_profile(seed: int, sample_index: int, band: str):
    slot = (int(seed) + int(sample_index)) % len(_BBOX_SCHEDULE)
    if slot < 3:
        return _CANONICAL_PROFILES[slot]
    bbox_h, bbox_w = _BBOX_SCHEDULE[slot]
    grid_h, grid_w = {
        "easy": (6, 7),
        "medium": (8, 11),
        "hard": (14, 14),
    }[band]
    return grid_h, grid_w, bbox_h, bbox_w, _SLANT_PHASE[slot % 4]


def _has_override(overrides: dict[str, Any], name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _draw_scheduled_int(
    ctx,
    overrides,
    name: str,
    scheduled: int,
    low: int,
    high: int,
) -> int:
    if _has_override(overrides, name):
        return ctx.draw_int_strict(name, low, high)
    return int(ctx.draw_choice(name, (scheduled,)))


def _draw_scheduled_slant(ctx, overrides, scheduled: str) -> str:
    options = ("positive", "negative")
    if _has_override(overrides, "slant"):
        value = overrides["slant"]
        if type(value) is not str:
            raise TypeError("slant override must be a string")
        return str(ctx.draw_choice("slant", options))
    return str(ctx.draw_choice("slant", (scheduled,)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket remains label authority."""
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    scheduled_h, scheduled_w, scheduled_bbox_h, scheduled_bbox_w, scheduled_slant = (
        _scheduled_profile(int(seed), int(sample_index), band)
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_h = _draw_scheduled_int(ctx, overrides, "grid_h", scheduled_h, 6, 14)
    grid_w = _draw_scheduled_int(ctx, overrides, "grid_w", scheduled_w, 6, 14)
    bbox_h = _draw_scheduled_int(
        ctx, overrides, "bbox_h", scheduled_bbox_h, 3, 6
    )
    bbox_w = _draw_scheduled_int(
        ctx, overrides, "bbox_w", scheduled_bbox_w, 3, 6
    )
    slant = _draw_scheduled_slant(ctx, overrides, scheduled_slant)

    if bbox_h > grid_h or bbox_w > grid_w:
        raise ValueError(
            f"scheduled {bbox_h}x{bbox_w} bbox does not fit {grid_h}x{grid_w} grid"
        )
    rng = ctx.draw_rng("layout")
    r0 = rng.randint(0, grid_h - bbox_h)
    c0 = rng.randint(0, grid_w - bbox_w)
    r1 = r0 + bbox_h - 1
    c1 = c0 + bbox_w - 1

    grid = full_grid(grid_h, grid_w, 0)
    if slant == "positive":
        points = ((r0, c0), (r1, c1))
    else:
        points = ((r0, c1), (r1, c0))
    for r, c in points:
        grid[r][c] = 1
    return grid


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    grid_h = len(grid)
    grid_w = len(grid[0])
    if grid_w == 0 or any(not isinstance(row, list) or len(row) != grid_w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 6 <= grid_h <= 14:
        errors.append(f"grid height {grid_h} outside 6..14")
    if not 6 <= grid_w <= 14:
        errors.append(f"grid width {grid_w} outside 6..14")

    points: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or value not in (0, 1):
                errors.append(f"cell ({r},{c}) must be integer color 0 or 1, got {value!r}")
            elif value == 1:
                points.append((r, c))
    if any("must be integer color" in error for error in errors):
        return {"errors": errors}
    if len(points) != 2:
        errors.append(f"expected exactly two color-1 cells, got {len(points)}")
        return {"errors": errors, "grid_h": grid_h, "grid_w": grid_w, "points": points}

    points = sorted(points)
    (r0, first_c), (r1, second_c) = points
    if r0 == r1 or first_c == second_c:
        errors.append("the two color-1 cells must differ in both row and column")
        return {"errors": errors, "grid_h": grid_h, "grid_w": grid_w, "points": points}
    bbox_h = r1 - r0 + 1
    bbox_w = abs(second_c - first_c) + 1
    if not 3 <= bbox_h <= 6 or not 3 <= bbox_w <= 6:
        errors.append(f"bbox {bbox_h}x{bbox_w} must be within 3..6 on both axes")
    slant = "positive" if second_c > first_c else "negative"
    signature = (grid_h, grid_w, bbox_h, bbox_w, slant)
    return {
        "errors": errors,
        "grid_h": grid_h,
        "grid_w": grid_w,
        "points": points,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "slant": slant,
        "signature": signature,
        "row_min": r0,
        "row_max": r1,
        "col_min": min(first_c, second_c),
        "col_max": max(first_c, second_c),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "bbox_h": analysis["bbox_h"],
        "bbox_w": analysis["bbox_w"],
        "slant": analysis["slant"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    if analysis["signature"] not in _CANONICAL_SIGNATURES:
        return [f"linked profile {analysis['signature']!r} is not canonical"]
    return []


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "bbox_h": analysis["bbox_h"],
        "bbox_w": analysis["bbox_w"],
        "strict_canonical": analysis["signature"] in _CANONICAL_SIGNATURES,
        "rectangular_bbox": analysis["bbox_h"] != analysis["bbox_w"],
        "crop_changes_shape": (
            analysis["bbox_h"], analysis["bbox_w"]
        ) != (analysis["grid_h"], analysis["grid_w"]),
        "touches_border": (
            analysis["row_min"] == 0
            or analysis["col_min"] == 0
            or analysis["row_max"] == analysis["grid_h"] - 1
            or analysis["col_max"] == analysis["grid_w"] - 1
        ),
    }


def rule_mirror(grid):
    """Independent Python mirror used only for checks and executable rivals."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return full_grid(analysis["bbox_h"], analysis["bbox_w"], 8)


def _positive_slant_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return (
        rule_mirror(grid)
        if analysis["slant"] == "positive"
        else full_grid(1, 1, 8)
    )


def _negative_slant_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return (
        rule_mirror(grid)
        if analysis["slant"] == "negative"
        else full_grid(1, 1, 8)
    )


def _same_size_fill(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for r in range(analysis["row_min"], analysis["row_max"] + 1):
        for c in range(analysis["col_min"], analysis["col_max"] + 1):
            out[r][c] = 8
    return out


def _border_only_crop(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    h, w = analysis["bbox_h"], analysis["bbox_w"]
    out = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if r in (0, h - 1) or c in (0, w - 1):
                out[r][c] = 8
    return out


def _row_span_square(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return full_grid(analysis["bbox_h"], analysis["bbox_h"], 8)


def _column_span_square(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return full_grid(analysis["bbox_w"], analysis["bbox_w"], 8)


def _fixed_five_square(grid):
    return None if _analyze(grid)["errors"] else full_grid(5, 5, 8)


def _identity(grid):
    return [row[:] for row in grid]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "positive_slant_only": _positive_slant_only,
    "negative_slant_only": _negative_slant_only,
    "same_size_fill": _same_size_fill,
    "border_only_crop": _border_only_crop,
    "row_span_square": _row_span_square,
    "column_span_square": _column_span_square,
    "fixed_5x5_output": _fixed_five_square,
    "identity": _identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# The three canonical pairs already cover both orientations and three output
# sizes; none of the declared simple competitors fits all canonical labels.
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def _witness(grid, key: str) -> bool:
    observed = semantic_observables(grid)
    return not observed.get("errors") and bool(observed.get(key))


SEMANTIC_WITNESSES = {
    "strict_canonical_profile": lambda grid: _witness(grid, "strict_canonical"),
    "positive_slant": lambda grid: observe_overrides(grid).get("slant") == "positive",
    "negative_slant": lambda grid: observe_overrides(grid).get("slant") == "negative",
    "rectangular_bbox": lambda grid: _witness(grid, "rectangular_bbox"),
    "cropped_output": lambda grid: _witness(grid, "crop_changes_shape"),
}
WITNESS_RIVALS = {
    "positive_slant": ["negative_slant_only"],
    "negative_slant": ["positive_slant_only"],
    "rectangular_bbox": ["row_span_square", "column_span_square", "fixed_5x5_output"],
    "cropped_output": ["same_size_fill", "identity"],
    "strict_canonical_profile": ["border_only_crop"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demos leave a declared query-changing rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is outside the opposite-corner teaching grammar"]
    truth = rule_mirror(query_input)

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the cropped-fill rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != truth:
                reasons.append(
                    f"demos still fit competitor {name!r}, which changes the query answer"
                )
    return reasons
