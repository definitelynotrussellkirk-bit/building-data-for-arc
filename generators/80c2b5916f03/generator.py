"""Generator for puzzle 97999447.

Rule: for each non-bg, non-gray cell at (r, c), shoot a trail rightward
from (r, c) to (r, w-1), alternating between the cell's color and 5.

Combinatorial axes (8): grid_h/w, n_sources, palette_size,
source_layout, source_position_bias, decoy_density, decoy_palette_size,
column_constraint.
Degenerates: single_source, all_sources_at_right_edge, no_sources.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "80c2b5916f03"
VERSION = "2.0.2"
TASK_ID = "80c2b5916f03"
SUMMARY = (
    "0-bg grid (h~6-12, w~8-18) with 2-6 "
    "SPARSE NON-BG NON-GRAY (non-{0, 5}) "
    "SOURCE CELLS each placed in a DISTINCT "
    "row, following one of 5 LAYOUTS "
    "(evenly_spaced / clustered / left_"
    "biased / diagonal / random) and one "
    "of 3 POSITION BIASES (left / center / "
    "spread). Each source is painted with "
    "a color drawn from a small palette of "
    "2-4 distinct non-{0, 5} colors. Each "
    "source has ≥2 bg cells to its right "
    "(constraint: source column ≤ w - 4 to "
    "guarantee trail room). Optionally, "
    "decoy cells (0..0.05 density) in non-"
    "source non-trail palette are "
    "scattered. Rule (FOR EACH SOURCE CELL, "
    "SHOOT A COLOR/5 ALTERNATING TRAIL "
    "RIGHTWARD): for EACH non-bg non-gray "
    "SOURCE at (r, c) with color C: PAINT "
    "cells (r, c), (r, c+1), (r, c+2), "
    "..., (r, w-1) alternating between "
    "COLOR C and COLOR 5 — i.e., (r, c) = "
    "C, (r, c+1) = 5, (r, c+2) = C, (r, "
    "c+3) = 5, etc. The trail extends "
    "until the right edge. Other rows "
    "(non-source) stay unchanged. Net: "
    "each source casts a striped color/"
    "gray trail to the right wall."
)

INVARIANTS = [
    "background is 0",
    ">=2 non-bg, non-gray cells, each in a different row",
    "each source cell has >=2 bg cells to its right",
    "no source is in column w-1 (trail must have room)",
    "normal examples contain no decoy nonzero cells because every nonzero non-5 cell is a source",
]

SOURCE_LAYOUTS = ("evenly_spaced", "clustered", "left_biased",
                  "diagonal", "random")
DEGENERATE_TEXTURES = ("single_source", "all_sources_at_right_edge", "no_sources")
HELPFUL_TEXTURES = SOURCE_LAYOUTS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "grid_w":              {"type": "int", "default": "rng 8..14", "valid": "5..18"},
    "n_sources":           {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":        {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "source_layout":       {"type": "str", "default": "rng helpful",
                            "valid": "|".join(SOURCE_LAYOUTS)},
    "source_position_bias": {"type": "str", "default": "rng left|center|spread",
                             "valid": "left|center|spread"},
    "decoy_density":       {"type": "float", "default": "0", "valid": "0"},
    "decoy_palette_size":  {"type": "int", "default": "0", "valid": "0"},
    "texture":             {"type": "str", "default": "alias for source_layout",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify distinct-row source cells with trail room and no gray blockers."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    sources = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
               if grid[r][c] not in (0, 5)]
    if not sources:
        return []
    errs = []
    rows = [r for r, _, _ in sources]
    if len(sources) < 2:
        errs.append(f"expected at least two source cells, got {len(sources)}")
    if len(rows) != len(set(rows)):
        errs.append("normal examples should have at most one source cell per row")
    for r, c, color in sources:
        if c > w - 3:
            errs.append(f"source at {(r, c)} lacks at least two cells of trail room")
        if any(grid[r][cc] != 0 for cc in range(c + 1, w)):
            errs.append(f"source row {r} has nonzero cells to the right of the source")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 4, 6, 6, 9, 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 9, 12, 12, 18, 4, 6
    else:
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 6, 10, 8, 14, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_sources = int(overrides.get("n_sources",
                                  ctx.draw_int("n_sources", n_lo, n_hi)))
    n_sources = max(2, min(h, n_sources))
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 4)))
    palette = list(ctx.draw_distinct_colors(
        "palette", n=max(1, n_palette), exclude={0, 5})) or [1]
    layout = (overrides.get("texture") or overrides.get("source_layout")
              or ctx.draw_choice("source_layout", list(SOURCE_LAYOUTS)))
    pos_bias = overrides.get("source_position_bias",
                             ctx.draw_choice("source_position_bias",
                                             ["left", "center", "spread"]))
    if int(overrides.get("decoy_palette_size", 0)) != 0 or float(overrides.get("decoy_density", 0.0)) != 0.0:
        raise ValueError("decoy cells are disabled because the canonical rule treats every nonzero non-5 cell as a source")
    n_decoy = 0
    decoy_d = 0.0
    g = full_grid(h, w, 0)
    rows = _pick_rows(layout, h, n_sources, rng)
    cols = _pick_cols(layout, pos_bias, w, n_sources, rng)
    placed = 0
    for r, c in zip(rows, cols):
        c = max(0, min(w - 3, c))
        g[r][c] = palette[placed % len(palette)]
        placed += 1
    if placed < 2:
        for r in range(h):
            if all(v == 0 for v in g[r]):
                c = min(1, w - 3)
                g[r][c] = palette[placed % len(palette)]
                placed += 1
                if placed >= 2:
                    break
    if placed < 2:
        raise ValueError("could not place at least two source rows")
    decoy_pool = [c for c in range(1, 10) if c not in (0, 5) and c not in palette]
    rng.shuffle(decoy_pool)
    decoy_palette = decoy_pool[:max(0, n_decoy)]
    if decoy_palette and decoy_d > 0:
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and rng.random() < decoy_d:
                    g[r][c] = rng.choice(decoy_palette)
    return g


def _pick_rows(layout, h, n, rng):
    if layout == "evenly_spaced":
        step = max(1, h // (n + 1))
        return [step * (i + 1) for i in range(n) if step * (i + 1) < h]
    if layout == "clustered":
        cr = rng.randint(0, h - 1)
        rs = sorted(range(h), key=lambda r: abs(r - cr))
        return sorted(rs[:n])
    if layout == "diagonal":
        return list(range(min(n, h)))
    rs = list(range(h))
    rng.shuffle(rs)
    return sorted(rs[:n])


def _pick_cols(layout, bias, w, n, rng):
    if layout == "diagonal":
        return list(range(min(n, w - 3)))
    if bias == "left":
        return [rng.randint(0, max(0, w // 3)) for _ in range(n)]
    if bias == "center":
        return [rng.randint(max(0, w // 4), max(0, 3 * w // 4 - 3)) for _ in range(n)]
    return [rng.randint(0, max(0, w - 4)) for _ in range(n)]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = [c for c in range(1, 10) if c != 5]
    rng.shuffle(palette)
    if name == "single_source":
        g[h // 2][1] = palette[0]
        return g
    if name == "all_sources_at_right_edge":
        for r in range(min(3, h)):
            g[r][w - 1] = palette[r % len(palette)]
        return g
    if name == "no_sources":
        return g
    return g
