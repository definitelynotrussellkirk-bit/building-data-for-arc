"""Generator for arc_additional_puzzle_bank_volume8:H53.

Rule: among the color-7 blobs, find the one whose normalized cells are
diagonal- (transpose-) symmetric, and paint its 1-cell Manhattan ring
(empty cells at distance exactly 1) with color 8.

Combinatorial axes: grid size, the symmetric shape, the non-symmetric
distractor shapes, and all positions.
Degenerates: all_symmetric, no_symmetric, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "1c5dad6c3a74"
VERSION = "3.0.1"  # diversity: random symmetric blob + non-sym distractors + grid (was 2 fixed shapes)
TASK_ID = "1c5dad6c3a74"
SUMMARY = (
    "0-bg grid (size varies). Several COLOR-7 blobs: exactly ONE is "
    "DIAGONAL-SYMMETRIC (its normalized cell set is invariant under the "
    "transpose (r,c)->(c,r)), the rest are NOT. Rule: find the "
    "diagonal-symmetric 7-blob and paint its 1-CELL MANHATTAN RING (every "
    "empty cell at Manhattan distance exactly 1 from the blob) with COLOR "
    "8 (cyan); the blobs themselves and the non-symmetric distractors "
    "stay color 7. The grid size, the symmetric shape, the distractor "
    "shapes and all positions vary freely (was 2 fixed shapes + small "
    "grid variation)."
)

INVARIANTS = [
    "exactly one diagonal-symmetric color-7 blob",
    "one or more non-symmetric color-7 distractor blobs",
    "blobs are separated so the symmetric blob's ring is clear",
]

PALETTE_KINDS = ("default", "tri_top_left", "tri_top_right", "wide_grid")
DEGENERATE_TEXTURES = ("all_symmetric", "no_symmetric", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|tri_top_left|tri_top_right|wide_grid"},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "sym_diversity":  {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|tri_top_left|tri_top_right|wide_grid|all_symmetric|no_symmetric|no_blobs"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _diag_sym(cells):
    s = _norm(cells)
    t = _norm([(c, r) for r, c in cells])
    return s == t


def _connected(cells):
    cs = set(cells); st = [next(iter(cs))]; seen = {st[0]}
    while st:
        r, c = st.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in cs and (r + dr, c + dc) not in seen:
                seen.add((r + dr, c + dc)); st.append((r + dr, c + dc))
    return len(seen) == len(cs)


def _random_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return list(n)
    return [(0, 0), (1, 0), (1, 1)]


def _diag_sym_poly(rng, maxd):
    """Connected, diagonal-symmetric, NOT a single cell or full square."""
    for _ in range(200):
        base = _random_poly(rng, rng.randint(2, 5), maxd)
        cells = set(base) | set((c, r) for r, c in base)
        cells = list(_norm(cells))
        if 3 <= len(cells) and _connected(cells) and _diag_sym(cells):
            return cells
    return [(0, 0), (0, 1), (1, 0)]   # L-tromino (diag-symmetric)


def _free(occ, cells, top, left, h, w, ring):
    for r, c in cells:
        for dr in range(-ring, ring + 1):
            for dc in range(-ring, ring + 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nd = (10, 12), (11, 13), (1, 1)
    elif difficulty == "hard":
        hr, wr, nd = (13, 18), (13, 18), (2, 3)
    else:
        hr, wr, nd = (11, 14), (12, 15), (1, 2)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _place(cells, ring):
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _free(occ, cells, top, left, h, w, ring):
                    for r, c in cells:
                        g[top + r][left + c] = 7
                    for r in range(top - ring, top + bh + ring):
                        for c in range(left - ring, left + bw + ring):
                            if 0 <= r < h and 0 <= c < w:
                                occ[r][c] = True
                    return True
            return False

        # The diagonal-symmetric blob (ring=2 so its 1-cell ring stays clear).
        if not _place(_diag_sym_poly(rng, 4), 2):
            continue
        # Non-symmetric distractors.
        nplaced = 0
        for _ in range(rng.randint(*nd)):
            for _t in range(20):
                d = _random_poly(rng, rng.randint(3, 5), 4)
                if not _diag_sym(d):
                    if _place(d, 1):
                        nplaced += 1
                    break
        if nplaced >= 1:
            return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 color-7 blob cells (the symmetric target + distractor blobs)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    c7 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 7)
    if c7 < 2:
        errs.append(f"expected >=2 color-7 blob cells, found {c7}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    triangle = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)]
    nonsym = [(0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
    if name == "all_symmetric":
        paint_at(g, 1, 6, triangle, 7); paint_at(g, h - 5, 0, triangle, 7)
        return g
    if name == "no_symmetric":
        paint_at(g, 1, 6, nonsym, 7); paint_at(g, h - 5, 0, nonsym, 7)
        return g
    if name == "no_blobs":
        return g
    return g
