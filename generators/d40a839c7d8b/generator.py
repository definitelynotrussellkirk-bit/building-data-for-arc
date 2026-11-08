"""Generator for ARC task d40a839c7d8b.

The canonical rule recolors gray (5) cells in alternating columns, starting
from the right edge.  With zero-based columns this is exactly
``c % 2 == (width + 1) % 2``.  Gray cells in the opposite parity columns and
all non-gray cells are preserved.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d40a839c7d8b"
TASK_ID = "d40a839c7d8b"
VERSION = "3.0.0"
RULE_HASH = "c7049cdbce74"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A sparse grid contains gray(5) cells on both alternating column parities. "
    "Recolor only the gray cells in columns with c % 2 == (width + 1) % 2 "
    "to green(3); preserve gray cells in the other columns and preserve every "
    "non-gray cell. Ordinary lessons alternate even and odd widths so the "
    "right-edge anchoring, rather than a fixed left-column parity, is visible."
)

INVARIANTS = [
    "rectangular grid with height and width at least 3",
    "no green(3) appears in an input",
    "at least four gray(5) cells spanning at least two rows and three columns",
    "at least one gray lies in the trigger parity and one in the other parity",
    "at least one non-gray cell remains",
]

CANONICAL_WIDTHS = (10, 12, 13, 14, 17)
GRAY_LAYOUTS = ("random", "cluster", "row", "column", "diagonal", "scattered")

AXES = {
    "grid_h": {"type": "int", "default": "canonical 3 or difficulty-shaped", "valid": "3..18"},
    "grid_w": {"type": "int", "default": "alternating even/odd width", "valid": "3..18"},
    "gray_count": {"type": "int", "default": "canonical width or difficulty-shaped", "valid": "4..24"},
    "gray_layout": {"type": "str", "default": "rng", "valid": "|".join(GRAY_LAYOUTS)},
    "bg_color": {"type": "color", "default": "0 canonical; nonzero colored variants", "valid": "0..9 (≠3,5)"},
    "decoy_palette_size": {"type": "int", "default": "0 canonical; 1..3 colored variants", "valid": "0..6"},
}

MIN_STRICT_FRAC = 0.40


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["empty grid"]}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["rows must be non-empty lists"]}
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return {"errors": ["ragged grid"]}

    h = len(grid)
    if h < 3 or w < 3:
        errors.append("grid must be at least 3x3")
    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in flat):
        errors.append("grid values must be integer ARC colors 0..9")
    if 3 in flat:
        errors.append("input contains output color green(3)")

    grays = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    if len(grays) < 4:
        errors.append("fewer than four gray(5) cells")
    if len(grays) >= h * w:
        errors.append("gray fills the entire grid")
    if len({r for r, _ in grays}) < 2:
        errors.append("gray cells do not span at least two rows")
    if len({c for _, c in grays}) < 3:
        errors.append("gray cells do not span at least three columns")

    trigger = (w + 1) % 2
    trigger_grays = [(r, c) for r, c in grays if c % 2 == trigger]
    preserved_grays = [(r, c) for r, c in grays if c % 2 != trigger]
    if not trigger_grays:
        errors.append(f"no gray(5) at trigger parity col%2=={trigger}")
    if not preserved_grays:
        errors.append(f"no gray(5) at preserved parity col%2!={trigger}")

    palette = set(flat)
    return {
        "errors": errors,
        "h": h,
        "w": w,
        "palette": palette,
        "gray_count": len(grays),
        "gray_rows": {r for r, _ in grays},
        "gray_cols": {c for _, c in grays},
        "trigger": trigger,
        "trigger_grays": trigger_grays,
        "preserved_grays": preserved_grays,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar, not only palette and shape."""
    return list(_analysis(grid)["errors"])


def _base_h_values(difficulty: str | None, canonical_mode: bool) -> list[int]:
    if canonical_mode:
        return [3]
    if difficulty == "easy":
        return list(range(3, 6))
    if difficulty == "hard":
        return list(range(8, 13))
    return list(range(5, 9))


def _base_w_values(difficulty: str | None, canonical_mode: bool, parity: int) -> list[int]:
    if canonical_mode:
        values = list(CANONICAL_WIDTHS)
    elif difficulty == "easy":
        values = list(range(6, 11))
    elif difficulty == "hard":
        values = list(range(14, 19))
    else:
        values = list(range(10, 15))
    return [value for value in values if value % 2 == parity]


