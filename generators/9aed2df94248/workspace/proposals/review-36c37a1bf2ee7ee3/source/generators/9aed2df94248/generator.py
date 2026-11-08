"""Generator for arc_additional_puzzles_21_set17_bundle:H114.

Rule: three panels separated by blank columns. Crop each. Infer the
transform code (0-5: id / rot-cw / rot-180 / transpose / flip-lr /
flip-ud) where apply(A,code) == B, then output apply(C,code).

Combinatorial axes: the shape A (and the chosen transform, which sets
B), the shape C, the panel positions, and the color.
Degenerates: identity_transform, A_B_unrelated, missing_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9aed2df94248"
VERSION = "3.0.2"  # robust D4-asymmetric fallback and deterministic exhaustion scene
TASK_ID = "9aed2df94248"
SUMMARY = (
    "0-bg grid (size varies) with THREE PANELS separated by blank "
    "zero-columns, all one color. Panel A is a random D4-ASYMMETRIC shape "
    "(unique transform); panel B is A under a chosen detectable transform "
    "(code 1-5: rot-cw / rot-180 / transpose / flip-lr / flip-ud — NOT "
    "rot-ccw or anti-transpose, which this rule cannot infer); panel C is "
    "another asymmetric shape. Rule: infer the A->B transform and output "
    "it applied to C. Each panel has no internal blank column. The shapes, "
    "transform, positions and color all vary freely (was a fixed 6x13 "
    "layout with 2 transforms x ~8 colors, ~16 distinct)."
)

INVARIANTS = [
    "three panels separated by >=1 blank zero-column, each a single content band",
    "panel A is D4-asymmetric so exactly one transform code maps A->B",
    "the transform is one of the 5 detectable non-identity codes (no ccw/anti-transpose)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_transform", "A_B_unrelated", "missing_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

_CODES = (1, 2, 3, 4, 5)  # detectable non-identity transforms for THIS rule
_FALLBACK_SHAPE = [(0, 0), (0, 1), (0, 2), (1, 0)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "5..10"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "transform":      {"type": "str", "default": "varies", "valid": "rot|flip"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "three_panels", "valid": "three_panels"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "identity_transform|A_B_unrelated|missing_panel"},
}


def _apply(cells, code):
    if code == 0:
        return list(cells)
    if code == 1:   # rot-cw
        return [(c, -r) for r, c in cells]
    if code == 2:   # rot-180
        return [(-r, -c) for r, c in cells]
    if code == 3:   # transpose
        return [(c, r) for r, c in cells]
    if code == 4:   # flip-lr
        return [(r, -c) for r, c in cells]
    return [(-r, c) for r, c in cells]   # flip-ud


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _all8(cells):
    # all 8 dihedral images (incl ccw + anti-transpose) for asymmetry test
    base = list(cells)
    imgs = set()
    for op in range(6):
        imgs.add(tuple(_norm(_apply(base, op))))
    imgs.add(tuple(_norm([(-c, r) for r, c in base])))   # ccw
    imgs.add(tuple(_norm([(-c, -r) for r, c in base])))  # anti-transpose
    return imgs


def _asym_no_blank_col(rng, size, maxd):
    for _ in range(120):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) >= maxd or max(c for r, c in n) >= maxd:
            continue
        cols = {c for r, c in n}
        if len(cols) != max(c for r, c in n) + 1:   # has an empty column
            continue
        if len(_all8(n)) == 8:                      # fully D4-asymmetric
            return n
    return list(_FALLBACK_SHAPE)


def _no_blank_col(cells):
    n = _norm(cells)
    cols = {c for r, c in n}
    return len(cols) == max(c for r, c in n) + 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        szr, md = (3, 4), 3
    elif difficulty == "hard":
        szr, md = (4, 6), 4
    else:
        szr, md = (3, 5), 4

    for _attempt in range(40):
        a = _asym_no_blank_col(rng, rng.randint(*szr), md)
        code = rng.choice(_CODES)
        b = _norm(_apply(a, code))
        if not _no_blank_col(b):
            continue
        c = _asym_no_blank_col(rng, rng.randint(*szr), md)
        panels = [a, b, c]
        color = rng.randint(1, 9)

        heights = [max(r for r, cc in p) + 1 for p in panels]
        widths = [max(cc for r, cc in p) + 1 for p in panels]
        gaps = [rng.randint(1, 2), rng.randint(1, 2)]
        total_w = 1 + widths[0] + gaps[0] + widths[1] + gaps[1] + widths[2] + 1
        h = max(heights) + rng.randint(1, 3)
        g = full_grid(h, total_w, 0)
        col = 1
        for i, p in enumerate(panels):
            roff = rng.randint(0, h - heights[i])
            for r, cc in p:
                g[roff + r][col + cc] = color
            col += widths[i] + (gaps[i] if i < 2 else 0)
        return g

    # Deterministic last-resort scene.  This is independent of the rejected
    # candidate loop so an exhausted sampler cannot return an uninitialized grid.
    a = list(_FALLBACK_SHAPE)
    b = _norm(_apply(a, 1))
    c = _norm(_apply(a, 4))
    panels = [a, b, c]
    heights = [max(r for r, _ in p) + 1 for p in panels]
    widths = [max(cc for _, cc in p) + 1 for p in panels]
    g = full_grid(max(heights) + 2, 1 + sum(widths) + 2 + 1, 0)
    col = 1
    for index, panel in enumerate(panels):
        roff = index % 2
        for r, cc in panel:
            g[roff + r][col + cc] = 4
        col += widths[index] + (1 if index < 2 else 0)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 13, 0)
    a = [(0, 0), (1, 0), (1, 1)]
    c = [(0, 0), (0, 1), (1, 1)]

    def place(r, c0, cells, color):
        for dr, dc in cells:
            g[r + dr][c0 + dc] = color

    if name == "identity_transform":
        place(1, 0, a, 4); place(1, 4, a, 4); place(1, 9, c, 4)
        return g
    if name == "A_B_unrelated":
        place(1, 0, a, 4); place(1, 4, [(0, 0), (0, 2), (1, 1)], 4); place(1, 9, c, 4)
        return g
    if name == "missing_panel":
        place(1, 0, a, 4); place(1, 9, c, 4)
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: at least 2 full-height all-zero columns separating 3 panels; panels have nonzero cells."""
    msgs = []
    h, w = len(grid), len(grid[0])
    blank_cols = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    if len(blank_cols) < 2:
        msgs.append(f"expected >=2 blank separator columns, got {len(blank_cols)}")
        return msgs
    # Check that there are nonzero cells (panels have content)
    nz = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nz == 0:
        msgs.append("grid is all-zero (no panel content)")
    return msgs
