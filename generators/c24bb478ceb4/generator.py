"""Semantic generator for ARC task ``c24bb478ceb4``.

Each nonzero color marks exactly three corners of one axis-aligned rectangle.
The missing fourth corner is blank and must be painted with that same color.
Ordinary draws stay on one of the four canonical ``(height, width, count)``
profiles while varying rectangle geometry, missing-corner orientation, and
color band. Explicit overrides expose a wider, fully observable legal envelope.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c24bb478ceb4"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "237d8e244b45"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains two or three distinct nonzero colors. "
    "For each color, exactly three cells occupy three corners of one "
    "axis-aligned rectangle and the fourth corner is blank. Complete every "
    "rectangle by painting only its missing corner with the same color."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly two or three foreground colors",
    "each foreground color occurs exactly three times",
    "each color's cells span exactly two rows and two columns",
    "the implied fourth corner is blank",
    "different colors have disjoint implied rectangle corners",
]

COUNTER_HYPOTHESES = [
    "leave the input unchanged",
    "always fill one fixed corner orientation",
    "complete only the first or largest rectangle",
    "fill every cell of each bounding box rather than only its missing corner",
    "complete only 2x2 rectangles",
    "paint every missing corner with one modal or fixed color",
    "infer one rectangle's missing orientation and reuse it for every color",
]

PALETTE_KINDS = ("low", "mid", "high")
PALETTE_POOLS = {
    "low": (1, 2, 3),
    "mid": (4, 5, 6),
    "high": (7, 8, 9),
}
CORNER_NAMES = ("top_left", "top_right", "bottom_left", "bottom_right")
MISSING_PATTERNS = CORNER_NAMES + ("mixed",)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "8..12",
    },
    "n_rects": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "2..3",
    },
    "palette_kind": {
        "type": "str",
        "default": "cycles low|mid|high",
        "valid": "low|mid|high",
    },
    "missing_pattern": {
        "type": "str",
        "default": "cycles all four corners plus mixed",
        "valid": "top_left|top_right|bottom_left|bottom_right|mixed",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_CANONICAL_PROFILE_SPECS = {
    "canonical_7x8_two": (7, 8, 2),
    "canonical_8x9_two": (8, 9, 2),
    "canonical_8x10_two": (8, 10, 2),
    "canonical_9x9_three": (9, 9, 3),
}
SCHEDULE_PROFILES = tuple(_CANONICAL_PROFILE_SPECS)
_PROFILE_SCHEDULES = {
    "easy": (
        "canonical_7x8_two",
        "canonical_8x9_two",
        "canonical_8x10_two",
        "canonical_7x8_two",
        "canonical_9x9_three",
    ),
    "medium": (
        "canonical_8x9_two",
        "canonical_9x9_three",
        "canonical_8x10_two",
        "canonical_7x8_two",
    ),
    "hard": (
        "canonical_9x9_three",
        "canonical_8x10_two",
        "canonical_9x9_three",
        "canonical_8x9_two",
        "canonical_7x8_two",
    ),
}
# Alternate fixed and mixed cases so every three-demo lesson, including every
# one-of-four query rotation, retains a within-grid mixed-orientation witness.
_MISSING_SCHEDULE = (
    "top_left",
    "mixed",
    "bottom_right",
    "mixed",
    "top_right",
    "mixed",
    "bottom_left",
    "mixed",
)


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return str(difficulty)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")

    int_bounds = {"grid_h": (7, 10), "grid_w": (8, 12), "n_rects": (2, 3)}
    enum_values = {
        "palette_kind": PALETTE_KINDS,
        "missing_pattern": MISSING_PATTERNS,
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in int_bounds:
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"override {name!r} must be an integer")
            lo, hi = int_bounds[name]
            if not lo <= value <= hi:
                raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")
        elif value not in enum_values[name]:
            raise ValueError(
                f"override {name!r}={value!r} not in {enum_values[name]!r}"
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic canonical-profile schedule used by ordinary draws."""
    del seed
    band = _validate_difficulty(difficulty)
    profiles = _PROFILE_SCHEDULES[band]
    return profiles[sample_index % len(profiles)]


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    if not 7 <= len(grid) <= 10:
        errors.append(f"grid height {len(grid)} outside 7..10")
    if not 8 <= width <= 12:
        errors.append(f"grid width {width} outside 8..12")
    return errors


