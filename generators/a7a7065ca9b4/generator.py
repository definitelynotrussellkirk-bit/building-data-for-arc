"""Generator for ARC task 62b74c02 (canonical task a7a7065ca9b4).

The first all-zero column ends a left source prefix.  The output preserves that
prefix, copies it *unchanged* into the rightmost columns, and fills every cell
between the two copies with the first color of its row.

Ordinary lessons deliberately mix three source-prefix modes.  Dense edge-
matched scenes stay close to the canonical examples; dense edge-mismatch
scenes disprove the shortcut that assumes the copied prefix ends in the row
color; sparse scenes contain copied zero holes and disprove nonzero-overlay
shortcuts.  Four consecutive sample indices contain all three modes, so every
materialized lesson identifies the exact copy-and-fill rule.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a7a7065ca9b4"
TASK_ID = "a7a7065ca9b4"
VERSION = "3.0.0"
RULE_HASH = "9c55d00ff53c"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find the first all-zero column; it ends the left source prefix. Preserve "
    "that prefix, copy it in the same orientation to the right edge, and fill "
    "the intervening columns of each row with that row's column-0 color."
)

INVARIANTS = [
    "background is 0",
    "column 0 is nonzero in every row and supplies the row fill color",
    "the first all-zero column is the source-prefix width (3 or 4)",
    "every source column before the divider has a nonzero witness",
    "the input is entirely background from the divider through the right edge",
    "the canvas leaves at least two middle columns between the two prefix copies",
    "some source cell differs from its row's column-0 color, so copying is visible",
    "ordinary lessons include edge-matched, edge-mismatch, and copied-zero-hole scenes",
]

PATTERN_MODES = (
    "edge_matched_dense",
    "edge_mismatch_dense",
    "sparse_holes",
)
_MODE_SCHEDULE = (
    "edge_matched_dense",
    "edge_mismatch_dense",
    "sparse_holes",
    "edge_mismatch_dense",
)

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors plus 3..5 easy, 5..8 medium, 8..12 hard",
        "valid": "3..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors plus 10..14 easy, 12..16 medium, 14..18 hard",
        "valid": "10..18",
    },
    "pattern_w": {
        "type": "int",
        "default": "scheduled 3|4",
        "valid": "3..4",
    },
    "palette_size": {
        "type": "int",
        "default": "2..4 easy, 3..5 medium, 4..6 hard",
        "valid": "2..6",
    },
    "pattern_mode": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "|".join(PATTERN_MODES),
    },
}

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CANONICAL_ANCHORS = (
    # (height, width, prefix width, nonzero palette size).  Including 0, these
    # exactly match the four canonical mechanical profiles.
    (3, 10, 3, 3),
    (4, 12, 3, 3),
    (3, 14, 4, 3),
    (4, 14, 4, 4),
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "pattern_w", "palette_size"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer")
    if (
        "pattern_mode" in overrides
        and overrides["pattern_mode"] is not None
        and overrides["pattern_mode"] not in PATTERN_MODES
    ):
        raise ValueError(f"pattern_mode must be one of {PATTERN_MODES}")


def _scheduled_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Record a scheduled default while preserving the full override domain."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _default_axes(ctx, sample_index: int, difficulty: str | None) -> tuple[int, int, int, int]:
    """Return deterministic, band-aware defaults with recurring canonical anchors."""
    band = "medium" if difficulty is None else difficulty
    # One fifth of ordinary draws is an exact canonical mechanical-profile
    # anchor in every band.  The remaining draws expand scale by difficulty.
    if sample_index % 5 == 0:
        default_h, default_w, default_pw, default_palette = _CANONICAL_ANCHORS[
            (sample_index // 5) % len(_CANONICAL_ANCHORS)
        ]
    elif band == "easy":
        default_h = ctx.draw_rng("grid_h_default").randint(3, 5)
        default_w = ctx.draw_rng("grid_w_default").randint(10, 14)
        default_pw = (3, 4)[sample_index % 2]
        default_palette = ctx.draw_rng("palette_size_default").randint(2, 4)
    elif band == "hard":
        default_h = ctx.draw_rng("grid_h_default").randint(8, 12)
        default_w = ctx.draw_rng("grid_w_default").randint(14, 18)
        default_pw = (3, 4)[sample_index % 2]
        default_palette = ctx.draw_rng("palette_size_default").randint(4, 6)
    else:
        default_h = ctx.draw_rng("grid_h_default").randint(5, 8)
        default_w = ctx.draw_rng("grid_w_default").randint(12, 16)
        default_pw = (3, 4)[sample_index % 2]
        default_palette = ctx.draw_rng("palette_size_default").randint(3, 5)

    height = _scheduled_int(ctx, "grid_h", 3, 12, default_h)
    width = _scheduled_int(ctx, "grid_w", 10, 18, default_w)
    pattern_width = _scheduled_int(ctx, "pattern_w", 3, 4, default_pw)
    palette_size = _scheduled_int(ctx, "palette_size", 2, 6, default_palette)
    return height, width, pattern_width, palette_size


def _row_colors(height: int, palette: list[int], rng) -> list[int]:
    """Use at least two row colors while retaining broad deterministic order."""
    order = list(palette)
    rng.shuffle(order)
    offset = rng.randrange(len(order))
    return [order[(offset + row) % len(order)] for row in range(height)]


def _fill_remaining_slots(
    grid: list[list[int]],
    slots: list[tuple[int, int]],
    palette: list[int],
    rng,
) -> None:
    """Fill slots and guarantee every requested palette color is observable."""
    counts = Counter(value for row in grid for value in row if value != 0)
    missing = [color for color in palette if counts[color] == 0]
    rng.shuffle(slots)
    if len(missing) > len(slots):
        raise ValueError("palette_size exceeds the observable source-prefix capacity")
    for (row, col), color in zip(slots, missing):
        grid[row][col] = color
    for row, col in slots[len(missing) :]:
        grid[row][col] = rng.choice(palette)


def _different_color(color: int, palette: list[int]) -> int:
    return next(candidate for candidate in palette if candidate != color)


def _build_prefix(
    height: int,
    width: int,
    pattern_width: int,
    palette: list[int],
    mode: str,
    rng,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    row_colors = _row_colors(height, palette, rng)
    for row, color in enumerate(row_colors):
        grid[row][0] = color

    if mode == "edge_matched_dense":
        # The last source cell agrees with the fill color, matching the
        # canonical cue.  Interior cells still contain a visible contrast.
        interior = [
            (row, col)
            for row in range(height)
            for col in range(1, pattern_width - 1)
        ]
        missing = [color for color in palette if color not in set(row_colors)]
        contrast_color = missing.pop(0) if missing else _different_color(row_colors[0], palette)
        grid[0][1] = contrast_color
        remaining = [slot for slot in interior if slot != (0, 1)]
        # Seed any still-missing colors before random fill.
        rng.shuffle(remaining)
        for slot, color in zip(remaining, missing):
            grid[slot[0]][slot[1]] = color
        for row, col in remaining[len(missing) :]:
            grid[row][col] = rng.choice(palette)
        for row in range(height):
            grid[row][pattern_width - 1] = grid[row][0]

    elif mode == "edge_mismatch_dense":
        source_slots = [
            (row, col)
            for row in range(height)
            for col in range(1, pattern_width)
        ]
        missing = [color for color in palette if color not in set(row_colors)]
        # Reserve two different semantic cells: col 1 makes adjacent-copy
        # placement visible, and the last source column refutes the canonical
        # edge-matched shortcut.
        reserved = [(0, 1), (0, pattern_width - 1)]
        remaining = [slot for slot in source_slots if slot not in reserved]
        seeded: list[int] = []
        for slot in reserved:
            if missing:
                color = missing.pop(0)
            else:
                color = _different_color(row_colors[slot[0]], palette)
            if color == row_colors[slot[0]]:
                color = _different_color(row_colors[slot[0]], palette)
            grid[slot[0]][slot[1]] = color
            seeded.append(color)
        rng.shuffle(remaining)
        for slot, color in zip(remaining, missing):
            grid[slot[0]][slot[1]] = color
        for row, col in remaining[len(missing) :]:
            grid[row][col] = rng.choice(palette)

    elif mode == "sparse_holes":
        # Two fixed-role holes are enough to make exact background copying
        # observable while leaving every source column nonempty.
        holes = {(0, 1), (1, pattern_width - 1)}
        source_slots = [
            (row, col)
            for row in range(height)
            for col in range(1, pattern_width)
            if (row, col) not in holes
        ]
        _fill_remaining_slots(grid, source_slots, palette, rng)
    else:  # guarded by _validate_call, retained as a loud internal invariant
        raise ValueError(f"unsupported pattern_mode {mode!r}")

    # The divider and all input cells to its right remain background.
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list of rows"]}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["grid rows must be nonempty lists"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid colors must be integers in 0..9")

    height = len(grid)
    if height < 3:
        errors.append("grid must have at least 3 rows")
    if width < 10:
        errors.append("grid must have at least 10 columns")
    if any(grid[row][0] == 0 for row in range(height)):
        errors.append("column 0 must be nonzero in every row")

    pattern_width = next(
        (
            col
            for col in range(width)
            if all(grid[row][col] == 0 for row in range(height))
        ),
        None,
    )
    if pattern_width is None:
        errors.append("missing all-zero divider column")
        pattern_width = width
    elif not 3 <= pattern_width <= 4:
        errors.append(f"first all-zero divider must be column 3 or 4, got {pattern_width}")

    if pattern_width < width:
        if any(
            grid[row][col] != 0
            for row in range(height)
            for col in range(pattern_width, width)
        ):
            errors.append("divider and every input cell to its right must be background")
        if width < 2 * pattern_width + 2:
            errors.append("canvas must leave at least two middle columns between prefix copies")

    contrast_cells: list[tuple[int, int]] = []
    if 1 < pattern_width <= width:
        contrast_cells = [
            (row, col)
            for row in range(height)
            for col in range(1, pattern_width)
            if grid[row][col] != grid[row][0]
        ]
        if not contrast_cells:
            errors.append("source prefix must contain a cell different from its row fill color")

    nonzero_colors = sorted({value for row in grid for value in row if value != 0})
    if len(nonzero_colors) < 2:
        errors.append("source prefix must use at least two nonzero colors")

    mode = "unknown"
    if 1 < pattern_width <= width:
        has_hole = any(
            grid[row][col] == 0
            for row in range(height)
            for col in range(1, pattern_width)
        )
        if has_hole:
            mode = "sparse_holes"
        elif all(grid[row][pattern_width - 1] == grid[row][0] for row in range(height)):
            mode = "edge_matched_dense"
        else:
            mode = "edge_mismatch_dense"

    return {
        "errors": sorted(set(errors)),
        "grid_h": height,
        "grid_w": width,
        "pattern_w": pattern_width,
        "palette_size": len(nonzero_colors),
        "pattern_mode": mode,
        "row_colors": [grid[row][0] for row in range(height)],
        "contrast_cells": contrast_cells,
        "middle_width": max(0, width - 2 * pattern_width),
        "zero_holes": [
            (row, col)
            for row in range(height)
            for col in range(1, min(pattern_width, width))
            if grid[row][col] == 0
        ],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, and rule-hiding input scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "pattern_w": analysis["pattern_w"],
        "palette_size": analysis["palette_size"],
        "pattern_mode": analysis["pattern_mode"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; the Racket rule remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    height = analysis["grid_h"]
    width = analysis["grid_w"]
    pattern_width = analysis["pattern_w"]
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            if col < pattern_width:
                output[row][col] = grid[row][col]
            elif col >= width - pattern_width:
                output[row][col] = grid[row][col - (width - pattern_width)]
            else:
                output[row][col] = grid[row][0]
    return output


def _lawful_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def strict_canonical_like(grid) -> list[str]:
    """Return [] exactly for lawful instances of this task's input grammar."""
    return list(_analyze(grid)["errors"])


