"""Generator for arc_additional_puzzles_21_set21_bundle:H142.

Rule: three panels separated by blank zero-columns. Crop each. Infer the
dihedral transform code k (1-7: id / rot-cw / rot-180 / rot-ccw /
flip-lr / flip-ud / transpose) such that crop(apply(A,k)) == B, then
output crop(apply(C,k)).

Combinatorial axes: the shape A (and the chosen transform, which sets
B), the shape C, the panel positions, and the color.
Degenerates: identity_transform, A_B_unrelated, missing_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99e7ba062bec"
VERSION = "3.0.1"  # diversity: random asymmetric A/C + transform + positions + color (was fixed ~9)
TASK_ID = "99e7ba062bec"
SUMMARY = (
    "0-bg grid (size varies) with THREE PANELS separated by blank "
    "zero-columns, all one color. Panel A is a random D4-ASYMMETRIC shape "
    "(so the transform is unique); panel B is A under a chosen detectable "
    "transform (code 1-7: id / rot-cw / rot-180 / rot-ccw / flip-lr / "
    "flip-ud / transpose — NOT anti-transpose); panel C is another "
    "asymmetric shape. Rule: infer the A->B transform and output it "
    "applied to C (cropped). Each panel has no internal blank column so "
    "the split is clean. The shapes, transform, positions and color all "
    "vary freely (was a fixed 6x13 layout, ~9 distinct)."
)

INVARIANTS = [
    "three panels separated by >=1 blank zero-column, each a single content band",
    "panel A is D4-asymmetric so exactly one transform code maps A->B",
    "the transform is one of the 7 detectable codes (not anti-transpose)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_transform", "A_B_unrelated", "missing_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "5..10"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "command":        {"type": "str", "default": "varies", "valid": "rot|flip"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "three_panels", "valid": "three_panels"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "identity_transform|A_B_unrelated|missing_panel"},
}

_CODES = (2, 3, 4, 5, 6, 7)  # detectable non-identity transforms


def _apply(cells, code):
    # cells = list of (r,c); return transformed list (un-normalized)
    if code == 1:
        return list(cells)
    if code == 2:   # rot-cw: (r,c) -> (c, -r)
        return [(c, -r) for r, c in cells]
    if code == 3:   # 180: (-r,-c)
        return [(-r, -c) for r, c in cells]
    if code == 4:   # rot-ccw: (-c, r)
        return [(-c, r) for r, c in cells]
    if code == 5:   # flip-lr: (r,-c)
        return [(r, -c) for r, c in cells]
    if code == 6:   # flip-ud: (-r,c)
        return [(-r, c) for r, c in cells]
    return [(c, r) for r, c in cells]   # transpose


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _asym_no_blank_col(rng, size, maxd):
    """A connected polyomino, D4-asymmetric, with no empty bbox column."""
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
        if len(cols) != max(c for r, c in n) + 1:   # an empty column exists
            continue
        if len({tuple(_norm(_apply(n, k))) for k in range(1, 8)}) == 7:  # asymmetric
            return n
    return [(0, 0), (1, 0), (1, 1)]


def _no_blank_col(cells):
    n = _norm(cells)
    cols = {c for r, c in n}
    return len(cols) == max(c for r, c in n) + 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 all-zero columns (separators) exist in the interior."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    zero_cols = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    if len(zero_cols) < 2:
        return [f"expected >=2 all-zero separator columns; found {len(zero_cols)}: {zero_cols}"]
    return []


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

        # lay out the three panels left-to-right with blank-col gaps
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

    return g   # fallback (rare)


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
        place(1, 0, a, 4); place(1, 4, a, 4)
        return g
    return g
