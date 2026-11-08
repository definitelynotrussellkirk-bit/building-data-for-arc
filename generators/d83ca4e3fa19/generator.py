"""Reviewed generator for ARC task d83ca4e3fa19.

Four equal nonzero cells mark the corners of one axis-aligned rectangle on a
zero background.  The canonical Racket rule is the sole output authority: it
replaces the four markers with the complete border of their bounding box while
leaving the interior and the rest of the grid zero.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d83ca4e3fa19"
TASK_ID = "d83ca4e3fa19"
VERSION = "3.0.0"
RULE_HASH = "5e968529140e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Generate exactly four equal nonzero cells at the corners of one "
    "axis-aligned rectangle.  Default draws cycle the five linked canonical "
    "(grid height, grid width, rectangle height, rectangle width) profiles, "
    "while color and placement vary deterministically.  The canonical Racket "
    "rule draws only the complete rectangle border in the marker color."
)

INVARIANTS = [
    "background is color 0 and every cell is an ARC color in 0..9",
    "exactly four nonzero cells are present",
    "all four nonzero cells have one common color",
    "the nonzero cells are exactly the Cartesian product of two rows and two columns",
    "the marked rectangle is at least 3x5 and fits within the grid",
    "ordinary draws use one complete canonical-linked size profile",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "6..9",
    },
    "grid_w": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "8..11",
    },
    "rect_h": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "3..7",
    },
    "rect_w": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "5..9",
    },
    "corner_color": {
        "type": "color",
        "default": "sample-index schedule over 1..9",
        "valid": "1..9",
    },
}

# Exact (grid_h, grid_w, rect_h, rect_w) tuples from the four canonical train
# inputs and the held-out test input.  The default distribution chooses one
# complete tuple before varying only lawful nuisance factors (translation and
# color), preventing independent-marginal recombinations from masquerading as
# canonical support.
_CANONICAL_PROFILES: tuple[tuple[int, int, int, int], ...] = (
    (7, 9, 5, 6),
    (8, 8, 7, 5),
    (6, 10, 3, 7),
    (9, 11, 7, 9),
    (8, 10, 6, 8),
)
_CANONICAL_PROFILE_KEYS = set(_CANONICAL_PROFILES)
_PLACEMENT_MODES = ("top", "bottom", "left", "right", "interior")
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 4}


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{name} must be an integer")


def _draw_exact_or_override(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    """Record every exact axis through GenCtx while honoring its full domain."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _resolve_dimensions(ctx, overrides, profile: tuple[int, int, int, int]):
    profile_h, profile_w, profile_rh, profile_rw = profile

    h_override = overrides.get("grid_h") is not None
    rh_override = overrides.get("rect_h") is not None
    if h_override:
        h_default = profile_h
    elif rh_override:
        h_default = max(profile_h, int(overrides["rect_h"]))
    else:
        h_default = profile_h
    h = _draw_exact_or_override(ctx, overrides, "grid_h", h_default, 6, 9)

    if rh_override:
        rh_default = profile_rh
    elif h_override:
        rh_default = min(profile_rh, h)
    else:
        rh_default = profile_rh
    rh = _draw_exact_or_override(ctx, overrides, "rect_h", rh_default, 3, 7)
    if rh > h:
        raise ValueError(f"rect_h={rh} cannot fit inside grid_h={h}")

    w_override = overrides.get("grid_w") is not None
    rw_override = overrides.get("rect_w") is not None
    if w_override:
        w_default = profile_w
    elif rw_override:
        w_default = max(profile_w, int(overrides["rect_w"]))
    else:
        w_default = profile_w
    w = _draw_exact_or_override(ctx, overrides, "grid_w", w_default, 8, 11)

    if rw_override:
        rw_default = profile_rw
    elif w_override:
        rw_default = min(profile_rw, w)
    else:
        rw_default = profile_rw
    rw = _draw_exact_or_override(ctx, overrides, "rect_w", rw_default, 5, 9)
    if rw > w:
        raise ValueError(f"rect_w={rw} cannot fit inside grid_w={w}")
    return h, w, rh, rw


