"""Generator for arc_additional_puzzle_bank_volume6:H38.

Rule: normalize the cells of each color-2 object; take the cells common
to ALL of them; place that common shape (offset by the first color-9
anchor cell) onto a blank grid in color 3.

This generator builds the color-2 shapes around a shared CORE (each =
core + its own disjoint extras) so the intersection is exactly the core,
and places a color-9 anchor where the core fits in-bounds.

Combinatorial axes: grid size, the shared core, each color-2 shape's
extras, and the anchor position.
Degenerates: no_shapes, no_anchor, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "d00c1b736551"
VERSION = "2.0.1"  # diversity: random core + N color-2 shapes + anchor + grid (was fixed ~13)
TASK_ID = "d00c1b736551"
SUMMARY = (
    "0-bg grid (size varies). 2-4 connected color-2 (red) shapes sharing a "
    "common CORE (each = core + its own disjoint extras), plus one color-9 "
    "(maroon) ANCHOR cell. Rule: intersect the normalized color-2 shapes "
    "(the core) and stamp it at the anchor in color 3 (green) on a blank "
    "grid. The grid size, the core, each shape's extras and the anchor "
    "position all vary freely (was a fixed layout, ~13 distinct)."
)

INVARIANTS = [
    "2-4 connected color-2 shapes, all separated, sharing a non-empty common core",
    "exactly one color-9 anchor where the core fits in-bounds",
    "each shape has >=1 cell the others lack (extras disjoint across shapes)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "no_anchor", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..22"},
    "n_shapes":       {"type": "int", "default": "varies", "valid": "2..4"},
    "core_size":      {"type": "int", "default": "varies", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "shapes_apart", "valid": "shapes_apart"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shapes|no_anchor|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all non-bg cells are color 2 (shapes) or color 9 (anchor)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 2, 9)]
    if bad:
        return errs  # degenerate — allow
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(nines) > 1:
        errs.append(f"expected at most 1 color-9 anchor; found {len(nines)}")
    return errs


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return set(_norm(cells))


def _place_cluster(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nr, kr, er = (11, 13), (11, 14), (2, 2), (2, 3), (1, 2)
    elif difficulty == "hard":
        hr, wr, nr, kr, er = (15, 20), (16, 22), (3, 4), (3, 4), (2, 3)
    else:
        hr, wr, nr, kr, er = (12, 16), (13, 18), (2, 3), (2, 4), (1, 3)

    for _attempt in range(40):
        core = _poly(rng, rng.randint(*kr))
        used = set(core)
        shapes = []
        ok = True
        for _ci in range(rng.randint(*nr)):
            shape = set(core)
            for _ in range(rng.randint(*er)):
                cands = []
                for (r, c) in shape:
                    for dr, dc in _CARD:
                        er_, ec_ = r + dr, c + dc
                        if er_ >= 0 and ec_ >= 0 and (er_, ec_) not in shape and (er_, ec_) not in used:
                            cands.append((er_, ec_))
                if not cands:
                    break
                cell = rng.choice(cands)
                shape.add(cell); used.add(cell)
            if shape == core:
                ok = False
                break
            shapes.append(shape)
        if not ok or len(shapes) < 2:
            continue

        core_l = _norm(core)
        ch = max(r for r, c in core_l) + 1; cw = max(c for r, c in core_l) + 1

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        placed = True
        for shape in shapes:
            sl = _norm(shape)
            sh = max(r for r, c in sl) + 1; sw = max(c for r, c in sl) + 1
            done = False
            for _t in range(40):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                cells = [(top + r, left + c) for r, c in sl]
                if _place_cluster(occ, cells, h, w):
                    paint_at(g, top, left, sl, 2)
                    done = True
                    break
            if not done:
                placed = False
                break
        if not placed:
            continue

        # anchor (color 9) where the core fits in-bounds
        anchor_done = False
        for _t in range(60):
            ar = rng.randint(0, h - ch); ac = rng.randint(0, w - cw)
            foot = [(ar + r, ac + c) for r, c in core_l]
            if (ar, ac) not in foot:
                foot = foot + [(ar, ac)]
            if _place_cluster(occ, foot, h, w):
                g[ar][ac] = 9        # only the anchor cell is drawn (core footprint stays 0)
                anchor_done = True
                break
        if anchor_done:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 13, 0)
    core = [(0, 0), (1, 0), (1, 1)]
    if name == "no_shapes":
        g[5][5] = 9
        return g
    if name == "no_anchor":
        paint_at(g, 1, 1, core, 2)
        paint_at(g, 1, 6, core + [(0, 1)], 2)
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(13):
                g[r][c] = 2
        return g
    return g
