"""Generator for arc_puzzle_bank_21_set19_s:S19_H3 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8fb95be218da"
VERSION = "2.1.1"
TASK_ID = "8fb95be218da"

SUMMARY = (
    "Grid split into N panels (~5-6) by 1-wide full-height "
    "color-9 (maroon) separator COLUMNS. Panel 0 = SOURCE "
    "motif; panel 1 = TARGET motif; panels 2..N-1 = "
    "CANDIDATES. Each panel has 1-3 cells in some non-{0,9} "
    "color. Rule: split panels. Compute source cells (panel-"
    "relative positions where panel value != 0); same for "
    "target. For each candidate panel, compute its cells, "
    "union with source's cells, then check if the UNION "
    "(sorted, deduped) equals target's cells. The FIRST "
    "candidate matching that test is selected. Output: that "
    "candidate panel with all non-zero cells recolored to 8 "
    "(cyan). If no match → empty (zeros) grid of candidate "
    "size."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "grid splits into ≥3 panels by 1-wide color-9 separator columns",
    "panel 0 and panel 1 hold source and target motifs",
    "exactly one candidate panel's cells, unioned with source's, equals target's cells",
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
    """Verify: >=1 full-height color-9 divider column and >=1 non-{0,9} cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_dividers", "empty_panels", "single_panel"):
        return errs
    has_9col = any(all(grid[r][c] == 9 for r in range(h)) for c in range(w))
    if not has_9col:
        errs.append("no full-height color-9 divider column found")
    has_motif = any(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    if not has_motif:
        errs.append("no non-{0,9} motif cells found")
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

    panel_positions = [(r, c) for r in range(h) for c in range(panel_w)]
    src_cells = set(rng.sample(panel_positions, k=rng.randint(2, max(2, len(panel_positions) // 3))))
    # Target = src + extra cells. Extra cells become the "matching candidate".
    extra_cells = set(rng.sample([p for p in panel_positions if p not in src_cells],
                                 k=rng.randint(1, max(1, len(panel_positions) // 3))))
    tgt_cells = src_cells | extra_cells
    matching_cand = extra_cells  # union with src gives tgt

    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])

    def paint_panel(p_idx, cells):
        c_off = p_idx * (panel_w + 1)
        for (r, c) in cells:
            g[r][c_off + c] = color

    paint_panel(0, src_cells)
    paint_panel(1, tgt_cells)

    # Place matching candidate at a random slot among candidates [2..n-1].
    cand_slots = list(range(2, n))
    rng.shuffle(cand_slots)
    if cand_slots:
        paint_panel(cand_slots[0], matching_cand)
    # Fill the rest with distractor cells that don't satisfy the union == target.
    for k in cand_slots[1:]:
        for _try in range(40):
            distractor = set(rng.sample(panel_positions, k=rng.randint(1, max(1, len(panel_positions) // 3))))
            union_with_src = src_cells | distractor
            if union_with_src != tgt_cells and distractor != matching_cand:
                paint_panel(k, distractor)
                break
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