def _axis_position(mode: str, slack: int, rng) -> int:
    if slack <= 0:
        return 0
    if mode in ("top", "left"):
        return 0
    if mode in ("bottom", "right"):
        return slack
    if slack >= 2:
        return rng.randint(1, slack - 1)
    # A strict interior location does not exist when there is only one spare
    # row/column.  Placement is not a declared override, so choose either edge
    # rather than hiding or clamping an exact user request.
    return rng.randint(0, slack)


def _place_rectangle(mode: str, h: int, w: int, rh: int, rw: int, rng):
    row_slack = h - rh
    col_slack = w - rw
    if mode == "top":
        r0 = 0
        c0 = rng.randint(0, col_slack)
    elif mode == "bottom":
        r0 = row_slack
        c0 = rng.randint(0, col_slack)
    elif mode == "left":
        r0 = rng.randint(0, row_slack)
        c0 = 0
    elif mode == "right":
        r0 = rng.randint(0, row_slack)
        c0 = col_slack
    else:
        r0 = _axis_position("interior", row_slack, rng)
        c0 = _axis_position("interior", col_slack, rng)
    return r0, c0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    offset = _BAND_OFFSETS[difficulty]
    profile_index = (sample_index + offset) % len(_CANONICAL_PROFILES)
    profile = _CANONICAL_PROFILES[profile_index]
    h, w, rh, rw = _resolve_dimensions(ctx, overrides, profile)

    scheduled_color = 1 + ((int(seed) + sample_index + offset) % 9)
    color = _draw_exact_or_override(
        ctx, overrides, "corner_color", scheduled_color, 1, 9
    )
    # Decouple profile and placement schedules so a sequential census traverses
    # every canonical shape in every meaningful edge/interior relation.
    mode_index = ((sample_index // len(_CANONICAL_PROFILES)) + offset) % len(
        _PLACEMENT_MODES
    )
    mode = _PLACEMENT_MODES[mode_index]
    layout_rng = ctx.draw_rng(
        f"layout|profile={profile_index}|mode={mode}|dims={h}x{w}|rect={rh}x{rw}"
    )
    r0, c0 = _place_rectangle(mode, h, w, rh, rw, layout_rng)
    r1 = r0 + rh - 1
    c1 = c0 + rw - 1

    grid = full_grid(h, w, 0)
    for row, col in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
        grid[row][col] = color

    errors = self_check(
        grid,
        meta={
            "grid_h": h,
            "grid_w": w,
            "rect_h": rh,
            "rect_w": rw,
            "corner_color": color,
        },
    )
    if errors:
        raise AssertionError("generated invalid rectangle markers: " + "; ".join(errors))
    return grid


def _coerce_grid(grid) -> list[list[int]]:
    if not isinstance(grid, list):
        raise ValueError("grid must be a list")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be lists, tuples, or digit strings")
    return result


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    if not values or not values[0]:
        return {"errors": ["grid must be non-empty"]}
    width = len(values[0])
    if any(len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}
    height = len(values)
    if not 6 <= height <= 9:
        errors.append("grid height must be in 6..9")
    if not 8 <= width <= 11:
        errors.append("grid width must be in 8..11")
    if any(type(value) is not int or not 0 <= value <= 9 for row in values for value in row):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values, "height": height, "width": width}

    cells = [
        (row, col, value)
        for row, line in enumerate(values)
        for col, value in enumerate(line)
        if value != 0
    ]
    if len(cells) != 4:
        errors.append("expected exactly four nonzero corner cells")
    colors = {value for _, _, value in cells}
    if len(colors) != 1:
        errors.append("all four corner cells must share one nonzero color")

    rows = sorted({row for row, _, _ in cells})
    cols = sorted({col for _, col, _ in cells})
    if len(rows) != 2 or len(cols) != 2:
        errors.append("corner cells must occupy exactly two rows and two columns")
        rect_h = rect_w = 0
        expected: set[tuple[int, int]] = set()
    else:
        rect_h = rows[1] - rows[0] + 1
        rect_w = cols[1] - cols[0] + 1
        expected = {(row, col) for row in rows for col in cols}
        if not 3 <= rect_h <= 7:
            errors.append("rectangle height must be in 3..7")
        if not 5 <= rect_w <= 9:
            errors.append("rectangle width must be in 5..9")
    actual = {(row, col) for row, col, _ in cells}
    if expected and actual != expected:
        errors.append("the four nonzero cells must be exactly the rectangle corners")

    color = next(iter(colors)) if len(colors) == 1 else None
    top = rows[0] if len(rows) == 2 else None
    bottom = rows[1] if len(rows) == 2 else None
    left = cols[0] if len(cols) == 2 else None
    right = cols[1] if len(cols) == 2 else None
    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "rect_h": rect_h,
        "rect_w": rect_w,
        "color": color,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "cells": tuple(cells),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    expected = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rect_h": analysis["rect_h"],
        "rect_w": analysis["rect_w"],
        "corner_color": analysis["color"],
    }
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    for name, actual in expected.items():
        value = requested.get(name)
        if value is not None and value != actual:
            errors.append(f"meta {name} requested {value!r}, observed {actual!r}")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rect_h": analysis["rect_h"],
        "rect_w": analysis["rect_w"],
        "corner_color": analysis["color"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    key = (
        analysis["height"],
        analysis["width"],
        analysis["rect_h"],
        analysis["rect_w"],
    )
    if key not in _CANONICAL_PROFILE_KEYS:
        errors.append(f"size profile {key!r} is not one linked canonical profile")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Test-only Python mirror of the unchanged canonical Racket rule."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid rectangle-marker scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    top, bottom = analysis["top"], analysis["bottom"]
    left, right = analysis["left"], analysis["right"]
    color = analysis["color"]
    for col in range(left, right + 1):
        output[top][col] = color
        output[bottom][col] = color
    for row in range(top, bottom + 1):
        output[row][left] = color
        output[row][right] = color
    return output


def _aspect_tall(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["rect_h"] > analysis["rect_w"]


def _aspect_wide(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["rect_w"] > analysis["rect_h"]


def _touches_top(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["top"] == 0


def _touches_bottom(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["bottom"] == analysis["height"] - 1


def _touches_left(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["left"] == 0


def _touches_right(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["right"] == analysis["width"] - 1


def _strictly_interior(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["top"] > 0
        and analysis["bottom"] < analysis["height"] - 1
        and analysis["left"] > 0
        and analysis["right"] < analysis["width"] - 1
    )


SEMANTIC_WITNESSES = {
    "tall_rectangle": _aspect_tall,
    "wide_rectangle": _aspect_wide,
    "touches_top": _touches_top,
    "touches_bottom": _touches_bottom,
    "touches_left": _touches_left,
    "touches_right": _touches_right,
    "strictly_interior": _strictly_interior,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that permit fixed-size/aspect/identity shortcuts."""
    errors: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        analysis = _analyze(pair["input"])
        if analysis.get("errors"):
            errors.append(f"demo {index} input is malformed")
            continue
        if rule_mirror(pair["input"]) != _coerce_grid(pair["output"]):
            errors.append(f"demo {index} output is not the rectangle border")
            continue
        if pair["input"] == pair["output"]:
            errors.append(f"demo {index} is an identity example")
        analyses.append(analysis)

    if len(analyses) == len(demos):
        sizes = {(item["rect_h"], item["rect_w"]) for item in analyses}
        if len(sizes) < 3:
            errors.append("demonstrations do not vary rectangle size")
        if not any(item["rect_h"] > item["rect_w"] for item in analyses):
            errors.append("demonstrations omit the tall-rectangle branch")
        if not any(item["rect_w"] > item["rect_h"] for item in analyses):
            errors.append("demonstrations omit the wide-rectangle branch")
        colors = {item["color"] for item in analyses}
        if len(colors) < 2:
            errors.append("demonstrations permit a fixed-color shortcut")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing its input")
    elif _analyze(query["input"]).get("errors"):
        errors.append("query input is malformed")
    return errors
