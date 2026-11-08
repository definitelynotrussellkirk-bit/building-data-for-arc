"""Semantic input generator for ARC task ``0d877a4c52fd``.

Each foreground color occupies exactly three corners of one axis-aligned
rectangle.  The selected Racket rule completes the fourth corner in that same
color.  Ordinary draws stay on the canonical 9x9 profile while deliberately
including adjacent-side rectangles that the public examples omit; explicit
overrides expose a wider, fully observable geometry envelope.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d877a4c52fd"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bf8c9dd4f7fa"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.4

SUMMARY = (
    "A zero-background grid contains two or three distinct foreground colors. "
    "Each color marks exactly three corners of one axis-aligned rectangle and "
    "its fourth corner is blank. Complete every rectangle by painting only "
    "that missing corner with the same color."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly two or three foreground colors",
    "each foreground color occurs exactly three times",
    "each color spans exactly two rows and two columns",
    "the implied fourth corner is blank",
    "different colors have disjoint implied rectangle corners",
]

COUNTER_HYPOTHESES = [
    "leave the input unchanged",
    "always complete one fixed corner orientation",
    "complete only the first color",
    "fill each whole bounding box",
    "complete only exact 2x2 rectangles",
    "complete only rectangles whose two side spans are at least two",
    "complete only rectangles having an adjacent side",
    "paint all missing corners with one foreground color",
]

PALETTE_KINDS = ("low", "mid", "high")
PALETTE_POOLS = {
    "low": (1, 2, 3),
    "mid": (4, 5, 6),
    "high": (7, 8, 9),
}
CORNER_NAMES = ("top_left", "top_right", "bottom_left", "bottom_right")
MISSING_PATTERNS = CORNER_NAMES + ("mixed",)
SPAN_PATTERNS = ("adjacent", "spaced", "mixed")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 9",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9",
        "valid": "6..12",
    },
    "n_rects": {
        "type": "int",
        "default": "cycles 2|3",
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
    "span_pattern": {
        "type": "str",
        "default": "cycles adjacent|spaced|mixed",
        "valid": "adjacent|spaced|mixed",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_HEIGHT_SCHEDULE = (9, 9, 9, 9, 9, 9, 6, 7, 8, 10, 11, 12)
_WIDTH_SCHEDULE = (9, 9, 9, 9, 9, 9, 12, 11, 10, 8, 7, 6)
_COUNT_SCHEDULE = (2, 3)
_PALETTE_SCHEDULE = PALETTE_KINDS
_MISSING_SCHEDULE = (
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
    "mixed",
)
_SPAN_SCHEDULE = ("adjacent", "spaced", "mixed")
_BAND_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}


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

    int_bounds = {"grid_h": (6, 12), "grid_w": (6, 12), "n_rects": (2, 3)}
    enum_values = {
        "palette_kind": PALETTE_KINDS,
        "missing_pattern": MISSING_PATTERNS,
        "span_pattern": SPAN_PATTERNS,
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in int_bounds:
            if type(value) is not int:
                raise TypeError(f"override {name!r} must be an integer")
            lo, hi = int_bounds[name]
            if not lo <= value <= hi:
                raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")
        elif value not in enum_values[name]:
            raise ValueError(
                f"override {name!r}={value!r} not in {enum_values[name]!r}"
            )


def _scheduled(sequence: tuple[Any, ...], sample_index: int, band: str) -> Any:
    return sequence[(sample_index + _BAND_OFFSETS[band]) % len(sequence)]


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
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    if not 6 <= len(grid) <= 12:
        errors.append(f"grid height {len(grid)} outside 6..12")
    if not 6 <= width <= 12:
        errors.append(f"grid width {width} outside 6..12")
    return errors


def _corner_map(
    rows: tuple[int, int], cols: tuple[int, int]
) -> dict[str, tuple[int, int]]:
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
        missing_name = next(
            name for name, cell in corner_by_name.items() if cell == missing_cell
        )
        row_span = rows[1] - rows[0]
        col_span = cols[1] - cols[0]
        rectangles.append(
            {
                "color": color,
                "cells": tuple(sorted(cells)),
                "rows": rows,
                "cols": cols,
                "corners": tuple(sorted(corners)),
                "missing": missing_cell,
                "missing_name": missing_name,
                "row_span": row_span,
                "col_span": col_span,
                "adjacent_span": row_span == 1 or col_span == 1,
                "bbox_area": (row_span + 1) * (col_span + 1),
            }
        )
    return errors, rectangles


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete three-corners-per-color input grammar."""
    del meta
    _validate_difficulty(difficulty)
    errors, _ = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require a lawful input on one of the task's exact 9x9 count profiles."""
    errors, rectangles = _analyze(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len(rectangles))
    if profile not in {(9, 9, 2), (9, 9, 3)}:
        return [f"profile {profile} is outside canonical 9x9 two/three-color support"]
    return []


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors, rectangles = _analyze(grid)
    if errors:
        return {"errors": errors, "rectangles": rectangles}

    orientations = tuple(rect["missing_name"] for rect in rectangles)
    colors = tuple(rect["color"] for rect in rectangles)
    adjacent = tuple(rect["adjacent_span"] for rect in rectangles)
    if all(adjacent):
        span_pattern = "adjacent"
    elif not any(adjacent):
        span_pattern = "spaced"
    else:
        span_pattern = "mixed"
    missing_pattern = orientations[0] if len(set(orientations)) == 1 else "mixed"
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "n_rects": len(rectangles),
        "colors": colors,
        "rectangles": rectangles,
        "missing_orientations": orientations,
        "missing_pattern": missing_pattern,
        "span_pattern": span_pattern,
        "has_adjacent_span": any(adjacent),
        "has_spaced_span": not all(adjacent),
        "has_non_2x2": any(
            rect["row_span"] > 1 or rect["col_span"] > 1 for rect in rectangles
        ),
    }


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact axis from returned pixels."""
    facts = semantic_observables(grid)
    if facts["errors"]:
        raise ValueError("cannot observe override axes: " + "; ".join(facts["errors"]))
    colors = set(facts["colors"])
    matches = [name for name, pool in PALETTE_POOLS.items() if colors <= set(pool)]
    if len(matches) != 1:
        raise ValueError(
            f"foreground colors {sorted(colors)} do not identify one palette kind"
        )
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_rects": facts["n_rects"],
        "palette_kind": matches[0],
        "missing_pattern": facts["missing_pattern"],
        "span_pattern": facts["span_pattern"],
    }


def rule_mirror(grid):
    """Python test oracle; the selected Racket program remains authoritative."""
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


def _desired_span_kinds(pattern: str, count: int, rng) -> list[str]:
    if pattern != "mixed":
        return [pattern] * count
    kinds = ["adjacent", "spaced"]
    while len(kinds) < count:
        kinds.append(rng.choice(("adjacent", "spaced")))
    rng.shuffle(kinds)
    return kinds


def _rect_corners(rect: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, r1, c0, c1 = rect
    return {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}


def _rectangle_candidates(
    height: int, width: int, span_kind: str
) -> list[tuple[int, int, int, int]]:
    candidates: list[tuple[int, int, int, int]] = []
    for r0 in range(height - 1):
        for r1 in range(r0 + 1, height):
            for c0 in range(width - 1):
                for c1 in range(c0 + 1, width):
                    adjacent = (r1 - r0) == 1 or (c1 - c0) == 1
                    if (span_kind == "adjacent" and adjacent) or (
                        span_kind == "spaced" and not adjacent
                    ):
                        candidates.append((r0, r1, c0, c1))
    return candidates


def _place_rectangles(
    height: int,
    width: int,
    span_kinds: list[str],
    rng,
) -> list[tuple[int, int, int, int]]:
    """Backtrack over disjoint full corner sets; never shorten the request."""
    candidate_lists = [
        _rectangle_candidates(height, width, span_kind) for span_kind in span_kinds
    ]
    for candidates in candidate_lists:
        rng.shuffle(candidates)
    order = sorted(range(len(span_kinds)), key=lambda index: len(candidate_lists[index]))
    chosen: list[tuple[int, int, int, int] | None] = [None] * len(span_kinds)
    used: set[tuple[int, int]] = set()

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        for rect in candidate_lists[index]:
            corners = _rect_corners(rect)
            if corners & used:
                continue
            chosen[index] = rect
            used.update(corners)
            if search(depth + 1):
                return True
            used.difference_update(corners)
            chosen[index] = None
        return False

    if not search(0):
        raise ValueError(
            f"could not place {len(span_kinds)} disjoint rectangle-corner sets "
            f"in {height}x{width} for span kinds {span_kinds!r}"
        )
    return [rect for rect in chosen if rect is not None]


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
    explicit = any(value is not None for value in overrides.values())

    if explicit:
        height = ctx.draw_int_strict("grid_h", 6, 12)
        width = ctx.draw_int_strict("grid_w", 6, 12)
        count = ctx.draw_int_strict("n_rects", 2, 3)
    else:
        scheduled_height = _scheduled(_HEIGHT_SCHEDULE, sample_index, band)
        scheduled_width = _scheduled(_WIDTH_SCHEDULE, sample_index, band)
        height = ctx.draw_int_strict("grid_h", scheduled_height, scheduled_height)
        width = ctx.draw_int_strict("grid_w", scheduled_width, scheduled_width)
        scheduled_count = _scheduled(_COUNT_SCHEDULE, sample_index, band)
        count = ctx.draw_int_strict("n_rects", scheduled_count, scheduled_count)

    if overrides.get("palette_kind") is not None:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    else:
        scheduled_palette = _scheduled(_PALETTE_SCHEDULE, sample_index, band)
        palette_kind = ctx.draw_choice("palette_kind", (scheduled_palette,))

    if overrides.get("missing_pattern") is not None:
        missing_pattern = ctx.draw_choice("missing_pattern", MISSING_PATTERNS)
    else:
        scheduled_missing = _scheduled(_MISSING_SCHEDULE, sample_index, band)
        missing_pattern = ctx.draw_choice("missing_pattern", (scheduled_missing,))

    if overrides.get("span_pattern") is not None:
        span_pattern = ctx.draw_choice("span_pattern", SPAN_PATTERNS)
    else:
        scheduled_span = _scheduled(_SPAN_SCHEDULE, sample_index, band)
        span_pattern = ctx.draw_choice("span_pattern", (scheduled_span,))

    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(list(PALETTE_POOLS[palette_kind]), count)
    layout_rng = ctx.draw_rng("layout")
    orientations = _desired_orientations(missing_pattern, count, layout_rng)
    span_kinds = _desired_span_kinds(span_pattern, count, layout_rng)
    rectangles = _place_rectangles(height, width, span_kinds, layout_rng)

    grid = full_grid(height, width, 0)
    for color, orientation, rect in zip(colors, orientations, rectangles):
        r0, r1, c0, c1 = rect
        corner_by_name = _corner_map((r0, r1), (c0, c1))
        missing = corner_by_name[orientation]
        for cell in corner_by_name.values():
            if cell != missing:
                grid[cell[0]][cell[1]] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
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
        r, c = _corner_map(rect["rows"], rect["cols"])[corner_name]
        out[r][c] = rect["color"]
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


def _spaced_only(grid):
    """Canonical-fitting shortcut: ignores any rectangle with an adjacent side."""
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    for rect in rectangles:
        if rect["row_span"] >= 2 and rect["col_span"] >= 2:
            r, c = rect["missing"]
            out[r][c] = rect["color"]
    return out


def _adjacent_only(grid):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    for rect in rectangles:
        if rect["adjacent_span"]:
            r, c = rect["missing"]
            out[r][c] = rect["color"]
    return out


def _monochrome_completion(grid):
    errors, rectangles = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
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
    "fill_bounding_boxes": _fill_bounding_boxes,
    "complete_2x2_only": _complete_2x2_only,
    "spaced_only": _spaced_only,
    "adjacent_only": _adjacent_only,
    "monochrome_completion": _monochrome_completion,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"spaced_only": _spaced_only}


def _has_missing(grid, corner_name: str) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and corner_name in facts["missing_orientations"]


def _multiple_rectangles(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and facts["n_rects"] >= 2


def _non_2x2_rectangle(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and facts["has_non_2x2"]


def _has_adjacent_span(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and facts["has_adjacent_span"]


def _has_spaced_span(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and facts["has_spaced_span"]


def _multiple_colors(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts["errors"] and len(set(facts["colors"])) >= 2


SEMANTIC_WITNESSES = {
    "missing_top_left": lambda grid: _has_missing(grid, "top_left"),
    "missing_top_right": lambda grid: _has_missing(grid, "top_right"),
    "missing_bottom_left": lambda grid: _has_missing(grid, "bottom_left"),
    "missing_bottom_right": lambda grid: _has_missing(grid, "bottom_right"),
    "multiple_rectangles": _multiple_rectangles,
    "non_2x2_rectangle": _non_2x2_rectangle,
    "adjacent_span": _has_adjacent_span,
    "spaced_span": _has_spaced_span,
    "multiple_colors": _multiple_colors,
}
WITNESS_RIVALS = {
    "missing_top_left": ["fixed_top_right", "fixed_bottom_left", "fixed_bottom_right"],
    "missing_top_right": ["fixed_top_left", "fixed_bottom_left", "fixed_bottom_right"],
    "missing_bottom_left": ["fixed_top_left", "fixed_top_right", "fixed_bottom_right"],
    "missing_bottom_right": ["fixed_top_left", "fixed_top_right", "fixed_bottom_left"],
    "multiple_rectangles": ["identity", "first_color_only"],
    "non_2x2_rectangle": ["fill_bounding_boxes", "complete_2x2_only"],
    "adjacent_span": ["spaced_only"],
    "spaced_span": ["adjacent_only", "complete_2x2_only"],
    "multiple_colors": ["monochrome_completion"],
}


def _grids_equal(left, right) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when a declared wrong rule survives every demonstration."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if not all(
                _grids_equal(rival(pair["input"]), pair["output"]) for pair in demos
            ):
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives demos and query")
            else:
                reasons.append(
                    f"competitor {name!r} fits all demos but disagrees on query"
                )
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