def _corner_map(rows: tuple[int, int], cols: tuple[int, int]) -> dict[str, tuple[int, int]]:
    r0, r1 = rows
    c0, c1 = cols
    return {
        "top_left": (r0, c0),
        "top_right": (r0, c1),
        "bottom_left": (r1, c0),
        "bottom_right": (r1, c1),
    }


def _analyze(grid: Any) -> tuple[list[str], list[dict[str, Any]]]:
    errors = _basic_grid_errors(grid)
    if errors:
        return errors, []

    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))

    if not 2 <= len(by_color) <= 3:
        errors.append(f"expected 2-3 foreground colors, got {len(by_color)}")

    rectangles: list[dict[str, Any]] = []
    used_corners: set[tuple[int, int]] = set()
    for color, cells in sorted(by_color.items()):
        if len(cells) != 3:
            errors.append(f"color {color} appears {len(cells)} times, expected exactly 3")
            continue
        rows = tuple(sorted({r for r, _ in cells}))
        cols = tuple(sorted({c for _, c in cells}))
        if len(rows) != 2 or len(cols) != 2:
            errors.append(f"color {color} cells must span exactly two rows and two columns")
            continue
        corner_by_name = _corner_map(rows, cols)
        corners = set(corner_by_name.values())
        present = set(cells)
        missing = corners - present
        if len(missing) != 1:
            errors.append(f"color {color} is not exactly three corners of its rectangle")
            continue
        missing_cell = next(iter(missing))
        if grid[missing_cell[0]][missing_cell[1]] != 0:
            errors.append(f"color {color} missing corner {missing_cell} is not blank")
        overlap = used_corners & corners
        if overlap:
            errors.append(
                f"color {color} shares implied rectangle corner(s) {sorted(overlap)}"
            )
        used_corners |= corners
        missing_name = next(name for name, cell in corner_by_name.items() if cell == missing_cell)
        rectangles.append(
            {
                "color": color,
                "cells": tuple(sorted(cells)),
                "rows": rows,
                "cols": cols,
                "corners": tuple(sorted(corners)),
                "missing": missing_cell,
                "missing_name": missing_name,
                "row_span": rows[1] - rows[0],
                "col_span": cols[1] - cols[0],
                "bbox_area": (rows[1] - rows[0] + 1) * (cols[1] - cols[0] + 1),
            }
        )
    return errors, rectangles


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible three-corners-per-color grammar."""
    del meta
    _validate_difficulty(difficulty)
    errors, _ = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require a lawful grid on one of the four real canonical profiles."""
    errors, rectangles = _analyze(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len(rectangles))
    if profile not in set(_CANONICAL_PROFILE_SPECS.values()):
        return [f"profile {profile} is outside the canonical train/test profile set"]
    return []


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors, rectangles = _analyze(grid)
    if errors:
        return {"errors": errors, "rectangles": rectangles}
    orientations = [rect["missing_name"] for rect in rectangles]
    colors = tuple(rect["color"] for rect in rectangles)
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "n_rects": len(rectangles),
        "colors": colors,
        "rectangles": rectangles,
        "missing_orientations": tuple(orientations),
        "missing_pattern": orientations[0] if len(set(orientations)) == 1 else "mixed",
        "has_non_2x2": any(
            rect["row_span"] > 1 or rect["col_span"] > 1 for rect in rectangles
        ),
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts["errors"]:
        raise ValueError("cannot observe override axes: " + "; ".join(facts["errors"]))
    colors = set(facts["colors"])
    matches = [name for name, pool in PALETTE_POOLS.items() if colors <= set(pool)]
    if len(matches) != 1:
        raise ValueError(f"foreground colors {sorted(colors)} do not identify one palette kind")
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_rects": facts["n_rects"],
        "palette_kind": matches[0],
        "missing_pattern": facts["missing_pattern"],
    }


def rule_mirror(grid):
    """Python mirror for tests and named rivals; Racket remains authoritative."""
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for rect in rectangles:
        r, c = rect["missing"]
        out[r][c] = rect["color"]
    return out


def _desired_orientations(pattern: str, count: int, rng) -> list[str]:
    if pattern != "mixed":
        return [pattern] * count
    choices = list(CORNER_NAMES)
    rng.shuffle(choices)
    return choices[:count]


