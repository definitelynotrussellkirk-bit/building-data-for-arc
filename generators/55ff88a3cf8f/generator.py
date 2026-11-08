"""Generator for bank 385e738e9e70:M95.

Rule: take the color-6 shape, rotate it (ctrl-1) quarter turns where ctrl
is the value of the first color-1..4 cell, and stamp it in color 3
anchored at the first color-8 cell (keeping the rest of the grid).

This generator draws a color-6 shape, a color-8 anchor, and one control
cell (color 1-4), placed so the rotated stamp fits.

Combinatorial axes: grid size, the shape, the control (rotation), and the
anchor position.
Degenerates: no_shape, no_anchor, no_ctrl.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "55ff88a3cf8f"
VERSION = "2.1.0"  # diversity: random color-6 shape + control rotation + anchor (was fixed ~25)
TASK_ID = "55ff88a3cf8f"
SUMMARY = (
    "0-bg grid (size varies). A color-6 shape, a color-8 anchor cell, and "
    "one control cell (color 1-4). Rule: rotate the shape (ctrl-1 quarter "
    "turns) and stamp it in color 3 at the anchor. The grid size, shape, "
    "control rotation and anchor position vary freely (was a fixed setup, "
    "~25 distinct)."
)

INVARIANTS = [
    "one color-6 shape, one color-8 anchor, one color-1..4 control cell",
    "the rotated shape (ctrl-1 turns) fits in bounds at the anchor",
    "the output stamps that rotated shape in color 3 at the anchor",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shape", "no_anchor", "no_ctrl")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "shape_size":     {"type": "int", "default": "varies", "valid": "3..7"},
    "ctrl":           {"type": "int", "default": "rng 1..4", "valid": "1|2|3|4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "shape_anchor_ctrl",
                       "valid": "shape_anchor_ctrl"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shape|no_anchor|no_ctrl"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _rot90(cells):
    cells = _norm(cells); h = max(r for r, c in cells) + 1
    return _norm([(c, h - 1 - r) for r, c in cells])


def _rotk(cells, k):
    cur = _norm(cells)
    for _ in range(k % 4):
        cur = _rot90(cur)
    return cur


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

    if difficulty == "easy":
        hr, wr, ss = (12, 14), (12, 16), (3, 4)
    elif difficulty == "hard":
        hr, wr, ss = (16, 22), (18, 24), (5, 7)
    else:
        hr, wr, ss = (13, 18), (14, 20), (3, 6)

    ctrl = int(overrides["ctrl"]) if "ctrl" in overrides else rng.randint(1, 4)

    for _attempt in range(40):
        shape = _poly(rng, rng.randint(*ss))
        sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
        rotated = _rotk(shape, ctrl - 1)
        th = max(r for r, c in rotated) + 1; tw = max(c for r, c in rotated) + 1

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        if sh + 1 > h or sw + 1 > w:
            continue
        sr = rng.randint(0, h - sh); sc = rng.randint(0, w - sw)
        if not _reserve(occ, sr, sc, sh, sw, h, w):
            continue
        paint_at(g, sr, sc, shape, 6)

        placed_anchor = None
        for _t in range(60):
            ar = rng.randint(0, h - th); ac = rng.randint(0, w - tw)
            foot = [(ar + r, ac + c) for r, c in rotated]
            if any(occ[r][c] for r, c in foot):
                continue
            placed_anchor = (ar, ac, foot); break
        if not placed_anchor:
            continue
        ar, ac, foot = placed_anchor
        for (r, c) in foot:
            occ[r][c] = True
        # The anchor is the stamp top-left, not necessarily a cell of the
        # rotated footprint. Reserve it explicitly so the control marker cannot
        # overwrite the only color-8 anchor.
        occ[ar][ac] = True
        g[ar][ac] = 8

        free = [(r, c) for r in range(h) for c in range(w) if not occ[r][c]]
        if not free:
            continue
        cr, cc = rng.choice(free)
        g[cr][cc] = ctrl
        return g

    return _fallback_instance(ctrl)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    paint_at(g, 2, 2, [(0, 0), (1, 0), (1, 1)], 6)
    g[6][8] = 8
    g[0][0] = 2
    if name == "no_shape":
        g2 = full_grid(12, 14, 0); g2[6][8] = 8; g2[0][0] = 2
        return g2
    if name == "no_anchor":
        g[6][8] = 0
        return g
    if name == "no_ctrl":
        g[0][0] = 0
        return g
    return g


def _fallback_instance(ctrl):
    g = full_grid(12, 14, 0)
    shape = [(0, 0), (1, 0), (1, 1)]
    paint_at(g, 2, 2, shape, 6)
    g[6][8] = 8
    g[0][0] = ctrl
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-8 anchor; got {len(anchors)}")
    ctrl_cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (1, 2, 3, 4)]
    if len(ctrl_cells) != 1:
        errors.append(f"expected exactly one control cell in colors 1..4; got {len(ctrl_cells)}")
    shape_cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6]
    if len(shape_cells) < 3:
        errors.append("color-6 source shape must have at least three cells")
    return errors
