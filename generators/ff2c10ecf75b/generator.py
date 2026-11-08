"""Generator for arc_puzzle_bank_21_set19_s:S19_M2 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ff2c10ecf75b"
VERSION = "3.0.0"  # well-formed: guaranteed unique matching pair + distinct distractors; wider panels/motifs
TASK_ID = "ff2c10ecf75b"

SUMMARY = (
    "Horizontally-assembled 0-bg grid: n (4-7) PANELS (each panel_w "
    "4-5 cols wide, panel_h 4-6 tall) separated by FULL-HEIGHT COLOR-9 "
    "1-col DIVIDERS. PANEL 0 holds a QUERY motif (1-5 connected cells "
    "in a non-{0,9} color); EXACTLY ONE other panel holds the SAME "
    "shape (any color/position); every remaining panel holds a "
    "DISTINCT-shape distractor. Rule: split on the 9-dividers; take "
    "panel 0's normalized occupied-cell shape; find the first later "
    "panel whose normalized shape matches; OUTPUT that matched panel "
    "recolored to 8 (or an empty grid if none matches)."
)

INVARIANTS = [
    "background is 0",
    "panels separated by full-height color-9 divider columns",
    "panel 0 holds the query motif; exactly one later panel matches its shape",
    "all other panels are distinct-shape distractors (so the match is unique)",
    "motif colors are non-{0, 9} (the rule matches by shape, color-blind)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..6", "valid": "3..6"},
    "panel_w":        {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "n_panels":       {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "rng 1..5", "valid": "1..5"},
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
    guard = 0
    while len(cells) < k and guard < 200:
        guard += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        panel_h = ctx.draw_int("panel_h", 4, 5)
        panel_w = ctx.draw_int("panel_w", 4, 4)
        n = ctx.draw_int("n_panels", 4, 5)
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 6)
        panel_w = ctx.draw_int("panel_w", 4, 5)
        n = ctx.draw_int("n_panels", 5, 7)
    else:
        panel_h = ctx.draw_int("panel_h", 4, 6)
        panel_w = ctx.draw_int("panel_w", 4, 5)
        n = ctx.draw_int("n_panels", 5, 6)
    rng = ctx.draw_rng("layout")

    # W = n*(panel_w+1) - 1 must fit the 30-col canvas.
    n = min(n, 31 // (panel_w + 1))
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h):
            g[r][c] = 9

    pal = [1, 2, 3, 4, 5, 6, 7, 8]
    mmax = min(5, panel_h * panel_w)

    def fitting_motif(exclude_norm=None):
        for _ in range(60):
            cells = _build_motif(rng, rng.randint(1, mmax))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            if max(rs) - min(rs) + 1 > h or max(cs) - min(cs) + 1 > panel_w:
                continue
            nrm = _norm(cells)
            if exclude_norm is not None and nrm == exclude_norm:
                continue
            return cells, nrm
        return [(0, 0)], ((0, 0),)

    def paint(k, cells):
        c0 = k * (panel_w + 1)
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        top = rng.randint(0, h - sh); left = rng.randint(0, panel_w - sw)
        color = rng.choice(pal)
        for r, c in cells:
            g[top + r - min(rs)][c0 + left + c - min(cs)] = color

    # WELL-FORMED: panel 0 holds the QUERY shape; plant the SAME shape (any color,
    # any in-panel position -> the rule normalizes, so it still matches) in exactly
    # ONE other panel; all remaining panels get shapes whose normalized form differs
    # from the query (distractors). This guarantees the rule finds the unique match
    # (was: independent random motifs -> usually no match -> empty output).
    query, qn = fitting_motif()
    match_idx = rng.randint(1, n - 1) if n > 1 else 0
    for k in range(n):
        if k == 0 or k == match_idx:
            paint(k, query)
        else:
            cells, _ = fitting_motif(exclude_norm=qn)
            paint(k, cells)
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


def _selfcheck_norm(cells):
    if not cells:
        return tuple()
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _selfcheck_panel_shape(panel):
    return _selfcheck_norm([(r, c) for r, row in enumerate(panel) for c, v in enumerate(row) if v not in (0, 9)])


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not (3 <= len(divs) <= 6):
        errors.append(f"expected 4..7 panels separated by 3..6 full dividers, found {len(divs)} dividers")
    panels = []
    last = 0
    for d in divs:
        panels.append([row[last:d] for row in grid]); last = d + 1
    panels.append([row[last:w] for row in grid])
    panels = [p for p in panels if p and p[0]]
    if any(v == 9 for p in panels for row in p for v in row):
        errors.append("panel interiors must not contain color 9; 9 is reserved for dividers")
    if len(panels) >= 2:
        query = _selfcheck_panel_shape(panels[0])
        if not query:
            errors.append("query panel must contain a motif")
        matches = [i for i, p in enumerate(panels[1:], start=1) if _selfcheck_panel_shape(p) == query]
        if len(matches) != 1:
            errors.append(f"expected exactly one later panel matching panel 0, found {matches}")
    return errors

