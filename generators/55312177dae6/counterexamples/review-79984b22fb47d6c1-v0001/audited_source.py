"""Generator for arc_puzzle_bank_21_set5_s:S5_H4.

Rule: among the color-1 components, find the canonical rotational form
that appears >=2 times (a shape and its rotation), output that canonical
shape painted cyan, cropped to its bbox.

Combinatorial axes: grid size, the shared shape (and which rotation), the
distractor shapes, and all positions.
Degenerates: no_match, all_same, no_distractor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "55312177dae6"
VERSION = "3.0.1"
TASK_ID = "55312177dae6"
SUMMARY = (
    "0-bg grid (size varies), all components color 1. TWO components "
    "share the same NORMALIZED ROTATIONAL form (one is a rotation of the "
    "other); the remaining DISTRACTOR components each have a different "
    "canonical form. Rule: for each color-1 component compute its "
    "canonical rotation (normalize, take the lex-min of its 4 rotations); "
    "find the canonical form that appears >=2 times and output that shape "
    "painted COLOR 8 (cyan), cropped to its bbox. The grid size, the "
    "shared shape (and its rotation), the distractors and all positions "
    "vary freely (was a fixed 8x10 grid with 8 hardcoded families)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "all components are color 1",
    "exactly one canonical rotational form appears in 2 components",
    "the other (distractor) components have different canonical forms",
    "components are isolated (8-conn separated)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_match", "all_same", "no_distractor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "family":         {"type": "int", "default": "n/a (random shapes)", "valid": "0..7"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "rotation_pair_plus_distractor",
                       "valid": "rotation_pair_plus_distractor"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_match|all_same|no_distractor"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _rot(cells):
    h = max(r for r, c in cells) + 1
    return _norm([(c, h - 1 - r) for r, c in cells])


def _canonical(cells):
    forms = []
    cur = _norm(cells)
    for _ in range(4):
        forms.append(cur)
        cur = _rot(cur)
    return min(forms)


def _random_poly(rng, size, maxd):
    for _ in range(200):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return list(n)
    return [(0, 0), (1, 0), (1, 1)]


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


def _place(g, occ, rng, cells, h, w):
    bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
    for _ in range(40):
        top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
        if _free(occ, cells, top, left, h, w):
            for r, c in cells:
                g[top + r][left + c] = 1
                occ[top + r][left + c] = True
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; all non-bg cells are color 1; ≥2 components present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not non_bg:
        return errors  # degenerate (no_match) — allowed
    wrong = [grid[r][c] for r, c in non_bg if grid[r][c] != 1]
    if wrong:
        errors.append(f"all non-bg cells must be color 1, found: {set(wrong)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    # larger shapes -> many more distinct canonical-rotation forms (the old
    # 3-6 cell / 4x4-bbox shapes gave only ~24 distinct outputs).
    if difficulty == "easy":
        hr, wr, szr, ndist, md = (8, 11), (10, 13), (3, 5), (1, 1), 4
    elif difficulty == "hard":
        hr, wr, szr, ndist, md = (13, 20), (14, 22), (6, 10), (2, 3), 6
    else:
        hr, wr, szr, ndist, md = (10, 15), (11, 17), (4, 8), (1, 2), 5

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        shared = _random_poly(rng, rng.randint(*szr), md)
        shared_canon = _canonical(shared)
        # A rotation of the shared shape (prefer one that visibly differs).
        rotated = _norm(shared)
        for _ in range(rng.randint(1, 3)):
            rotated = _rot(rotated)
        rotated = list(rotated)

        if not _place(g, occ, rng, list(shared), h, w):
            continue
        if not _place(g, occ, rng, rotated, h, w):
            continue

        used = {shared_canon}
        ok = True
        for _ in range(rng.randint(*ndist)):
            placed = False
            for _t in range(20):
                d = _random_poly(rng, rng.randint(*szr), md)
                if _canonical(d) not in used:
                    if _place(g, occ, rng, d, h, w):
                        used.add(_canonical(d)); placed = True
                    break
            if not placed:
                ok = False
                break
        if ok:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    f0 = [(0, 0), (1, 0), (1, 1)]
    f1 = [(0, 0), (0, 1), (1, 1), (2, 1)]
    dd = [(0, 0), (0, 1), (0, 2)]
    def paint(top, left, cells):
        for r, c in cells:
            g[top + r][left + c] = 1
    if name == "no_match":
        paint(1, 1, f0); paint(1, 6, f1); paint(5, 5, dd)
        return g
    if name == "all_same":
        paint(1, 1, f0); paint(1, 6, f0); paint(5, 5, f0)
        return g
    if name == "no_distractor":
        paint(1, 1, f0); paint(1, 6, list(_rot(f0)))
        return g
    return g
