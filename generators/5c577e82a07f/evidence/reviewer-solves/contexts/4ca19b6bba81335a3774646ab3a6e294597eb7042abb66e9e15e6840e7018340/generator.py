"""Semantic generator for ARC task ``5c577e82a07f``.

Every nonzero color marks exactly the four corners of one axis-aligned
rectangle.  The output completes the whole border of every rectangle while
leaving rectangle interiors and the zero background unchanged.

The ordinary three-example schedule deliberately cycles through fully thick,
thin-horizontal, and thin-vertical rectangles.  Easy and medium lessons also
schedule one three-color scene in every three-example window.  Together those choices
make both the full-border rule and its all-colors scope identifiable even
though the canonical examples contain no thin-horizontal rectangle and never
contain a third color.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5c577e82a07f"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "486ca16c83e1"
MIN_STRICT_FRAC = 0.08
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 7..15 by 9..18 zero-background grid contains two or three distinct "
    "colors.  Each color appears exactly four times at the Cartesian corners "
    "of one axis-aligned rectangle.  Complete every rectangle's full border "
    "in its own color; preserve all rectangle interiors and all other cells."
)

INVARIANTS = [
    "background is 0 and every foreground color is in 1..9",
    "there are exactly 2 or 3 foreground colors and each occurs at four corners",
    "the four cells of each color are exactly two rows crossed with exactly two columns",
    "different rectangle borders never intersect",
    "every ordinary scene contains a thick rectangle with a nonempty interior",
]

COUNTER_HYPOTHESES = [
    "return the input unchanged",
    "fill each rectangle's entire bounding box",
    "complete only the top and bottom edges",
    "complete only the left and right edges",
    "complete only the first or lowest-colored rectangle",
    "complete only the first two or two lowest-colored rectangles",
    "ignore rectangles that are exactly two cells high",
    "ignore rectangles that are exactly two cells wide",
]

PALETTE_KINDS = ("even", "odd", "mixed")
GEOMETRY_PROFILES = ("thick_only", "with_thin_horizontal", "with_thin_vertical")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = GEOMETRY_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 7..15",
        "valid": "7..15",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 9..18",
        "valid": "9..18",
    },
    "n_rects": {
        "type": "int",
        "default": "one scheduled 3 in every easy/medium 3-window; 3 on hard",
        "valid": "2..3",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng even|odd|mixed",
        "valid": "even|odd|mixed",
    },
    "geometry_profile": {
        "type": "str",
        "default": "sample_index cycle across all three profiles",
        "valid": "thick_only|with_thin_horizontal|with_thin_vertical",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# Exact canonical inputs in train-then-test order.  Keeping them local makes
# strict-canonical anchoring auditable without importing mutable shared data.
_CANONICAL_SPECS = (
    (8, 10, ((6, 1, 1, 4, 4), (3, 2, 6, 6, 8))),
    (9, 11, ((6, 1, 2, 5, 7), (8, 6, 0, 8, 3))),
    (7, 9, ((4, 0, 0, 3, 5), (2, 2, 7, 6, 8))),
    (9, 12, ((6, 1, 1, 5, 5), (7, 3, 8, 7, 10))),
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
    int_bounds = {"grid_h": (7, 15), "grid_w": (9, 18), "n_rects": (2, 3)}
    enum_values = {
        "palette_kind": set(PALETTE_KINDS),
        "geometry_profile": set(GEOMETRY_PROFILES),
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
        elif not isinstance(value, str):
            raise TypeError(f"override {name!r} must be a string")
        elif value not in enum_values[name]:
            raise ValueError(
                f"override {name!r}={value!r} not in {sorted(enum_values[name])}"
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Any three consecutive sample indexes expose all rectangle geometries."""
    del seed, difficulty
    return GEOMETRY_PROFILES[sample_index % len(GEOMETRY_PROFILES)]


def schedule_n_rects(seed: int, sample_index: int, difficulty=None) -> int:
    """Keep every ordinary medium three-demo window decisive about color scope.

    Canonical anchors occur only when ``(seed + sample_index) % 6 == 0``.
    Scheduling the three-color scene at residue 1 therefore guarantees that an
    anchor never replaces the sole three-color counterexample in a window.
    """
    band = _validate_difficulty(difficulty)
    if band == "hard":
        return 3
    return 3 if (seed + sample_index) % 3 == 1 else 2


