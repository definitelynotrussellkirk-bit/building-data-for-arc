"""Generator for arc_additional_puzzles_21_set12_bundle:E81 — Apply rotation/flip code to bbox-cropped content.

Rule: code at (0,0) ∈ 1..4 selects: 1=cw, 2=180, 3=lr, 4=ud (else
ud). After ignoring (0,0), bbox-crop the rest then apply.

Combinatorial axes (8): grid_h, grid_w, palette_kind, code,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_code, code_out_of_range, symmetric_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "c53c24435976"
VERSION = "1.4.0"  # honor code overrides; accept canonical same-color command/object pairs
TASK_ID = "c53c24435976"
SUMMARY = "Code at (0,0) ∈ 1..4 + asymmetric shape elsewhere."

INVARIANTS = [
    "(0,0) ∈ 1..4",
    "asymmetric shape (so each transform produces a different output)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_code", "code_out_of_range", "symmetric_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "code":           {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "code_at_origin_with_asym_shape",
                       "valid": "code_at_origin_with_asym_shape"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}



def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 8, 9); k_lo, k_hi = 4, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 10, 13); k_lo, k_hi = 5, 9
    else:
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11); k_lo, k_hi = 4, 7
    code = ctx.draw_int("code", 1, 4)  # public axis; explicit overrides must be exact
    rng = ctx.draw_rng("layout")
    color = rng.choice([c for c in [2, 3, 4, 5, 6, 7, 8, 9] if c != code])
    # Random polyomino with varied bbox (incl non-square) -> the transformed crop
    # output varies in dims AND content.  v1.2.0 still leaked symmetric crops: for
    # example a 2x2 square under code=2/3/4 is an identity transform, so the demo
    # does not teach the selected operation.  Draw until the *selected* transform
    # visibly changes the crop and the crop fits below/right of the code cell.
    for _ in range(80):
        s = _poly(rng, rng.randint(k_lo, k_hi))
        sh = max(r for r, _ in s) + 1
        sw = max(c for _, c in s) + 1
        if sh > h - 1 or sw > w - 1:
            continue
        if not _selected_transform_changes(s, code):
            continue
        break
    else:
        # Deterministic asymmetric fallback: non-square L/Z hybrid, valid for
        # every code in 1..4 and small enough for every difficulty grid.
        s = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)]
        sh, sw = 3, 3
    g = full_grid(h, w, 0)
    g[0][0] = code
    # place below/right of the (0,0) cmd cell, separated from it
    top = rng.randint(1, h - sh)
    left = rng.randint(1, w - sw)
    paint_at(g, top, left, s, color)
    return g


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _occ(cells):
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        out[r][c] = 1
    return out


def _rot_cw(g):
    h, w = len(g), len(g[0])
    return [[g[h - 1 - r][c] for r in range(h)] for c in range(w)]


def _rot_180(g):
    return [list(reversed(row)) for row in reversed(g)]


def _flip_lr(g):
    return [list(reversed(row)) for row in g]


def _flip_ud(g):
    return list(reversed(g))


def _apply_code(g, code):
    if code == 1:
        return _rot_cw(g)
    if code == 2:
        return _rot_180(g)
    if code == 3:
        return _flip_lr(g)
    return _flip_ud(g)


def _selected_transform_changes(cells, code):
    g = _occ(cells)
    return _apply_code(g, code) != g


def _shape_cells(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v != 0 and (r, c) != (0, 0)]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return [(r - r0, c - c0) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    code = grid[0][0]
    if code not in (1, 2, 3, 4):
        errs.append(f"expected transform code 1..4 at (0,0), got {code}")
    shape_cells = _shape_cells(grid)
    if len(shape_cells) < 3:
        errs.append("expected a bbox-cropped shape with at least 3 cells")
        return errs
    shape_colors = {grid[r][c] for r, row in enumerate(grid) for c, v in enumerate(row)
                    if v != 0 and (r, c) != (0, 0)}
    if len(shape_colors) != 1:
        errs.append(f"expected exactly one shape color, got {sorted(shape_colors)}")
    if code in (1, 2, 3, 4) and not _selected_transform_changes(shape_cells, code):
        errs.append("selected transform is identity for this crop (symmetric rule-hiding shape)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_code":
        # (0,0) is 0 → no transform code, rule has no operation defined
        s = [(0, 0), (1, 0), (1, 1), (2, 1)]
        paint_at(g, 3, 3, s, 4)
        return g
    if name == "code_out_of_range":
        # code = 5 (outside 1..4) → falls through to ud default (rule docs say "else ud")
        g[0][0] = 5
        s = [(0, 0), (1, 0), (1, 1), (2, 1)]
        paint_at(g, 3, 3, s, 4)
        return g
    if name == "symmetric_shape":
        # symmetric shape (4-fold) → all 4 transforms produce the same output (no signal)
        g[0][0] = 1
        s = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]   # plus (4-fold sym)
        paint_at(g, 3, 3, s, 4)
        return g
    return g
