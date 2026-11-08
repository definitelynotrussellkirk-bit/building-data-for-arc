"""Generator for arc_additional_puzzles_21_set6:H38.

Rule: the two color-4 blobs, sorted by left column (a then b), define a
translation vector (b.r1 - a.r1, b.c1 - a.c1). Translate the color-3
blob by that vector and paint it on a fresh grid.

Combinatorial axes: grid size, the two color-4 blobs (positions, hence
the vector), and the color-3 blob (shape + position).
Degenerates: no_4blobs, no_3blob, single_4blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "99a2a1384e22"
VERSION = "3.0.1"  # diversity: random 4-blob vector + 3-blob shape/pos + grid (was fixed ~11)
TASK_ID = "99a2a1384e22"
SUMMARY = (
    "0-bg grid (size varies) with TWO color-4 (yellow) BLOBS (a left of "
    "b) defining a translation VECTOR (b.bbox_topleft - a.bbox_topleft, "
    "with the column delta > 0), and ONE color-3 (green) BLOB. Rule: "
    "translate the green blob by that vector and paint it on a fresh "
    "grid. The green blob is placed so its translation lands fully "
    "in-bounds. The grid size, the two yellow blobs' positions (hence the "
    "vector), and the green blob's shape/position all vary freely (was "
    "fixed diagonal blobs, ~11 distinct)."
)

INVARIANTS = [
    "exactly 2 non-touching color-4 blobs with distinct left columns (a left of b)",
    "exactly 1 color-3 blob, disjoint from the 4-blobs",
    "the 3-blob translated by (b-a) lands fully in-bounds",
]

PALETTE_KINDS = ("default", "small_delta", "medium_delta", "large_delta")
DEGENERATE_TEXTURES = ("no_4blobs", "no_3blob", "single_4blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|small_delta|medium_delta|large_delta"},
    "delta_dr":       {"type": "int", "default": "varies", "valid": "-6..6"},
    "delta_dc":       {"type": "int", "default": "varies", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "split", "valid": "split"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "shape_kind":     {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|small_delta|medium_delta|large_delta|"
                                "no_4blobs|no_3blob|single_4blob"},
}


def _conn_poly(rng, size, maxd):
    for _ in range(60):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        n = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (1, 1)]


def _free(occ, cells, h, w):
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    if (rr, cc) not in set(cells):
                        return False
    return all(0 <= r < h and 0 <= c < w and not occ[r][c] for r, c in cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 2 color-4 components; exactly 1 color-3 component."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])

    def count_comps(color):
        seen = set(); n = 0
        for r0 in range(h):
            for c0 in range(w):
                if (r0, c0) in seen or grid[r0][c0] != color:
                    continue
                stack = [(r0, c0)]; seen.add((r0, c0))
                while stack:
                    r, c = stack.pop()
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                            seen.add((nr, nc)); stack.append((nr, nc))
                n += 1
        return n

    errs = []
    c4 = count_comps(4)
    c3 = count_comps(3)
    if c4 != 2:
        errs.append(f"expected exactly 2 color-4 components; found {c4}")
    if c3 != 1:
        errs.append(f"expected exactly 1 color-3 component; found {c3}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, qr, md = (11, 13), (12, 13), (2, 3), 3
    elif difficulty == "hard":
        hr, wr, qr, md = (13, 16), (14, 18), (3, 5), 4
    else:
        hr, wr, qr, md = (11, 15), (12, 16), (2, 4), 4

    for _attempt in range(50):
        h = rng.randint(*hr); w = rng.randint(*wr)
        dr = rng.randint(-(h // 2), h // 2)
        dc = rng.randint(1, max(1, w // 2))   # b is right of a
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        # two color-4 marker blobs: a at (ar,ac), b at (ar+dr, ac+dc)
        a4 = _conn_poly(rng, rng.randint(1, 2) + 1, 2)
        ah = max(r for r, c in a4) + 1; aw = max(c for r, c in a4) + 1
        placed = False
        for _t in range(40):
            ar = rng.randint(max(0, -dr), min(h - ah, h - ah - dr))
            ac = rng.randint(0, w - aw - dc) if w - aw - dc >= 0 else -1
            if ac < 0:
                break
            acells = [(ar + r, ac + c) for r, c in a4]
            bcells = [(ar + dr + r, ac + dc + c) for r, c in a4]
            if all(0 <= r < h and 0 <= c < w for r, c in acells + bcells) and \
               _free(occ, acells, h, w):
                for r, c in acells:
                    g[r][c] = 4; occ[r][c] = True
                if not _free(occ, bcells, h, w):
                    # undo a, retry
                    for r, c in acells:
                        g[r][c] = 0; occ[r][c] = False
                    continue
                for r, c in bcells:
                    g[r][c] = 4; occ[r][c] = True
                placed = True
                break
        if not placed:
            continue

        # color-3 query blob, placed so its translate is in-bounds
        q = _conn_poly(rng, rng.randint(*qr), md)
        qh = max(r for r, c in q) + 1; qw = max(c for r, c in q) + 1
        rlo = max(0, -dr); rhi = min(h - qh, h - qh - dr)
        clo = max(0, -dc); chi = min(w - qw, w - qw - dc)
        if rlo > rhi or clo > chi:
            continue
        qplaced = False
        for _t in range(40):
            qt = rng.randint(rlo, rhi); ql = rng.randint(clo, chi)
            qcells = [(qt + r, ql + c) for r, c in q]
            if _free(occ, qcells, h, w):
                for r, c in qcells:
                    g[r][c] = 3; occ[r][c] = True
                qplaced = True
                break
        if qplaced:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    s = [(0, 0), (1, 1)]
    if name == "no_4blobs":
        paint_at(g, 7, 1, s, 3)
        return g
    if name == "no_3blob":
        paint_at(g, 1, 1, s, 4)
        paint_at(g, 4, 4, s, 4)
        return g
    if name == "single_4blob":
        paint_at(g, 1, 1, s, 4)
        paint_at(g, 7, 1, s, 3)
        return g
    return g