def _grid_from_spec(spec) -> list[list[int]]:
    h, w, rectangles = spec
    grid = full_grid(h, w, 0)
    for color, r0, c0, r1, c1 in rectangles:
        for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
            grid[r][c] = color
    return grid


_CANONICAL_INPUTS = tuple(_grid_from_spec(spec) for spec in _CANONICAL_SPECS)


def _grid_errors(grid: Any) -> list[str]:
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
    return errors


def _border_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, r1, c0, c1 = box
    cells = {(r0, c) for c in range(c0, c1 + 1)}
    cells.update((r1, c) for c in range(c0, c1 + 1))
    cells.update((r, c0) for r in range(r0, r1 + 1))
    cells.update((r, c1) for r in range(r0, r1 + 1))
    return cells


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    h, w = len(grid), len(grid[0])
    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color[value].append((r, c))

    rectangles: list[dict[str, Any]] = []
    for color in sorted(by_color):
        cells = by_color[color]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        box = None
        complete_corners = False
        border: set[tuple[int, int]] = set()
        if len(rows) == 2 and len(cols) == 2:
            box = (rows[0], rows[1], cols[0], cols[1])
            complete_corners = set(cells) == {
                (rows[0], cols[0]), (rows[0], cols[1]),
                (rows[1], cols[0]), (rows[1], cols[1]),
            }
            border = _border_cells(box)
        rectangles.append(
            {
                "color": color,
                "cells": tuple(cells),
                "cell_count": len(cells),
                "rows": tuple(rows),
                "cols": tuple(cols),
                "box": box,
                "height": (rows[1] - rows[0] + 1) if len(rows) == 2 else None,
                "width": (cols[1] - cols[0] + 1) if len(cols) == 2 else None,
                "complete_corners": complete_corners,
                "border": border,
            }
        )

    border_overlaps: list[tuple[int, int, tuple[int, int]]] = []
    for i, left in enumerate(rectangles):
        for right in rectangles[i + 1:]:
            for cell in sorted(left["border"] & right["border"]):
                border_overlaps.append((left["color"], right["color"], cell))

    colors = sorted(by_color)
    all_even = bool(colors) and all(color % 2 == 0 for color in colors)
    all_odd = bool(colors) and all(color % 2 == 1 for color in colors)
    palette_kind = "even" if all_even else "odd" if all_odd else "mixed"

    valid_rectangles = [
        rect for rect in rectangles
        if rect["cell_count"] == 4 and rect["complete_corners"]
    ]
    thin_h = sum(rect["height"] == 2 and (rect["width"] or 0) >= 3 for rect in valid_rectangles)
    thin_v = sum(rect["width"] == 2 and (rect["height"] or 0) >= 3 for rect in valid_rectangles)
    thick = sum((rect["height"] or 0) >= 3 and (rect["width"] or 0) >= 3 for rect in valid_rectangles)
    no_op = sum(rect["height"] == 2 and rect["width"] == 2 for rect in valid_rectangles)
    if thin_h == 1 and thin_v == 0 and thick == len(valid_rectangles) - 1:
        geometry_profile = "with_thin_horizontal"
    elif thin_v == 1 and thin_h == 0 and thick == len(valid_rectangles) - 1:
        geometry_profile = "with_thin_vertical"
    elif thin_h == 0 and thin_v == 0 and thick == len(valid_rectangles):
        geometry_profile = "thick_only"
    else:
        geometry_profile = "other"

    result.update(
        {
            "height": h,
            "width": w,
            "colors": tuple(colors),
            "n_rects": len(colors),
            "palette_kind": palette_kind,
            "rectangles": rectangles,
            "border_overlaps": tuple(border_overlaps),
            "thick_count": thick,
            "thin_horizontal_count": thin_h,
            "thin_vertical_count": thin_v,
            "noop_2x2_count": no_op,
            "geometry_profile": geometry_profile,
            "added_border_cells": sum(max(0, len(rect["border"]) - 4) for rect in valid_rectangles),
        }
    )
    return result


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return ("invalid", tuple(facts["errors"]))
    return (
        facts["height"], facts["width"], facts["n_rects"],
        facts["palette_kind"], facts["geometry_profile"],
        tuple(
            (rect["height"], rect["width"], rect["color"])
            for rect in facts["rectangles"]
        ),
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full teaching distribution and every canonical input."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors
    h, w = facts["height"], facts["width"]
    if not 7 <= h <= 15 or not 9 <= w <= 18:
        errors.append(f"grid must be within 7..15 by 9..18, found {h}x{w}")
    if not 2 <= facts["n_rects"] <= 3:
        errors.append(f"expected 2 or 3 distinct rectangle colors, found {facts['n_rects']}")
    for rect in facts["rectangles"]:
        color = rect["color"]
        if rect["cell_count"] != 4:
            errors.append(f"color {color} has {rect['cell_count']} cells, expected exactly 4")
            continue
        if not rect["complete_corners"]:
            errors.append(f"color {color} is not the Cartesian product of two rows and two columns")
            continue
        if rect["height"] == 2 and rect["width"] == 2:
            errors.append(f"color {color} forms a 2x2 no-op border; teaching scenes must require completion")
    if facts["border_overlaps"]:
        errors.append("rectangle borders intersect, making color ownership ambiguous")
    if facts["geometry_profile"] not in GEOMETRY_PROFILES:
        errors.append(
            "scene must be thick-only or contain exactly one horizontal/vertical thin rectangle"
        )
    if facts["thick_count"] < 1:
        errors.append("scene must include at least one thick rectangle with an interior")
    if facts["added_border_cells"] <= 0:
        errors.append("scene is a no-op; at least one border cell must be added")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    normalized = [list(row) for row in grid]
    if normalized not in _CANONICAL_INPUTS:
        reasons.append("input is not one of the four exact canonical train/test inputs")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_rects": facts["n_rects"],
        "palette_kind": facts["palette_kind"],
        "geometry_profile": facts["geometry_profile"],
    }


