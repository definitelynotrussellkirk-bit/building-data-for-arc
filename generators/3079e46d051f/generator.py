"""Generator for arc_puzzle_bank_21_set6_s:S6_H6 — most-common-shape canonical.

Rule: among connected motifs (all in color 6), find the most-common canonical
shape and output it in color 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_distinct.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3079e46d051f"
VERSION = "3.1.0"  # ensure minority motif is not rotation-equivalent to majority; distinct=3: majority color-6 shape came from a fixed 5-shape bank -> output (the majority shape recolored to 2) had 3 values. Now RANDOM majority shape (3-6 cells) + random minority.
TASK_ID = "3079e46d051f"

SUMMARY = (
    "0-bg grid (h~7-9, w~12-15) with 3-4 small "
    "CONNECTED MOTIFS, all in COLOR 6, "
    "scattered at non-overlapping positions. "
    "The MAJORITY (n-1) of motifs share the "
    "SAME normalized shape; one motif may have "
    "a different shape (odd-one-out). Rule: "
    "identify each color-6 connected motif. "
    "NORMALIZE each motif's shape. FIND the "
    "MODE shape (canonical normalized shape "
    "appearing most). Output: that "
    "MOST-COMMON SHAPE in COLOR 2 (red) — the "
    "bbox-cropped subgrid. Net: input is "
    "magenta motifs; output is the mode "
    "shape recolored to red."
)

INVARIANTS = [
    "background is 0",
    "3-4 connected color-6 motifs (each size 2-4)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_distinct")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "scattered_color6_motifs",
                       "valid": "scattered_color6_motifs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1)],
]

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _rotate_norm(cells):
    cells = _norm(cells)
    maxr = max(r for r, _ in cells)
    return _norm([(c, maxr - r) for r, c in cells])


def _canon_rot(cells):
    outs = []
    cur = _norm(cells)
    for _ in range(4):
        outs.append(tuple(sorted(cur)))
        cur = _rotate_norm(cur)
    return min(outs)


def _rand_shape(rng, k):
    """Random connected polyomino (k cells), normalized to the origin."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 14, 17)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 12, 15)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        # output = the MOST COMMON color-6 shape (rotation-canonical) recolored to 2.
        # majority was a fixed 5-shape bank (distinct=3); a RANDOM majority varies it.
        majority_shape = _rand_shape(rng, rng.randint(4, 8))
        majority_canon = _canon_rot(majority_shape)
        minority_shape = None
        for _minority_try in range(40):
            cand = _rand_shape(rng, rng.randint(2, 7))
            if _canon_rot(cand) != majority_canon:
                minority_shape = cand
                break
        if minority_shape is None:
            continue
        ok = True
        for i in range(n):
            shape = majority_shape if i < (n - 1) else minority_shape
            rs = [r for r, _ in shape]; cs = [c for _, c in shape]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in shape:
                    g[r0 + r][c0 + c] = 6
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 8, 13
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no shapes to count.
        return g
    if name == "single_motif":
        # Only one color-6 motif — rule's mode-of-shape is
        # trivially that motif.
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 6
        return g
    if name == "all_distinct":
        # 3 motifs, each a different shape — no mode (all
        # frequencies = 1); rule's "most common" tie-break
        # ambiguous.
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 6
        for r, c in [(1, 5), (1, 6), (1, 7)]: g[r][c] = 6
        for r, c in [(5, 9), (5, 10)]: g[r][c] = 6
        return g
    return g



def _components6(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 6 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 6:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    if any(v not in (0, 6) for row in grid for v in row):
        errs.append("default input should contain only color-6 motifs on background 0")
    comps = _components6(grid)
    if len(comps) < 3:
        errs.append(f"expected at least 3 color-6 motifs, saw {len(comps)}")
        return errs
    counts = {}
    for cells in comps:
        counts[_canon_rot(cells)] = counts.get(_canon_rot(cells), 0) + 1
    max_count = max(counts.values())
    if max_count < 2:
        errs.append("no majority shape appears more than once")
    if sum(1 for v in counts.values() if v == max_count) != 1:
        errs.append("majority shape is tied or ambiguous")
    if len(counts) < 2:
        errs.append("minority motif is rotation-equivalent to the majority")
    return errs
