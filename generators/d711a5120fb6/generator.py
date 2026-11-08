"""Generator for arc_puzzle_bank_twelfth21:H79 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d711a5120fb6"
VERSION = "2.1.1"  # holistic: oversize n-clamp + AXES literals + diversity (8-color palette + random in-panel position)
TASK_ID = "d711a5120fb6"

SUMMARY = (
    "Grid laid out as N PANELS (5-6) of size panel_h × 4 "
    "(panel_h~4-5), side-by-side, separated by full-"
    "height color-9 (maroon) DIVIDER columns. Each panel "
    "contains a small 4-conn motif (1-3 cells) in some "
    "non-{0, 9} color. Rule: detect the panels by "
    "splitting at the color-9 divider columns. Find the "
    "MATCHING PAIR (two panels with the same shape "
    "modulo color or rotation). Output: a compact "
    "representation."
)

INVARIANTS = [
    "background is 0",
    "panels separated by full-height color-9 divider columns (1 col wide)",
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
        n = ctx.draw_int("n_panels", 6, 6)   # rule XORs panels 3&4 -> 6th panel; needs exactly 6 panels (starts[5])
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 5)
        n = ctx.draw_int("n_panels", 6, 6)
    else:
        panel_h = ctx.draw_int("panel_h", 4, 5)
        n = ctx.draw_int("n_panels", 6, 6)
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
    # The canonical rule XORs panel 3 and panel 4 (0-indexed), then pastes the
    # result into panel 5.  The target panel must therefore start empty, and the
    # two source panels must not have identical occupancy masks; otherwise the
    # generated demonstration can be an identity/no-op.
    masks = []
    for k in range(n):
        c0 = k * (panel_w + 1)
        if k == 5:
            masks.append(set())
            continue
        for _attempt in range(40):
            cells = _build_motif(rng, rng.randint(1, 3))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            if sh > h or sw > panel_w:
                continue
            top = rng.randint(0, h - sh); left = rng.randint(0, panel_w - sw)
            norm = {(top + r - min(rs), left + c - min(cs)) for r, c in cells}
            if k == 4 and len(masks) > 3 and norm == masks[3]:
                continue
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
            for rr, cc in norm:
                g[rr][c0 + cc] = color
            masks.append(norm)
            break
        else:
            # Conservative fallback: a single cell that differs from panel 3.
            rr, cc = (0, 0) if k != 4 or not masks[3] or (0, 0) not in masks[3] else (0, 1)
            g[rr][c0 + cc] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
            masks.append({(rr, cc)})
    return g


def _panel_masks(grid):
    seps = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    starts = [0] + [c + 1 for c in seps]
    ends = seps + [len(grid[0])]
    masks = []
    for a, b in zip(starts, ends):
        if b <= a:
            continue
        masks.append({(r, c - a) for r, row in enumerate(grid)
                      for c in range(a, b) if row[c] not in (0, 9)})
    return masks


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    seps = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    if len(seps) < 5:
        errs.append("expected at least five full-height color-9 divider columns")
    masks = _panel_masks(grid)
    if len(masks) < 6:
        errs.append(f"expected at least six panels, found {len(masks)}")
        return errs
    if not masks[3] or not masks[4]:
        errs.append("source panels 3 and 4 must both contain motif evidence")
    if masks[3] == masks[4]:
        errs.append("source panels 3 and 4 must differ so their XOR is nonempty")
    if masks[5]:
        errs.append("target panel 5 should start empty before the XOR paste")
    return errs


def _draw_from_degenerate(name, rng):
    panel_h, n, panel_w = 4, 6, 4   # rule needs 6 panels
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
