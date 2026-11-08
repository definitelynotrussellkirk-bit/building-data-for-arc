"""Generator for v3_rich_schema:hard_03_dual_key_select_and_recolor.

Rule: a singleton shape key (1=L-triomino, 4=plus) and a singleton color
key (2/6/8) select which green family to recolor to the key color.

Combinatorial axes: grid size, the keys, the number / orientation /
position of the L's, pluses and decoy green shapes.
Degenerates: no_shape_key, no_color_key, no_matching_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f151fbd31cb2"
VERSION = "2.1.0"  # drop decoy green shapes (canonical has only L's + pluses; decoys were rule-ignored + canonical-absent)
TASK_ID = "f151fbd31cb2"
SUMMARY = (
    "0-bg grid (size varies). Several GREEN (color-3) objects, ONLY "
    "L-triominoes (any of 4 orientations) and plus-pentominoes (>=1 of "
    "each). A singleton SHAPE KEY marker (color 1 = L family, 4 = plus "
    "family) and a singleton COLOR KEY marker (2/6/8) sit at random free "
    "cells. Rule: read both keys (each the unique cell of its color) and "
    "recolor every green object of the SELECTED family to the color key; "
    "the other family stays green. Grid size, both keys, and the count / "
    "orientation / position of every shape vary. (Was: also added decoy "
    "green shapes the rule ignores and canonical lacks.)"
)

INVARIANTS = [
    "one singleton shape key is either 1 for L-triominoes or 4 for plus-shapes",
    "one singleton color key is one of 2,6,8",
    "green objects include at least one L-triomino and one plus-shape",
    "only the selected family is recolored to the color key",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shape_key", "no_color_key", "no_matching_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "shape_key":      {"type": "enum", "default": "rng", "valid": "1|4"},
    "color_key":      {"type": "enum", "default": "rng", "valid": "2|6|8"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "two_keys_with_two_shape_families",
                       "valid": "two_keys_with_two_shape_families"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shape_key|no_color_key|no_matching_shape"},
}

_SHAPE_KEYS = [1, 4]
_COLOR_KEYS = [2, 6, 8]
_L_ORIENTS = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 1), (1, 0), (1, 1)],
]
_PLUS = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
_DECOYS = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],   # 2x2 square
    [(0, 0), (0, 1), (0, 2)],           # I-triomino (horizontal)
    [(0, 0), (1, 0), (2, 0)],           # I-triomino (vertical)
    [(0, 0), (0, 1)],                   # domino
]


def _paint(g, top, left, cells, color=3):
    for r, c in cells:
        g[top + r][left + c] = color


def _free(g, cells, top, left):
    H = len(g); W = len(g[0])
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < H and 0 <= cc < W):
                        return False
                    continue
                if 0 <= rr < H and 0 <= cc < W and g[rr][cc] != 0:
                    return False
    return True


def _try_place(g, rng, cells, color):
    H = len(g); W = len(g[0])
    bh = max(r for r, c in cells) + 1
    bw = max(c for r, c in cells) + 1
    for _ in range(40):
        top = rng.randint(0, H - bh); left = rng.randint(0, W - bw)
        if _free(g, cells, top, left):
            _paint(g, top, left, cells, color)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nl, npl = (10, 11), (12, 14), (1, 2), (1, 1)
    elif difficulty == "hard":
        hr, wr, nl, npl = (14, 18), (15, 20), (2, 4), (2, 3)
    else:
        hr, wr, nl, npl = (11, 14), (13, 16), (1, 3), (1, 2)

    shape_key = rng.choice(_SHAPE_KEYS)
    color_key = rng.choice(_COLOR_KEYS)

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        n_l = max(1, rng.randint(*nl))
        n_p = max(1, rng.randint(*npl))
        ok = True
        for _ in range(n_l):
            ok &= _try_place(g, rng, rng.choice(_L_ORIENTS), 3)
        for _ in range(n_p):
            ok &= _try_place(g, rng, _PLUS, 3)
        if not ok:
            continue
        # Two singleton key markers in free cells.
        if not (_try_place(g, rng, [(0, 0)], shape_key) and
                _try_place(g, rng, [(0, 0)], color_key)):
            continue
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_shape_key":
        g[9][11] = 6
        _paint(g, 2, 2, _L_ORIENTS[0]); _paint(g, 5, 2, _L_ORIENTS[2]); _paint(g, 2, 8, _PLUS)
        return g
    if name == "no_color_key":
        g[0][0] = 1
        _paint(g, 2, 2, _L_ORIENTS[0]); _paint(g, 5, 2, _L_ORIENTS[2]); _paint(g, 2, 8, _PLUS)
        return g
    if name == "no_matching_shape":
        g[0][0] = 4; g[9][11] = 6
        _paint(g, 2, 2, _L_ORIENTS[0]); _paint(g, 5, 2, _L_ORIENTS[2]); _paint(g, 2, 8, _L_ORIENTS[0])
        return g
    return g
