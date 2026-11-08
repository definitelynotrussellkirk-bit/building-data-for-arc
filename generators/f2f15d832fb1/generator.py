"""Generator for arc_additional_puzzle_bank_volume4:M23 — rotate each object CW in place.

Rule: for each 4-connected object, normalize its cells, rotate them 90 deg CW, and
paint them at the object's original top-left (obj_r1, obj_c1) on a fresh grid in the
object's color. Net: every blob rotates CW, anchored at its top-left.

Prior generator hardcoded exactly 2 blobs at FIXED corners (1,1) and (h-5,w-5),
drawn from only 3 fixed 4x4 patterns. Canonical has 2-3 IRREGULAR blobs (non-square
bboxes) at VARIED positions. This version scatters 2-4 random connected blobs and
reserves a square region per blob (side = max(bbox dims)) so the CW rotation always
lands in-bounds and never overlaps another blob's rotated footprint.

Rule-safe diversity: grid size, blob count, blob shapes/sizes, positions, colors.
Degenerates: no_objects, square_bboxes, touching_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "f2f15d832fb1"
VERSION = "3.0.0"  # varied irregular blobs at scattered positions (was 2 fixed-corner 4x4 patterns)
TASK_ID = "f2f15d832fb1"
SUMMARY = (
    "0-bg grid with 2-4 ISOLATED irregular connected blobs (4-8 cells, often "
    "non-square bbox) in distinct non-0 colors at scattered positions. Each blob "
    "reserves a square region (side = max bbox dim) so its 90 deg CW rotation fits. "
    "Rule: rotate each object's cells CW and paint at its original top-left on a "
    "fresh grid, in its color. Net: every blob rotates CW in place. (Was: 2 fixed "
    "4x4 patterns at fixed corners.)"
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-4 non-touching blobs in distinct non-0 colors",
    "each blob's CW rotation fits in-bounds and does not overlap another blob's footprint",
    "blobs are separate 4-connected components (1-cell buffer)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "square_bboxes", "touching_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":     {"type": "int", "default": "11-12 easy / 11-14 med / 13-17 hard", "valid": "9..18"},
    "grid_w":     {"type": "int", "default": "11-12 easy / 11-14 med / 13-17 hard", "valid": "9..18"},
    "n_objects":  {"type": "int", "default": "2 easy / 2-3 med / 3-4 hard", "valid": "1..5"},
    "blob_size":  {"type": "int", "default": "4-6", "valid": "3..8"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PATTERNS_4x4 = [
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3)],
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (3, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 0), (3, 0), (3, 1), (3, 2)],
]


def _rand_blob(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _sq_free(occ, r0, c0, s, h, w):
    if r0 < 0 or c0 < 0 or r0 + s > h or c0 + s > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + s + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + s + 1)):
            if occ[r][c]:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, nr, szr = (11, 12), (2, 2), (4, 6)
    elif difficulty == "hard":
        hr, nr, szr = (13, 17), (3, 4), (4, 7)
    else:
        hr, nr, szr = (11, 14), (2, 3), (4, 6)
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*hr)
    n = rng.randint(*nr)
    colors = list(range(1, 10)); rng.shuffle(colors)
    g = full_grid(h, w, 0)
    occ = [[False] * w for _ in range(h)]
    placed = 0
    for i in range(n * 8):
        if placed >= n:
            break
        blob = _rand_blob(rng, rng.randint(*szr))
        th = max(r for r, _ in blob) + 1; tw = max(c for _, c in blob) + 1
        s = max(th, tw)                       # square region holds blob + its rotation
        for _ in range(80):
            r0 = rng.randint(0, max(0, h - s)); c0 = rng.randint(0, max(0, w - s))
            if _sq_free(occ, r0, c0, s, h, w):
                paint_at(g, r0, c0, blob, colors[placed])
                for r in range(r0, r0 + s):
                    for c in range(c0, c0 + s):
                        occ[r][c] = True
                placed += 1
                break
    if placed < 2:                            # fallback to two fixed corner patterns
        g = full_grid(max(h, 12), max(w, 12), 0)
        paint_at(g, 1, 1, _PATTERNS_4x4[0], colors[0])
        paint_at(g, len(g) - 5, len(g[0]) - 5, _PATTERNS_4x4[1], colors[1])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_objects":
        return g
    if name == "square_bboxes":
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4; g[2][2] = 4
        g[8][8] = 6; g[8][9] = 6; g[9][8] = 6; g[9][9] = 6
        return g
    if name == "touching_blobs":
        for r, c in _PATTERNS_4x4[0]:
            g[3 + r][3 + c] = 4
        for r, c in _PATTERNS_4x4[1]:
            g[3 + r][7 + c] = 6
        return g
    return g
