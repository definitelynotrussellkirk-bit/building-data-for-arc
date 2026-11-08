"""Generator for arc_puzzle_bank_tenth_21_bundle:hard_70_decode_local_frame_template_codes.

Each color->=7 rectangular frame contains a TEMPLATE drawn in a selector
color, and two code cells in its bottom interior row: the selector color
(at c0+1) and a transform code (at c0+2, in {3,4,5,6} -> identity / rot-cw
/ rot-180 / flip-lr). The rule extracts the selector-colored template,
applies the transform, recolors it to the FRAME color, and horizontally
stacks all frames' parts (sorted by position), centered, with a 1-cell gap.

Combinatorial axes: grid size, the number of frames, each frame's size,
template shape, selector color, transform code, frame color and position.
Degenerates: no_frames, no_codes, no_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "ee602abaa45a"
VERSION = "2.0.0"  # diversity: random N frames / sizes / templates / sel / tf / colors / positions (was 2 fixed frames ~16)
TASK_ID = "ee602abaa45a"
SUMMARY = (
    "0-bg grid (size varies). 2-4 color->=7 FRAMES, each holding a template "
    "in a selector color plus two bottom-row code cells (selector + transform "
    "code 3/4/5/6 = identity/rot-cw/rot-180/flip-lr). Rule: extract each "
    "frame's selector template, transform it by its code, recolor to the "
    "frame color, and h-stack all parts centered with a 1-gap. The grid size, "
    "frame count/sizes/positions, template shapes, selector colors, transform "
    "codes and frame colors all vary freely (was two fixed frames, ~16 "
    "distinct)."
)

INVARIANTS = [
    "each frame is a color->=7 rectangular border with a selector template inside",
    "each frame's bottom interior row holds the selector color (c0+1) and code (c0+2)",
    "selector and code colors are < 7 so they are not mistaken for frames",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_codes", "no_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..26"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "2..4"},
    "code_a":         {"type": "int", "default": "varies", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "frames_apart", "valid": "frames_apart"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_codes|no_template"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size, hmax, wmax):
    for _ in range(30):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice(_CARD)
            cells.add((r + dr, c + dc))
        nl = _norm(cells)
        if max(r for r, c in nl) + 1 <= hmax and max(c for r, c in nl) + 1 <= wmax:
            return nl
    return [(0, 0)]


def _reserve(occ, top, left, bh, bw, h, w, margin=1):
    for r in range(top - margin, top + bh + margin):
        for c in range(left - margin, left + bw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nr, rtr, ctr = (8, 10), (12, 16), (2, 2), (1, 2), (2, 3)
    elif difficulty == "hard":
        hr, wr, nr, rtr, ctr = (12, 18), (18, 26), (3, 4), (2, 3), (2, 4)
    else:
        hr, wr, nr, rtr, ctr = (9, 13), (14, 20), (2, 3), (1, 3), (2, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        for _ in range(rng.randint(*nr)):
            R_t = rng.randint(*rtr); C_t = rng.randint(*ctr)
            fh = R_t + 3; fw = C_t + 2          # frame outer dims
            if fh > h or fw > w:
                continue
            for _t in range(30):
                top = rng.randint(0, h - fh); left = rng.randint(0, w - fw)
                if not _reserve(occ, top, left, fh, fw, h, w, margin=1):
                    continue
                r0, c0, r1, c1 = top, left, top + fh - 1, left + fw - 1
                fcolor = rng.choice([7, 8, 9])
                sel = rng.choice([1, 2, 3, 4, 5, 6])
                tf = rng.choice([3, 4, 5, 6])
                draw_frame(g, r0, c0, r1, c1, fcolor)
                shape = _poly(rng, rng.randint(1, max(1, R_t * C_t)), R_t, C_t)
                sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
                otop = (r0 + 1) + rng.randint(0, R_t - sh)
                oleft = (c0 + 1) + rng.randint(0, C_t - sw)
                for (r, c) in shape:
                    g[otop + r][oleft + c] = sel
                g[r1 - 1][c0 + 1] = sel          # selector code cell
                g[r1 - 1][c0 + 2] = tf           # transform code cell
                placed += 1
                break
        if placed >= 2:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 15, 0)
    pat = [(0, 0), (1, 0), (1, 1)]
    if name == "no_frames":
        for dr, dc in pat:
            g[2 + dr][2 + dc] = 2
        g[5][2] = 2; g[5][3] = 4
        return g
    if name == "no_codes":
        draw_frame(g, 1, 1, 6, 6, 7)
        draw_frame(g, 1, 8, 6, 13, 8)
        for dr, dc in pat:
            g[2 + dr][2 + dc] = 2
            g[2 + dr][9 + dc] = 3
        return g
    if name == "no_template":
        draw_frame(g, 1, 1, 6, 6, 7)
        draw_frame(g, 1, 8, 6, 13, 8)
        g[5][2] = 2; g[5][3] = 4
        g[5][9] = 3; g[5][10] = 5
        return g
    return g