def _palette(kind: str, n: int, rng) -> tuple[int, ...]:
    evens = [2, 4, 6, 8]
    odds = [1, 3, 5, 7, 9]
    if kind == "even":
        return tuple(rng.sample(evens, n))
    if kind == "odd":
        return tuple(rng.sample(odds, n))
    # Guarantee that the mixed category is observable rather than merely likely.
    colors = [rng.choice(evens), rng.choice(odds)]
    remaining = [c for c in range(1, 10) if c not in colors]
    if n == 3:
        colors.append(rng.choice(remaining))
    rng.shuffle(colors)
    return tuple(colors)


def _slots(h: int, w: int) -> tuple[tuple[int, int, int, int], ...]:
    gap_r, gap_c = h // 2, w // 2
    return (
        (0, gap_r - 1, 0, gap_c - 1),
        (0, gap_r - 1, gap_c + 1, w - 1),
        (gap_r + 1, h - 1, 0, gap_c - 1),
        (gap_r + 1, h - 1, gap_c + 1, w - 1),
    )


def _sample_box(slot, kind: str, rng) -> tuple[int, int, int, int]:
    sr0, sr1, sc0, sc1 = slot
    slot_h, slot_w = sr1 - sr0 + 1, sc1 - sc0 + 1
    if kind == "thin_horizontal":
        rh, rw = 2, rng.randint(3, slot_w)
    elif kind == "thin_vertical":
        rh, rw = rng.randint(3, slot_h), 2
    else:
        rh, rw = rng.randint(3, slot_h), rng.randint(3, slot_w)
    r0 = rng.randint(sr0, sr1 - rh + 1)
    c0 = rng.randint(sc0, sc1 - rw + 1)
    return r0, r0 + rh - 1, c0, c0 + rw - 1