def _draw_dimensions(ctx, *, canonical_mode: bool, required_area: int) -> tuple[int, int]:
    """Draw exact dimensions while accepting every declared single-axis bound."""
    desired_parity = ctx.sample_index % 2
    h_override = ctx.overrides.get("grid_h")
    w_override = ctx.overrides.get("grid_w")

    if w_override is not None:
        w = ctx.draw_int("grid_w", 3, 18)
    else:
        w_values = _base_w_values(ctx.difficulty, canonical_mode, desired_parity)
        if not w_values:
            w_values = [value for value in range(3, 19) if value % 2 == desired_parity]
        w = ctx.draw_choice("grid_w", w_values)

    if h_override is not None:
        h = ctx.draw_int("grid_h", 3, 18)
    else:
        h_values = _base_h_values(ctx.difficulty, canonical_mode)
        fitting = [value for value in h_values if value * w >= required_area]
        if not fitting:
            fitting = [value for value in range(3, 19) if value * w >= required_area]
        if not fitting:
            raise ValueError(
                f"requested exact axes need area {required_area}, but grid_w={w} cannot fit within height<=18"
            )
        h = ctx.draw_choice("grid_h", fitting)

    if h * w < required_area:
        # Both dimensions were explicit, or one explicit dimension made the
        # other band-constrained request impossible.  Multi-axis conflicts are
        # rejected loudly rather than silently clamped.
        raise ValueError(
            f"grid {h}x{w} has area {h*w}, below required exact-axis area {required_area}"
        )
    return h, w


def _layout_order(layout: str, h: int, w: int, cells: list[tuple[int, int]], rng) -> list[tuple[int, int]]:
    cells = list(cells)
    if layout == "random":
        rng.shuffle(cells)
        return cells
    if layout == "cluster":
        center = (rng.randrange(h), rng.randrange(w))
        rng.shuffle(cells)
        return sorted(cells, key=lambda rc: abs(rc[0] - center[0]) + abs(rc[1] - center[1]))
    if layout == "row":
        start = rng.randrange(h)
        rng.shuffle(cells)
        return sorted(cells, key=lambda rc: ((rc[0] - start) % h, rc[1]))
    if layout == "column":
        start = rng.randrange(w)
        rng.shuffle(cells)
        return sorted(cells, key=lambda rc: ((rc[1] - start) % w, rc[0]))
    if layout == "diagonal":
        rng.shuffle(cells)
        return sorted(cells, key=lambda rc: (abs(rc[0] - rc[1]), rc[0] + rc[1]))
    if layout == "scattered":
        phase = rng.randrange(2)
        rng.shuffle(cells)
        return sorted(cells, key=lambda rc: ((rc[0] + rc[1]) % 2 != phase, rc[0], rc[1]))
    raise ValueError(f"unknown gray_layout {layout!r}")


