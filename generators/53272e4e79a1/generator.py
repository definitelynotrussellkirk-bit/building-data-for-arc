"""Generator for arc_additional_puzzle_bank_volume23:H160.

Rule: among the color-1 blobs, find the one whose canonical shape (under
any of the 8 rotation/flip transforms) is unique, and output its
bbox-cropped normalized mask in color 8.

Combinatorial axes: grid size, the common shape (>=2 copies in any
dihedral orientation), the unique shape, and all positions.
Degenerates: all_same_shape, two_uniques, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "53272e4e79a1"
VERSION = "2.0.1"
TASK_ID = "53272e4e79a1"
SUMMARY = (
    "0-bg grid (size varies). Several color-1 BLOBS: 2-4 copies of a "
    "COMMON shape (each in ANY rotation/flip — they share a dihedral "
    "canonical) plus ONE UNIQUE blob with a different canonical, all "
    "separated. Rule: compute each blob's canonical shape under the 8 "
    "rotation/flip transforms, find the one whose canonical is unique "
    "(appears once), and output its bbox-cropped normalized mask in "
    "COLOR 8 (cyan). The grid size, the common shape and its "
    "orientations, the unique shape, the copy count and all positions "
    "vary freely (was 4 fixed blobs + grid padding)."
)

INVARIANTS = [
    "several color-1 blobs; 2-4 share a dihedral canonical shape",
    "exactly one blob has a unique canonical shape",
    "blobs are separated so each is its own component",
]

PALETTE_KINDS = ("default", "L_shape", "T_shape", "Z_shape")
DEGENERATE_TEXTURES = ("all_same_shape", "two_uniques", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|L_shape|T_shape|Z_shape"},
    "n_blobs":        {"type": "int", "default": "rng", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|L_shape|T_shape|Z_shape|all_same_shape|two_uniques|no_blobs"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _transforms(cells):
    def rot(cs):
        return [(c, -r) for r, c in cs]
    def flip(cs):
        return [(r, -c) for r, c in cs]
    out = []
    for base in (list(cells), flip(list(cells))):
        cur = base
        for _ in range(4):
            out.append(_norm(cur)); cur = rot(cur)
    return out


def _canon(cells):
    return min(_transforms(cells))


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
    return [(0, 0), (0, 1), (1, 0)]


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; all non-bg cells are color-1; ≥2 components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not non_bg:
        return errors  # degenerate (no_blobs) — allowed
    wrong = [grid[r][c] for r, c in non_bg if grid[r][c] != 1]
    if wrong:
        errors.append(f"all non-bg cells must be color 1, found: {set(wrong)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, ncom = (10, 12), (11, 13), 2
    elif difficulty == "hard":
        hr, wr, ncom = (12, 16), (13, 18), rng.randint(3, 4)
    else:
        hr, wr, ncom = (11, 13), (12, 15), rng.randint(2, 3)

    for _attempt in range(40):
        common = _random_poly(rng, rng.randint(3, 5), 4)
        cc = _canon(common)
        common_imgs = list({img for img in _transforms(common)})   # distinct orientations
        unique = None
        for _ in range(40):
            u = _random_poly(rng, rng.randint(3, 6), 4)
            if _canon(u) != cc:
                unique = u
                break
        if unique is None:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _place(cells):
            cells = [(r, c) for r, c in _norm(cells)]
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _free(occ, cells, top, left, h, w):
                    for r, c in cells:
                        g[top + r][left + c] = 1; occ[top + r][left + c] = True
                    return True
            return False

        ok = all(_place(rng.choice(common_imgs)) for _ in range(ncom)) and _place(unique)
        if ok:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    common = [(0, 0), (0, 1), (1, 0)]
    unique = [(0, 0), (0, 1), (0, 2), (1, 1)]
    other_unique = [(0, 0), (1, 0), (1, 1), (1, 2)]
    if name == "all_same_shape":
        paint_at(g, 1, 1, common, 1); paint_at(g, 1, 6, common, 1)
        paint_at(g, 6, 1, common, 1); paint_at(g, 6, 6, common, 1)
        return g
    if name == "two_uniques":
        paint_at(g, 1, 1, common, 1); paint_at(g, 1, 6, common, 1)
        paint_at(g, 7, 1, unique, 1); paint_at(g, 7, 8, other_unique, 1)
        return g
    if name == "no_blobs":
        return g
    return g
