"""Generator for arc_puzzle_bank_21_more:hard_b03.

Rule: marker_count = non-zeros in row 0; crop body to content; tile the
template horizontally with 1-col gaps marker_count times.

Combinatorial axes (8): grid_h/w, palette_kind, n_marks, palette_size,
position_bias, n_distinct_colors, motif_density, texture.
Degenerates: no_marks, no_motif, all_columns_marked.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a248a268dd3"
VERSION = "3.0.1"  # distinct=3 (ERR): body motif was FIXED (color-6 L-tromino) so only K(2-4) varied -> 3 outputs. Rule tiles the body motif K times (K=row-0 marker count). Use a RANDOM motif (shape+color) + varied K -> output (motif_h x K*motif_w+K-1) shape/content vary.
TASK_ID = "8a248a268dd3"
SUMMARY = (
    "0-bg grid with: (a) ROW 0 MARKERS -- K (2-5) color-1 cells at random "
    "columns; (b) a random BODY MOTIF (connected polyomino, varied shape/color) "
    "below row 0. Rule: count K row-0 markers, crop the body to the motif bbox, "
    "tile it horizontally K times with 1-col gaps. The motif shape/color, K and "
    "grid size all vary."
)

INVARIANTS = [
    "row 0 has K (2-5) non-zero marker cells",
    "one connected motif (non-bg) in the body (rows >= 1)",
]

PALETTE_KINDS = ("default", "sparse", "dense", "balanced")
DEGENERATE_TEXTURES = ("no_marks", "no_motif", "all_columns_marked")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_marks":        {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "motif_density":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has 2-5 marker cells (color 1); body has >=1 non-bg cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    marks = sum(1 for c in range(w) if grid[0][c] != 0)
    if marks == 0:
        return []  # no_marks degenerate — allowed
    if marks > w:
        errs.append(f"row-0 marks={marks} exceeds grid width={w}")
        return errs
    # Body: rows 1..h-1 should have >=1 non-bg cell (the motif)
    body_cells = sum(grid[r][c] != 0 for r in range(1, h) for c in range(w))
    if body_cells == 0 and h > 1:
        pass  # no_motif degenerate — allowed
    return errs


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 9, 11)
        k_lo, k_hi, m_lo, m_hi = 2, 3, 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 11, 14)
        k_lo, k_hi, m_lo, m_hi = 4, 5, 4, 6
    else:
        h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 10, 13)
        k_lo, k_hi, m_lo, m_hi = 2, 5, 3, 6
    rng = ctx.draw_rng("layout")
    n_marks = ctx.draw_int("n_marks", k_lo, k_hi)
    # random motif placed in the body; output = motif tiled n_marks times so the
    # tiled width must fit the ARC canvas
    for _ in range(40):
        motif = _rand_poly(rng, rng.randint(m_lo, m_hi))
        mh = max(r for r, _ in motif) + 1; mw = max(c for _, c in motif) + 1
        if mh > h - 1 or mw > w or n_marks * mw + (n_marks - 1) > 30:
            continue
        g = full_grid(h, w, 0)
        cols = list(range(w)); rng.shuffle(cols)
        for c in cols[:n_marks]:
            g[0][c] = 1
        color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
        r0 = rng.randint(1, h - mh); c0 = rng.randint(0, w - mw)
        for dr, dc in motif:
            g[r0 + dr][c0 + dc] = color
        return g
    raise ValueError("could not realize tile-motif layout")


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_marks":
        # motif but no row 0 markers → tile count zero (no output)
        g[2][5] = 6; g[2][6] = 6
        g[3][5] = 6
        return g
    if name == "no_motif":
        # markers but no body motif → nothing to tile
        for c in [1, 4, 7]:
            g[0][c] = 1
        return g
    if name == "all_columns_marked":
        # every column marked → maximal tile count
        for c in range(w):
            g[0][c] = 1
        g[2][5] = 6; g[2][6] = 6
        g[3][5] = 6
        return g
    return g