def _gray_cells(layout: str, h: int, w: int, count: int, rng) -> list[tuple[int, int]]:
    """Return exactly count cells with both rule branches structurally visible."""
    if count < 4:
        raise ValueError("gray_count must be at least 4")
    available = [(r, c) for r in range(h) for c in range(w) if (r, c) != (0, 0)]
    if count > len(available):
        raise ValueError(f"gray_count={count} exceeds non-anchor capacity {len(available)}")

    # Layout-specific RNG makes gray_layout observable even at gray_count=4.
    start = rng.randrange(w - 2)
    row_values = list(range(1, h))
    rng.shuffle(row_values)
    r1 = row_values[0]
    r2 = row_values[1] if len(row_values) > 1 else 0
    anchors = [(r1, start), (r1, start + 1), (r2, start + 1), (r2, start + 2)]
    anchors = list(dict.fromkeys(anchors))
    if len(anchors) != 4:
        raise AssertionError("branch anchors must be four distinct cells")

    remainder = [cell for cell in available if cell not in set(anchors)]
    ordered = _layout_order(layout, h, w, remainder, rng)
    return anchors + ordered[: count - 4]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_mode = sample_index % 4 in (0, 1)
    requested_gray = int(overrides.get("gray_count", 0) or 0)
    requested_decoys = (
        int(overrides["decoy_palette_size"])
        if overrides.get("decoy_palette_size") is not None
        else (0 if canonical_mode else 3)
    )
    required_area = max(0, requested_gray + requested_decoys + 1)
    h, w = _draw_dimensions(ctx, canonical_mode=canonical_mode, required_area=required_area)

    if "bg_color" in overrides and overrides["bg_color"] is not None:
        bg = ctx.draw_color("bg_color", exclude={3, 5})
    elif canonical_mode:
        bg = ctx.draw_choice("bg_color", [0])
    else:
        bg = ctx.draw_choice("bg_color", [1, 2, 4, 6, 7, 8, 9])

    if "decoy_palette_size" in overrides and overrides["decoy_palette_size"] is not None:
        decoy_count = ctx.draw_int("decoy_palette_size", 0, 6)
    elif canonical_mode:
        decoy_count = ctx.draw_int("decoy_palette_size", 0, 0)
    else:
        decoy_count = ctx.draw_int("decoy_palette_size", 1, 3)

    max_gray = h * w - 1 - decoy_count
    if "gray_count" in overrides and overrides["gray_count"] is not None:
        gray_count = ctx.draw_int("gray_count", 4, 24)
    elif canonical_mode and h == 3 and w in CANONICAL_WIDTHS:
        gray_count = ctx.draw_choice("gray_count", [w])
    else:
        lo = 6 if difficulty == "easy" else 8 if difficulty != "hard" else 12
        hi = min(24, max_gray, lo + (4 if difficulty == "easy" else 8 if difficulty != "hard" else 12))
        if hi < lo:
            lo = 4
            hi = min(24, max_gray)
        gray_count = ctx.draw_int("gray_count", lo, hi)
    if gray_count > max_gray:
        raise ValueError(
            f"gray_count={gray_count} leaves insufficient room for anchor background and {decoy_count} decoy colors"
        )

    layout = ctx.draw_choice("gray_layout", GRAY_LAYOUTS)
    placement_rng = ctx.draw_rng(f"placement:{layout}")
    gray_cells = _gray_cells(layout, h, w, gray_count, placement_rng)

    grid = full_grid(h, w, bg)
    for r, c in gray_cells:
        grid[r][c] = 5

    if decoy_count:
        decor_colors = ctx.draw_distinct_colors(
            "decor_colors", n=decoy_count, exclude={bg, 3, 5}
        )
        remaining = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if (r, c) != (0, 0) and grid[r][c] == bg
        ]
        if len(remaining) < decoy_count:
            raise ValueError("not enough non-gray cells to realize every decoy color")
        placement_rng.shuffle(remaining)
        trigger = (w + 1) % 2
        trigger_candidates = [cell for cell in remaining if cell[1] % 2 == trigger]
        chosen: list[tuple[int, int]] = []
        if trigger_candidates:
            chosen.append(trigger_candidates[0])
        for cell in remaining:
            if len(chosen) >= decoy_count:
                break
            if cell not in chosen:
                chosen.append(cell)
        if len(chosen) != decoy_count:
            raise ValueError("could not place one cell for every decoy color")
        for cell, color in zip(chosen, decor_colors):
            grid[cell[0]][cell[1]] = color

        # Repeat a few decoys so colored variants are not single-pixel labels.
        extra_limit = min(len(remaining) - len(chosen), decoy_count * 2)
        extras = [cell for cell in remaining if cell not in chosen][:extra_limit]
        for index, (r, c) in enumerate(extras):
            grid[r][c] = decor_colors[index % decoy_count]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator constructed invalid grid: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared numeric/color axis from a generated grid."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    bg = grid[0][0]  # generated grids reserve this anchor as background
    decoy_colors = info["palette"] - {bg, 5}
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "gray_count": info["gray_count"],
        "bg_color": bg,
        "decoy_palette_size": len(decoy_colors),
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the actual canonical 3-row sparse-dot manifold."""
    info = _analysis(grid)
    reasons = list(info["errors"])
    if reasons:
        return reasons
    if info["h"] != 3:
        reasons.append("canonical inputs have exactly three rows")
    if info["w"] not in CANONICAL_WIDTHS:
        reasons.append(f"width {info['w']} is outside canonical widths {CANONICAL_WIDTHS}")
    if info["palette"] != {0, 5}:
        reasons.append("canonical inputs use exactly colors {0,5}")
    if info["gray_count"] != info["w"]:
        reasons.append("canonical inputs contain exactly one width's worth of gray cells")
    return reasons


def _lawful(grid) -> dict[str, Any] | None:
    info = _analysis(grid)
    return None if info["errors"] else info


def _witness(predicate: Callable[[dict[str, Any]], bool], grid) -> bool:
    info = _lawful(grid)
    return False if info is None else bool(predicate(info))


def _has_adjacent_split(info: dict[str, Any]) -> bool:
    trigger = set(info["trigger_grays"])
    preserved = set(info["preserved_grays"])
    return any(
        (r, c + 1) in preserved or (r, c - 1) in preserved
        for r, c in trigger
    )


def _has_trigger_decoy(grid) -> bool:
    info = _lawful(grid)
    if info is None:
        return False
    bg = grid[0][0]
    return any(
        c % 2 == info["trigger"] and value not in {bg, 5}
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
    )


SEMANTIC_WITNESSES = {
    "canonical_profile_anchor": lambda grid: not strict_canonical_like(grid),
    "even_width_recolors_odd_columns": lambda grid: _witness(
        lambda info: info["w"] % 2 == 0 and info["trigger"] == 1, grid
    ),
    "odd_width_recolors_even_columns": lambda grid: _witness(
        lambda info: info["w"] % 2 == 1 and info["trigger"] == 0, grid
    ),
    "changed_and_preserved_gray_branches": lambda grid: _witness(
        lambda info: bool(info["trigger_grays"] and info["preserved_grays"]), grid
    ),
    "adjacent_columns_split_by_parity": lambda grid: _witness(_has_adjacent_split, grid),
    "nonzero_background_variant": lambda grid: _witness(lambda info: grid[0][0] != 0, grid),
    "non_gray_decoy_in_trigger_column": _has_trigger_decoy,
    "height_width_parity_disagree": lambda grid: _witness(
        lambda info: info["h"] % 2 != info["w"] % 2, grid
    ),
}


def rule_mirror(grid) -> list[list[int]]:
    """Python audit mirror only; the canonical Racket rule remains authoritative."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [row[:] for row in grid]
    for r, c in info["trigger_grays"]:
        out[r][c] = 3
    return out


