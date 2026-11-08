"""Generator for 836938f29751: fill the rectangle marked by four corners.

The input contains exactly four equal-colour cells at the corners of one
axis-aligned rectangle.  The authoritative Racket rule paints every cell in
that bounding rectangle with the marker colour on a fresh zero canvas.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "836938f29751"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c51a915c15a5"

SUMMARY = (
    "On a zero-background grid, exactly four equal-colour cells mark the four "
    "corners of one axis-aligned rectangle. Fill the complete bounding "
    "rectangle, including its interior, with that colour on a fresh zero "
    "canvas of the same dimensions."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is rectangular, uses ARC colours 0..9, and background is 0",
    "exactly four non-zero cells share one colour",
    "the four cells occupy exactly two rows and two columns and realize all four cross-products",
    "the marked rectangle is at least 4x4, so outline and solid-fill answers differ",
    "the rectangle never covers the whole grid, so full-grid fill is visibly wrong",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical-weighted", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "scheduled canonical-weighted", "valid": "8..14"},
    "rect_h": {"type": "int", "default": "scheduled 4..6", "valid": "4..6"},
    "rect_w": {"type": "int", "default": "scheduled 4..7", "valid": "4..7"},
    "color": {"type": "color", "default": "scheduled canonical-weighted", "valid": "1..9"},
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# Four consecutive sample indices always contain border and interior placements,
# multiple rectangle sizes, and multiple colours.  The dimensions/palettes are
# canonical profiles, so every difficulty band remains anchored to the source.
_PROFILES = (
    {"name": "canonical_top_left", "h": 7, "w": 9, "rh": 5, "rw": 4, "color": 7, "anchor": "border"},
    {"name": "canonical_interior", "h": 8, "w": 8, "rh": 5, "rw": 5, "color": 3, "anchor": "interior"},
    {"name": "canonical_bottom_right", "h": 9, "w": 9, "rh": 6, "rw": 5, "color": 5, "anchor": "border"},
    {"name": "canonical_wide_interior", "h": 6, "w": 10, "rh": 4, "rw": 5, "color": 2, "anchor": "interior"},
    {"name": "canonical_test_profile", "h": 8, "w": 10, "rh": 5, "rw": 7, "color": 4, "anchor": "border"},
    {"name": "small_interior", "h": 10, "w": 12, "rh": 4, "rw": 6, "color": 1, "anchor": "interior"},
    {"name": "large_border", "h": 11, "w": 13, "rh": 6, "rw": 7, "color": 9, "anchor": "border"},
    {"name": "compact_interior", "h": 7, "w": 11, "rh": 4, "rw": 4, "color": 6, "anchor": "interior"},
    {"name": "large_canvas_border", "h": 12, "w": 14, "rh": 5, "rw": 6, "color": 8, "anchor": "border"},
    {"name": "wide_interior", "h": 9, "w": 12, "rh": 4, "rw": 7, "color": 2, "anchor": "interior"},
    {"name": "tall_border", "h": 10, "w": 10, "rh": 6, "rw": 4, "color": 5, "anchor": "border"},
    {"name": "medium_interior", "h": 8, "w": 13, "rh": 4, "rw": 6, "color": 3, "anchor": "interior"},
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[int(sample_index) % len(_PROFILES)]["name"]


def _draw_exact_int(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 12:
        errors.append(f"grid height must be in 6..12, found {height}")
    if not 8 <= width <= 14:
        errors.append(f"grid width must be in 8..14, found {width}")

    markers = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if len(markers) != 4:
        errors.append(f"expected exactly 4 non-zero corner markers, found {len(markers)}")
        return {"errors": errors, "height": height, "width": width, "markers": markers}
    colors = {v for _, _, v in markers}
    if len(colors) != 1:
        errors.append(f"corner markers must share one colour, found {sorted(colors)}")
    rows = sorted({r for r, _, _ in markers})
    cols = sorted({c for _, c, _ in markers})
    if len(rows) != 2 or len(cols) != 2:
        errors.append("markers must occupy exactly two rows and two columns")
        return {"errors": errors, "height": height, "width": width, "markers": markers}
    wanted = {(rows[0], cols[0]), (rows[0], cols[1]), (rows[1], cols[0]), (rows[1], cols[1])}
    got = {(r, c) for r, c, _ in markers}
    if got != wanted:
        errors.append("markers are not exactly the four rectangle corners")
    rect_h = rows[1] - rows[0] + 1
    rect_w = cols[1] - cols[0] + 1
    if not 4 <= rect_h <= 6:
        errors.append(f"rectangle height must be in 4..6, found {rect_h}")
    if not 4 <= rect_w <= 7:
        errors.append(f"rectangle width must be in 4..7, found {rect_w}")
    if rect_h == height and rect_w == width:
        errors.append("rectangle may not cover the entire grid")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "markers": markers,
        "color": next(iter(colors)) if len(colors) == 1 else None,
        "top": rows[0],
        "left": cols[0],
        "bottom": rows[1],
        "right": cols[1],
        "rect_h": rect_h,
        "rect_w": rect_w,
        "touches_border": rows[0] == 0 or cols[0] == 0 or rows[1] == height - 1 or cols[1] == width - 1,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rect_h": analysis["rect_h"],
        "rect_w": analysis["rect_w"],
        "color": analysis["color"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid corner-rectangle grid: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row in range(analysis["top"], analysis["bottom"] + 1):
        for col in range(analysis["left"], analysis["right"] + 1):
            output[row][col] = analysis["color"]
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_outline(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row in range(analysis["top"], analysis["bottom"] + 1):
        for col in range(analysis["left"], analysis["right"] + 1):
            if row in (analysis["top"], analysis["bottom"]) or col in (analysis["left"], analysis["right"]):
                output[row][col] = analysis["color"]
    return output


def _rival_full_grid(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return full_grid(analysis["height"], analysis["width"], analysis["color"])


def _rival_fixed_5x5(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    if analysis["top"] + 4 >= analysis["height"] or analysis["left"] + 4 >= analysis["width"]:
        return _rival_identity(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row in range(analysis["top"], analysis["top"] + 5):
        for col in range(analysis["left"], analysis["left"] + 5):
            output[row][col] = analysis["color"]
    return output


def _rival_ignore_border_rectangles(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["touches_border"]:
        return _rival_identity(grid)
    return rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "marker_as_answer": _rival_identity,
    "outline_only": _rival_outline,
    "fill_entire_grid": _rival_full_grid,
    "fixed_5x5_from_top_left": _rival_fixed_5x5,
    "ignore_border_rectangles": _rival_ignore_border_rectangles,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"fixed_5x5_from_top_left": _rival_fixed_5x5}


def _witness_solid_interior(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["rect_h"] >= 4 and analysis["rect_w"] >= 4


def _witness_background_outside(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["rect_h"] * analysis["rect_w"] < analysis["height"] * analysis["width"]


def _witness_border_position(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["touches_border"]


def _witness_non_5x5(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and (analysis["rect_h"], analysis["rect_w"]) != (5, 5)


SEMANTIC_WITNESSES = {
    "solid_interior_refutes_outline": _witness_solid_interior,
    "outside_background_refutes_full_grid": _witness_background_outside,
    "border_position_refutes_fixed_interior": _witness_border_position,
    "non_5x5_refutes_fixed_size": _witness_non_5x5,
}
WITNESS_RIVALS = {
    "solid_interior_refutes_outline": ["marker_as_answer", "outline_only"],
    "outside_background_refutes_full_grid": ["fill_entire_grid"],
    "border_position_refutes_fixed_interior": ["ignore_border_rectangles"],
    "non_5x5_refutes_fixed_size": ["fixed_5x5_from_top_left"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
    sizes: set[tuple[int, int]] = set()
    colors: set[int] = set()
    saw_border = False
    saw_interior = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output does not match solid bounding-rectangle fill")
        sizes.add((analysis["rect_h"], analysis["rect_w"]))
        colors.add(analysis["color"])
        saw_border |= analysis["touches_border"]
        saw_interior |= not analysis["touches_border"]
    if len(sizes) < 2:
        reasons.append("demonstrations do not refute a fixed rectangle-size shortcut")
    if len(colors) < 2:
        reasons.append("demonstrations do not show that marker colour is arbitrary")
    if not saw_border or not saw_interior:
        reasons.append("demonstrations must include both border-touching and interior rectangles")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos if isinstance(demo, dict) and "input" in demo and "output" in demo):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _choose_anchor(rng, profile_anchor: str, height: int, width: int, rect_h: int, rect_w: int) -> tuple[int, int]:
    max_top = height - rect_h
    max_left = width - rect_w
    interior = [(r, c) for r in range(1, max_top) for c in range(1, max_left)]
    border = [
        (r, c)
        for r in range(max_top + 1)
        for c in range(max_left + 1)
        if r in (0, max_top) or c in (0, max_left)
    ]
    if profile_anchor == "interior" and interior:
        return rng.choice(interior)
    if border:
        return rng.choice(border)
    return rng.randint(0, max_top), rng.randint(0, max_left)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, value in overrides.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer, got {value!r}")

    profile = _PROFILES[int(sample_index) % len(_PROFILES)]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_exact_int(ctx, overrides, "grid_h", profile["h"], 6, 12)
    width = _draw_exact_int(ctx, overrides, "grid_w", profile["w"], 8, 14)
    rect_h = _draw_exact_int(ctx, overrides, "rect_h", profile["rh"], 4, 6)
    rect_w = _draw_exact_int(ctx, overrides, "rect_w", profile["rw"], 4, 7)
    color = _draw_exact_int(ctx, overrides, "color", profile["color"], 1, 9)

    rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    top, left = _choose_anchor(rng, profile["anchor"], height, width, rect_h, rect_w)
    bottom, right = top + rect_h - 1, left + rect_w - 1
    grid = full_grid(height, width, 0)
    grid[top][left] = color
    grid[top][right] = color
    grid[bottom][left] = color
    grid[bottom][right] = color
    return grid
