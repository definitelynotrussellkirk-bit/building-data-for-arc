"""Generator for bank 8ed83d4e427b:H28 -- XOR of two color masks, cropped.

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

GENERATOR_ID = "efb59efe0080"
VERSION = "2.1.0"  # widen shape sizes (output depends only on shapes) for richer XOR diversity
TASK_ID = "efb59efe0080"
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, ss = (12, 14), (12, 16), (3, 5)
    elif difficulty == "hard":
        hr, wr, ss = (16, 22), (18, 24), (6, 10)
    else:
        hr, wr, ss = (13, 18), (14, 20), (4, 8)

    for _attempt in range(40):
        # draw the two shapes independently (often different sizes -> richer XOR)
        s2 = _poly(rng, rng.randint(*ss))
        s3 = _poly(rng, rng.randint(*ss))
        if set(s2) == set(s3):
            continue   # need a non-empty XOR
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        if not _place(rng, g, occ, s2, 2, h, w):
            continue
        if not _place(rng, g, occ, s3, 3, h, w):
            continue
        return g

    return g   # fallback (rare)


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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components, norm
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    comps2 = components(grid, colors={2})
    comps3 = components(grid, colors={3})
    if len(comps2) != 1 or len(comps3) != 1:
        errors.append(f"expected exactly one color-2 and one color-3 component, got {len(comps2)} and {len(comps3)}")
        return errors
    n2 = norm(comps2[0]["cells"])
    n3 = norm(comps3[0]["cells"])
    if n2 == n3:
        errors.append("normalized color-2 and color-3 masks are identical, so XOR would be empty")
    return errors
