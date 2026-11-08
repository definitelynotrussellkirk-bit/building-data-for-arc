"""Generator for arc_puzzle_bank_21_set13_s:S13_M7.

Rule: split the grid into 3 vertical panels by full color-5 columns. For
each panel, the signature is the SORTED multiset of its objects' hole
counts (enclosed empty regions). Two panels share a signature and one is
different; the output is a 1x3 grid with 8 at the odd panel's index.

This generator builds 3 panels where two realize a common hole-count
signature and one realizes a different one, using 0-, 1- and 2-hole
shape primitives.

Combinatorial axes: grid height, panel widths, the common/odd signatures,
the odd index, the object shapes/sizes/colors and positions.
Degenerates: no_dividers, all_same, all_distinct.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ec92cd82c85"
VERSION = "2.1.0"  # robustness: reject >30-col layouts in the retry loop (hard 3*11+2=35)
TASK_ID = "1ec92cd82c85"
SUMMARY = (
    "0-bg grid (size varies). Three vertical PANELS separated by full "
    "color-5 columns; each panel holds objects whose enclosed HOLE counts "
    "form a sorted signature. Two panels share a signature and one differs. "
    "Rule: output a 1x3 grid with 8 at the ODD panel's index. The grid "
    "height, panel widths, the signatures, odd index, object "
    "shapes/sizes/colors and positions all vary freely (was a fixed layout, "
    "~16 distinct)."
)

INVARIANTS = [
    "three vertical panels separated by full color-5 columns",
    "two panels have equal sorted hole-count signatures; one is different",
    "each object is a single-color connected shape with a definite hole count",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "all_same", "all_distinct")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "20..30"},
    "odd_index":      {"type": "int", "default": "varies", "valid": "0..2"},
    "objects_per_panel": {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "three_panels", "valid": "three_panels"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "1..6"},
    "density":        {"type": "str", "default": "objects", "valid": "objects"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_dividers|all_same|all_distinct"},
}

_OBJ_COLORS = [1, 2, 3, 4, 6, 7, 8, 9]   # non-{0,5}


def _solid(rng):
    hh = rng.randint(2, 3); ww = rng.randint(2, 3)
    return [(r, c) for r in range(hh) for c in range(ww)]


def _hollow(rng):
    hh = rng.randint(3, 4); ww = rng.randint(3, 4)
    return [(r, c) for r in range(hh) for c in range(ww)
            if r in (0, hh - 1) or c in (0, ww - 1)]


def _divider(rng):
    hh = rng.randint(3, 4); ww = rng.choice([5, 7])
    mid = ww // 2
    return [(r, c) for r in range(hh) for c in range(ww)
            if r in (0, hh - 1) or c in (0, ww - 1, mid)]


_SHAPES = {0: _solid, 1: _hollow, 2: _divider}


def _bbox(cells):
    rs = [r for r, c in cells]; cs = [c for r, c in cells]
    return max(rs) + 1, max(cs) + 1


def _reserve(occ, cells, h, w):
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


def _diff_sig(rng, base, k):
    for _ in range(40):
        cand = sorted(rng.randint(0, 2) for _ in range(k))
        if cand != base:
            return cand
    return sorted([(base[0] + 1) % 3] + base[1:])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        Hr, Wr, kr = (9, 12), (7, 9), (1, 2)
    elif difficulty == "hard":
        Hr, Wr, kr = (12, 16), (8, 11), (2, 3)
    else:
        Hr, Wr, kr = (10, 14), (7, 10), (1, 3)

    for _attempt in range(40):
        H = rng.randint(*Hr)
        widths = [rng.randint(*Wr) for _ in range(3)]
        W = sum(widths) + 2
        if W > 30 or H > 30:        # must fit the 30x30 canvas; redraw if not
            continue
        g = full_grid(H, W, 0)
        occ = [[False] * W for _ in range(H)]

        # column ranges per panel + separators
        starts = []
        acc = 0
        for i in range(3):
            starts.append(acc); acc += widths[i] + 1
        sep_cols = [starts[1] - 1, starts[2] - 1]
        for sc in sep_cols:
            for r in range(H):
                g[r][sc] = 5

        k = rng.randint(*kr)
        common = sorted(rng.randint(0, 2) for _ in range(k))
        odd = _diff_sig(rng, common, k)
        odd_index = rng.randint(0, 2)
        sigs = [odd if i == odd_index else common for i in range(3)]

        ok = True
        for i in range(3):
            cs, ce = starts[i], starts[i] + widths[i] - 1
            for hole in sigs[i]:
                shape = _SHAPES[hole](rng)
                oh, ow = _bbox(shape)
                color = rng.choice(_OBJ_COLORS)
                done = False
                for _t in range(40):
                    if H - oh < 0 or ce - ow + 1 < cs:
                        break
                    top = rng.randint(0, H - oh); left = rng.randint(cs, ce - ow + 1)
                    cells = [(top + r, left + c) for r, c in shape]
                    if _reserve(occ, cells, H, W):
                        for (r, c) in cells:
                            g[r][c] = color
                        done = True
                        break
                if not done:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    H, W = 9, 17
    g = full_grid(H, W, 0)
    for r in range(H):
        g[r][5] = 5; g[r][11] = 5

    def hollow(top, left):
        for r in range(3):
            for c in range(3):
                if r in (0, 2) or c in (0, 2):
                    g[top + r][left + c] = 2

    if name == "no_dividers":
        g2 = full_grid(H, W, 0)   # no color-5 separators -> single panel
        for r in range(3):
            for c in range(3):
                if r in (0, 2) or c in (0, 2):
                    g2[1 + r][1 + c] = 2
        return g2
    if name == "all_same":
        hollow(1, 1); hollow(1, 7); hollow(1, 13)
        return g
    if name == "all_distinct":
        # solid, hollow, divider -> all different -> no unique-by-count? actually all unique
        g[1][1] = 2; g[1][2] = 2; g[2][1] = 2; g[2][2] = 2
        hollow(1, 7)
        for r in range(3):
            for c in range(5):
                if r in (0, 2) or c in (0, 2, 4):
                    g[1 + r][13 + c] = 2
        return g
    return g
