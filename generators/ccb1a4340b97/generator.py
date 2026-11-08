"""Generator for arc_puzzle_bank_seventeenth_21_bundle:hard_114 — decode the library strip.

Rule (verified from canonical Racket): the area above the last row is a LIBRARY of
colour-keyed shapes (each connected object, keyed by its colour). The LAST ROW is a
token sequence read as triplets (key-colour, transform-code 1-7, recolour-colour)
separated by 0 gaps (stride 4). Each token looks up the library shape by key,
transforms it, recolours it; the decoded shapes are packed into a gallery row.

The previous body was the generic scatter template; it had no library keyed by
colour and no triplet sequence, so the decode produced nothing (distinct_out=3,
fired=0). This rewrite CONSTRUCTS a colour-keyed library plus a last-row token
sequence referencing those keys.

Axes: grid size, library size/shapes, token count, transform/recolour codes.
Degenerates: empty_sequence, single_token, repeated_token.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ccb1a4340b97"
VERSION = "2.2.0"  # canonical-scale margins (right pad + taller separators; area coverage) on top of the 30-col cap
TASK_ID = "ccb1a4340b97"

SUMMARY = ("A colour-keyed library of shapes above a last-row token sequence of "
           "(key, transform 1-7, recolour) triplets; the rule decodes each token (look up, "
           "transform, recolour) and galleries them. Library, token count and codes vary.")

INVARIANTS = [
    "the area above the last row holds a library of colour-keyed shapes",
    "the last row is triplets (key, transform-code, recolour) separated by 0 gaps (stride 4)",
    "every token's key colour exists in the library",
]

DEGENERATE_TEXTURES = ("empty_sequence", "single_token", "repeated_token")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "n_lib":      {"type": "int", "default": "rng 3..5 library shapes", "valid": "2..6"},
    "n_tokens":   {"type": "int", "default": "2-3 easy / 3-4 hard", "valid": "1..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|empty_sequence|single_token|repeated_token"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; last row has ≤1 non-zero cell in every 4th position (stride-4 triplets)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
    # last row should have values only at col indices 0,1,2, 4,5,6, 8,9,10, ...
    last = grid[h - 1]
    allowed = {base + off for base in range(0, w, 4) for off in (0, 1, 2)}
    bad_cols = [c for c in range(w) if last[c] != 0 and c not in allowed]
    if bad_cols:
        errs.append(f"last-row triplet stride violated at cols {bad_cols[:5]}")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _build_motif(rng, k, s):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if 0 <= nr < s and 0 <= nc < s and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n_lib = ctx.draw_int("n_lib", 3, 3); n_tok = ctx.draw_int("n_tokens", 2, 3); s = 3; sep = ctx.draw_int("sep", 1, 2)
    elif difficulty == "hard":
        n_lib = ctx.draw_int("n_lib", 4, 5); n_tok = ctx.draw_int("n_tokens", 3, 4); s = ctx.draw_int("tile", 4, 5); sep = ctx.draw_int("sep", 2, 5)
    else:
        n_lib = ctx.draw_int("n_lib", 3, 4); n_tok = ctx.draw_int("n_tokens", 2, 3); s = ctx.draw_int("tile", 3, 4); sep = ctx.draw_int("sep", 1, 4)
    rng = ctx.draw_rng("layout")

    # ARC cap: w = n_lib*(s+1)+1 <= 30 (hard n_lib=5, s=5 drew 31 wide)
    while s > 3 and n_lib * (s + 1) + 1 > 30:
        s -= 1
    lib_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_lib)
    shapes = [_build_motif(rng, rng.randint(2, s * 2), s) for _ in range(n_lib)]

    # library occupies rows 0..s-1; `sep` blank separator rows; sequence on last row.
    # Canonical demos carry generous blank margins (area median ~216 vs the old
    # tight packing's <=182) — pad the right edge and allow taller separators.
    lib_w = n_lib * (s + 1)
    seq_w = n_tok * 4
    w = min(30, max(lib_w, seq_w) + rng.randint(1, 6))
    h = s + sep + 1                                # library rows, blank rows, seq row
    g = full_grid(h, w, 0)
    # place library shapes left to right, each in its own colour, spaced
    cx = 0
    for color, cells in zip(lib_colors, shapes):
        for (r, c) in cells:
            g[r][cx + c] = color
        cx += s + 1
    # last row: triplets (key, transform 1-7, recolour) at cols 0,1,2 | 4,5,6 | ...
    for t in range(n_tok):
        base = t * 4
        if base + 2 >= w:
            break
        g[h - 1][base] = rng.choice(lib_colors)        # key
        g[h - 1][base + 1] = rng.randint(1, 7)         # transform code
        g[h - 1][base + 2] = rng.randint(1, 9)         # recolour
    return g


def _draw_from_degenerate(name, rng):
    s = 3
    h = s + 2
    w = 13
    g = full_grid(h, w, 0)
    # a 2-shape library: colour 4 and colour 5
    for (r, c) in [(0, 0), (0, 1), (1, 0)]:
        g[r][c] = 4
    for (r, c) in [(0, 0), (1, 0), (1, 1)]:
        g[r][4 + c] = 5
    if name == "empty_sequence":
        return g                                       # no tokens -> no parts -> [[0]]
    if name == "single_token":
        g[h - 1][0] = 4; g[h - 1][1] = 2; g[h - 1][2] = 6
        return g
    # repeated_token -> same key twice -> two decoded copies
    g[h - 1][0] = 4; g[h - 1][1] = 1; g[h - 1][2] = 6
    g[h - 1][4] = 4; g[h - 1][5] = 3; g[h - 1][6] = 7
    return g
