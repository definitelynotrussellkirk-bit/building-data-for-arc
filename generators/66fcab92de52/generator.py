"""Generator for ARC task 66fcab92de52 (bd5af378).

Input grammar: a two-color grid whose non-background color forms one complete
L on two adjacent outer edges.  The canonical Racket rule erases that outer L,
moves both arms one cell inward, paints the region beyond the new L cyan (8),
marks the old and new L corners cyan, then restores a background-colored
diagonal through the cyan rectangle.

The public examples cover top-left, bottom-left, and bottom-right Ls but no
top-right L.  Generation therefore schedules all four corners so a learner
cannot silently adopt the public-only shortcut "the top-right case never
occurs".
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "66fcab92de52"
TASK_ID = "66fcab92de52"
VERSION = "2.0.1"
RULE_HASH = "e36095ccf386"

SUMMARY = (
    "A 5..10 grid has exactly two non-cyan colors: a nonzero modal background "
    "and a second color forming a complete L on two adjacent outer edges. The rule "
    "erases the old L, moves its arms one cell inward, fills the region beyond "
    "the new L cyan (8), marks the old/new L corners cyan, and cuts a "
    "background-colored diagonal through that cyan region."
)

INVARIANTS = [
    "grid size is 5..10 by 5..10 and all cells are ARC colors 0..9",
    "exactly two input colors are present and neither is cyan (8)",
    "the modal background is nonzero (the canonical DSL mode primitive excludes 0)",
    "one color is the background everywhere except a single complete outer-edge L",
    "the other color occupies exactly one full edge row and one adjacent full edge column",
    "the L corner is exactly one of the four grid corners",
]

CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 5..10",
        "valid": "5..10",
        "doc": "Full input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 5..10",
        "valid": "5..10",
        "doc": "Full input-grid width.",
    },
    "corner": {
        "type": "str",
        "default": "four-corner lesson schedule",
        "valid": "|".join(CORNERS),
        "doc": "Corner occupied by the input L.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = CORNERS


def _difficulty_offset(difficulty) -> int:
    if difficulty is None:
        return 0
    if difficulty == "easy":
        return 0
    if difficulty == "medium":
        return 1
    if difficulty == "hard":
        return 2
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the scheduled corner; every four consecutive slots cover all."""
    del seed
    return CORNERS[(int(sample_index) + _difficulty_offset(difficulty)) % 4]


def _inclusive_range(a: int, b: int) -> range:
    return range(a, b + 1) if a <= b else range(a, b - 1, -1)


def _corner_geometry(corner: str, h: int, w: int) -> tuple[int, int, int, int]:
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    top = corner.startswith("top")
    left = corner.endswith("left")
    return (0 if top else h - 1, 0 if left else w - 1, 1 if top else -1, 1 if left else -1)


def _grid_shape_errors(grid: Any) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"], 0, 0
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be non-empty and rectangular"], h, w
    if not 5 <= h <= 10:
        errors.append(f"grid height {h} outside 5..10")
    if not 5 <= w <= 10:
        errors.append(f"grid width {w} outside 5..10")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    return errors, h, w


def _analyze(grid: Any) -> dict[str, Any]:
    errors, h, w = _grid_shape_errors(grid)
    if (
        not h
        or not w
        or any("rectangular" in e or "invalid ARC color" in e for e in errors)
    ):
        return {"errors": errors}

    colors = sorted({value for row in grid for value in row})
    if len(colors) != 2:
        errors.append(f"expected exactly 2 input colors, got {colors}")
        return {"errors": errors}
    if 8 in colors:
        errors.append("input colors must exclude cyan 8, which is reserved for the output")
        return {"errors": errors}

    matches: list[tuple[str, int, int]] = []
    for corner in CORNERS:
        rr, cc, _, _ = _corner_geometry(corner, h, w)
        border_cells = {(rr, c) for c in range(w)} | {(r, cc) for r in range(h)}
        for border in colors:
            bg = colors[1] if border == colors[0] else colors[0]
            if all(
                grid[r][c] == (border if (r, c) in border_cells else bg)
                for r in range(h)
                for c in range(w)
            ):
                matches.append((corner, bg, border))

    if len(matches) != 1:
        errors.append(
            "expected exactly one complete outer-edge L over a uniform background; "
            f"matched {len(matches)} orientations"
        )
        return {"errors": errors}

    corner, bg, border = matches[0]
    if bg == 0:
        errors.append(
            "background color must be nonzero because the canonical DSL mode primitive excludes 0"
        )
        return {"errors": errors}
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "corner": corner,
        "bg_color": bg,
        "border_color": border,
    }


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "corner": analysis["corner"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _difficulty_offset(difficulty)  # validates the public difficulty contract
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 5, 10)
    # draw_int_diff maps the named medium band onto widths 7..8 when given
    # the public 5..10 range, which makes the canonical 8x6 profile
    # unreachable.  Medium therefore samples the honest in-range support
    # 6..8 directly. Explicit overrides still use the full public 5..10 range.
    if difficulty == "medium" and overrides.get("grid_w") is None:
        w = ctx.draw_choice("grid_w", (6, 7, 8))
    else:
        w = ctx.draw_int_diff("grid_w", 5, 10)

    scheduled_corner = schedule_profile(seed, sample_index, difficulty)
    if "corner" in overrides and overrides["corner"] is not None:
        corner = ctx.draw_choice("corner", CORNERS)
    else:
        corner = ctx.draw_choice("corner", (scheduled_corner,))

    bg = ctx.draw_color("bg_color", exclude={0, 8})
    border = ctx.draw_color("border_color", exclude={bg, 8})
    grid = full_grid(h, w, bg)
    rr, cc, _, _ = _corner_geometry(corner, h, w)
    for c in range(w):
        grid[rr][c] = border
    for r in range(h):
        grid[r][cc] = border

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid L-border lesson: " + "; ".join(errors))

    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed.get(axis) != requested.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return grid


