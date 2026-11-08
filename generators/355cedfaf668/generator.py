"""Generator for fe9bb13a9b18:S14_M2 -- corner-coded row/column span fill.

Rule: if the top-left cell g[0][0] == 1, every object whose color is not in
{1,2} has each of its ROWS filled solid between that row's min and max column
(row-span fill). Otherwise the same is done per COLUMN (col-span fill).
Color-1 and color-2 objects are left untouched.

This generator draws several non-{1,2} shapes (frames and one-side-open C
shapes, so row vs column fill differ visibly) plus a top-left control cell
that selects the axis.

Combinatorial axes: grid size, the shapes/colors/positions, and the control
cell (axis).
Degenerates: no_shapes, solid_block, all_banned.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "355cedfaf668"
VERSION = "2.1.0"  # +self_check  # diversity: frames/C-shapes + corner-coded row/col span fill (was fixed ~27)
TASK_ID = "355cedfaf668"
SUMMARY = (
    "0-bg grid (size varies) with several non-{1,2} shapes (frames and "
    "one-side-open C shapes) and a top-left control cell. Rule: if g[0][0]==1 "
    "fill each object's per-row span solid, else per-column span. The grid "
    "size, shapes/colors/positions and the control axis vary freely (was a "
    "fixed setup, ~27 distinct)."
)

INVARIANTS = [
    "top-left cell g[0][0] selects row-span (==1) vs column-span fill",
    "non-{1,2} objects get their per-row or per-column span filled solid",
    "shapes are separated so spans stay within their own object",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "solid_block", "all_banned")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = [3, 4, 5, 6, 7, 8, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_shapes":       {"type": "int", "default": "varies", "valid": "1..4"},
    "axis":           {"type": "str", "default": "rng", "valid": "row|col"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shapes|solid_block|all_banned"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: g[0][0] in {0,1} (axis: 1=row-fill, 0=col-fill), ≥1 non-{0,1} shape cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    axis_code = grid[0][0]
    if axis_code not in (0, 1):
        errs.append(f"g[0][0] = {axis_code}, expected 0 (col-fill) or 1 (row-fill)")
    shapes_present = any(grid[r][c] not in (0, 1)
                         for r in range(h) for c in range(w))
    if not shapes_present:
        errs.append("no non-{0,1} shape cells found")
    return errs


def _c_shape(rng, hh, ww, force_side=None):
    """rectangle outline of size hh x ww, optionally missing one side (C/U).

    A full frame (side "none") always has its interior filled under either
    axis, so it guarantees a visible change; pass force_side="none" for that.
    """
    cells = [(r, c) for r in range(hh) for c in range(ww)
             if r in (0, hh - 1) or c in (0, ww - 1)]
    side = force_side or rng.choice(["none", "top", "bottom", "left", "right"])
    if side == "top":
        cells = [(r, c) for (r, c) in cells if not (r == 0 and 0 < c < ww - 1)]
    elif side == "bottom":
        cells = [(r, c) for (r, c) in cells if not (r == hh - 1 and 0 < c < ww - 1)]
    elif side == "left":
        cells = [(r, c) for (r, c) in cells if not (c == 0 and 0 < r < hh - 1)]
    elif side == "right":
        cells = [(r, c) for (r, c) in cells if not (c == ww - 1 and 0 < r < hh - 1)]
    return cells


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    axis = overrides.get("axis") or rng.choice(["row", "col"])

    if difficulty == "easy":
        hr, wr, nr, sr = (12, 15), (12, 16), (1, 2), (3, 5)
    elif difficulty == "hard":
        hr, wr, nr, sr = (18, 24), (18, 24), (3, 4), (4, 7)
    else:
        hr, wr, nr, sr = (14, 19), (14, 20), (2, 3), (3, 6)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        occ[0][0] = True   # keep the control cell clear of shapes
        placed = 0
        nshapes = rng.randint(*nr)
        for _idx in range(nshapes):
            sh = rng.randint(*sr); sw = rng.randint(*sr)
            if sh > h - 1 or sw > w - 1:
                continue
            # first shape is a full frame -> guaranteed to change under either axis
            force = "none" if placed == 0 else None
            shape = _c_shape(rng, sh, sw, force_side=force)
            color = rng.choice(_COLORS)
            for _t in range(30):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                if _reserve(occ, top, left, sh, sw, h, w):
                    for (r, c) in shape:
                        g[top + r][left + c] = color
                    placed += 1; break
        if placed < 1:
            continue
        g[0][0] = 1 if axis == "row" else 0
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    for (r, c) in _c_shape(rng, 5, 5):
        g[3 + r][4 + c] = 3
    if name == "no_shapes":
        g2 = full_grid(h, w, 0); g2[0][0] = 1
        return g2
    if name == "all_banned":
        g3 = full_grid(h, w, 0)
        for (r, c) in _c_shape(rng, 5, 5):
            g3[3 + r][4 + c] = 2
        g3[0][0] = 1
        return g3
    if name == "solid_block":
        for r in range(3, 8):
            for c in range(4, 9):
                g[r][c] = 3
    g[0][0] = 1
    return g
