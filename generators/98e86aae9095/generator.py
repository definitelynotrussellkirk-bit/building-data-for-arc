"""Generator for arc_puzzle_bank_fifteenth_21_bundle:hard_105_select_by_key_and_apply_transform_sequence.

Combinatorial axes (8): grid_h, grid_w, palette_kind, shape, sequence,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_sequence, no_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "98e86aae9095"
VERSION = "2.0.1"  # in_sh=1 / out_sh=3 / dup33%: fixed 8x10 grid + 4-shape + 4-seq banks. Rule selects the key-color object and applies the top-row transform-code sequence. Randomize the key shape (random polyomino), the sequence (random 1..4 codes), and grid size -> output shape/content vary.
TASK_ID = "98e86aae9095"
SUMMARY = "Top row holds a transform-code sequence (codes 1..4); bottom-left cell names the selected object color; the rule crops that object and applies the sequence. Shape, sequence and grid size vary."

INVARIANTS = [
    "top-row nonzero cells are transform sequence codes in 1..4",
    "the bottom-left cell gives the selected object color",
    "there is one largest component of the selected color",
    "other nonzero components use different colors and are ignored",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_sequence", "no_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8", "valid": "8..13"},
    "grid_w":         {"type": "int", "default": "10", "valid": "10..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "shape":          {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "sequence":       {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "header_seq_plus_keyed_shape",
                       "valid": "header_seq_plus_keyed_shape"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]
_SEQS = [
    [1, 2],
    [2, 3],
    [4, 1, 2],
    [3, 2, 4],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, r0, c0, sh, sw):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def _place_clear(g, rng, shape, color, top_min):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    h, w = len(g), len(g[0])
    for _ in range(120):
        r0 = rng.randint(top_min, h - sh); c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, sh, sw):
            _paint(g, r0, c0, shape, color)
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: top row has ≥1 nonzero cell in 1..4 (transform code); bottom-left cell is nonzero (key)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    top_codes = [v for v in grid[0] if v in (1, 2, 3, 4)]
    if not top_codes:
        errs.append("top row has no transform code cells in {1,2,3,4}")
    key = grid[h - 1][0]
    if key == 0:
        errs.append("bottom-left cell is 0 (expected nonzero key color)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 10, 11)
        k_lo, k_hi, seq_len = 4, 5, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 12, 14)
        k_lo, k_hi, seq_len = 5, 8, 3
    else:
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13)
        k_lo, k_hi, seq_len = 4, 7, rng.randint(2, 3)
    key = rng.choice([5, 6, 7, 8, 9])
    other = rng.choice([c for c in [2, 3, 4, 5, 6, 7, 8, 9] if c != key])
    # Random transform-code sequence (codes 1..4 = id/cw/180/ccw) in the top row.
    seq = [rng.randint(1, 4) for _ in range(min(seq_len, w))]
    g = full_grid(h, w, 0)
    for c, code in enumerate(seq):
        g[0][c] = code
    # Bottom-left key marker (names the selection) placed FIRST so the shapes'
    # 1-cell clearance keeps them off it; the rule zeros it before selecting.
    g[h - 1][0] = key
    # Random key-color shape (the selected object) + a distractor object, both
    # below the header row.
    _place_clear(g, rng, _rand_poly(rng, rng.randint(k_lo, k_hi)), key, 2)
    _place_clear(g, rng, _rand_poly(rng, rng.randint(2, 4)), other, 2)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "no_key":
        # transform sequence + shape but no bottom-left key → no selection color
        for c, code in enumerate(_SEQS[0]):
            g[0][c] = code
        _paint(g, 2, 2, _SHAPES[0], 5)
        _paint(g, 5, 7, [(0, 0), (1, 0)], 6)
        return g
    if name == "no_sequence":
        # key + shape but no transform sequence → no operation defined
        _paint(g, 2, 2, _SHAPES[0], 5)
        _paint(g, 5, 7, [(0, 0), (1, 0)], 6)
        g[7][0] = 5
        return g
    if name == "no_shape":
        # sequence + key but no shape of key color → nothing to transform
        for c, code in enumerate(_SEQS[0]):
            g[0][c] = code
        _paint(g, 5, 7, [(0, 0), (1, 0)], 6)
        g[7][0] = 5
        return g
    return g