def _canonical_anchor(seed: int, sample_index: int, band: str):
    del band
    # About 1/9 of all draws are exact anchors, split across thick and
    # thin-vertical profiles.  The seed-dependent ticket avoids collapsing a
    # fixed sample index to only the canonical grids during diversity probes.
    profile = schedule_profile(seed, sample_index)
    if (seed + sample_index) % 6 != 0:
        return None
    if profile == "thick_only":
        choices = (0, 1, 3)
    elif profile == "with_thin_vertical":
        choices = (2,)
    else:
        return None
    return _CANONICAL_SPECS[choices[(seed + sample_index) % len(choices)]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    # ``None`` is the public spelling for "axis not overridden".  Strip those
    # entries before any branch decisions so an all-None call is byte-for-byte
    # equivalent to omitting the kwargs, including canonical anchoring and
    # difficulty-aware bounds.
    active_overrides = {
        key: value for key, value in overrides.items() if value is not None
    }
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=active_overrides,
    )

    anchor = None if active_overrides else _canonical_anchor(seed, sample_index, band)
    if anchor is not None:
        h0, w0, specs = anchor
        colors0 = tuple(spec[0] for spec in specs)
        profile0 = "with_thin_vertical" if any(
            spec[4] - spec[2] + 1 == 2 for spec in specs
        ) else "thick_only"
        kind0 = "even" if all(c % 2 == 0 for c in colors0) else (
            "odd" if all(c % 2 == 1 for c in colors0) else "mixed"
        )
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
        n = ctx.draw_int("n_rects", len(specs), len(specs))
        palette_kind = ctx.draw_choice("palette_kind", (kind0,))
        geometry_profile = ctx.draw_choice("geometry_profile", (profile0,))
        grid = _grid_from_spec(anchor)
    else:
        if active_overrides:
            h_bounds, w_bounds, n_bounds = (7, 15), (9, 18), (2, 3)
        elif band == "easy":
            scheduled_n = schedule_n_rects(seed, sample_index, band)
            h_bounds, w_bounds, n_bounds = (7, 9), (9, 12), (scheduled_n, scheduled_n)
        elif band == "hard":
            h_bounds, w_bounds, n_bounds = (12, 15), (15, 18), (3, 3)
        else:
            scheduled_n = schedule_n_rects(seed, sample_index, band)
            h_bounds, w_bounds, n_bounds = (9, 12), (11, 15), (scheduled_n, scheduled_n)
        h = ctx.draw_int("grid_h", *h_bounds)
        w = ctx.draw_int("grid_w", *w_bounds)
        n = ctx.draw_int("n_rects", *n_bounds)
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
        scheduled = schedule_profile(seed, sample_index, band)
        geometry_profile = ctx.draw_choice(
            "geometry_profile",
            (scheduled,) if not active_overrides or "geometry_profile" not in active_overrides
            else GEOMETRY_PROFILES,
        )
        layout_rng = ctx.draw_rng("layout")
        colors = _palette(palette_kind, n, ctx.draw_rng("palette"))
        chosen_slots = layout_rng.sample(list(_slots(h, w)), n)
        kinds = ["thick"] * n
        if geometry_profile == "with_thin_horizontal":
            kinds[0] = "thin_horizontal"
        elif geometry_profile == "with_thin_vertical":
            kinds[0] = "thin_vertical"
        order = list(range(n))
        layout_rng.shuffle(order)
        kinds = [kinds[i] for i in order]
        grid = full_grid(h, w, 0)
        for color, slot, kind in zip(colors, chosen_slots, kinds):
            r0, r1, c0, c1 = _sample_box(slot, kind, layout_rng)
            for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
                grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected!r}, observed {observed[axis]!r}"
            )
    if set(ctx.overrides_used()) != set(active_overrides):
        raise ValueError("internal override accounting mismatch")
    return grid


def rule_mirror(grid):
    output = [list(row) for row in grid]
    facts = semantic_observables(grid)
    for rect in facts.get("rectangles", ()):
        if not rect.get("complete_corners"):
            continue
        for r, c in rect["border"]:
            output[r][c] = rect["color"]
    return output


# ---------------------------------------------------------------------------
# Named rivals, witnesses, and lesson-level identifiability
# ---------------------------------------------------------------------------

