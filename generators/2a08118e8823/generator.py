"""Generator for v2_meta_puzzles:H3 — connect 2 motif pairs by line.

Rule: 2 color-3 motifs and 2 color-4 motifs at varied positions; output
draws connecting lines between same-color pairs.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_endpoint, mismatched_pair_counts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2a08118e8823"
VERSION = "3.0.1"
TASK_ID = "2a08118e8823"

SUMMARY = (
    "0-bg grid with exactly ONE matching pair of identical-shape objects (a small "
    "polyomino placed twice, in two DISTINCT colours, aligned either in the same rows "
    "or the same columns with a gap between), plus 1-2 DECOY objects of UNIQUE shapes "
    "in other colours. Rule: find the first pair of objects with identical normalized "
    "shape and paint the straight line between their bounding boxes (the shared "
    "row/column corridor) with COLOUR 8. Decoys (no shape match) are untouched."
)

INVARIANTS = [
    "background is 0",
    "exactly one pair of objects shares a normalized shape (the matched pair)",
    "the matched pair is aligned (same rows or same columns) with a clear gap",
    "any decoy objects have shapes distinct from the pair and each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_endpoint", "mismatched_pair_counts")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_motif_pairs",
                       "valid": "two_motif_pairs"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 distinct non-zero colors (one matched pair + possibly decoys)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_motifs", "single_endpoint", "mismatched_pair_counts"):
        return []
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct non-zero color(s); expected ≥2")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 10, 13); n_decoy = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 13, 18); n_decoy = rng_n(ctx, 1, 2)
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 11, 15); n_decoy = rng_n(ctx, 1, 2)
    rng = ctx.draw_rng("layout")
    pool = [1, 2, 3, 4, 6, 7, 9]                  # colour 8 is reserved for the output line

    for _outer in range(60):
        g = full_grid(h, w, 0)
        M = _norm(_build_motif(rng, rng.randint(2, 4)))
        sh = max(r for r, _ in M) + 1; sw = max(c for _, c in M) + 1
        if sh >= h - 1 or sw >= w - 1:
            continue
        rng.shuffle(pool)
        cA, cB = pool[0], pool[1]
        decoy_colors = pool[2:2 + n_decoy]
        orient = rng.choice(["h", "v"])
        if orient == "h":                         # same rows, gap between -> 8-line at shared row
            r0 = rng.randint(0, h - sh)
            gap = rng.randint(2, 4)
            ca = rng.randint(0, max(0, w - (2 * sw + gap)))
            cb = ca + sw + gap
            if cb + sw > w:
                continue
            _paint(g, M, r0, ca, cA); _paint(g, M, r0, cb, cB)
            box = (r0, ca, r0 + sh - 1, cb + sw - 1)
        else:                                     # same cols, gap -> vertical 8-line
            c0 = rng.randint(0, w - sw)
            gap = rng.randint(2, 4)
            ra = rng.randint(0, max(0, h - (2 * sh + gap)))
            rb = ra + sh + gap
            if rb + sh > h:
                continue
            _paint(g, M, ra, c0, cA); _paint(g, M, rb, c0, cB)
            box = (ra, c0, rb + sh - 1, c0 + sw - 1)
        # reserve the pair's enclosing rectangle (incl. the connection corridor)
        occ = [[False] * w for _ in range(h)]
        for r in range(max(0, box[0] - 1), min(h, box[2] + 2)):
            for c in range(max(0, box[1] - 1), min(w, box[3] + 2)):
                occ[r][c] = True
        # decoys: unique shapes (!= M and != each other), placed clear of the pair
        used_shapes = {tuple(M)}
        ok = True
        for dc in decoy_colors:
            D = None
            for _ in range(30):
                cand = _norm(_build_motif(rng, rng.randint(2, 4)))
                if tuple(cand) not in used_shapes:
                    D = cand; break
            if D is None:
                continue
            dh = max(r for r, _ in D) + 1; dw = max(c for _, c in D) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - dh); c0 = rng.randint(0, w - dw)
                if _box_free(g, occ, r0, c0, dh, dw):
                    _paint(g, D, r0, c0, dc)
                    for r in range(max(0, r0 - 1), min(h, r0 + dh + 1)):
                        for c in range(max(0, c0 - 1), min(w, c0 + dw + 1)):
                            occ[r][c] = True
                    placed = True; break
            if placed:
                used_shapes.add(tuple(D))
        if ok:
            return g
    raise ValueError("could not realize same-shape-pair layout")


def rng_n(ctx, lo, hi):
    return ctx.draw_int("n_decoy", lo, hi)


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _paint(g, cells, r0, c0, color):
    for r, c in cells:
        g[r0 + r][c0 + c] = color


def _box_free(g, occ, r0, c0, dh, dw):
    h, w = len(g), len(g[0])
    for r in range(max(0, r0 - 1), min(h, r0 + dh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + dw + 1)):
            if g[r][c] != 0 or occ[r][c]:
                return False
    return True


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no pairs to connect.
        return g
    if name == "single_endpoint":
        # Each color appears once — rule's "connect pair"
        # precondition fails; lines undefined.
        g[2][2] = 3; g[5][7] = 4
        return g
    if name == "mismatched_pair_counts":
        # 1 color-3 motif and 3 color-4 motifs — rule's "exactly 2
        # of each color" filter rejects; rule's connect branch can't
        # decide which color-4 pair to use.
        g[2][2] = 3
        g[5][5] = 4; g[7][9] = 4; g[2][10] = 4
        return g
    return g
