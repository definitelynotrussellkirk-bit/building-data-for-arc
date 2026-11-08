"""Generator for 56b8d7075625:H156 -- 3-panel boolean combine, recolor to C.

Rule: split the grid by full color-8 columns into panels A, B, C (cropped to
nonzero bbox). If their dims differ, output C; else compute binary support
masks a,b,c and output, per cell, on iff
  (c AND NOT(a AND NOT b)) OR (NOT a AND b),
recolored to C's dominant color.

This generator draws three same-bbox masks (each touching all four edges so
the crop dims match) in separate panels split by 8-columns.

Combinatorial axes: panel size, the three masks, the colors.
Degenerates: dims_mismatch, sparse, tiny.

NOTE: the output is a small HxW mask, so OUTPUTS are bounded; distinct INPUTS
are large.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "955b7dee0e47"
VERSION = "2.1.1"  # add self_check  # diversity: 3 same-bbox masks -> boolean combine (was ~37)
TASK_ID = "955b7dee0e47"
SUMMARY = (
    "Grid split by full color-8 columns into three panels (masks). Rule: "
    "output a per-cell boolean combination of the three supports, recolored "
    "to C's dominant color. The panel size, masks and colors vary freely (was "
    "a fixed setup, ~37 distinct). Output is a small mask, so bounded; inputs "
    "are large."
)

INVARIANTS = [
    "three panels separated by full color-8 columns, equal cropped dims",
    "each mask touches all four bbox edges so the crops align",
    "the output is the boolean combination recolored to C's color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("dims_mismatch", "sparse", "tiny")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = [1, 2, 3, 4, 5, 6, 7, 9]   # mask colors (not 8, the divider)

AXES = {
    "panel_h":        {"type": "int", "default": "varies", "valid": "3..7"},
    "panel_w":        {"type": "int", "default": "varies", "valid": "3..7"},
    "fill_frac":      {"type": "float", "default": "varies", "valid": "0.3..0.7"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "panels", "valid": "panels"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|dims_mismatch|sparse|tiny"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 full-height color-8 divider columns; ≥1 non-{0,8} content cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    div_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(div_cols) < 2:
        errs.append(f"expected ≥2 full-height color-8 divider columns; got {div_cols}")
    has_content = any(grid[r][c] not in (0, 8) for r in range(h) for c in range(w))
    if not has_content:
        errs.append("no non-{0,8} content cells found")
    return errs


def _mask(rng, H, W, frac):
    """binary mask touching all four edges (so its bbox is HxW)."""
    m = [[1 if rng.random() < frac else 0 for _ in range(W)] for _ in range(H)]
    # force the 4 corners on -> bbox is exactly HxW
    m[0][0] = m[0][W - 1] = m[H - 1][0] = m[H - 1][W - 1] = 1
    return m


def _assemble(masks_colored, H, W):
    """three HxW colored panels joined by single full-8 divider columns."""
    n = 3 * W + 2
    g = full_grid(H, n, 0)
    col = 0
    for i, panel in enumerate(masks_colored):
        for r in range(H):
            for c in range(W):
                g[r][col + c] = panel[r][c]
        col += W
        if i < 2:
            for r in range(H):
                g[r][col] = 8
            col += 1
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, fr = (3, 4), (3, 5), (0.3, 0.6)
    elif difficulty == "hard":
        hr, wr, fr = (5, 7), (5, 7), (0.3, 0.7)
    else:
        hr, wr, fr = (4, 6), (4, 6), (0.3, 0.7)

    for _attempt in range(40):
        H = rng.randint(*hr); W = rng.randint(*wr)
        f = rng.uniform(*fr)
        cols = rng.sample(_COLORS, 3)
        panels = []
        for ci in range(3):
            m = _mask(rng, H, W, f)
            panels.append([[cols[ci] if m[r][c] else 0 for c in range(W)]
                           for r in range(H)])
        return _assemble(panels, H, W)

    return _draw_from_degenerate("tiny", rng)   # fallback (rare)


def _draw_from_degenerate(name, rng):
    H, W = (3, 3) if name == "tiny" else (4, 4)
    cols = [2, 3, 4]
    f = 0.2 if name == "sparse" else 0.5
    panels = []
    for ci in range(3):
        m = _mask(rng, H, W, f)
        panels.append([[cols[ci] if m[r][c] else 0 for c in range(W)]
                       for r in range(H)])
    if name == "dims_mismatch":
        # make C a different size by trimming a row of content
        panels[2] = [[0] * W for _ in range(H)]
        panels[2][0][0] = 4
    return _assemble(panels, H, W)