def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_solid_bbox(grid):
    output = [list(row) for row in grid]
    for rect in semantic_observables(grid).get("rectangles", ()):
        if not rect.get("complete_corners"):
            continue
        r0, r1, c0, c1 = rect["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = rect["color"]
    return output


def _rival_horizontal_edges_only(grid):
    output = [list(row) for row in grid]
    for rect in semantic_observables(grid).get("rectangles", ()):
        if not rect.get("complete_corners"):
            continue
        r0, r1, c0, c1 = rect["box"]
        for c in range(c0, c1 + 1):
            output[r0][c] = rect["color"]
            output[r1][c] = rect["color"]
    return output


def _rival_vertical_edges_only(grid):
    output = [list(row) for row in grid]
    for rect in semantic_observables(grid).get("rectangles", ()):
        if not rect.get("complete_corners"):
            continue
        r0, r1, c0, c1 = rect["box"]
        for r in range(r0, r1 + 1):
            output[r][c0] = rect["color"]
            output[r][c1] = rect["color"]
    return output


def _rival_first_color_only(grid):
    output = [list(row) for row in grid]
    rectangles = semantic_observables(grid).get("rectangles", ())
    for rect in rectangles[:1]:
        if rect.get("complete_corners"):
            for r, c in rect["border"]:
                output[r][c] = rect["color"]
    return output


def _rival_first_two_colors_only(grid):
    """Complete only the two lowest-valued colors, ignoring any third one."""
    output = [list(row) for row in grid]
    rectangles = semantic_observables(grid).get("rectangles", ())
    for rect in rectangles[:2]:
        if rect.get("complete_corners"):
            for r, c in rect["border"]:
                output[r][c] = rect["color"]
    return output


def _rival_ignore_thin_horizontal(grid):
    output = [list(row) for row in grid]
    for rect in semantic_observables(grid).get("rectangles", ()):
        if rect.get("complete_corners") and rect["height"] != 2:
            for r, c in rect["border"]:
                output[r][c] = rect["color"]
    return output


def _rival_ignore_thin_vertical(grid):
    output = [list(row) for row in grid]
    for rect in semantic_observables(grid).get("rectangles", ()):
        if rect.get("complete_corners") and rect["width"] != 2:
            for r, c in rect["border"]:
                output[r][c] = rect["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "identity": _rival_identity,
    "solid_bbox": _rival_solid_bbox,
    "horizontal_edges_only": _rival_horizontal_edges_only,
    "vertical_edges_only": _rival_vertical_edges_only,
    "first_color_only": _rival_first_color_only,
    "first_two_colors_only": _rival_first_two_colors_only,
    "ignore_thin_horizontal": _rival_ignore_thin_horizontal,
    "ignore_thin_vertical": _rival_ignore_thin_vertical,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "ignore_thin_horizontal": _rival_ignore_thin_horizontal,
    "first_two_colors_only": _rival_first_two_colors_only,
}


def _facts_ok(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    return facts if not self_check(grid) else {}


def _witness_completion(grid) -> bool:
    return bool(_facts_ok(grid)) and rule_mirror(grid) != [list(row) for row in grid]


def _witness_interior(grid) -> bool:
    return _facts_ok(grid).get("thick_count", 0) >= 1


def _witness_horizontal_span(grid) -> bool:
    facts = _facts_ok(grid)
    return bool(facts) and any((r["width"] or 0) >= 3 for r in facts["rectangles"])


def _witness_vertical_span(grid) -> bool:
    facts = _facts_ok(grid)
    return bool(facts) and any((r["height"] or 0) >= 3 for r in facts["rectangles"])


def _witness_multicolor(grid) -> bool:
    return _facts_ok(grid).get("n_rects", 0) >= 2


def _witness_three_colors(grid) -> bool:
    return _facts_ok(grid).get("n_rects", 0) == 3


def _witness_thin_horizontal(grid) -> bool:
    return _facts_ok(grid).get("thin_horizontal_count", 0) == 1


def _witness_thin_vertical(grid) -> bool:
    return _facts_ok(grid).get("thin_vertical_count", 0) == 1


SEMANTIC_WITNESSES = {
    "non_identity_completion": _witness_completion,
    "interior_preserved": _witness_interior,
    "horizontal_edges_required": _witness_horizontal_span,
    "vertical_edges_required": _witness_vertical_span,
    "all_colors_completed": _witness_multicolor,
    "three_colors_completed": _witness_three_colors,
    "thin_horizontal_completed": _witness_thin_horizontal,
    "thin_vertical_completed": _witness_thin_vertical,
}
WITNESS_RIVALS = {
    "non_identity_completion": ["identity"],
    "interior_preserved": ["solid_bbox"],
    "horizontal_edges_required": ["vertical_edges_only"],
    "vertical_edges_required": ["horizontal_edges_only"],
    "all_colors_completed": ["first_color_only"],
    "three_colors_completed": ["first_two_colors_only"],
    "thin_horizontal_completed": ["ignore_thin_horizontal"],
    "thin_vertical_completed": ["ignore_thin_vertical"],
}


def _grids_equal(left, right) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            )
            if not fits:
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives all demos and the query")
            else:
                reasons.append(f"competitor {name!r} fits all demos but disagrees on query")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