def _all_rectangles(height: int, width: int) -> list[tuple[int, int, int, int]]:
    return [
        (r0, r1, c0, c1)
        for r0 in range(height - 1)
        for r1 in range(r0 + 1, height)
        for c0 in range(width - 1)
        for c1 in range(c0 + 1, width)
    ]


def _place_rectangles(
    height: int,
    width: int,
    orientations: list[str],
    rng,
) -> list[tuple[int, int, int, int]]:
    """Backtrack over disjoint inferred-corner sets; force one non-2x2 box."""
    candidates = _all_rectangles(height, width)
    rng.shuffle(candidates)
    chosen: list[tuple[int, int, int, int]] = []
    used: set[tuple[int, int]] = set()

    def corners(rect):
        r0, r1, c0, c1 = rect
        return {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}

    def search(index: int) -> bool:
        if index == len(orientations):
            return any((r1 - r0) > 1 or (c1 - c0) > 1 for r0, r1, c0, c1 in chosen)
        for rect in candidates:
            rect_corners = corners(rect)
            if rect_corners & used:
                continue
            if index == 0 and (rect[1] - rect[0]) == 1 and (rect[3] - rect[2]) == 1:
                continue
            chosen.append(rect)
            used.update(rect_corners)
            if search(index + 1):
                return True
            chosen.pop()
            used.difference_update(rect_corners)
        return False

    if not search(0):
        raise ValueError(
            f"could not place {len(orientations)} disjoint rectangle-corner sets "
            f"in {height}x{width}"
        )
    return list(chosen)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    if overrides:
        height = ctx.draw_int("grid_h", 7, 10)
        width = ctx.draw_int("grid_w", 8, 12)
        count = ctx.draw_int("n_rects", 2, 3)
    else:
        profile = schedule_profile(seed, sample_index, band)
        ph, pw, pn = _CANONICAL_PROFILE_SPECS[profile]
        height = ctx.draw_int("grid_h", ph, ph)
        width = ctx.draw_int("grid_w", pw, pw)
        count = ctx.draw_int("n_rects", pn, pn)

    if "palette_kind" in overrides:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    else:
        offset = {"easy": 0, "medium": 1, "hard": 2}[band]
        default_palette = PALETTE_KINDS[(sample_index + offset) % len(PALETTE_KINDS)]
        palette_kind = ctx.draw_choice("palette_kind", (default_palette,))

    if "missing_pattern" in overrides:
        missing_pattern = ctx.draw_choice("missing_pattern", MISSING_PATTERNS)
    else:
        default_missing = _MISSING_SCHEDULE[sample_index % len(_MISSING_SCHEDULE)]
        missing_pattern = ctx.draw_choice("missing_pattern", (default_missing,))

    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(list(PALETTE_POOLS[palette_kind]), count)
    layout_rng = ctx.draw_rng("layout")
    orientations = _desired_orientations(missing_pattern, count, layout_rng)
    rectangles = _place_rectangles(height, width, orientations, layout_rng)

    grid = full_grid(height, width, 0)
    for color, orientation, (r0, r1, c0, c1) in zip(colors, orientations, rectangles):
        corner_by_name = _corner_map((r0, r1), (c0, c1))
        missing = corner_by_name[orientation]
        for cell in corner_by_name.values():
            if cell != missing:
                grid[cell[0]][cell[1]] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    if not semantic_observables(grid)["has_non_2x2"]:
        raise ValueError("internal generation error: missing non-2x2 rectangle witness")

    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected!r}, "
                f"observed {observed[axis]!r}"
            )
    return grid


# ---------------------------------------------------------------------------
# Named rival rules and semantic witnesses
# ---------------------------------------------------------------------------


def _copy_grid(grid):
    return [list(row) for row in grid]


def _fixed_corner_completion(grid, corner_name: str):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    for rect in rectangles:
        corner = _corner_map(rect["rows"], rect["cols"])[corner_name]
        out[corner[0]][corner[1]] = rect["color"]
    return out


def _complete_first_color_only(grid):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    rect = min(rectangles, key=lambda item: item["color"])
    r, c = rect["missing"]
    out[r][c] = rect["color"]
    return out


