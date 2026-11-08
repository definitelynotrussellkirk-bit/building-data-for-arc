"""Generator for 16b:m107 — transform and recolor object by corner codes.

Rule: cell (0,0) holds a transform code; cell (0, w-1) holds a target
color. The single body shape is cropped, transformed per code, and
recolored to the target color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_code, no_target_color, symmetric_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e62829d062fa"
VERSION = "3.0.0"  # rule supports codes 1..7 (1=id,2=cw,3=180,4=ccw,5=flip-lr,6=flip-ud,7=transpose) but gen only emitted 1..5 -> codes 6,7 (flip-ud, transpose) never exercised; only 4 fixed shapes -> dup-outputs 44%. Now: codes 1..7 by difficulty + random asymmetric polyomino body (4..6 cells) -> full branch coverage + diverse output shapes (transpose makes non-square crops)
TASK_ID = "e62829d062fa"
SUMMARY = (
    "0-bg grid (h~8-10, w~"
    "9-11) with: (a) "
    "TRANSFORM CODE at "
    "(0, 0) in COLOR ∈ "
    "{1, 2, 3, 4, 5} "
    "encoding rotation/"
    "flip (1=IDENTITY, "
    "2=ROT CW, 3=ROT "
    "180, 4=ROT CCW, "
    "5=FLIP LR or "
    "similar); (b) TARGET "
    "COLOR at (0, w-1) in "
    "some non-{0, code, "
    "body_color} color "
    "(the destination "
    "color for the "
    "transformed body); "
    "(c) BODY SHAPE — one "
    "ASYMMETRIC SHAPE "
    "from a small bank "
    "(L-tetromino, T-"
    "tetromino, S-"
    "tetromino) in a "
    "DISTINCT non-{0, "
    "code, target} color "
    "at random interior "
    "position. Rule "
    "(CROP THE BODY "
    "SHAPE, TRANSFORM "
    "PER CODE, RECOLOR "
    "TO TARGET COLOR): "
    "READ the CODE from "
    "(0, 0) and TARGET "
    "COLOR from (0, w-1)"
    ". CROP the body "
    "shape to its BBOX. "
    "APPLY the transform "
    "encoded by CODE. "
    "RECOLOR all "
    "non-bg cells in "
    "the transformed "
    "crop to TARGET "
    "COLOR. OUTPUT is "
    "the transformed "
    "+ recolored body. "
    "Code, target, and "
    "original body are "
    "discarded. Net: the "
    "body is rotated/"
    "flipped per code "
    "and painted in the "
    "target color."
)

INVARIANTS = [
    "background is 0",
    "cell (0,0) is a transform code (1-5)",
    "cell (0, w-1) is the target color",
    "exactly one multi-cell shape in the body, asymmetric, in some 3rd color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_code", "no_target_color", "symmetric_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "two_corner_codes_with_body",
                       "valid": "two_corner_codes_with_body"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_ASYM_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
]


def _rand_poly(rng, k):
    """Random connected polyomino of k cells, normalized to (0,0) origin."""
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        code = rng.randint(1, 4); k = rng.randint(4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        code = rng.randint(1, 7); k = rng.randint(5, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        code = rng.randint(1, 7); k = rng.randint(4, 6)
    g = full_grid(h, w, 0)
    target_color, body_color = rng.sample([3, 4, 6, 7, 8, 9], 2)
    g[0][0] = code
    g[0][w - 1] = target_color
    shape = _rand_poly(rng, k)            # random asymmetric body
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(1, h - sh); c0 = rng.randint(1, w - sw - 1)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = body_color
        break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_code":
        # Body + target color but (0,0) empty — rule's transform
        # code lookup fails.
        g[0][w - 1] = 7
        for r, c in [(3, 3), (4, 3), (5, 3), (5, 4)]: g[r][c] = 4
        return g
    if name == "no_target_color":
        # Code + body but (0, w-1) empty — rule's recolor target
        # is undefined.
        g[0][0] = 2
        for r, c in [(3, 3), (4, 3), (5, 3), (5, 4)]: g[r][c] = 4
        return g
    if name == "symmetric_shape":
        # Body shape symmetric — every transform code yields the
        # same shape; rule's transform branch is invisible (only
        # recolor effect remains).
        g[0][0] = 2
        g[0][w - 1] = 7
        for r, c in [(3, 3), (3, 4), (4, 3), (4, 4)]: g[r][c] = 4
        return g
    return g