def _witness(grid: Any, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _lawful_analysis(grid)
    return False if analysis is None else bool(predicate(analysis))


def _fill_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = _lawful_analysis(grid)
    if analysis is None:
        raise ValueError("malformed source grid")
    pw = analysis["pattern_w"]
    out = [row[:] for row in grid]
    for row in range(analysis["grid_h"]):
        for col in range(pw, analysis["grid_w"]):
            out[row][col] = grid[row][0]
    return out


def _mirror_copy(grid: list[list[int]]) -> list[list[int]]:
    analysis = _lawful_analysis(grid)
    if analysis is None:
        raise ValueError("malformed source grid")
    h, w, pw = analysis["grid_h"], analysis["grid_w"], analysis["pattern_w"]
    out = full_grid(h, w, 0)
    for row in range(h):
        for col in range(w):
            if col < pw:
                out[row][col] = grid[row][col]
            elif col >= w - pw:
                offset = col - (w - pw)
                out[row][col] = grid[row][pw - 1 - offset]
            else:
                out[row][col] = grid[row][0]
    return out


def _edge_matched_only_copy(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: assume the copied prefix always ends in the row color."""
    analysis = _lawful_analysis(grid)
    if analysis is None:
        raise ValueError("malformed source grid")
    out = rule_mirror(grid)
    last = analysis["grid_w"] - 1
    for row in range(analysis["grid_h"]):
        out[row][last] = grid[row][0]
    return out


def _nonzero_overlay(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: copy only nonzero source cells over a row-color fill."""
    analysis = _lawful_analysis(grid)
    if analysis is None:
        raise ValueError("malformed source grid")
    h, w, pw = analysis["grid_h"], analysis["grid_w"], analysis["pattern_w"]
    out = _fill_only(grid)
    for row in range(h):
        for offset in range(pw):
            value = grid[row][offset]
            if value != 0:
                out[row][w - pw + offset] = value
    return out


def _modal_fill(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: fill every middle row with one global modal row color."""
    analysis = _lawful_analysis(grid)
    if analysis is None:
        raise ValueError("malformed source grid")
    out = rule_mirror(grid)
    modal = Counter(analysis["row_colors"]).most_common(1)[0][0]
    for row in range(analysis["grid_h"]):
        for col in range(analysis["pattern_w"], analysis["grid_w"] - analysis["pattern_w"]):
            out[row][col] = modal
    return out


def _adjacent_copy(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: duplicate the prefix immediately after its divider."""
    analysis = _lawful_analysis(grid)
    if analysis is None:
        raise ValueError("malformed source grid")
    h, w, pw = analysis["grid_h"], analysis["grid_w"], analysis["pattern_w"]
    out = full_grid(h, w, 0)
    for row in range(h):
        for col in range(w):
            if col < pw:
                out[row][col] = grid[row][col]
            elif col < 2 * pw:
                out[row][col] = grid[row][col - pw]
            else:
                out[row][col] = grid[row][0]
    return out


SEMANTIC_RIVALS = {
    "fill_only": _fill_only,
    "mirror_copy": _mirror_copy,
    "edge_matched_only_copy": _edge_matched_only_copy,
    "nonzero_overlay": _nonzero_overlay,
    "modal_fill": _modal_fill,
    "adjacent_copy": _adjacent_copy,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "edge_matched_only_copy": _edge_matched_only_copy,
    "nonzero_overlay": _nonzero_overlay,
}

SEMANTIC_WITNESSES = {
    "canonical_edge_match": lambda grid: _witness(
        grid, lambda a: a["pattern_mode"] == "edge_matched_dense"
    ),
    "edge_mismatch_copy": lambda grid: _witness(
        grid, lambda a: a["pattern_mode"] == "edge_mismatch_dense"
    ),
    "copied_zero_hole": lambda grid: _witness(
        grid, lambda a: bool(a["zero_holes"])
    ),
    "row_specific_fill": lambda grid: _witness(
        grid, lambda a: len(set(a["row_colors"])) >= 2 and a["middle_width"] >= 2
    ),
    "far_edge_placement": lambda grid: _witness(
        grid,
        lambda a: a["middle_width"] >= 2
        and any(col == 1 for _row, col in a["contrast_cells"]),
    ),
    "pattern_width_3": lambda grid: _witness(grid, lambda a: a["pattern_w"] == 3),
    "pattern_width_4": lambda grid: _witness(grid, lambda a: a["pattern_w"] == 4),
}

WITNESS_RIVALS = {
    "canonical_edge_match": ["fill_only"],
    "edge_mismatch_copy": ["mirror_copy", "edge_matched_only_copy"],
    "copied_zero_hole": ["nonzero_overlay"],
    "row_specific_fill": ["modal_fill"],
    "far_edge_placement": ["adjacent_copy"],
    "pattern_width_3": ["fill_only"],
    "pattern_width_4": ["fill_only"],
}

SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del seed, difficulty
    return sample_index % len(_MODE_SCHEDULE)


def lesson_identifiable(demos, query) -> list[str]:
    """Return [] when the demos eliminate every rival that changes the query."""
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    if _lawful_analysis(query_input) is None:
        return ["query input is not a lawful copy-and-fill scene"]
    query_truth = rule_mirror(query_input)

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or _lawful_analysis(demo.get("input")) is None:
            reasons.append(f"demo {index} input is not a lawful copy-and-fill scene")
            continue
        expected = rule_mirror(demo["input"])
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the copy-and-fill rule")
            continue
        valid_demos.append(demo)
    if reasons:
        return sorted(set(reasons))

    for name, rival in sorted(LESSON_COMPETITORS.items()):
        survives = all(rival(demo["input"]) == demo["output"] for demo in valid_demos)
        if survives and rival(query_input) != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo yet answers the query differently"
            )
    return sorted(set(reasons))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, observable, curriculum-safe input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, pattern_width, palette_size = _default_axes(ctx, sample_index, difficulty)
    mode = _scheduled_choice(
        ctx,
        "pattern_mode",
        PATTERN_MODES,
        _MODE_SCHEDULE[sample_index % len(_MODE_SCHEDULE)],
    )

    palette = list(ctx.draw_distinct_colors("palette", n=palette_size, exclude={0}))
    grid = _build_prefix(
        height,
        width,
        pattern_width,
        palette,
        mode,
        ctx.draw_rng("prefix_layout"),
    )
    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise ValueError("generated an invalid scene: " + "; ".join(findings))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "pattern_w": pattern_width,
        "palette_size": palette_size,
        "pattern_mode": mode,
    }
    if observed != expected:
        raise ValueError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return grid