def _complete_largest_rectangle_only(grid):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    rect = max(rectangles, key=lambda item: (item["bbox_area"], -item["color"]))
    r, c = rect["missing"]
    out[r][c] = rect["color"]
    return out


def _first_orientation_for_all(grid):
    """Wrong rule: reuse the lowest color's missing orientation globally."""
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    orientation = min(rectangles, key=lambda item: item["color"])["missing_name"]
    for rect in rectangles:
        r, c = _corner_map(rect["rows"], rect["cols"])[orientation]
        out[r][c] = rect["color"]
    return out


def _fill_bounding_boxes(grid):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    for rect in rectangles:
        for r in range(rect["rows"][0], rect["rows"][1] + 1):
            for c in range(rect["cols"][0], rect["cols"][1] + 1):
                out[r][c] = rect["color"]
    return out


def _complete_2x2_only(grid):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    for rect in rectangles:
        if rect["row_span"] == 1 and rect["col_span"] == 1:
            r, c = rect["missing"]
            out[r][c] = rect["color"]
    return out


def _monochrome_completion(grid):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    fill_color = Counter(rect["color"] for rect in rectangles).most_common()[-1][0]
    fill_color = min(rect["color"] for rect in rectangles)
    for rect in rectangles:
        r, c = rect["missing"]
        out[r][c] = fill_color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "identity": _copy_grid,
    "fixed_top_left": lambda grid: _fixed_corner_completion(grid, "top_left"),
    "fixed_top_right": lambda grid: _fixed_corner_completion(grid, "top_right"),
    "fixed_bottom_left": lambda grid: _fixed_corner_completion(grid, "bottom_left"),
    "fixed_bottom_right": lambda grid: _fixed_corner_completion(grid, "bottom_right"),
    "first_color_only": _complete_first_color_only,
    "largest_rectangle_only": _complete_largest_rectangle_only,
    "first_orientation_for_all": _first_orientation_for_all,
    "fill_bounding_boxes": _fill_bounding_boxes,
    "complete_2x2_only": _complete_2x2_only,
    "monochrome_completion": _monochrome_completion,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "fixed_bottom_right": SEMANTIC_RIVALS["fixed_bottom_right"],
    "first_color_only": _complete_first_color_only,
    "fill_bounding_boxes": _fill_bounding_boxes,
    "monochrome_completion": _monochrome_completion,
}


def _has_missing(grid, corner_name: str) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and corner_name in facts["missing_orientations"]


def _multiple_rectangles(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and facts["n_rects"] >= 2


def _non_2x2_rectangle(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and facts["has_non_2x2"]


def _multiple_colors(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and len(set(facts["colors"])) >= 2


def _mixed_orientations(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and len(set(facts["missing_orientations"])) >= 2


SEMANTIC_WITNESSES = {
    "missing_top_left": lambda grid: _has_missing(grid, "top_left"),
    "missing_top_right": lambda grid: _has_missing(grid, "top_right"),
    "missing_bottom_left": lambda grid: _has_missing(grid, "bottom_left"),
    "missing_bottom_right": lambda grid: _has_missing(grid, "bottom_right"),
    "multiple_rectangles": _multiple_rectangles,
    "non_2x2_rectangle": _non_2x2_rectangle,
    "multiple_colors": _multiple_colors,
    "mixed_orientations": _mixed_orientations,
}
WITNESS_RIVALS = {
    "missing_top_left": ["fixed_top_right", "fixed_bottom_left", "fixed_bottom_right"],
    "missing_top_right": ["fixed_top_left", "fixed_bottom_left", "fixed_bottom_right"],
    "missing_bottom_left": ["fixed_top_left", "fixed_top_right", "fixed_bottom_right"],
    "missing_bottom_right": ["fixed_top_left", "fixed_top_right", "fixed_bottom_left"],
    "multiple_rectangles": ["identity", "first_color_only", "largest_rectangle_only"],
    "non_2x2_rectangle": ["fill_bounding_boxes", "complete_2x2_only"],
    "multiple_colors": ["monochrome_completion"],
    "mixed_orientations": ["first_orientation_for_all"],
}


def _grids_equal(left, right) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which a named wrong rule survives all demos."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if not all(_grids_equal(rival(pair["input"]), pair["output"]) for pair in demos):
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives demos and query")
            else:
                reasons.append(f"competitor {name!r} fits all demos but disagrees on query")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
