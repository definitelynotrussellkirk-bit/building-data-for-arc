"""Generator for d56f2372.

Rule: multicolor 8-connected objects; rule extracts the first
LR-symmetric one (row-major).

Combinatorial axes (8): grid_h/w, sym_h, sym_w, n_asym, palette_kind,
position_bias, anchor_corner, palette_size.
Degenerates: no_sym, all_sym, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "33c7592c5cf0"
VERSION = "2.1.1"  # reviewer fix: place deterministic asymmetric block instead of degenerate fallback; raise if impossible
TASK_ID = "33c7592c5cf0"
SUMMARY = (
    "0-bg grid (h, w ∈ 12-22, by "
    "difficulty) with: (a) ONE "
    "LR-SYMMETRIC MULTICOLOR BLOCK at "
    "the TOP (sr=1) — sh × sw (sh ∈ "
    "3-5, sw ∈ 3-7, forced odd for "
    "exact symmetry), built via "
    "_make_sym_block: each row's "
    "cells set so row[c] == row[sw-1-c]; "
    "painted in colors drawn from a "
    "4-color palette per PALETTE_KIND "
    "∈ {warm, cool, broad, primary}; "
    "(b) N_ASYM ∈ 1-3 ASYMMETRIC "
    "DISTRACTOR BLOCKS placed BELOW "
    "the symmetric block (rows ≥ "
    "sr+sh+1) — each 2-3 × 2-4, "
    "with corners forced different "
    "so LR-symmetry is broken. "
    "All blocks placed with 1-cell "
    "halo padding via _can_place. "
    "Rule (EXTRACT EVERY 8-CONNECTED "
    "MULTICOLOR OBJECT; SORT BY "
    "(MIN_ROW, MIN_COL) ROW-MAJOR; "
    "OUTPUT THE FIRST LR-SYMMETRIC "
    "ONE — ITS BBOX CROP IN ITS "
    "ORIGINAL COLORS): EXTRACT "
    "every non-bg 8-conn object. "
    "SORT by (min_r, min_c). For "
    "EACH in order: CHECK if its "
    "normalized bbox-mask is LR-"
    "symmetric (row[c] == "
    "row[w-1-c]). SELECT the "
    "FIRST symmetric one. CROP "
    "to its bbox. OUTPUT the "
    "multicolor crop. Net: "
    "topmost-leftmost LR-symmetric "
    "object extracted; "
    "asymmetric distractors "
    "discarded."
)

INVARIANTS = [
    "background is 0",
    "topmost-leftmost object is LR-symmetric",
    "other objects are NOT LR-symmetric",
    "objects separated by bg margin",
]

POSITION_BIASES = ("scattered", "stacked", "row_aligned", "centered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_sym", "all_sym", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "sym_h":          {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "sym_w":          {"type": "int", "default": "rng 3..5", "valid": "3..7"},
    "n_asym":         {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "warm|cool|broad|primary"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "scattered|stacked|row_aligned|centered"},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..5"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "scattered|stacked|row_aligned|centered|no_sym|all_sym|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify first 8-connected object is LR-symmetric and distractors are asymmetric."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    comps = _objects8(grid)
    if not comps:
        return ["all-zero grid: no blocks placed"]
    comps.sort(key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
    if not _is_lr_symmetric(grid, comps[0]):
        errs.append("topmost-leftmost object is not LR-symmetric")
    if not any(not _is_lr_symmetric(grid, cells) for cells in comps[1:]):
        errs.append("missing asymmetric distractor after the symmetric object")
    for i, cells in enumerate(comps):
        halo = {(r + dr, c + dc) for r, c in cells
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        for other in comps[i + 1:]:
            if halo & other:
                errs.append("objects are not separated by a background margin")
                break
    return errs


def _objects8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                                and grid[nr][nc] != 0):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            out.append(cells)
    return out


def _is_lr_symmetric(grid, cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if grid[r][c] != grid[r][c1 + c2 - c]:
                return False
    return True


def _make_sym_block(rng, palette, sh, sw):
    if sw % 2 == 0:
        sw += 1
    block = [[0] * sw for _ in range(sh)]
    half = sw // 2
    for r in range(sh):
        for c in range(half + 1):
            v = rng.choice(palette)
            block[r][c] = v
            block[r][sw - 1 - c] = v
    return block


def _make_asym_block(rng, palette):
    sh = rng.randint(2, 3)
    sw = rng.randint(2, 4)
    block = [[rng.choice(palette) for _ in range(sw)] for _ in range(sh)]
    block[0][0] = palette[0]
    block[0][sw - 1] = palette[1] if len(palette) > 1 else palette[0]
    if block[0][0] == block[0][sw - 1] and len(palette) > 2:
        block[0][sw - 1] = palette[2]
    return block


def _paint_block(g, block, rr, rc):
    sh = len(block)
    sw = len(block[0])
    for dr in range(sh):
        for dc in range(sw):
            v = block[dr][dc]
            if v != 0:
                g[rr + dr][rc + dc] = v


def _can_place(g, sh, sw, rr, rc, halo=1):
    h, w = len(g), len(g[0])
    for r in range(max(0, rr - halo), min(h, rr + sh + halo)):
        for c in range(max(0, rc - halo), min(w, rc + sw + halo)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 12, 14
        sh_lo, sh_hi = 3, 3
        sw_lo, sw_hi = 3, 3
        na_lo, na_hi = 1, 1
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
        sh_lo, sh_hi = 4, 5
        sw_lo, sw_hi = 5, 7
        na_lo, na_hi = 2, 3
    else:
        h_lo, h_hi = 14, 18
        sh_lo, sh_hi = 3, 4
        sw_lo, sw_hi = 3, 5
        na_lo, na_hi = 1, 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, 4, rng)
    g = full_grid(h, w, 0)
    sh = int(overrides.get("sym_h",
                           ctx.draw_int("sym_h", sh_lo, sh_hi)))
    sw = int(overrides.get("sym_w",
                           ctx.draw_int("sym_w", sw_lo, sw_hi)))
    sym = _make_sym_block(rng, palette, sh, sw)
    sh, sw = len(sym), len(sym[0])
    sr = 1
    sc = rng.randint(1, max(1, w - sw - 1))
    _paint_block(g, sym, sr, sc)
    n_asym = int(overrides.get("n_asym",
                               ctx.draw_int("n_asym", na_lo, na_hi)))
    n_asym = max(1, min(3, n_asym))
    placed = 0
    for _try in range(40):
        if placed >= n_asym:
            break
        ablock = _make_asym_block(rng, palette)
        ah, aw = len(ablock), len(ablock[0])
        rr = rng.randint(sr + sh + 1, max(sr + sh + 1, h - ah - 1))
        rc = rng.randint(0, max(0, w - aw))
        if not _can_place(g, ah, aw, rr, rc):
            continue
        _paint_block(g, ablock, rr, rc)
        placed += 1
    if placed < 1:
        ablock = [[palette[0], palette[1]], [palette[1], palette[1]]]
        ah, aw = len(ablock), len(ablock[0])
        rr = min(h - ah, sr + sh + 1)
        for rc in range(0, max(1, w - aw + 1)):
            if _can_place(g, ah, aw, rr, rc):
                _paint_block(g, ablock, rr, rc)
                placed = 1
                break
    if placed < 1:
        raise ValueError("could not place asymmetric distractor")
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_sym":
        g[3][3] = 2; g[3][4] = 3; g[3][5] = 4
        return g
    if name == "all_sym":
        g[3][3] = 2; g[3][4] = 3; g[3][5] = 2
        g[8][7] = 4; g[8][8] = 5; g[8][9] = 4
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