def _competitor(grid, mode: str) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [row[:] for row in grid]
    flat_grays = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    bg = grid[0][0]

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            paint = False
            if mode == "identity":
                paint = False
            elif mode == "all_gray":
                paint = value == 5
            elif mode == "fixed_even":
                paint = value == 5 and c % 2 == 0
            elif mode == "fixed_odd":
                paint = value == 5 and c % 2 == 1
            elif mode == "opposite_parity":
                paint = value == 5 and c % 2 != info["trigger"]
            elif mode == "height_parity":
                paint = value == 5 and c % 2 == (info["h"] + 1) % 2
            elif mode == "whole_trigger_columns":
                paint = c % 2 == info["trigger"]
            elif mode == "all_non_background":
                paint = value != bg
            elif mode == "row_major_alternate":
                paint = value == 5 and flat_grays.index((r, c)) % 2 == 0
            else:
                raise ValueError(mode)
            if paint:
                out[r][c] = 3
    return out


_LESSON_COMPETITORS = {
    "copy input unchanged": "identity",
    "recolor every gray": "all_gray",
    "use fixed even columns": "fixed_even",
    "use fixed odd columns": "fixed_odd",
    "use the opposite alternating parity": "opposite_parity",
    "derive parity from height": "height_parity",
    "paint whole trigger columns": "whole_trigger_columns",
    "paint every non-background cell": "all_non_background",
    "recolor every other gray in scan order": "row_major_alternate",
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a concrete shortcut survives demos but changes query."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is not an input/output pair")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"{role} input is malformed: {findings[:2]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with the width-parity rule")
    if reasons:
        return reasons

    for label, mode in _LESSON_COMPETITORS.items():
        if all(_competitor(pair["input"], mode) == pair["output"] for pair in demos):
            if _competitor(query["input"], mode) != query["output"]:
                reasons.append(f"demos do not falsify shortcut '{label}'")
    return reasons
