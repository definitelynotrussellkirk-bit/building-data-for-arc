"""Generator for ARC task f65705efd235: rectangle borders from corner quads.

Each nonzero color appears at exactly the four corners of one axis-aligned
rectangle.  The answer starts from an all-zero canvas and paints every complete
rectangle border in ascending color order.  Later (larger) colors therefore
win where borders overlap, matching the selected canonical Racket authority.

The four-position curriculum deliberately contains:

* a two-cell-thick canonical rectangle (a real canonical subcase omitted by
  the previous generator),
* a thick hollow rectangle, so outline and fill are distinguishable,
* overlapping borders, so color order is observable, and
* both two-rectangle and >2-rectangle scenes, so a fixed-two shortcut fails.
"""
from __future__ import annotations

import copy
from itertools import combinations
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f65705efd235"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "635fcfe4fd6f"

SUMMARY = (
    "A 7..24 by 7..24 zero-background grid contains 2..6 distinct nonzero "
    "colors. Each color occupies exactly the four corners of one axis-aligned "
    "rectangle. Draw every full rectangle border on a fresh zero canvas in "
    "ascending color order; larger colors overwrite smaller colors where "
    "borders cross. The scheduled curriculum includes canonical two-cell-wide "
    "rectangles, hollow interiors, overlapping outlines, and >2 colors."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "the grid is rectangular, uses literal ARC colors 0..9, and is 7..24 in each dimension",
    "there are exactly 2..6 distinct nonzero colors",
    "each nonzero color appears exactly four times at the Cartesian product of two rows and two columns",
    "no rectangle is 2x2, so every corner quad expands by at least one non-corner border cell",
    "corner cells belonging to different colors never collide",
    "every scheduled scene contains a thin canonical rectangle, a thick rectangle, and overlapping borders",
    "every three consecutive schedule positions contain a scene with more than two rectangles",
]

