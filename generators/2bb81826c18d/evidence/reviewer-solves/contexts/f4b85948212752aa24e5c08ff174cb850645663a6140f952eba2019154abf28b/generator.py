"""Reviewed generator for ARC task 2bb81826c18d.

Input contract: one to four separated, solid, monochromatic rectangles on a
zero background.  Every rectangle is at least 3x3.  The canonical Racket rule
is the sole output authority: it preserves each rectangle's border and erases
alternating interior cells using a checker phase anchored to that rectangle's
own top-left interior cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid


GENERATOR_ID = "2bb81826c18d"
TASK_ID = "2bb81826c18d"
VERSION = "2.0.0"
RULE_HASH = "b0e1d6662c7a"

SUMMARY = (
    "Generate 1..4 separated solid rectangles, each at least 3x3 and with a "
    "distinct nonzero color.  Dimensions, object count, palette family, size "
    "profile, and boundary contact are explicit controls.  The canonical "
    "Racket rule keeps every rectangle border and checker-erases its interior "
    "in rectangle-relative coordinates."
)

INVARIANTS = [
    "the input is a rectangular 10..24 by 10..24 ARC grid",
    "background 0 is present",
    "there are exactly 1..4 four-connected nonzero components",
    "each component is one solid monochromatic rectangle at least 3x3",
    "rectangle colors are distinct and rectangles do not touch orthogonally",
    "all randomness is deterministic and keyed through GenCtx",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

SIZE_PROFILES = ("compact", "mixed", "large")
PALETTE_KINDS = ("warm", "cool", "primary", "broad")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 10..24",
        "valid": "10..24",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 10..24",
        "valid": "10..24",
    },
    "n_rects": {
        "type": "int",
        "default": "difficulty-aware rng 1..4",
        "valid": "1..4",
    },
    "size_profile": {
        "type": "enum",
        "default": "rng",
        "valid": "compact|mixed|large",
    },
    "palette_kind": {
        "type": "enum",
        "default": "rng",
        "valid": "warm|cool|primary|broad",
    },
    "edge_touch": {
        "type": "bool",
        "default": "rng true|false",
        "valid": "true|false",
    },
}

_VALID_DIM = (10, 24)
_BAND_DIMS = {
    "easy": (10, 14),
    "medium": (13, 19),
    "hard": (18, 24),
}
_BAND_COUNTS = {
    "easy": (1, 2),
    "medium": (1, 3),
    "hard": (2, 4),
}
_PALETTE_POOLS = {
    "warm": (2, 3, 4, 6, 9),
    "cool": (1, 5, 7, 8),
    "primary": (1, 2, 3, 4),
    "broad": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label in ("grid_h", "grid_w", "n_rects"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    value = overrides.get("edge_touch")
    if value is not None and type(value) is not bool:
        raise ValueError("edge_touch must be a boolean")
    value = overrides.get("size_profile")
    if value is not None and value not in SIZE_PROFILES:
        raise ValueError(
            "size_profile must be one of " + ", ".join(SIZE_PROFILES)
        )
    value = overrides.get("palette_kind")
    if value is not None and value not in PALETTE_KINDS:
        raise ValueError(
            "palette_kind must be one of " + ", ".join(PALETTE_KINDS)
        )


def _coerce_grid(grid):
    coerced = []
    for row in grid:
        values = list(row) if isinstance(row, str) else list(row)
        coerced.append(
            [
                int(value)
                if isinstance(value, str) and len(value) == 1 and value.isdigit()
                else value
                for value in values
            ]
        )
    return coerced


def _analyze(grid) -> dict:
    """Return structural facts without mutating ``grid``."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "components": []}
    if not all(isinstance(row, (list, str)) and len(row) > 0 for row in grid):
        return {
            "errors": ["grid rows must be non-empty lists or digit strings"],
            "components": [],
        }

    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return {"errors": ["grid must be rectangular"], "components": []}

    height = len(coerced)
    if not _VALID_DIM[0] <= height <= _VALID_DIM[1]:
        errors.append("grid height must be in 10..24")
    if not _VALID_DIM[0] <= width <= _VALID_DIM[1]:
        errors.append("grid width must be in 10..24")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {
            "errors": errors,
            "components": [],
            "grid": coerced,
            "height": height,
            "width": width,
        }

    flat = [value for row in coerced for value in row]
    if 0 not in flat:
        errors.append("background 0 must be present")
    if not any(value != 0 for value in flat):
        errors.append("at least one nonzero rectangle is required")

    visited: set[tuple[int, int]] = set()
    components: list[dict] = []
    for start_row in range(height):
        for start_col in range(width):
            color = coerced[start_row][start_col]
            if color == 0 or (start_row, start_col) in visited:
                continue
            stack = [(start_row, start_col)]
            visited.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for nr, nc in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in visited
                        and coerced[nr][nc] == color
                    ):
                        visited.add((nr, nc))
                        stack.append((nr, nc))

            top = min(row for row, _ in cells)
            bottom = max(row for row, _ in cells)
            left = min(col for _, col in cells)
            right = max(col for _, col in cells)
            rect_h = bottom - top + 1
            rect_w = right - left + 1
            solid = len(cells) == rect_h * rect_w and all(
                coerced[row][col] == color
                for row in range(top, bottom + 1)
                for col in range(left, right + 1)
            )
            edge_touch = (
                top == 0
                or left == 0
                or bottom == height - 1
                or right == width - 1
            )
            components.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "top": top,
                    "bottom": bottom,
                    "left": left,
                    "right": right,
                    "height": rect_h,
                    "width": rect_w,
                    "area": len(cells),
                    "solid": solid,
                    "edge_touch": edge_touch,
                }
            )

    if not 1 <= len(components) <= 4:
        errors.append("there must be exactly 1..4 nonzero components")
    colors = [component["color"] for component in components]
    if len(colors) != len(set(colors)):
        errors.append("each rectangle must use a distinct nonzero color")
    for index, component in enumerate(components):
        if not component["solid"]:
            errors.append(f"component {index} must be a solid rectangle")
        if component["height"] < 3 or component["width"] < 3:
            errors.append(f"component {index} must be at least 3x3")

    touching_colors = False
    for row in range(height):
        for col in range(width):
            value = coerced[row][col]
            if value == 0:
                continue
            if row + 1 < height:
                below = coerced[row + 1][col]
                touching_colors |= below != 0 and below != value
            if col + 1 < width:
                right = coerced[row][col + 1]
                touching_colors |= right != 0 and right != value
    if touching_colors:
        errors.append("rectangles must not touch orthogonally")

    return {
        "errors": errors,
        "components": components,
        "grid": coerced,
        "height": height,
        "width": width,
        "n_rects": len(components),
        "edge_touch": any(c["edge_touch"] for c in components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors or not isinstance(meta, dict):
        return errors

    expected = {
        "grid_h": analysis.get("height"),
        "grid_w": analysis.get("width"),
        "n_rects": analysis.get("n_rects"),
        "edge_touch": analysis.get("edge_touch"),
    }
    for label, actual in expected.items():
        requested = meta.get(label)
        if requested is not None and requested != actual:
            errors.append(
                f"meta {label} requested {requested!r}, observed {actual!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int | bool]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe overrides: " + "; ".join(analysis["errors"])
        )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_rects": analysis["n_rects"],
        "edge_touch": analysis["edge_touch"],
    }


def rule_mirror(grid):
    """Test-only Python mirror; generated outputs still come from Racket."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    output = [row[:] for row in analysis["grid"]]
    for component in analysis["components"]:
        top = component["top"]
        bottom = component["bottom"]
        left = component["left"]
        right = component["right"]
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                interior_row = row - top - 1
                interior_col = col - left - 1
                if (interior_row + interior_col) % 2 == 0:
                    output[row][col] = 0
    return output


def _split_interval(start: int, stop: int, rng):
    """Split a half-open interval into two parts with a one-cell gap."""
    available = stop - start - 1
    first = available // 2
    second = available - first
    if rng.choice((False, True)):
        first, second = second, first
    middle = start + first
    return (start, middle), (middle + 1, middle + 1 + second)


def _layout_zones(height: int, width: int, n_rects: int, margin: int, rng):
    row_start, row_stop = margin, height - margin
    col_start, col_stop = margin, width - margin
    if n_rects == 1:
        return [(row_start, row_stop, col_start, col_stop)]
    if n_rects == 2:
        if rng.choice(("horizontal", "vertical")) == "horizontal":
            rows = _split_interval(row_start, row_stop, rng)
            return [
                (top, bottom, col_start, col_stop)
                for top, bottom in rows
            ]
        cols = _split_interval(col_start, col_stop, rng)
        return [
            (row_start, row_stop, left, right)
            for left, right in cols
        ]

    rows = _split_interval(row_start, row_stop, rng)
    cols = _split_interval(col_start, col_stop, rng)
    zones = [
        (rows[0][0], rows[0][1], cols[0][0], cols[0][1]),
        (rows[0][0], rows[0][1], cols[1][0], cols[1][1]),
        (rows[1][0], rows[1][1], cols[0][0], cols[0][1]),
        (rows[1][0], rows[1][1], cols[1][0], cols[1][1]),
    ]
    if n_rects == 3:
        # Keep the top-left zone so edge_touch=True is always constructive.
        del zones[rng.choice((1, 2, 3))]
    return zones


def _size_bounds(span: int, profile: str) -> tuple[int, int]:
    if profile == "compact":
        return 3, min(span, 5)
    if profile == "mixed":
        lower = max(3, min(span, max(4, (span + 2) // 3)))
        return lower, min(span, 9)
    upper = min(span, 12)
    lower = max(3, min(upper, max(7, (3 * span + 3) // 4)))
    return lower, upper


def _rectangle_in_zone(
    zone,
    *,
    profile: str,
    force_outer_edge: bool,
    height: int,
    width: int,
    rng,
):
    top, bottom, left, right = zone
    zone_h = bottom - top
    zone_w = right - left
    h_lo, h_hi = _size_bounds(zone_h, profile)
    w_lo, w_hi = _size_bounds(zone_w, profile)
    rect_h = rng.randint(h_lo, h_hi)
    rect_w = rng.randint(w_lo, w_hi)
    if (
        force_outer_edge
        and top == 0
        and bottom == height
        and left == 0
        and right == width
        and rect_h == height
        and rect_w == width
    ):
        # Keep at least one background strip even for the smallest full-canvas
        # large-profile case.  The explicit size profile remains honored, and
        # edge contact is preserved.
        if rng.choice(("height", "width")) == "height":
            rect_h -= 1
        else:
            rect_w -= 1

    max_top = bottom - rect_h
    max_left = right - rect_w
    row = rng.randint(top, max_top)
    col = rng.randint(left, max_left)

    if force_outer_edge:
        sides = []
        if top == 0:
            sides.append("top")
        if bottom == height:
            sides.append("bottom")
        if left == 0:
            sides.append("left")
        if right == width:
            sides.append("right")
        side = rng.choice(sides)
        if side == "top":
            row = 0
        elif side == "bottom":
            row = height - rect_h
        elif side == "left":
            col = 0
        else:
            col = width - rect_w
    return row, col, rect_h, rect_w


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
    band = difficulty or "medium"

    height = ctx.draw_int(
        "grid_h",
        *(
            _VALID_DIM
            if overrides.get("grid_h") is not None
            else _BAND_DIMS[band]
        ),
    )
    width = ctx.draw_int(
        "grid_w",
        *(
            _VALID_DIM
            if overrides.get("grid_w") is not None
            else _BAND_DIMS[band]
        ),
    )
    n_rects = ctx.draw_int(
        "n_rects",
        *(
            (1, 4)
            if overrides.get("n_rects") is not None
            else _BAND_COUNTS[band]
        ),
    )
    size_profile = ctx.draw_choice("size_profile", SIZE_PROFILES)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    edge_touch = ctx.draw_choice("edge_touch", (False, True))

    layout_rng = ctx.draw_rng(
        f"layout|n={n_rects}|edge={edge_touch}|profile={size_profile}"
    )
    margin = 0 if edge_touch else 1
    zones = _layout_zones(height, width, n_rects, margin, layout_rng)

    palette_rng = ctx.draw_rng(f"palette|{palette_kind}|n={n_rects}")
    colors = palette_rng.sample(list(_PALETTE_POOLS[palette_kind]), n_rects)
    grid = full_grid(height, width, 0)
    for index, (zone, color) in enumerate(zip(zones, colors)):
        rect_rng = ctx.draw_rng(
            f"rectangle|{index}|{size_profile}|{zone}|{edge_touch}"
        )
        row, col, rect_h, rect_w = _rectangle_in_zone(
            zone,
            profile=size_profile,
            force_outer_edge=edge_touch and index == 0,
            height=height,
            width=width,
            rng=rect_rng,
        )
        draw_rect(grid, row, col, rect_h, rect_w, color)

    errors = self_check(
        grid,
        meta={
            "grid_h": height,
            "grid_w": width,
            "n_rects": n_rects,
            "edge_touch": edge_touch,
        },
    )
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