def _rule_core(grid: list[list[int]], *, draw_diagonal: bool = True) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    h = analysis["grid_h"]
    w = analysis["grid_w"]
    corner = analysis["corner"]
    bg = analysis["bg_color"]
    border = analysis["border_color"]
    lc_r, lc_c, dr, dc = _corner_geometry(corner, h, w)
    nlc_r, nlc_c = lc_r + dr, lc_c + dc

    out = full_grid(h, w, bg)
    nlrow_cstart = lc_c + 2 * dc
    nlrow_cend = w - 1 if dc == 1 else 0
    for c in _inclusive_range(nlrow_cstart, nlrow_cend):
        out[nlc_r][c] = border
    nlcol_rstart = lc_r + 2 * dr
    nlcol_rend = h - 1 if dr == 1 else 0
    for r in _inclusive_range(nlcol_rstart, nlcol_rend):
        out[r][nlc_c] = border

    ni_rstart = nlc_r + dr
    ni_rend = h - 1 if dr == 1 else 0
    ni_cstart = nlc_c + dc
    ni_cend = w - 1 if dc == 1 else 0
    for r in _inclusive_range(ni_rstart, ni_rend):
        for c in _inclusive_range(ni_cstart, ni_cend):
            out[r][c] = 8

    out[lc_r][lc_c] = 8
    out[nlc_r][nlc_c] = 8
    if draw_diagonal:
        span = min(abs(ni_rend - ni_rstart) + 1, abs(ni_cend - ni_cstart) + 1)
        for i in range(span):
            out[ni_rstart + i * dr][ni_cstart + i * dc] = bg
    return out


def rule_mirror(grid):
    """Pure Python mirror used only for semantic auditing; Racket is authority."""
    return _rule_core(grid, draw_diagonal=True)


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "bg_color": analysis["bg_color"],
        "border_color": analysis["border_color"],
        "is_square": analysis["grid_h"] == analysis["grid_w"],
        "diagonal_span": min(analysis["grid_h"] - 2, analysis["grid_w"] - 2),
    }


def strict_canonical_like(grid) -> list[str]:
    # The repaired default distribution intentionally stays inside the exact
    # canonical size envelope while adding the missing top-right orientation.
    return self_check(grid)


def _witness_corner(grid, corner: str) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and obs.get("corner") == corner


SEMANTIC_WITNESSES = {
    "corner_top_left": lambda grid: _witness_corner(grid, "top_left"),
    "corner_top_right": lambda grid: _witness_corner(grid, "top_right"),
    "corner_bottom_left": lambda grid: _witness_corner(grid, "bottom_left"),
    "corner_bottom_right": lambda grid: _witness_corner(grid, "bottom_right"),
}


def _rival_no_diagonal(grid):
    return _rule_core(grid, draw_diagonal=False)


def _rival_keep_old_l(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    out = rule_mirror(grid)
    rr, cc, _, _ = _corner_geometry(
        analysis["corner"], analysis["grid_h"], analysis["grid_w"]
    )
    border = analysis["border_color"]
    for c in range(analysis["grid_w"]):
        out[rr][c] = border
    for r in range(analysis["grid_h"]):
        out[r][cc] = border
    return out


def _rival_skip_top_right(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["corner"] == "top_right":
        return _rival_no_diagonal(grid)
    return rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "no_background_diagonal": _rival_no_diagonal,
    "keep_old_outer_l": _rival_keep_old_l,
    "skip_top_right": _rival_skip_top_right,
}
WITNESS_RIVALS = {
    "corner_top_left": ["no_background_diagonal", "keep_old_outer_l"],
    "corner_top_right": ["no_background_diagonal", "keep_old_outer_l", "skip_top_right"],
    "corner_bottom_left": ["no_background_diagonal", "keep_old_outer_l"],
    "corner_bottom_right": ["no_background_diagonal", "keep_old_outer_l"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # No canonical input has a top-right L, so this wrong rule fits every
    # public pair and can only be killed by generated top-right evidence.
    "skip_top_right": _rival_skip_top_right,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful L-border scene: " + "; ".join(query_errors)]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the inward-L rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
    return reasons
