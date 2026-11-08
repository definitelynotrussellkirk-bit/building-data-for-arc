"""Generator for arc_puzzle_bank_21_set12_s:S12_H2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, odd_panel, odd_shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, all_same, no_odd.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c60ba52071ec"
VERSION = "2.2.0"  # fix all_background: the output is the odd cluster recolored to 8; a block-polyomino with a FILLED bbox (odd_k=2 always; the 2x2 square; the I-line) yields a solid-8 rectangle. Use odd_k in {4,5,6} only and reject solid-rectangle polyominoes so the odd union always has a notch (output keeps 8 and 0).
TASK_ID = "c60ba52071ec"
SUMMARY = (
    "Fixed 8×26 0-bg grid with: "
    "(a) 2 FULL-HEIGHT COLOR-5 "
    "(gray) DIVIDER COLUMNS at "
    "col 8 and col 17, "
    "splitting the grid into "
    "3 PANELS of width 8 each; "
    "(b) TWO PANELS each "
    "contain a 3-COMPONENT "
    "CONTACT CHAIN (3 2×2 "
    "blocks at (3, 1), (3, 3), "
    "(3, 5)) — degree pattern "
    "[1, 1, 2]; (c) ONE PANEL "
    "(odd_panel ∈ 0..2) "
    "contains a 4-COMPONENT "
    "CHAIN drawn from 3 "
    "hardcoded shapes — "
    "degree pattern [1, 1, 2, "
    "2]. Each panel uses 4 "
    "distinct colors from "
    "{1..9}\\{0, 5}. Output "
    "uniq_out=3 (intrinsic — "
    "3 odd chain shapes, "
    "output recolored to 8). "
    "Rule (FIND ODD PANEL BY "
    "DEGREE MULTISET, CROP & "
    "RECOLOR TO 8): identify "
    "the 3 PANELS (separated "
    "by 5-divs). For EACH "
    "PANEL, compute the "
    "contact-chain DEGREE "
    "MULTISET. Find the "
    "ODD panel (unique "
    "degree multiset). EMIT "
    "the ODD panel's cluster "
    "cropped and RECOLORED "
    "uniformly to COLOR 8. "
    "Net: odd-out panel's "
    "shape, in cyan."
)

INVARIANTS = [
    "two full color-5 columns split the grid into three panels",
    "two panels contain a three-component contact chain with degree pattern [1,1,2]",
    "one panel contains a four-component contact chain with degree pattern [1,1,2,2]",
    "the output is the odd panel's contact cluster recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "all_same", "no_odd")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8", "valid": "8..12"},
    "grid_w":         {"type": "int", "default": "26", "valid": "26..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "odd_panel":      {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "odd_shape":      {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "3_panels_with_one_odd_chain",
                       "valid": "3_panels_with_one_odd_chain"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_ODD_CHAINS = [
    [(3, 0), (3, 2), (3, 4), (3, 6)],
    [(0, 3), (2, 3), (4, 3), (6, 3)],
    [(1, 1), (1, 3), (3, 3), (3, 5)],
]


def _block(g, top, left, color):
    for r in range(2):
        for c in range(2):
            g[top + r][left + c] = color


def _paint_chain(g, panel_left, starts, colors):
    for (top, left), color in zip(starts, colors):
        _block(g, top, panel_left + left, color)


def _block_poly(rng, k, max_bh, max_bw):
    """Connected block-lattice polyomino of k cells fitting in max_bh x max_bw
    (lattice cells); returns block-lattice coords normalized to origin."""
    for _ in range(60):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
        norm = [(r - rmin, c - cmin) for r, c in cells]
        bh = max(r for r, _ in norm) + 1
        bw = max(c for _, c in norm) + 1
        # Reject solid-rectangle polyominoes: their block-union is a filled
        # rectangle -> the recolored-to-8 output is a solid board.
        if bh <= max_bh and bw <= max_bw and len(norm) < bh * bw:
            return norm
    # Fallback: row-major fill of a max_bw-wide band, then bump the last cell
    # to a fresh row so the shape is never a filled rectangle.
    width = max(2, max_bw)
    fb = [(i // width, i % width) for i in range(k)]
    bh = max(r for r, _ in fb) + 1
    bw = max(c for _, c in fb) + 1
    if len(fb) == bh * bw:
        fb[-1] = (bh, 0)
    return fb


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # Salt the layout rng with the band so the odd cluster shape (which drives
    # the output) differs across bands at the same seed.
    rng = ctx.draw_rng("layout_" + str(difficulty))
    # 3 panels split by color-5 columns. Common panels hold a linear-3 chain
    # (degree signature [1,1,2], length 3). The ODD panel holds a connected
    # block-polyomino of k != 3 blocks -> its degree multiset has length != 3, so
    # it is ALWAYS the unique signature; its varied shape -> varied output.
    # odd_k must be != 3 (unique signature) AND >= 4 (k=2 blocks always form a
    # filled rectangle -> solid-8 output).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); pw = ctx.draw_int("panel_w", 8, 8); odd_k = rng.choice([4, 5])
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12); pw = ctx.draw_int("panel_w", 8, 9); odd_k = rng.choice([4, 5, 6])
    else:
        h = ctx.draw_int("grid_h", 8, 11); pw = ctx.draw_int("panel_w", 8, 9); odd_k = rng.choice([4, 5, 6])
    odd_panel = ctx.draw_int("odd_panel", 0, 2)
    g = full_grid(h, 3 * pw + 2, 0)
    sep = (pw, 2 * pw + 1)
    for r in range(h):
        for c in sep:
            g[r][c] = 5
    panel_lefts = [0, pw + 1, 2 * pw + 2]
    # block-lattice capacity within a panel: blocks are 2x2 -> max bh/bw in lattice
    max_bh = (h - 1) // 2; max_bw = (pw - 1) // 2
    for idx, left in enumerate(panel_lefts):
        colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], min(8, max(4, odd_k)))
        if idx == odd_panel:
            poly = _block_poly(rng, odd_k, max_bh, max_bw)
            bh = max(r for r, _ in poly) + 1; bw = max(c for _, c in poly) + 1
            br0 = rng.randint(0, max(0, (h - 2 * bh) // 2))
            bc0 = rng.randint(0, max(0, (pw - 2 * bw)))
            for i, (br, bc) in enumerate(poly):
                _block(g, br0 + 2 * br, left + bc0 + 2 * bc, colors[i % len(colors)])
        else:
            # linear-3 chain (degree sig [1,1,2]); centered-ish in the panel
            top = (h - 2) // 2
            for i in range(3):
                _block(g, top, left + 1 + 2 * i, colors[i])
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Three panels split by full color-5 columns; the odd panel's cluster
    (the output, recolored to 8) must be NON-rectangular so it is not solid."""
    h, w = len(grid), len(grid[0])
    sep_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(sep_cols) != 2:
        return [f"expected 2 color-5 divider columns, found {len(sep_cols)}"]
    bounds = [(0, sep_cols[0]), (sep_cols[0] + 1, sep_cols[1]),
              (sep_cols[1] + 1, w)]
    non_rect = 0
    for (c0, c1) in bounds:
        cells = [(r, c) for r in range(h) for c in range(c0, c1)
                 if grid[r][c] not in (0, 5)]
        if not cells:
            return ["a panel is empty"]
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if len(cells) < area:               # bbox not fully filled
            non_rect += 1
    if non_rect < 1:
        return ["no panel has a non-rectangular cluster -> odd output is solid"]
    return []


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 26, 0)
    if name == "no_dividers":
        # chains but no 5-divider columns → no panel boundaries
        for left in [0, 9, 18]:
            _paint_chain(g, left, [(3, 1), (3, 3), (3, 5)], [4, 6, 7])
        return g
    if name == "all_same":
        # all 3 panels have identical chain → no odd panel
        for r in range(8):
            g[r][8] = 5; g[r][17] = 5
        for left in [0, 9, 18]:
            _paint_chain(g, left, [(3, 1), (3, 3), (3, 5)], [4, 6, 7])
        return g
    if name == "no_odd":
        # 2 panels normal, 1 empty → can't tell odd from absent
        for r in range(8):
            g[r][8] = 5; g[r][17] = 5
        for left in [0, 9]:
            _paint_chain(g, left, [(3, 1), (3, 3), (3, 5)], [4, 6, 7])
        return g
    return g
