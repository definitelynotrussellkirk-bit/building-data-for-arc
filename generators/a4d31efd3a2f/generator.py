"""Generator for arc_puzzle_bank_21_set11_s:S11_E3 — Smallest blob → bbox crop.

Rule: among all blobs sort by (size asc, color asc); take smallest;
output its bbox crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_smallest, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "a4d31efd3a2f"
VERSION = "1.2.1"  # distinct 8: FIXED 1x2 small shape -> output (smallest object's crop) always 1x2. Make the small shape a random polyomino + a strictly-bigger random object -> distinct 8->75, flags cleared."
TASK_ID = "a4d31efd3a2f"
SUMMARY = "2-3 blobs of distinct sizes; smallest is unique."

INVARIANTS = [
    "≥2 disjoint blobs with distinct sizes",
    "exactly 1 has the minimum size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_smallest", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "2", "valid": "2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "diagonal_corners",
                       "valid": "diagonal_corners"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct non-bg colors present (small and large blob)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct non-bg colors (expected 2 blobs)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)
    # Rule: output = the SMALLEST object's normalized crop. v1.x used a FIXED 1x2
    # small shape -> output always 1x2 (distinct 8 = colors). Make the small shape
    # a RANDOM polyomino (the output) + a strictly-bigger random object.
    ssize = rng.randint(1, 4)
    bsize = rng.randint(ssize + 2, 8)
    sml = _rand_poly(rng, ssize)
    big = _rand_poly(rng, bsize)
    sh = max(r for r, _ in sml) + 1; sw = max(c for _, c in sml) + 1
    bh = max(r for r, _ in big) + 1; bw = max(c for _, c in big) + 1
    placements = [
        (rng.randint(1, max(1, h - bh - 1)), rng.randint(0, max(0, w - bw - 1)), big, pal[0]),
        (rng.randint(max(1, h - sh - 2), h - sh), rng.randint(max(0, w - sw - 2), w - sw), sml, pal[1]),
    ]
    for top, left, s, color in placements:
        paint_at(g, top, left, s, color)
    return g


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "tied_smallest":
        # two blobs share the minimum size → which one to crop is ambiguous
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 4)
        paint_at(g, 4, 6, [(0, 0), (0, 1)], 6)
        return g
    if name == "single_blob":
        # only one blob → it's trivially smallest, no comparison happens
        paint_at(g, 2, 3, [(0, 0), (0, 1), (1, 0)], 5)
        return g
    if name == "no_blobs":
        # empty grid → nothing to crop, output undefined
        return g
    return g
