"""Generator for arc_additional_puzzle_bank_volume8:M50.

Rule: v = position(first blue 1) - position(first red 2). Take the
largest color-4 blob and paint an 8-colored copy of it translated by v
onto the existing grid (in-bounds cells only). The original blob and
the two markers stay.

Combinatorial axes: grid size, the 4-shape, the translation vector (via
the red/blue marker positions), and the placements.
Degenerates: no_blob, no_markers, markers_collide.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "6ffe98f1ccad"
VERSION = "3.0.1"  # diversity: random shape + vector + markers + size (was fixed shape/markers ~13)
TASK_ID = "6ffe98f1ccad"
SUMMARY = (
    "0-bg grid (size varies). One color-4 (yellow) connected BLOB, one "
    "color-2 (red) marker and one color-1 (blue) marker; the vector v = "
    "blue - red. Rule: translate the blob by v and paint the copy in "
    "color-8 (cyan) onto the grid. The copy region is reserved in-bounds "
    "and disjoint from the blob, so the cyan ghost is clean. The grid size, "
    "the blob shape, the vector and all placements vary freely (was a fixed "
    "blob with fixed markers, ~13 distinct)."
)

INVARIANTS = [
    "exactly one color-2 cell, one color-1 cell, one color-4 blob",
    "the translated copy lands fully in-bounds and disjoint from the blob",
    "the vector blue-red is non-zero",
]

PALETTE_KINDS = ("default", "small_blob", "wide_offset", "diagonal_offset")
DEGENERATE_TEXTURES = ("no_blob", "no_markers", "markers_collide")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|small_blob|wide_offset|diagonal_offset"},
    "marker_offset":  {"type": "str", "default": "varies", "valid": "varies"},
    "blob_size":      {"type": "int", "default": "varies", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "blob_plus_vector_plus_copy",
                       "valid": "blob_plus_vector_plus_copy"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|small_blob|wide_offset|diagonal_offset|"
                                "no_blob|no_markers|markers_collide"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _place_cluster(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one color-1, one color-2, some color-4 cells; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    blues = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    yellows = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if len(blues) != 1:
        errs.append(f"expected exactly 1 blue(1) marker, found {len(blues)}")
    if len(reds) != 1:
        errs.append(f"expected exactly 1 red(2) marker, found {len(reds)}")
    if not yellows:
        errs.append("no yellow(4) blob cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, sr = (12, 14), (12, 14), (3, 4)
    elif difficulty == "hard":
        hr, wr, sr = (16, 22), (16, 24), (4, 6)
    else:
        hr, wr, sr = (13, 18), (13, 18), (3, 5)

    for _attempt in range(50):
        shape = _poly(rng, rng.randint(*sr))
        th = max(r for r, c in shape) + 1; tw = max(c for r, c in shape) + 1

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        # place the blob (color 4)
        bt = rng.randint(0, h - th); bl = rng.randint(0, w - tw)
        blob = [(bt + r, bl + c) for r, c in shape]
        if not _place_cluster(occ, blob, h, w):
            continue
        paint_at(g, bt, bl, shape, 4)

        # choose a disjoint in-bounds copy placement; v = copy_origin - blob_origin
        v = None
        for _t in range(60):
            ct = rng.randint(0, h - th); cl = rng.randint(0, w - tw)
            copy = [(ct + r, cl + c) for r, c in shape]
            if _place_cluster(occ, copy, h, w):
                v = (ct - bt, cl - bl)        # copy cells stay 0 (rule paints 8)
                break
        if v is None or v == (0, 0):
            continue

        # place red + blue markers encoding v (blue = red + v)
        placed_m = False
        for _t in range(80):
            pr = (rng.randint(0, h - 1), rng.randint(0, w - 1))
            pb = (pr[0] + v[0], pr[1] + v[1])
            if not (0 <= pb[0] < h and 0 <= pb[1] < w):
                continue
            if pr == pb:
                continue
            if _place_cluster(occ, [pr], h, w) and _place_cluster(occ, [pb], h, w):
                g[pr[0]][pr[1]] = 2
                g[pb[0]][pb[1]] = 1
                placed_m = True
                break
        if placed_m:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    blob = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 0)]
    if name == "no_blob":
        g[h // 2][2] = 2
        g[h // 2 - 2][5] = 1
        return g
    if name == "no_markers":
        paint_at(g, h - 4, 0, blob, 4)
        return g
    if name == "markers_collide":
        paint_at(g, h - 4, 0, blob, 4)
        g[h // 2][3] = 1            # 1 and 2 at same cell → zero vector
        g[h // 2][3] = 2
        return g
    return g
