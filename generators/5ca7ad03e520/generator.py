"""Generator for arc_puzzle_bank_21_set19_s:S19_M3 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5ca7ad03e520"
VERSION = "2.2.0"  # oversize n-clamp (hard n7 -> w34 -> clipped) + AXES literals + wider palette
TASK_ID = "5ca7ad03e520"

SUMMARY = (
    "Grid split into N panels (~5-6) by 1-wide full-height "
    "color-9 (maroon) separator COLUMNS. Each panel of width "
    "panel_w (~4-5). Panel 0 holds a SOURCE motif (1-3 cells "
    "in some non-{0,9} color); remaining panels are CANDIDATES "
    "(each with their own 1-3 cell motif). Rule: split by "
    "color-9 cols. Normalize source's cells (anchored at "
    "(0,0)). For each candidate panel, normalize its cells "
    "the same way. Compare normalized cell-sets to source's. "
    "Output: 1×(N-1) strip where cell c is 8 (cyan) if "
    "candidate panel c's normalized cells match source's "
    "exactly, else 0."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "panels separated by 1-wide full-height color-9 columns",
    "each panel has a small motif (1-3 cells) in some non-{0, 9} color",
    "≥1 candidate panel matches the source motif (normalized) so output has a cyan cell",
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
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 5)
        n = ctx.draw_int("n_panels", 6, 7)
    else:
        panel_h = ctx.draw_int("panel_h", 4, 5)
        n = ctx.draw_int("n_panels", 5, 6)
    rng = ctx.draw_rng("layout")

    panel_w = 4
    # W = n*(panel_w+1) - 1 must fit the 30-col canvas (hard n=7 -> 34 -> clipped/corrupt).
    n = min(n, 31 // (panel_w + 1))
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h): g[r][c] = 9

    # Build a source motif and place it in panel 0.
    src_cells = _build_motif(rng, rng.randint(2, 3))
    rs = [r for r, _ in src_cells]; cs = [c for _, c in src_cells]
    src_norm = sorted([(r - min(rs), c - min(cs)) for r, c in src_cells])
    sh = max(r for r, _ in src_norm) + 1
    sw = max(c for _, c in src_norm) + 1
    if sh > h or sw > panel_w:
        src_norm = [(0, 0), (0, 1)]; sh, sw = 1, 2
    src_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    # Place panel 0 motif at a random position
    tr = rng.randint(0, max(0, h - sh))
    tc = rng.randint(0, max(0, panel_w - sw))
    for r, c in src_norm:
        g[tr + r][tc + c] = src_color

    # For each remaining panel, either:
    # - place a translated/recolored copy of src (matches normalized → 8)
    # - place a different motif (doesn't match → 0)
    cand_motifs = [
        [(0, 0)],
        [(0, 0), (1, 0)],
        [(0, 0), (0, 1)],
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 1)],
    ]
    n_match = rng.randint(1, max(1, n - 2))
    match_slots = set(rng.sample(range(1, n), n_match))
    for k in range(1, n):
        c_off = k * (panel_w + 1)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        if k in match_slots:
            tr2 = rng.randint(0, max(0, h - sh))
            tc2 = rng.randint(0, max(0, panel_w - sw))
            for r, c in src_norm:
                g[tr2 + r][c_off + tc2 + c] = color
        else:
            for _try in range(20):
                cand = rng.choice([m for m in cand_motifs if sorted(m) != src_norm])
                cr = [r for r, _ in cand]; cc = [c for _, c in cand]
                cnorm = sorted([(r - min(cr), c - min(cc)) for r, c in cand])
                ch = max(r for r, _ in cnorm) + 1
                cw = max(c for _, c in cnorm) + 1
                if ch > h or cw > panel_w:
                    continue
                if cnorm == src_norm:
                    continue
                tr2 = rng.randint(0, max(0, h - ch))
                tc2 = rng.randint(0, max(0, panel_w - cw))
                for r, c in cnorm:
                    g[tr2 + r][c_off + tc2 + c] = color
                break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, color-9 dividers present, >=2 non-{0,9} motif cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    nines = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not nines:
        errs.append("no full-height color-9 divider columns found")
    motif = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 9)]
    if len(motif) < 2:
        errs.append(f"expected >=2 motif cells, found {len(motif)}")
    return errs


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