# Honest caller-facing controls.  Palette, placement, orientation, and color
# order are keyed local variation rather than pretend overrides.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile difficulty schedule",
        "valid": "7..24",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile difficulty schedule",
        "valid": "7..24",
    },
    "n_rects": {
        "type": "int",
        "default": "four-profile difficulty schedule",
        "valid": "2..6",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

SCHEDULE_PROFILES = (0, 1, 2, 3)
_DIFFICULTIES = (None, "easy", "medium", "hard")
_PROFILE_VALUES: dict[str | None, tuple[tuple[int, int, int], ...]] = {
    # Exact canonical profiles occur frequently, but the other positions keep
    # the previous scale curriculum and force dynamic object counts.
    None: (
        (9, 10, 2),
        (12, 13, 3),
        (10, 16, 2),
        (14, 12, 4),
    ),
    "easy": (
        (8, 8, 2),
        (9, 9, 3),
        (7, 10, 2),
        (8, 9, 4),
    ),
    "medium": (
        (9, 10, 2),
        (12, 13, 3),
        (10, 16, 2),
        (14, 12, 4),
    ),
    "hard": (
        (9, 10, 2),
        (16, 18, 5),
        (14, 14, 2),
        (20, 24, 6),
    ),
}

_CANONICAL_PROFILES = {
    (8, 8, 2),
    (9, 9, 2),
    (7, 10, 2),
    (8, 9, 2),
    (9, 10, 2),
}

Rect = tuple[int, int, int, int]
Grid = list[list[int]]


def _strict_int(name: str, value: Any, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, found {type(value).__name__}")
    if not lo <= value <= hi:
        raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    return value


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        lo, hi = (2, 6) if name == "n_rects" else (7, 24)
        _strict_int(name, value, lo, hi)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic four-position curriculum profile."""
    del seed
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    if isinstance(sample_index, bool) or not isinstance(sample_index, int):
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, name: str, scheduled: int, lo: int, hi: int) -> int:
    """Record a schedule value honestly while keeping all overrides reachable."""
    if name in ctx.overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _rect_corners(rect: Rect) -> tuple[tuple[int, int], ...]:
    r0, c0, r1, c1 = rect
    return ((r0, c0), (r0, c1), (r1, c0), (r1, c1))


def _border_cells(rect: Rect) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = rect
    cells = {(r0, c) for c in range(c0, c1 + 1)}
    cells.update((r1, c) for c in range(c0, c1 + 1))
    cells.update((r, c0) for r in range(r0 + 1, r1))
    cells.update((r, c1) for r in range(r0 + 1, r1))
    return cells


def _transform_rect(
    rect: Rect, height: int, width: int, *, flip_rows: bool, flip_cols: bool
) -> Rect:
    r0, c0, r1, c1 = rect
    if flip_rows:
        r0, r1 = height - 1 - r1, height - 1 - r0
    if flip_cols:
        c0, c1 = width - 1 - c1, width - 1 - c0
    return r0, c0, r1, c1


def _teaching_pair(height: int, width: int, rng) -> list[Rect]:
    """Return a thin border-touching rectangle crossing a thick interior one."""
    if rng.randrange(2) == 0:
        # Width two is canonical: adjacent corner columns still define a real
        # rectangle.  Its lower edge crosses the thick rectangle's border.
        rects: list[Rect] = [
            (0, 2, height - 2, 3),
            (1, 1, height - 2, width - 2),
        ]
    else:
        rects = [
            (2, 0, 3, width - 2),
            (1, 1, height - 2, width - 2),
        ]
    flip_rows = bool(rng.randrange(2))
    flip_cols = bool(rng.randrange(2))
    return [
        _transform_rect(
            rect, height, width, flip_rows=flip_rows, flip_cols=flip_cols
        )
        for rect in rects
    ]


def _candidate_rect(rng, height: int, width: int) -> Rect:
    r0, r1 = sorted(rng.sample(range(height), 2))
    c0, c1 = sorted(rng.sample(range(width), 2))
    return r0, c0, r1, c1


def _protected_hollow_cell(rects: Sequence[Rect]) -> tuple[int, int]:
    """Pick one thick-rectangle interior cell no teaching border touches.

    Keeping this cell off every later border guarantees a visible background
    counterexample to the tempting solid-fill rule, even in crowded scenes.
    """
    thin, thick = rects[:2]
    r0, c0, r1, c1 = thick
    candidates = sorted(
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if (r, c) not in _border_cells(thin)
    )
    if not candidates:
        raise AssertionError("teaching pair has no protected hollow interior cell")
    return candidates[len(candidates) // 2]


def _usable_rect(
    rect: Rect,
    used_corners: set[tuple[int, int]],
    seen: set[Rect],
    protected_hollow: tuple[int, int],
) -> bool:
    r0, c0, r1, c1 = rect
    if rect in seen:
        return False
    if (r1 - r0 == 1) and (c1 - c0 == 1):
        return False  # a 2x2 outline adds nothing beyond the four corners
    if protected_hollow in _border_cells(rect):
        return False
    return not any(cell in used_corners for cell in _rect_corners(rect))


def _exhaustive_extra_rect(
    height: int,
    width: int,
    used_corners: set[tuple[int, int]],
    seen: set[Rect],
    protected_hollow: tuple[int, int],
    offset: int,
) -> Rect | None:
    """Deterministic no-under-delivery fallback after random placement attempts."""
    row_pairs = list(combinations(range(height), 2))
    col_pairs = list(combinations(range(width), 2))
    total = len(row_pairs) * len(col_pairs)
    if not total:
        return None
    start = offset % total
    for step in range(total):
        flat = (start + step) % total
        rp = row_pairs[flat // len(col_pairs)]
        cp = col_pairs[flat % len(col_pairs)]
        rect = (rp[0], cp[0], rp[1], cp[1])
        if _usable_rect(rect, used_corners, seen, protected_hollow):
            return rect
    return None


def _place_rectangles(height: int, width: int, count: int, rng) -> list[Rect]:
    rects = _teaching_pair(height, width, rng)
    protected_hollow = _protected_hollow_cell(rects)
    used_corners = set().union(*(_rect_corners(rect) for rect in rects))
    seen = set(rects)

    while len(rects) < count:
        selected: Rect | None = None
        for _ in range(5000):
            candidate = _candidate_rect(rng, height, width)
            if _usable_rect(candidate, used_corners, seen, protected_hollow):
                selected = candidate
                break
        if selected is None:
            selected = _exhaustive_extra_rect(
                height,
                width,
                used_corners,
                seen,
                protected_hollow,
                offset=rng.randrange(max(1, height * width * height * width)),
            )
        if selected is None:
            raise RuntimeError(
                f"could not place {count} corner-disjoint rectangles on {height}x{width}"
            )
        rects.append(selected)
        seen.add(selected)
        used_corners.update(_rect_corners(selected))
    return rects


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_request(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_n = _PROFILE_VALUES[difficulty][profile]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, "grid_h", scheduled_h, 7, 24)
    width = _draw_scheduled_int(ctx, "grid_w", scheduled_w, 7, 24)
    n_rects = _draw_scheduled_int(ctx, "n_rects", scheduled_n, 2, 6)

    layout_rng = ctx.draw_rng("rectangle_layout")
    rects = _place_rectangles(height, width, n_rects, layout_rng)
    colors = list(ctx.draw_distinct_colors("rectangle_colors", n=n_rects, exclude={0}))

    grid = full_grid(height, width, 0)
    for color, rect in zip(colors, rects):
        for r, c in _rect_corners(rect):
            if grid[r][c] != 0:  # construction bug, never a recoverable branch
                raise AssertionError(f"corner collision at {(r, c)}")
            grid[r][c] = color

    findings = self_check(grid, meta={"overrides": overrides})
    if findings:
        raise AssertionError("generated invalid scene: " + "; ".join(findings))
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Executable grammar and Python rule mirror
# ---------------------------------------------------------------------------


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "rectangles": []}

    height, width = len(grid), len(grid[0])
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                by_color.setdefault(color, []).append((r, c))

    rectangles: list[dict[str, Any]] = []
    for color in sorted(by_color):
        points = by_color[color]
        if len(points) != 4:
            errors.append(f"color {color} must appear exactly 4 times, found {len(points)}")
            continue
        rows = sorted({r for r, _ in points})
        cols = sorted({c for _, c in points})
        if len(rows) != 2 or len(cols) != 2:
            errors.append(
                f"color {color} must occupy exactly two rows and two columns, "
                f"found rows={rows}, cols={cols}"
            )
            continue
        expected = {(r, c) for r in rows for c in cols}
        if set(points) != expected:
            errors.append(f"color {color} does not occupy all four rectangle corners")
            continue
        rect = (rows[0], cols[0], rows[1], cols[1])
        rect_h = rows[1] - rows[0] + 1
        rect_w = cols[1] - cols[0] + 1
        border = _border_cells(rect)
        interior = {
            (r, c)
            for r in range(rows[0] + 1, rows[1])
            for c in range(cols[0] + 1, cols[1])
        }
        rectangles.append(
            {
                "color": color,
                "corners": tuple(sorted(expected)),
                "rows": tuple(rows),
                "cols": tuple(cols),
                "bbox": rect,
                "rect_h": rect_h,
                "rect_w": rect_w,
                "border": border,
                "interior": interior,
                "touches_border": (
                    rows[0] == 0
                    or cols[0] == 0
                    or rows[1] == height - 1
                    or cols[1] == width - 1
                ),
            }
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "colors": sorted(by_color),
        "rectangles": rectangles,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or lesson-hiding scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors and "height" not in analysis:
        return errors

    height, width = analysis["height"], analysis["width"]
    if not 7 <= height <= 24 or not 7 <= width <= 24:
        errors.append(f"grid dimensions must each be in 7..24, found {height}x{width}")

    n_rects = len(analysis["colors"])
    if not 2 <= n_rects <= 6:
        errors.append(f"expected 2..6 distinct nonzero colors, found {n_rects}")

    for rect in analysis["rectangles"]:
        if rect["rect_h"] == 2 and rect["rect_w"] == 2:
            errors.append(
                f"color {rect['color']} forms a 2x2 rectangle whose border is only its corners"
            )
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must remain visible")

    requested = _meta_overrides(meta)
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, wanted in requested.items():
            if name in AXES and observed.get(name) != wanted:
                errors.append(
                    f"override {name}={wanted!r} was not realized; observed "
                    f"{observed.get(name)!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid rectangle-corner grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_rects": len(analysis["rectangles"]),
    }


def _paint_borders(grid: Sequence[Sequence[int]], colors: Iterable[int]) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid rectangle-corner grid: " + "; ".join(analysis["errors"]))
    by_color = {rect["color"]: rect for rect in analysis["rectangles"]}
    output = full_grid(analysis["height"], analysis["width"], 0)
    for color in colors:
        rect = by_color.get(color)
        if rect is None:
            continue
        for r, c in rect["border"]:
            output[r][c] = color
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror; canonical Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid rectangle-corner grid: " + "; ".join(analysis["errors"]))
    return _paint_borders(grid, sorted(analysis["colors"]))


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    profile = (observed["grid_h"], observed["grid_w"], observed["n_rects"])
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside the five canonical input profiles"]
    return []


# ---------------------------------------------------------------------------
# Plausible wrong rules and their explicit counterexamples
# ---------------------------------------------------------------------------


def _rival_corners_only(grid):
    return [list(row) for row in grid]


def _rival_fill_rectangles(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid rectangle-corner grid")
    output = full_grid(analysis["height"], analysis["width"], 0)
    for rect in analysis["rectangles"]:  # sorted ascending by color
        r0, c0, r1, c1 = rect["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = rect["color"]
    return output


def _rival_first_two_colors(grid):
    analysis = _analysis(grid)
    return _paint_borders(grid, sorted(analysis["colors"])[:2])


def _rival_reverse_color_order(grid):
    analysis = _analysis(grid)
    return _paint_borders(grid, sorted(analysis["colors"], reverse=True))


def _rival_ignore_thin_rectangles(grid):
    analysis = _analysis(grid)
    keep = [
        rect["color"]
        for rect in analysis["rectangles"]
        if rect["rect_h"] > 2 and rect["rect_w"] > 2
    ]
    return _paint_borders(grid, sorted(keep))


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "keep_only_the_four_corners": _rival_corners_only,
    "fill_each_rectangle_solid": _rival_fill_rectangles,
    "process_only_two_colors": _rival_first_two_colors,
    "paint_colors_in_reverse_order": _rival_reverse_color_order,
    "ignore_two_cell_thick_rectangles": _rival_ignore_thin_rectangles,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# These two wrong rules fit every canonical demonstration: all canonical inputs
# have exactly two colors, and their rectangle borders never overlap.  The
# generated curriculum supplies the missing counterexamples.
CANONICAL_SHORTCUTS = {
    "process_only_two_colors": _rival_first_two_colors,
    "paint_colors_in_reverse_order": _rival_reverse_color_order,
}


def _lawful_analysis(grid) -> dict[str, Any] | None:
    if self_check(grid):
        return None
    return _analysis(grid)


def _witness_outline_adds_cells(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(
        analysis
        and any(len(rect["border"]) > 4 for rect in analysis["rectangles"])
        and _rival_corners_only(grid) != rule_mirror(grid)
    )


def _witness_hollow_interior(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(
        analysis
        and any(rect["interior"] for rect in analysis["rectangles"])
        and _rival_fill_rectangles(grid) != rule_mirror(grid)
    )


def _witness_more_than_two_rectangles(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(
        analysis
        and len(analysis["rectangles"]) > 2
        and _rival_first_two_colors(grid) != rule_mirror(grid)
    )


def _witness_overlap_order(grid) -> bool:
    analysis = _lawful_analysis(grid)
    if not analysis:
        return False
    rectangles = analysis["rectangles"]
    overlap = any(
        rectangles[i]["border"] & rectangles[j]["border"]
        for i in range(len(rectangles))
        for j in range(i + 1, len(rectangles))
    )
    return bool(overlap and _rival_reverse_color_order(grid) != rule_mirror(grid))


def _witness_thin_rectangle(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(
        analysis
        and any(
            rect["rect_h"] == 2 or rect["rect_w"] == 2
            for rect in analysis["rectangles"]
        )
        and _rival_ignore_thin_rectangles(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "outline_adds_noncorner_cells": _witness_outline_adds_cells,
    "strict_interior_stays_background": _witness_hollow_interior,
    "more_than_two_rectangles": _witness_more_than_two_rectangles,
    "overlap_exposes_ascending_color_order": _witness_overlap_order,
    "two_cell_thick_rectangle_is_lawful": _witness_thin_rectangle,
}
WITNESS_RIVALS = {
    "outline_adds_noncorner_cells": ["keep_only_the_four_corners"],
    "strict_interior_stays_background": ["fill_each_rectangle_solid"],
    "more_than_two_rectangles": ["process_only_two_colors"],
    "overlap_exposes_ascending_color_order": ["paint_colors_in_reverse_order"],
    "two_cell_thick_rectangle_is_lawful": ["ignore_two_cell_thick_rectangles"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to falsify every registered plausible rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is outside the rule domain: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the rectangle-border rule")
        else:
            valid_demos.append(pair)

    try:
        query_expected = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query input is outside the rule domain: {exc}")
        return reasons
    if "output" in query and query["output"] != query_expected:
        reasons.append("query output disagrees with the rectangle-border rule")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Named malformed scenes used by focused and future-agent probes."""
    valid = generate(7001, 1, difficulty="medium", grid_h=9, grid_w=10, n_rects=2)
    analysis = _analysis(valid)
    rect = analysis["rectangles"][0]
    color = rect["color"]
    fixtures: list[tuple[str, Grid]] = []

    missing_corner = copy.deepcopy(valid)
    r, c = rect["corners"][0]
    missing_corner[r][c] = 0
    fixtures.append(("missing_corner", missing_corner))

    fifth_cell = copy.deepcopy(valid)
    spot = next(
        (r, c)
        for r in range(len(fifth_cell))
        for c in range(len(fifth_cell[0]))
        if fifth_cell[r][c] == 0
    )
    fifth_cell[spot[0]][spot[1]] = color
    fixtures.append(("fifth_same_color_cell", fifth_cell))

    non_corner_quad = copy.deepcopy(valid)
    old_r, old_c = rect["corners"][0]
    non_corner_quad[old_r][old_c] = 0
    spot = next(
        (r, c)
        for r in range(len(non_corner_quad))
        for c in range(len(non_corner_quad[0]))
        if non_corner_quad[r][c] == 0
        and r not in rect["rows"]
        and c not in rect["cols"]
    )
    non_corner_quad[spot[0]][spot[1]] = color
    fixtures.append(("non_rectangular_quad", non_corner_quad))
    return fixtures
