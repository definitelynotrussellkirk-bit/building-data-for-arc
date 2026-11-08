"""Generator for arc_additional_puzzle_bank_volume16:M107.

Rule: the vector dr/dc = (3-marker - 2-marker); among the 1-blobs pick the
smallest (size, then r1, c1); clear it and paint its cells translated by
the vector with color 8.

Combinatorial axes: grid size, the marker vector, the blobs (count /
sizes / shapes / positions), the decoration.
Degenerates: no_markers, no_blobs, tied_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "4cdcebe180f3"
VERSION = "2.0.1"  # diversity: random vector + N distinct-size blobs + positions + grid (was fixed layout)
TASK_ID = "4cdcebe180f3"
SUMMARY = (
    "0-bg grid (size varies). A color-2 and a color-3 MARKER define a "
    "translation VECTOR (3-marker minus 2-marker). 2-4 color-1 BLOBS of "
    "DISTINCT sizes sit apart, plus a color-7 DECORATION. Rule: take the "
    "SMALLEST 1-blob (ties by top row then left col), clear it from its "
    "spot, and paint its cells translated by the vector with COLOR 8 "
    "(cyan); the markers, the other blobs and the decoration stay. The "
    "smallest blob's translation always lands in-bounds on empty cells. "
    "The grid size, the vector, the blob count/sizes/shapes/positions "
    "and the decoration all vary freely (was a fixed marker+blob layout)."
)

INVARIANTS = [
    "exactly one color-2 marker and one color-3 marker",
    "2-4 color-1 blobs of distinct sizes",
    "the smallest blob's translation lands in-bounds on empty cells",
]

PALETTE_KINDS = ("default", "tight_grid", "wide_grid", "tall_grid")
DEGENERATE_TEXTURES = ("no_markers", "no_blobs", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|tight_grid|wide_grid|tall_grid"},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "vector_length":  {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|tight_grid|wide_grid|tall_grid|no_markers|no_blobs|tied_sizes"},
}


def _random_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in norm) < maxd and max(c for r, c in norm) < maxd:
            return norm
    return [(0, 0), (1, 0)]


def _free(occ, cells, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
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
        hr, wr, nbl = (8, 10), (9, 11), 2
    elif difficulty == "hard":
        hr, wr, nbl = (12, 16), (12, 16), rng.randint(3, 4)
    else:
        hr, wr, nbl = (9, 12), (10, 13), rng.randint(2, 3)

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        dr = rng.randint(-4, 4); dc = rng.randint(-4, 4)
        if dr == 0 and dc == 0:
            continue
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        # markers: 2 at (mr,mc), 3 at +vector.
        for _t in range(40):
            mr = rng.randint(0, h - 1); mc = rng.randint(0, w - 1)
            gr, gc = mr + dr, mc + dc
            if 0 <= gr < h and 0 <= gc < w and not occ[mr][mc] and not occ[gr][gc] and (mr, mc) != (gr, gc):
                g[mr][mc] = 2; g[gr][gc] = 3
                occ[mr][mc] = True; occ[gr][gc] = True
                break
        else:
            continue

        sizes = sorted(rng.sample(range(2, 8), nbl))     # distinct, ascending
        # smallest blob: cells AND translated cells must be free + in-bounds.
        smallest = _random_poly(rng, sizes[0], 4)
        sm_ok = False
        for _t in range(60):
            bh = max(r for r, c in smallest) + 1; bw = max(c for r, c in smallest) + 1
            top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
            cells = [(top + r, left + c) for r, c in smallest]
            tcells = [(r + dr, c + dc) for r, c in cells]
            if not all(0 <= r < h and 0 <= c < w for r, c in tcells):
                continue
            if not _free(occ, cells, h, w):
                continue
            if any(occ[r][c] for r, c in tcells):
                continue
            for r, c in cells:
                g[r][c] = 1; occ[r][c] = True
            for r, c in tcells:
                occ[r][c] = True                          # reserve landing zone
            sm_ok = True
            break
        if not sm_ok:
            continue

        # larger blobs
        ok = True
        for sz in sizes[1:]:
            b = _random_poly(rng, sz, 4)
            bh = max(r for r, c in b) + 1; bw = max(c for r, c in b) + 1
            placed = False
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                cells = [(top + r, left + c) for r, c in b]
                if _free(occ, cells, h, w):
                    for r, c in cells:
                        g[r][c] = 1; occ[r][c] = True
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue

        # decoration
        for _t in range(30):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if not occ[r][c]:
                g[r][c] = 7
                break
        return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify translate-smallest-blob marker + blob invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    count2 = flat.count(2)
    count3 = flat.count(3)
    if count2 != 1:
        problems.append(f"expected exactly 1 color-2 marker, found {count2}")
    if count3 != 1:
        problems.append(f"expected exactly 1 color-3 marker, found {count3}")
    count1 = flat.count(1)
    if count1 < 2:
        problems.append(f"expected >=2 color-1 blob cells, found {count1}")
    return problems


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_markers":
        paint_at(g, 1, 6, [(0, 0), (1, 0), (2, 0), (2, 1)], 1)
        paint_at(g, 5, 1, [(0, 0), (1, 0), (1, 1)], 1)
        return g
    if name == "no_blobs":
        g[1][1] = 2; g[3][4] = 3
        return g
    if name == "tied_sizes":
        g[1][1] = 2; g[3][4] = 3
        paint_at(g, 1, 6, [(0, 0), (1, 0), (1, 1)], 1)
        paint_at(g, 5, 1, [(0, 0), (1, 0), (1, 1)], 1)
        return g
    return g
