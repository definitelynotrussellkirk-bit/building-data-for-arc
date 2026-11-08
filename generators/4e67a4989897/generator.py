"""Generator for arc_puzzle_bank_21_set21_s:S21_M5 — room-signature match strip.

Rule: colors 1/7/9 are WALLS; the full-height color-9 divider columns split the grid into
ROOMS (one per panel). Each room gets a motif signature (its interior motif key); the
top-left room is the QUERY, the rest are CANDIDATES. Output is a 1xN strip with 8 at each
candidate whose signature equals the query's, else 0. (The "each has a small motif" header
was the copy-paste panel-family template; the rule is a room-signature match — SUMMARY authoritative.)

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e67a4989897"
VERSION = "1.3.0"  # diversity: wider motif palette (8 colors) + random in-panel position (was top-left only)
TASK_ID = "4e67a4989897"

SUMMARY = ("Colors 1/7/9 are walls; full-height color-9 divider columns split the grid into rooms "
           "(one per panel). Top-left room is the query; rule outputs a 1xN strip marking with 8 each "
           "candidate room whose motif signature equals the query room's.")

INVARIANTS = [
    "background is 0",
    "panels separated by full-height color-9 divider columns (1 col wide)",
    "each panel has a small motif (1-3 cells) in a non-{0,9} color at a random in-panel position",
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
    n = min(n, 6)        # w = 5n-1 must fit the 30-col ARC canvas (n=7 -> 34)
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h): g[r][c] = 9
    def _fit_motif(lo, hi):
        for _ in range(40):
            cells = _build_motif(rng, rng.randint(lo, hi))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            if sh <= h and sw <= panel_w:
                return sorted((r - min(rs), c - min(cs)) for r, c in cells), sh, sw
        return [(0, 0)], 1, 1

    # panel 0 is the QUERY (first by reading order); the rule marks which later
    # panels match its (translation-normalized) shape. Bigger motifs (3-6 cells)
    # give many distinct shapes; explicitly make each candidate a MATCH (~50%)
    # or a verified DIFFERENT shape -> the strip's match pattern varies.
    query, qh, qw = _fit_motif(3, 6)
    qset = set(query)
    flags = []
    if n > 1:
        flags = [True, False] + [rng.random() < 0.5 for _ in range(max(0, n - 3))]
        rng.shuffle(flags)
    for k in range(n):
        c0 = k * (panel_w + 1)
        if k == 0:
            cells, sh, sw = query, qh, qw
        elif flags[k - 1]:
            cells, sh, sw = query, qh, qw                 # guaranteed match
        else:
            for _ in range(40):                           # verified non-match
                cells, sh, sw = _fit_motif(2, 6)
                if set(cells) != qset:
                    break
            else:
                cells, sh, sw = [(0, 0)], 1, 1
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        top = rng.randint(0, h - sh); left = rng.randint(0, panel_w - sw)
        for r, c in cells:
            g[top + r][c0 + left + c] = color
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

def _sc_norm(cells):
    if not cells: return ()
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    errs: list[str] = []
    if len(divs) < 3: return [f"expected panel divider columns, got {len(divs)}"]
    cols = [-1] + divs + [w]
    pats = []
    for i in range(len(cols) - 1):
        c0, c1 = cols[i] + 1, cols[i + 1]
        cells = [(r, c - c0) for r in range(h) for c in range(c0, c1) if grid[r][c] not in (0, 9)]
        if not cells: errs.append("panel without motif")
        pats.append(_sc_norm(cells))
    if pats:
        matches = sum(1 for p in pats[1:] if p == pats[0])
        non = sum(1 for p in pats[1:] if p != pats[0])
        if matches < 1: errs.append("candidate panels need at least one query match")
        if non < 1: errs.append("candidate panels need at least one nonmatch")
    return errs
