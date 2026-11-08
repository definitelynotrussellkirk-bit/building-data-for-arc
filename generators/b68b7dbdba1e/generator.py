"""Generator for arc_puzzle_bank_21_set7:hard_g20 — token-driven transform gallery.

Rule (verified from canonical): the BOTTOM ROW holds TOKEN cells of colors
{1,2,3,4} at various columns; the FIELD is everything above the bottom row
(and excluding the last column). Every 4-connected non-bg component in the
field is cropped to its bbox, then TRANSFORMED by the key of the token whose
column is NEAREST its horizontal center (1=rotate-cw, 2=rotate-180,
3=flip-lr, 4=transpose). Components are packed left-to-right into a small
gallery (center-aligned, 1-cell gap). So the discriminator is the
token-column -> transform-key mapping, which MUST vary across instances and
across motifs within one instance.

Combinatorial axes (8): grid_h, grid_w, n_motifs, palette_kind, token_keys,
motif_size, motif_asym, position_bias.
Degenerates: no_tokens, single_motif, all_identity.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b68b7dbdba1e"
VERSION = "3.1.0"  # 2.0.0 had NO token row (colors 1-4) -> rule's transform
# branch (keys 1-4) never exercised, all motifs went through identity, and
# docstring described a wrong "vertical color pack". 3.0.0 places a real
# bottom token row + non-token-colored motifs so every transform key fires.
TASK_ID = "b68b7dbdba1e"

SUMMARY = (
    "0-bg grid (h=4, w=7-8, canonical-sized). The BOTTOM "
    "ROW carries TOKEN cells of colors {1,2,3,4} "
    "at scattered columns (each token = a "
    "transform KEY: 1=rotate-cw, 2=rotate-180, "
    "3=flip-lr, 4=transpose). Above the bottom "
    "row (the FIELD, last column excluded) sit "
    "N_MOTIFS = 2 small 4-connected blobs in "
    "DISTINCT colors drawn from {5,6,7,8,9} (NOT "
    "the token colors), each grown by random "
    "adjacency walk and placed with an 8-conn "
    "1-cell buffer. Tokens are placed so each "
    "motif's nearest token varies (keys differ "
    "across motifs). Rule: extract every "
    "4-connected field component, crop to bbox, "
    "TRANSFORM by the key of the NEAREST bottom "
    "token (by horizontal center), then PACK the "
    "transformed crops left-to-right into a small "
    "center-aligned gallery with 1-cell gaps."
)

INVARIANTS = [
    "background is 0",
    "the bottom row holds >=1 token of color in {1,2,3,4}",
    "field motifs use colors in {5,6,7,8,9}, disjoint from token colors",
    "each motif is a distinct 4-connected component in a distinct color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_tokens", "single_motif", "all_identity")
HELPFUL_TEXTURES = PALETTE_KINDS

TOKEN_COLORS = (1, 2, 3, 4)
FIELD_COLORS = (5, 6, 7, 8, 9)

# Canonical train instances are compact 4-row grids with two small upper-field
# components and two bottom-row transform tokens. Keep the generator on that
# manifold instead of scaling into large multi-motif galleries.
_CANONICAL_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
)

AXES = {
    "grid_h":         {"type": "int", "default": "4", "valid": "4..4"},
    "grid_w":         {"type": "int", "default": "rng 7..8", "valid": "7..8"},
    "n_motifs":       {"type": "int", "default": "2", "valid": "2..2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "token_keys":     {"type": "str", "default": "varied per motif",
                       "valid": "varied"},
    "motif_size":     {"type": "int", "default": "3", "valid": "3..3"},
    "motif_asym":     {"type": "bool", "default": "varied", "valid": "true|false"},
    "position_bias":  {"type": "str", "default": "scattered_field_motifs",
                       "valid": "scattered_field_motifs"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_tokens|single_motif|all_identity"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: field rows use only {0,5..9}; bottom row uses only {0,1..4}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h < 2:
        return []
    errs = []
    for r in range(h - 1):
        for c in range(w):
            v = grid[r][c]
            if v not in (0, 5, 6, 7, 8, 9):
                errs.append(f"field cell ({r},{c})={v} not in {{0,5..9}}")
    for c in range(w):
        v = grid[h - 1][c]
        if v not in (0, 1, 2, 3, 4):
            errs.append(f"bottom row col {c}={v} not in {{0,1..4}}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # Match the canonical support: 3 field rows + 1 token row, width 7 or 8,
    # exactly two motifs. The previous 7..14-row/2..5-motif widening was a
    # different gallery distribution and triggered the drift gate.
    h = ctx.draw_int("grid_h", 4, 4)
    w = ctx.draw_int("grid_w", 7, 8)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    colors = rng.sample(list(FIELD_COLORS), 2)
    shapes = rng.sample(list(_CANONICAL_SHAPES), 2)
    placements = [
        (rng.randint(0, 1), rng.randint(0, 1)),
        (rng.randint(0, 1), w - 3),
    ]
    centers = []
    for color, shape, (top, left) in zip(colors, shapes, placements):
        for dr, dc in shape:
            g[top + dr][left + dc] = color
        centers.append(2 * left + 1)  # all canonical shapes have width 2

    keys = _varied_keys(rng, 2)
    used_cols = set()
    for center2, key in zip(centers, keys):
        target_c = min(w - 1, max(0, round(center2 / 2)))
        tc = _nearest_free_col(target_c, used_cols, w)
        if tc is None:
            raise ValueError("could not place token")
        g[h - 1][tc] = key
        used_cols.add(tc)
    return g


def _varied_keys(rng, n):
    """Pick n token keys (1..4) maximizing variety; never all identical."""
    base = list(TOKEN_COLORS)
    rng.shuffle(base)
    if n <= len(base):
        return base[:n]
    keys = base[:]
    while len(keys) < n:
        keys.append(rng.choice(TOKEN_COLORS))
    rng.shuffle(keys)
    return keys


def _nearest_free_col(target, used, w):
    for off in range(w):
        for cand in (target + off, target - off):
            if 0 <= cand < w and cand not in used:
                return cand
    return None


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_tokens":
        # No bottom tokens — rule has no transform key to apply.
        for r, c in [(2, 2), (2, 3), (3, 3)]:
            g[r][c] = 6
        return g
    if name == "single_motif":
        # Only 1 field motif + 1 token — trivial single-cell gallery.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]:
            g[r][c] = 7
        g[h - 1][3] = 1
        return g
    if name == "all_identity":
        # All tokens are key 5 (else branch -> identity); but key must be
        # in {1,2,3,4} to be a token, so use the no-effect identity via key 2
        # twice on symmetric motifs.
        for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            g[r][c] = 5
        for r, c in [(1, 6), (1, 7), (2, 6), (2, 7)]:
            g[r][c] = 8
        g[h - 1][1] = 2
        g[h - 1][6] = 2
        return g
    return g
