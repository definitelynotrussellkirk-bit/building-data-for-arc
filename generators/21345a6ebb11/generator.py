"""Generator for arc_additional_puzzles_21_set9:E63.

Rule: among all non-bg blobs, find the one with the largest size;
output bbox subgrid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, size_spread, texture.
Degenerates: equal_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "21345a6ebb11"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 distinct non-zero colors (blobs); exactly one has the max cell count."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 2:
        errs.append(f"expected >=2 blob colors, got {len(counts)}")
        return errs
    max_count = max(counts.values())
    maxes = [c for c, n in counts.items() if n == max_count]
    if len(maxes) > 1:
        errs.append(f"no unique largest blob: {len(maxes)} blobs share max size {max_count}")
    return errs
TASK_ID = "21345a6ebb11"
SUMMARY = "2-4 blobs of distinct sizes; the largest is unique; output = its bbox crop."

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _orient(cells, code):
    out = cells
    if code & 1: out = [(c, r) for r, c in out]
    if code & 2: out = [(r, -c) for r, c in out]
    if code & 4: out = [(-r, c) for r, c in out]
    return _norm(out)


def _rand_poly(rng, k):
    # random-walk polyomino, normalised + a random dihedral orientation. The output is
    # the largest blob's bbox crop, so varying this shape is what diversifies the output.
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    return _orient(_norm(cells), rng.randint(0, 7))

INVARIANTS = [
    "≥2 disjoint blobs",
    "exactly 1 has the maximum size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("equal_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 10..15", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "big_size":       {"type": "int", "default": "rng 5..9", "valid": "3..11"},
    "n_blobs":        {"type": "int", "default": "rng 1..3 decoys", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "spread_corners",
                       "valid": "spread_corners"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "size_spread":    {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 9, 11)
        big_k = ctx.draw_int("big_size", 4, 6); n_dec = ctx.draw_int("n_blobs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 17); w = ctx.draw_int("grid_w", 12, 18)
        big_k = ctx.draw_int("big_size", 7, 11); n_dec = ctx.draw_int("n_blobs", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 10, 15)
        big_k = ctx.draw_int("big_size", 5, 9); n_dec = ctx.draw_int("n_blobs", 1, 3)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    occ = [[False] * w for _ in range(h)]  # cells blocked from new blobs (placed + 1-ring)

    def fits(cells, top, left):
        for dr, dc in cells:
            r, c = top + dr, left + dc
            if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
                return False
        return True

    def block(cells, top, left):
        for dr, dc in cells:
            r, c = top + dr, left + dc
            for rr in range(max(0, r - 1), min(h, r + 2)):
                for cc in range(max(0, c - 1), min(w, c + 2)):
                    occ[rr][cc] = True

    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], min(8, n_dec + 1))
    # place the unique-largest blob first; output = its bbox crop
    placed_big = False
    for _ in range(60):
        big = _rand_poly(rng, big_k)
        bh = max(r for r, _ in big) + 1; bw = max(c for _, c in big) + 1
        if bh > h or bw > w:
            continue
        top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
        if fits(big, top, left):
            paint_at(g, top, left, big, colors[0]); block(big, top, left)
            placed_big = True; break
    if not placed_big:
        paint_at(g, 0, 0, [(0, 0), (0, 1), (1, 0)], colors[0])
        block([(0, 0), (0, 1), (1, 0)], 0, 0)
    # decoys: each STRICTLY smaller than big so the largest is unique, distinct sizes
    sizes = list(range(1, big_k))
    rng.shuffle(sizes)
    for i in range(n_dec):
        k = sizes[i % len(sizes)]
        for _ in range(40):
            s = _rand_poly(rng, k)
            sh = max(r for r, _ in s) + 1; sw = max(c for _, c in s) + 1
            if sh > h or sw > w:
                continue
            top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
            if fits(s, top, left):
                paint_at(g, top, left, s, colors[(i + 1) % len(colors)]); block(s, top, left)
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    sml = [(0, 0), (1, 0)]
    if name == "equal_sizes":
        # all blobs share one size → "largest" is ambiguous, tie-break needed
        paint_at(g, 1, 1, sml, 3)
        paint_at(g, 1, w - 3, sml, 5)
        paint_at(g, h - 3, w // 2, sml, 7)
        return g
    if name == "single_blob":
        # only 1 blob → "largest" is trivially the only blob, rule reduces to bbox crop
        big = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)]
        paint_at(g, 2, 3, big, 4)
        return g
    if name == "no_blobs":
        # empty grid → no blobs to compare or crop
        return g
    return g
