"""Generator for arc_puzzle_bank_21_set23_s:S23_H6 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3642ceca5803"
VERSION = "1.4.0"  # +self_check  # robustness: clamp N panels to <=30 cols (hard reached 41)
TASK_ID = "3642ceca5803"

SUMMARY = "N panels separated by full color-9 columns, each with a small motif; rule picks the pair with matching shape."

# Rivals: 'output the leftmost motif' refuted by ≥2 demos where the
# matching pair is elsewhere. 'output a fixed color' refuted by ≥2
# demos with different matched-pair colors. 'output only one motif
# of the matching pair' refuted by ≥1 demo where both pair motifs
# are present in the output.
# 4 demos covering varied n_panels, panel_w, and matched-pair positions.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "panels separated by full color-9 columns of width 4",
    "each panel has a small motif (1-3 cells) in some non-{0, 9} color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "n_panels":       {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "horizontal_panels_9divs",
                       "valid": "horizontal_panels_9divs"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_dividers|empty_panels|single_panel"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 full color-9 column divider; ≥1 motif cell (non-{0,9})."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    has_div = any(all(grid[r][c] == 9 for r in range(h)) for c in range(w))
    if not has_div:
        errs.append("no full color-9 column divider found")
    has_motif = any(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    if not has_motif:
        errs.append("no motif cells (non-{0,9}) found")
    return errs


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        panel_h = ctx.draw_int("panel_h", 4, 4)
        n = ctx.draw_int("n_panels", 4, 5)
        panel_w = 3
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 6)
        n = ctx.draw_int("n_panels", 6, 7)
        panel_w = 5
    else:
        panel_h = ctx.draw_int("panel_h", 4, 5)
        n = ctx.draw_int("n_panels", 5, 6)
        panel_w = 4
    rng = ctx.draw_rng("layout")

    # Keep N panels + (N-1) separators within the 30-col ARC canvas (hard could
    # reach n=7 x pw=5 = 41). The rule only needs >=3 panels (it takes the 3rd).
    n = min(n, 31 // (panel_w + 1))

    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h): g[r][c] = 9
    # Color pool now includes 1 and 8 (was {2,3,4,5,6,7} only).
    color_pool = [1, 2, 3, 4, 5, 6, 7, 8]
    for k in range(n):
        c0 = k * (panel_w + 1)
        cells = _build_motif(rng, rng.randint(1, min(4, panel_h * panel_w // 2)))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        if sh > h or sw > panel_w: continue
        color = rng.choice(color_pool)
        # Random placement within panel (top/middle/bottom + left/center/right).
        top = rng.randint(0, h - sh)
        left = rng.randint(0, panel_w - sw)
        for r, c in cells:
            g[top + r - min(rs)][c0 + left + c - min(cs)] = color
    return g


def _draw_from_degenerate(name, rng):
    panel_h, n, panel_w = 4, 5, 4
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        for k in range(n):
            c0 = k * panel_w
            g[1][c0 + 1] = [4, 6, 7, 4, 6][k]
        return g
    if name == "empty_panels":
        for k in range(1, n):
            c = panel_w * k + (k - 1)
            for r in range(h): g[r][c] = 9
        return g
    if name == "single_panel":
        g[1][1] = 4
        return g
    return g
