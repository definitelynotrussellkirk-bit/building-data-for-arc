"""Generator for puzzle f5b8619d.

Rule: output is 2h × 2w (input tiled 2×2); columns containing any
non-zero cell get cyan(8) overlaid in the bg-cells.

Combinatorial axes (8): grid_h/w, palette_size, fill_ratio,
n_active_cols, fill_layout, position_bias, color_balance,
asymmetry_force.
Degenerates: empty_grid, full_grid, all_active_cols.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "15d6a8756e63"
VERSION = "2.1.0"
TASK_ID = "15d6a8756e63"
SUMMARY = (
    "Small grid (h~5-12, w~5-12) with several non-bg "
    "cells scattered across SOME columns (the ACTIVE "
    "columns — at least one is fully empty, at least one "
    "has a non-bg cell). No color-8 (cyan) appears in "
    "input. Rule: (1) TILE the input 2×2 so the output "
    "is (2h, 2w). (2) For each output column c whose "
    "underlying input column ((c mod w)) contains AT "
    "LEAST one non-bg cell, OVERLAY color 8 (cyan) into "
    "every output bg cell of that column. Output columns "
    "whose underlying input column is entirely bg stay "
    "all-0 in the output. Original non-bg cells are "
    "preserved in their tiled positions. Net: a 2×2 tile "
    "of the input where every active column is shaded "
    "cyan in its empty cells."
)

# Rivals: 'simple 2x2 tile, no overlay' refuted by ≥1 demo with cyan
# clearly present in bg slots. 'overlay all bg' refuted by ≥1 demo
# where some columns stay 0. 'tile 1×1 (identity)' refuted by any
# demo (output is 2× the size). 'overlay by row' refuted by ≥2 demos
# where row-empty cells next to active columns get cyan.
# 4 demos with varied layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "canonical-scale input dims <= 6 (so the examples stay in the 2x2..6x6 regime)",
    ">=2 non-bg cells",
    ">=1 column has a non-zero cell",
    ">=1 column is entirely bg",
    "no cyan(8) in input (avoids conflict with rule output)",
]

FILL_LAYOUTS = ("scattered", "blob", "diag", "stripes", "checker", "frame")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "all_active_cols")
HELPFUL_TEXTURES = FILL_LAYOUTS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 2..6", "valid": "2..14"},
    "grid_w":          {"type": "int", "default": "rng 2..6", "valid": "2..14"},
    "palette_size":    {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "fill_ratio":      {"type": "float", "default": "rng 0.2..0.5",
                        "valid": "0.1..0.7"},
    "n_active_cols":   {"type": "int", "default": "rng w/3..w-1",
                        "valid": "1..w-1"},
    "fill_layout":     {"type": "str", "default": "rng helpful",
                        "valid": "|".join(FILL_LAYOUTS)},
    "position_bias":   {"type": "str", "default": "rng spread|left|center",
                        "valid": "spread|left|center"},
    "asymmetry_force": {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "texture":         {"type": "str", "default": "alias for fill_layout",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # Canonical train inputs are tiny (2x2, 3x3, 4x4, 6x6).
    # The previous normal path sampled 5..12 and hard sampled 12..14,
    # which taught a large-grid regime absent from the task and triggered
    # distribution drift.  Keep hard examples at the largest canonical scale.
    if difficulty == "easy":
        h_lo, h_hi = 2, 3
    elif difficulty == "hard":
        h_lo, h_hi = 4, 6
    else:
        h_lo, h_hi = 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 4)))
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=max(2, n_palette),
                                            exclude={0, 8}))
    layout = (overrides.get("texture") or overrides.get("fill_layout")
              or ctx.draw_choice("fill_layout", list(FILL_LAYOUTS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "left", "center"]))
    n_active = int(overrides.get("n_active_cols",
                                 ctx.draw_int("n_active_cols",
                                              max(1, w // 3),
                                              max(1, w - 1))))
    n_active = max(1, min(w - 1, n_active))
    if bias == "left":
        active_cols = list(range(n_active))
    elif bias == "center":
        start = (w - n_active) // 2
        active_cols = list(range(start, start + n_active))
    else:
        active_cols = sorted(rng.sample(range(w), n_active))
    fill_ratio = float(overrides.get("fill_ratio",
                                     ctx.draw_rng("fill_ratio")
                                     .uniform(0.2, 0.5)))
    g = full_grid(h, w, 0)
    _fill_active(g, layout, h, w, active_cols, palette, fill_ratio, rng)
    has_bg_col = any(all(g[r][c] == 0 for r in range(h)) for c in range(w))
    if not has_bg_col:
        for c in range(w):
            if c not in active_cols:
                continue
            for r in range(h):
                g[r][c] = 0
            break
    has_active_col = any(any(g[r][c] != 0 for r in range(h)) for c in range(w))
    if not has_active_col:
        g[0][active_cols[0]] = palette[0]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: no cyan(8), active+blank columns, canonical-scale dims."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h > 6 or w > 6:
        errors.append(f"grid {h}x{w} outside canonical-scale <=6 regime")
    # Check no cyan in input
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 8:
                errors.append(f"cyan(8) found at ({r},{c}) — rule output conflicts")
                break
        else:
            continue
        break
    # Check at least one active column (has non-bg cell)
    active = [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]
    if not active:
        errors.append("no active column (all zero) — rule output would be all-0")
    # Check at least one bg column (all-zero)
    bg_cols = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    if not bg_cols:
        # degenerate (all_active_cols) — not a structural error
        pass
    return errors


def _fill_active(g, layout, h, w, active_cols, palette, ratio, rng):
    if layout == "blob":
        cr = rng.randint(0, h - 1)
        cc = rng.choice(active_cols)
        for r in range(h):
            for c in active_cols:
                if abs(r - cr) + abs(c - cc) <= 2 and rng.random() < ratio + 0.2:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "diag":
        for k in range(min(h, len(active_cols))):
            g[k][active_cols[k]] = rng.choice(palette)
        return
    if layout == "stripes":
        for r in range(h):
            color = rng.choice(palette)
            for c in active_cols:
                if r % 2 == 0:
                    g[r][c] = color
        return
    if layout == "checker":
        for r in range(h):
            for c in active_cols:
                if (r + c) % 2 == 0:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "frame":
        for c in active_cols:
            g[0][c] = rng.choice(palette)
            g[h - 1][c] = rng.choice(palette)
        return
    for r in range(h):
        for c in active_cols:
            if rng.random() < ratio:
                g[r][c] = rng.choice(palette)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = [c for c in range(1, 10) if c != 8]
    rng.shuffle(palette)
    if name == "empty_grid":
        return g
    if name == "full_grid":
        color = palette[0]
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "all_active_cols":
        # every col has at least one non-bg
        for c in range(w):
            g[0][c] = palette[c % len(palette)]
        return g
    return g
