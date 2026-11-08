"""Generator for arc_puzzle_bank_next21:H9 -- XOR of normalized supports.

Rule: normalize the color-2 and color-3 shapes to their own bbox corners;
output (max-dims grid) is color 8 where exactly one normalized shape has a
cell (their symmetric difference), else 0.

This generator draws two distinct polyomino shapes (one color-2, one
color-3), separated; their normalized XOR is the output.

Combinatorial axes: grid size, the two shapes, and positions.
Degenerates: identical_shapes, no_two, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "3cdfed241796"
VERSION = "2.1.0"  # diversity: two random shapes -> normalized XOR (was fixed ~26)
TASK_ID = "3cdfed241796"
SUMMARY = (
    "0-bg grid (size varies). A color-2 shape and a color-3 shape. Rule: "
    "normalize both to their bbox corners and output color 8 where exactly "
    "one has a cell (their XOR), on a max-dims grid. The grid size, the two "
    "shapes and positions vary freely (was a fixed setup, ~26 distinct)."
)

INVARIANTS = [
    "one color-2 shape and one color-3 shape, distinct when normalized",
    "the output is their normalized symmetric difference in color 8",
    "the XOR is non-empty (the shapes differ)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identical_shapes", "no_two", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "shape_size":     {"type": "int", "default": "varies", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "two_shapes", "valid": "two_shapes"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|identical_shapes|no_two|full_grid"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _place(rng, g, occ, cells, color, h, w):
    cells = _norm(cells)
    sh = max(r for r, c in cells) + 1; sw = max(c for r, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _t in range(50):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        if _reserve(occ, top, left, sh, sw, h, w):
            paint_at(g, top, left, cells, color)
            return True
    return False


def _axis_int(ctx, rng, label, lo, hi):
    if label in ctx.overrides and ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return rng.randint(lo, hi)


def _fallback_grid(h, w):
    h = max(h, 8); w = max(w, 10)
    g = full_grid(h, w, 0)
    paint_at(g, 1, 1, [(0, 0), (1, 0), (1, 1)], 2)
    paint_at(g, 1, 6 if w > 9 else 5, [(0, 0), (0, 1), (1, 1)], 3)
    return g


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

    h = _axis_int(ctx, rng, "grid_h", *hr)
    w = _axis_int(ctx, rng, "grid_w", *wr)
    shape_size = _axis_int(ctx, rng, "shape_size", *ss)

    for _attempt in range(40):
        s2 = _poly(rng, shape_size)
        s3 = _poly(rng, shape_size)
        if set(s2) == set(s3):
            continue   # need a non-empty XOR
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        if not _place(rng, g, occ, s2, 2, h, w):
            continue
        if not _place(rng, g, occ, s3, 3, h, w):
            continue
        return g

    return _fallback_grid(h, w)   # fallback (rare), still nontrivial



def _components_for_color(grid, color):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _norm_set(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return {(r - mr, c - mc) for r, c in cells}


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for normalized color-2/color-3 XOR inputs."""
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    colors = {v for row in grid for v in row if v != 0}
    if colors != {2, 3}:
        errs.append(f"expected exactly colors 2 and 3 on 0-bg, got {sorted(colors)}")
        return errs
    c2 = _components_for_color(grid, 2)
    c3 = _components_for_color(grid, 3)
    if len(c2) != 1 or len(c3) != 1:
        errs.append(f"expected one component of each color, got color2={len(c2)} color3={len(c3)}")
        return errs
    s2 = _norm_set(c2[0])
    s3 = _norm_set(c3[0])
    if s2 == s3:
        errs.append("normalized color-2 and color-3 shapes are identical; XOR would be empty")
    if not (s2 ^ s3):
        errs.append("normalized XOR support is empty")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    a = [(0, 0), (1, 0), (1, 1)]
    b = [(0, 0), (0, 1), (1, 1)]
    paint_at(g, 2, 2, a, 2)
    paint_at(g, 2, 8, b, 3)
    if name == "identical_shapes":
        paint_at(g, 2, 8, a, 3)
        return g
    if name == "no_two":
        g2 = full_grid(12, 14, 0); paint_at(g2, 2, 2, a, 2)
        return g2
    if name == "full_grid":
        return full_grid(12, 14, 2)
    return g
